from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import DEFAULT_MODEL
from app.services.parsing import TOOLS, TECHNICAL_SKILLS, SOFT_SKILLS, find_keywords

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover
    SentenceTransformer = None


@dataclass
class MatchResult:
    embedding_similarity: float
    skill_match_score: float
    experience_match_score: float
    final_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    suggestions: list[str]
    recommendation: str


class EmbeddingService:
    def __init__(self) -> None:
        self.model = None
        if SentenceTransformer:
            try:
                self.model = SentenceTransformer(DEFAULT_MODEL)
            except Exception:
                self.model = None

    def similarity(self, text_a: str, text_b: str) -> float:
        if self.model:
            embeddings = self.model.encode([text_a, text_b])
            score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(np.clip(score, 0.0, 1.0))

        vectors = TfidfVectorizer(stop_words="english").fit_transform([text_a, text_b])
        score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
        return float(np.clip(score, 0.0, 1.0))


def recommendation_from_score(score: float) -> str:
    if score >= 80:
        return "Strong Fit"
    if score >= 65:
        return "Good Fit"
    if score >= 50:
        return "Moderate Fit"
    return "Needs Improvement"


def build_suggestions(missing_skills: list[str], experience_score: float) -> list[str]:
    suggestions: list[str] = []
    if missing_skills:
        suggestions.append(
            f"Add projects or certifications demonstrating {', '.join(missing_skills[:5])}."
        )
    if experience_score < 0.7:
        suggestions.append("Quantify years of relevant experience and leadership impact more clearly.")
    suggestions.append("Align resume summary with the job title and top 5 required skills.")
    return suggestions


def compute_skill_match(resume_text: str, jd_text: str) -> tuple[float, list[str], list[str]]:
    all_skills = TECHNICAL_SKILLS | SOFT_SKILLS | TOOLS
    resume_skills = set(find_keywords(resume_text, all_skills))
    jd_skills = set(find_keywords(jd_text, all_skills))
    if not jd_skills:
        return 0.0, [], []
    matched = sorted(resume_skills.intersection(jd_skills))
    missing = sorted(jd_skills.difference(resume_skills))
    score = len(matched) / len(jd_skills)
    return float(score), matched, missing


def compute_experience_match(resume_years: float, required_years: float) -> float:
    if required_years <= 0:
        return 1.0
    return float(min(resume_years / required_years, 1.0))


def calculate_match(
    resume_text: str,
    jd_text: str,
    resume_years: float,
    required_years: float,
    embedding_service: EmbeddingService,
) -> MatchResult:
    embedding_similarity = embedding_service.similarity(resume_text, jd_text)
    skill_match_score, matched_skills, missing_skills = compute_skill_match(resume_text, jd_text)
    experience_match_score = compute_experience_match(resume_years, required_years)

    final_score = (
        0.5 * embedding_similarity
        + 0.3 * skill_match_score
        + 0.2 * experience_match_score
    ) * 100

    suggestions = build_suggestions(missing_skills, experience_match_score)

    return MatchResult(
        embedding_similarity=round(embedding_similarity * 100, 2),
        skill_match_score=round(skill_match_score * 100, 2),
        experience_match_score=round(experience_match_score * 100, 2),
        final_score=round(final_score, 2),
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        suggestions=suggestions,
        recommendation=recommendation_from_score(final_score),
    )
