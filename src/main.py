import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import get_settings
from src.api.routes import router as api_router, get_recommendation_service
from src.data.store import RestaurantStore
from src.services.orchestrator import RecommendationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
store = RestaurantStore()
service = RecommendationService(store)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global service, store
    settings = get_settings()

    try:
        logger.info("Loading data store from %s...", settings.data_path)
        store = RestaurantStore.from_parquet(settings.data_path)
        logger.info("Loaded %d restaurants.", len(store))
    except Exception as e:
        logger.error("Failed to load data store on startup: %s", e)
        # Allow the app to start, but health check will return 503.
        store = RestaurantStore()

    service = RecommendationService(store)
    yield
    logger.info("Shutting down application...")


app = FastAPI(
    title="Zomato Restaurant Recommendation API",
    description="AI-powered restaurant recommendation service",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for Web UI (Phase 6)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


# Dependency override function
def _get_recommendation_service() -> RecommendationService:
    return service


# Wire the dependency
app.dependency_overrides[get_recommendation_service] = _get_recommendation_service
