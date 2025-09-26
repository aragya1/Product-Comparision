# agents.py
"""
Agents for discovery, retrieval, processing, comparison, and output.
Connectors are imported from connectors.py
"""
import json
import math
import asyncio
from datetime import datetime
from typing import List, Optional, Callable, Any

from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import UserMessage
from autogen_core.tools import FunctionTool
from pydantic import ValidationError

import prompts

from model import get_gemini_client
# Schemas
from schemas import (
    DiscoveryOutput,
    RawProductSchema,
    RetrievalResultSchema,
    ProcessedProductSchema,
    ProcessingResultSchema,
    ComparisonSchema,
    ComparisonRow,
    FinalOutputSchema,
)

# Connectors
from connectors import (
    google_search,
    serpapi_amazon_search,
    ddg_fallback_search,
    fetch_images_google,
) 

# --------------------------------------------------------------------
# DiscoveryAgent
# --------------------------------------------------------------------
class DiscoveryAgent:
    def __init__(self, system_prompt: Optional[str] = None):
        self.client = get_gemini_client(response_format = DiscoveryOutput)
        google_search_tool = FunctionTool(google_search, description="Google Search", strict = True)

        self.agent = AssistantAgent(
                name="discovery_agent",
                model_client= self.client,
                system_message= prompts.DISCOVERY_SYSTEM,
                tools = [google_search_tool],
                output_content_type_format= DiscoveryOutput,
                reflect_on_tool_use=True,
            )
        

    async def classify(self, keyword: str) -> DiscoveryOutput:
        msg = prompts.discovery_user_prompt(keyword)
        out = await self.agent.run(task=msg)
        return out


# --------------------------------------------------------------------
# RetrievalAgent
# --------------------------------------------------------------------
class RetrievalAgent:
    def __init__(self, system_prompt: Optional[str] = None, connectors: Optional[List[Callable]] = None):
        self.client = get_gemini_client()
        self.agent = AssistantAgent(
            name="retrieval_agent",
            model_client=self.client,
            system_message=system_prompt or prompts.RETRIEVAL_SYSTEM,
        )
        self.connectors = connectors or [serpapi_amazon_search, ddg_fallback_search]

    async def run(self, keyword: str, domain: str = "physical_product", limit_per_connector: int = 5) -> RetrievalResultSchema:
        all_items = []
        for connector in self.connectors:
            try:
                items = connector(keyword, limit_per_connector)
                if items:
                    all_items.extend(items)
            except Exception as e:
                print(f"[RetrievalAgent] {connector.__name__} failed: {e}")
                continue
        print(self.connectors)
        normalized: List[RawProductSchema] = []
        for it in all_items:
            try:
                rp = RawProductSchema(
                    product_id=str(it.get("product_id") or it.get("url") or it.get("title")),
                    title=it.get("title") or "",
                    url=it.get("url"),
                    price=it.get("price"),
                    currency=it.get("currency"),
                    rating=it.get("rating"),
                    review_count=(len(it.get("reviews")) if it.get("reviews") else None),
                    source=it.get("source"),
                    raw_description=it.get("description"),
                    metadata=it.get("metadata") or {},
                    raw=it.get("raw") or it,
                    image_url=it.get("image_url"),
                )
                if not rp.image_url:
                    imgs = fetch_images_google(rp.title, num=2)
                    if imgs:
                        rp.image_url = imgs[0]
                normalized.append(rp)
            except Exception as e:
                print(f"[RetrievalAgent] Normalization failed: {e}")
                continue

        return RetrievalResultSchema(
            keyword=keyword,
            domain=domain,
            products=normalized,
            total_found=len(normalized),
        )


# # --------------------------------------------------------------------
# # ProcessingAgent
# # --------------------------------------------------------------------
class ProcessingAgent:
    def __init__(self, system_prompt: Optional[str] = None):
        self.client = get_gemini_client()
        self.agent = AssistantAgent(
            name="processing_agent",
            model_client=self.client,
            system_message=system_prompt or prompts.PROCESSING_SYSTEM,
        )

    async def analyze_product(self, raw: RawProductSchema, domain: str = "") -> ProcessedProductSchema:
        raw_json = raw.model_dump()
        prompt_text = prompts.processing_single_prompt(json.dumps(raw_json), domain)
        msg = UserMessage(content=prompt_text, source="user")
        return await run_with_schema(self.agent, msg, ProcessedProductSchema)

    async def run(self, retrieval_result: RetrievalResultSchema) -> ProcessingResultSchema:
        tasks = [self.analyze_product(r, retrieval_result.domain) for r in retrieval_result.products]
        processed_list = await asyncio.gather(*tasks) if tasks else []
        return ProcessingResultSchema(
            keyword=retrieval_result.keyword,
            domain=retrieval_result.domain,
            processed=list(processed_list),
        )


# # --------------------------------------------------------------------
# # ComparisonAgent
# # --------------------------------------------------------------------
def _simple_score_from_processed(p: ProcessedProductSchema) -> float:
    rating = (p.rating or 0) / 5.0
    rv = p.review_count or p.extra.get("review_count", 0) if p.extra else 0
    weight = 1 + math.log1p(rv) / 10.0
    return round(rating * weight, 4)


class ComparisonAgent:
    def __init__(self, system_prompt: Optional[str] = None):
        self.client = get_gemini_client()
        self.agent = AssistantAgent(
            name="comparison_agent",
            model_client=self.client,
            system_message=system_prompt or prompts.COMPARISON_SYSTEM,
        )

    async def run(self, processing_result: ProcessingResultSchema) -> ComparisonSchema:
        rows = [
            ComparisonRow(
                product_id=p.product_id or p.title[:50],
                title=p.title,
                price=p.price,
                currency=p.currency,
                rating=p.rating,
                review_count=p.review_count,
                pros=p.pros,
                cons=p.cons,
                summary=p.summary,
                url=p.url,
                source=p.source,
                score=_simple_score_from_processed(p),
                extra=p.extra,
            )
            for p in processing_result.processed
        ]
        rows_sorted = sorted(rows, key=lambda r: (r.score or 0), reverse=True)

        table_text = "\n".join(
            f"{r.title} | price: {r.price} | rating: {r.rating} | score: {r.score}"
            for r in rows_sorted[:20]
        )
        msg = UserMessage(content=prompts.comparison_pick_prompt(table_text), source="user")
        comp = await run_with_schema(self.agent, msg, ComparisonSchema)

        comp.keyword = processing_result.keyword
        comp.domain = processing_result.domain
        comp.rows = rows_sorted
        comp.generated_at = datetime.utcnow().isoformat() + "Z"
        return comp


# # --------------------------------------------------------------------
# # OutputAgent
# # --------------------------------------------------------------------
class OutputAgent:
    def __init__(self, system_prompt: Optional[str] = None):
        self.system_prompt = system_prompt

    def assemble(
        self,
        processing_result: ProcessingResultSchema,
        comparison: ComparisonSchema,
        domain_info: Optional[DiscoveryOutput] = None,
    ) -> FinalOutputSchema:
        top = comparison.best_overall or (comparison.rows[0].title if comparison.rows else None)
        insights = comparison.reasoning or "See comparison table."
        final = FinalOutputSchema(
            keyword=processing_result.keyword,
            domain=processing_result.domain or (domain_info.domain if domain_info else "unknown"),
            domain_confidence=domain_info.confidence if domain_info else None,
            top_recommendation=top,
            insights=insights,
            products=processing_result.processed,
            comparison=comparison,
        )
        return final
