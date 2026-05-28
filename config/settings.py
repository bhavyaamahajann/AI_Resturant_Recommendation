from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    dataset_name: str = "ManikaSaini/zomato-restaurant-recommendation"
    data_path: Path = Field(default=PROJECT_ROOT / "data" / "restaurants.parquet")
    ingest_valid_threshold: float = 0.9
    candidate_limit: int = 30
    default_top_n: int = 5
    budget_low_percentile: float = 33.0
    budget_medium_percentile: float = 66.0
    min_city_rows_for_percentiles: int = 10
    max_field_length: int = 500
    llm_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    llm_timeout_sec: int = 30

    @field_validator("data_path", mode="before")
    @classmethod
    def resolve_data_path(cls, v: object) -> Path:
        path = Path(v) if v else PROJECT_ROOT / "data" / "restaurants.parquet"
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path

    @field_validator("ingest_valid_threshold")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        if not 0 < v <= 1:
            raise ValueError("ingest_valid_threshold must be between 0 and 1")
        return v

    @field_validator("budget_low_percentile", "budget_medium_percentile")
    @classmethod
    def validate_percentiles(cls, v: float) -> float:
        if not 0 < v < 100:
            raise ValueError("budget percentiles must be between 0 and 100")
        return v


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.budget_low_percentile >= settings.budget_medium_percentile:
        raise ValueError(
            "budget_low_percentile must be less than budget_medium_percentile"
        )
    return settings
