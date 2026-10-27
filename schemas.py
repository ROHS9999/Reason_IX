"""Pydantic models = the exact shape we force the LLM to answer in (structured output)."""
from typing import List, Literal
from pydantic import BaseModel, Field, field_validator


class ExtractedClaim(BaseModel):
    chunk: int = Field(description="Number n of the passage [n] the claim comes from.")
    claim: str = Field(description="ONE self-contained factual statement. Name the subject; no 'it' or 'this study'.")
    evidence: str = Field(description="Short snippet (8-15 words) copied word-for-word from that passage. No double quotes.")


class SourceAnalysis(BaseModel):
    summary: List[str] = Field(default_factory=list, description="Exactly 3 one-sentence points.")
    claims: List[ExtractedClaim] = Field(default_factory=list)


class PairVerdict(BaseModel):
    relation: Literal["contradiction", "agreement", "neutral"]
    confidence: int = Field(description="How sure you are, 0-100.")
    explanation: str = Field(description="At most 15 words.")

    @field_validator("relation", mode="before")
    @classmethod
    def _normalise_relation(cls, v):
        # small models sometimes answer "Contradiction" or " contradiction."
        return str(v).strip().lower().rstrip(".")

    @field_validator("confidence", mode="before")
    @classmethod
    def _clamp_confidence(cls, v):
        try:
            v = int(float(str(v).strip().rstrip("%")))
        except ValueError:
            v = 50
        return max(0, min(100, v))


class PairItem(PairVerdict):
    id: int = Field(description="The pair number from the question (1-based).")


class BatchVerdicts(BaseModel):
    verdicts: List[PairItem] = Field(default_factory=list)


class WebVerdict(BaseModel):
    verdict: Literal["supported", "contradicted", "unverified"]
    confidence: int = Field(description="How sure you are, 0-100.")
    explanation: str = Field(description="At most 25 words.")
    source_numbers: List[int] = Field(default_factory=list, description="Numbers of the search results relied on.")

    @field_validator("verdict", mode="before")
    @classmethod
    def _normalise_verdict(cls, v):
        return str(v).strip().lower().rstrip(".")

    @field_validator("confidence", mode="before")
    @classmethod
    def _clamp_confidence(cls, v):
        try:
            v = int(float(str(v).strip().rstrip("%")))
        except ValueError:
            v = 50
        return max(0, min(100, v))
