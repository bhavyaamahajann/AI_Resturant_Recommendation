from typing import Optional
from src.data.preferences import UserPreferences
from src.data.llm_models import RecommendationResult
from src.data.store import RestaurantStore
from src.services.filter import CandidateFilterService, NoCandidatesError
from src.services.prompt import PromptBuilder
from src.services.llm import LLMGateway, LLMError
from src.services.parser import LLMParser
from config.settings import get_settings


class OrchestrationError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 500):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class RecommendationService:
    def __init__(self, store: RestaurantStore):
        self._store = store
        self._settings = get_settings()
        self._filter_service = CandidateFilterService(store=self._store, settings=self._settings)
        self._llm_gateway = LLMGateway()

    def recommend(self, preferences: UserPreferences) -> RecommendationResult:
        # 1. Filter
        try:
            candidates = self._filter_service.get_candidates(preferences)
        except NoCandidatesError as e:
            suggestions = f" Try: {', '.join(e.suggestions)}" if e.suggestions else ""
            raise OrchestrationError(
                code="NO_CANDIDATES",
                message=f"{str(e)}{suggestions}",
                status_code=404,
            )

        # 2. Prompt LLM
        messages = PromptBuilder.build(preferences, candidates.restaurants, preferences.top_n)

        # 3. Call LLM
        try:
            llm_response = self._llm_gateway.complete(messages)
            # 4. Parse & Enrich
            return LLMParser.parse_and_enrich(llm_response, candidates, preferences)
        except LLMError as e:
            # Deterministic fallback per architecture guidelines when LLM fails
            res = LLMParser.deterministic_fallback(candidates, preferences)
            res.metadata.warnings.append(f"AI error: {str(e)}")
            return res
