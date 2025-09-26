from pydantic import BaseModel, Field, condecimal, confloat, HttpUrl  
from typing import Literal,Optional, List, Any,Dict

# DOMAIN SCHEMA

class DiscoveredProduct(BaseModel):
    title: str = Field(..., description="Product title or name")
    url: Optional[str] = Field(None, description="Direct or search URL for this product")

class DiscoveryOutput(BaseModel):
    keyword: str
    domain: Literal["physical_product", "app", "ebook", "design","location", "other"]
    confidence: confloat(ge=0.0, le=1.0)
    recommended_platforms: List[str] = Field(default_factory=list)
    products: List[DiscoveredProduct] = Field(
        ..., description="List of discovered products with candidate URLs"
    )

# RETRIVAL SCHEMA

class RawProductSchema(BaseModel):
    """Raw/unprocessed product item returned by a retrieval connector."""
    product_id: str = Field(..., description="Unique identifier for the product")
    title: str = Field(..., description="Product or app title")
    url: Optional[HttpUrl] = Field(None, description="Link to the product page")
    price: Optional[float] = Field(None, description="Normalized price (float) if available")
    currency: Optional[str] = Field(None, description="Currency code for price, e.g., 'INR', 'USD'")
    rating: Optional[float] = Field(None, description="Average rating (1.0 - 5.0) if available")
    review_count: Optional[int] = Field(None, description="Number of reviews/ratings")
    source: Optional[str] = Field(None, description="Source identifier, e.g., 'amazon', 'itunes'")
    raw_description: Optional[str] = Field(None, description="Raw description or snippet")
    metadata: Optional[dict] = Field(default_factory=dict, description="Any provider-specific metadata")
    raw: Optional[dict] = Field(None, description="Full raw JSON from source (optional)")
    image_url: Optional[str] = Field(None, description="Link to product image")


class RetrievalResultSchema(BaseModel):
    product_id: str
    title: str
    url: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    source: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

# Rating Agent's output
# class RatingSummarySchema(BaseModel):
#     """Schema for the summary of product reviews and ratings."""
#     product_id: str
#     title: str
#     overall_sentiment: str = Field(
#         ...,
#         description="Overall sentiment of reviews (e.g., 'Positive', 'Mixed', 'Negative')."
#     )
#     pros: List[str] = Field(
#         ...,
#         description="List of key positive points mentioned in reviews."
#     )
#     cons: List[str] = Field(
#         ...,
#         description="List of key negative points mentioned in reviews."
#     )


# PROCESSING SCHEMA
class ProcessedProductSchema(BaseModel):
    """Normalized, LLM/NLP-enriched product representation for comparison & UI."""
    title: str
    url: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    image_url: Optional[str] = Field(None, description="Link to product image")

    # NLP augmentations
    summary: Optional[str] = Field(None, description="Concise summary (1-3 sentences)")
    pros: List[str] = Field(default_factory=list, description="Short list of positive aspects")
    cons: List[str] = Field(default_factory=list, description="Short list of negative aspects")
    sentiment: Optional[Literal["positive", "neutral", "negative"]] = Field(
        None, description="Overall aggregated sentiment"
    )
    sentiment_score: Optional[confloat(ge=-1.0, le=1.0)] = Field(
        None, description="Sentiment polarity score"
    )
    # internal fields
    source: Optional[str] = None
    score: Optional[float] = Field(None, description="Calculated ranking score (0..1+)")
    extra: Optional[dict] = Field(default_factory=dict, description="Any extra fields")


class ProcessingResultSchema(BaseModel):
    keyword: str
    domain: str
    processed: List[ProcessedProductSchema] = Field(default_factory=list)
    warnings: Optional[List[str]] = Field(default_factory=list)


# COMPARISION SCHEMA
class ComparisonRow(BaseModel):
    product_id: str
    title: str
    price: Optional[float] = None
    currency: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    score: Optional[float] = None
    extra: dict[str, Any] = Field(default_factory=dict)

class ComparisonSchema(BaseModel):
    keyword: str
    domain: str
    rows: List[ComparisonRow] = Field(default_factory=list)
    best_overall: Optional[str] = Field(None, description="Title of best overall item")
    best_budget: Optional[str] = Field(None, description="Title of best budget item")
    best_premium: Optional[str] = Field(None, description="Title of best premium item")
    reasoning: Optional[str] = Field(None, description="Short explanation for picks")
    generated_at: Optional[str] = Field(None, description="ISO timestamp when comparison was generated")
    meta: Optional[dict[str, Any]] = Field(default_factory=dict)

# OUTPUT SCHEMA

class FinalOutputSchema(BaseModel):
    keyword: str
    domain: str
    domain_confidence: Optional[float] = None
    top_recommendation: Optional[str] = Field(None, description="Title of top recommended product")
    insights: Optional[str] = Field(None, description="High-level AI summary / insights")
    products: List[ProcessedProductSchema] = Field(default_factory=list)
    comparison: Optional[ComparisonSchema] = None
    warnings: Optional[List[str]] = Field(default_factory=list)
    generated_at: Optional[str] = Field(
        None, description="ISO 8601 timestamp when output generated"
    )

