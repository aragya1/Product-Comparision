# pipeline.py
"""
Pipeline orchestrator that runs agents in sequence.
"""

import asyncio
from agents import DiscoveryAgent, RetrievalAgent, ProcessingAgent, ComparisonAgent, OutputAgent

async def run_pipeline(keyword: str):
    # Step 1: Discovery
    discovery_agent = DiscoveryAgent()
    domain_info = await discovery_agent.classify(keyword)
    print("Discovery:", domain_info.model_dump())

    # Step 2: Retrieval
    retrieval_agent = RetrievalAgent()
    retrieval_result = await retrieval_agent.run(keyword, domain=domain_info.domain)
    print("Retrieved:", len(retrieval_result.products), "items")

    # Step 3: Processing
    processing_agent = ProcessingAgent()
    processing_result = await processing_agent.run(retrieval_result)
    print("Processed:", len(processing_result.processed), "items")

    # Step 4: Comparison
    comparison_agent = ComparisonAgent()
    comparison = await comparison_agent.run(processing_result)
    print("Comparison picks:", comparison.best_overall, comparison.best_budget, comparison.best_premium)

    # Step 5: Output
    output_agent = OutputAgent()
    final_output = output_agent.assemble(processing_result, comparison, domain_info)
    return final_output


if __name__ == "__main__":
    keyword = "back heating pad"  # test input
    result = asyncio.run(run_pipeline(keyword))
    print("\n=== FINAL OUTPUT ===")
    print(result.model_dump_json(indent=2))
