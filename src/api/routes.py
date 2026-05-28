from fastapi import APIRouter, HTTPException, Depends, status
from src.data.preferences import UserPreferences
from src.data.llm_models import RecommendationResult
from src.services.orchestrator import RecommendationService, OrchestrationError
from src.api.schemas import ErrorResponse

# We'll use a factory function or dependency injection to provide the service
def get_recommendation_service():
    # This will be overridden in main.py or tests
    raise NotImplementedError()

router = APIRouter()

@router.post(
    "/api/v1/recommendations",
    response_model=RecommendationResult,
    responses={
        400: {"model": ErrorResponse, "description": "Validation Error"},
        404: {"model": ErrorResponse, "description": "No candidates found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def get_recommendations(
    preferences: UserPreferences,
    service: RecommendationService = Depends(get_recommendation_service)
):
    try:
        return service.recommend(preferences)
    except OrchestrationError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"code": e.code, "message": e.message}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "Something went wrong"}
        )

@router.get("/health")
async def health_check(service: RecommendationService = Depends(get_recommendation_service)):
    # Simple check if store is loaded
    if len(service._store.get_all()) == 0:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "degraded", "reason": "no data"}
        )
    return {"status": "ok", "llm_configured": bool(service._settings.llm_api_key)}

@router.get("/api/v1/locations")
async def list_locations(service: RecommendationService = Depends(get_recommendation_service)):
    """Return distinct area/neighborhood names for the location dropdown."""
    areas = service._store.known_areas(limit=200)
    return {"locations": areas}


@router.get("/api/v1/cuisines")
async def list_cuisines(service: RecommendationService = Depends(get_recommendation_service)):
    """Return distinct cuisine names for the cuisine dropdown."""
    cuisines = service._store.known_cuisines(limit=300)
    return {"cuisines": cuisines}
