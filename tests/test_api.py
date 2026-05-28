from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.main import app
from src.data.models import BudgetTier, Restaurant
from src.data.preferences import CandidateList, CandidateMetadata
from src.data.llm_models import RecommendationResult, RecommendationResultItem


client = TestClient(app)

from src.api.routes import get_recommendation_service

@patch("src.main.service")
def test_health_check_ok(mock_service):
    mock_service._store.get_all.return_value = ["dummy"]
    mock_service._settings.llm_api_key = "key"
    
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "llm_configured": True}


@patch("src.main.service")
def test_health_check_no_data(mock_service):
    mock_service._store.get_all.return_value = []
    
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"detail": {"status": "degraded", "reason": "no data"}}


def test_recommendations_success():
    mock_service = MagicMock()
    app.dependency_overrides[get_recommendation_service] = lambda: mock_service
    
    mock_service.recommend.return_value = RecommendationResult(
        summary="Test summary",
        recommendations=[
            RecommendationResultItem(
                rank=1,
                restaurant_id="1",
                name="Test",
                cuisine="Italian",
                rating=4.5,
                estimated_cost=1000,
                explanation="Good"
            )
        ],
        metadata=CandidateMetadata()
    )

    try:
        response = client.post(
            "/api/v1/recommendations",
            json={
                "location": "Bangalore",
                "budget": "medium",
                "cuisine": "Italian"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["summary"] == "Test summary"
        assert len(data["recommendations"]) == 1
        assert data["recommendations"][0]["name"] == "Test"
    finally:
        app.dependency_overrides.clear()


def test_recommendations_validation_error():
    mock_service = MagicMock()
    app.dependency_overrides[get_recommendation_service] = lambda: mock_service
    try:
        # Missing required fields like location, cuisine, budget
        response = client.post(
            "/api/v1/recommendations",
            json={}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    finally:
        app.dependency_overrides.clear()


def test_recommendations_no_candidates():
    mock_service = MagicMock()
    app.dependency_overrides[get_recommendation_service] = lambda: mock_service
    
    from src.services.orchestrator import OrchestrationError
    mock_service.recommend.side_effect = OrchestrationError(
        code="NO_CANDIDATES",
        message="No restaurants found",
        status_code=404
    )

    try:
        response = client.post(
            "/api/v1/recommendations",
            json={
                "location": "Bangalore",
                "budget": "medium",
                "cuisine": "Italian"
            }
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "NO_CANDIDATES"
        assert "No restaurants found" in data["detail"]["message"]
    finally:
        app.dependency_overrides.clear()
