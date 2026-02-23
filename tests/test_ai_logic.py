from app.services.ai_logic import EmbeddingService, calculate_match


def test_calculate_match_returns_scores_in_range():
    resume = "Python FastAPI developer with 5 years experience, Docker, AWS, teamwork"
    jd = "Need Python engineer with 3 years experience, FastAPI, AWS and communication"
    service = EmbeddingService()

    result = calculate_match(
        resume_text=resume,
        jd_text=jd,
        resume_years=5,
        required_years=3,
        embedding_service=service,
    )

    assert 0 <= result.final_score <= 100
    assert 0 <= result.skill_match_score <= 100
    assert 0 <= result.embedding_similarity <= 100
    assert isinstance(result.missing_skills, list)
