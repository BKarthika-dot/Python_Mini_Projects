from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ClassifyRequest(BaseModel):
    """Input for a classification request.

    Matches SRS section 3.1 (Input Handling Module): the user submits either
    a job posting URL or pasted job posting text/form details.
    """
    input_type: Literal["url", "text"] = Field(
        ..., description="Whether 'content' is a job posting URL or pasted text/form details"
    )
    content: str = Field(..., min_length=1, description="The job posting URL, or the pasted job posting text")
    company_domain: Optional[str] = Field(
        None, description="Optional known official domain of the claimed employer, used for email-mismatch checks"
    )


class ClassifyUrlRequest(BaseModel):
    """Convenience input for the primary flow: just a job posting URL."""
    url: str = Field(..., description="The job posting URL to fetch, extract text from, and classify")
    company_domain: Optional[str] = Field(
        None, description="Optional known official domain of the claimed employer, used for email-mismatch checks"
    )


class MatchedPattern(BaseModel):
    pattern_id: str
    label: Literal["scam", "legit"]
    description: str
    similarity: float


class ClassifyResponse(BaseModel):
    source_url: Optional[str]
    category: Literal["Safe", "Suspicious", "Unsafe"]
    confidence_score: float = Field(..., description="Overall fused fraud-likelihood score, 0 (safe) to 1 (unsafe)")
    rule_based_score: float
    ml_score: float
    rag_score: float
    explanation: List[str]
    matched_patterns: List[MatchedPattern]
    extracted_text_preview: str
