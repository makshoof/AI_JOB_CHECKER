from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class ParsedProfile(BaseModel):
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    years_experience: float = 0.0
    education: str = "Not specified"


class AnalyzeResponse(BaseModel):
    candidate_name: str
    match_percentage: float
    embedding_similarity: float
    skill_match_score: float
    experience_match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    suggestions: List[str]
    recommendation: str


class RankedCandidate(BaseModel):
    candidate_name: str
    match_percentage: float
    skill_match_percentage: float
    experience_score: float
    analysis_id: int


class RankedResponse(BaseModel):
    rankings: List[RankedCandidate]


class AnalysisHistoryItem(BaseModel):
    analysis_id: int
    candidate_name: str
    final_score: float
    created_at: datetime
