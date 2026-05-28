import json
import logging
from typing import Any

import httpx

from config.settings import get_settings


class LLMError(Exception):
    """Raised when the LLM provider fails."""


class LLMGateway:
    """Gateway for making requests to the LLM (Groq via OpenAI-compatible endpoint)."""

    def __init__(self) -> None:
        self._settings = get_settings()
        # Groq provides an OpenAI-compatible endpoint
        self._url = "https://api.groq.com/openai/v1/chat/completions"
        self._headers = None
        if self._settings.llm_api_key:
            self._headers = {
                "Authorization": f"Bearer {self._settings.llm_api_key}",
                "Content-Type": "application/json",
            }

    def complete(self, messages: list[dict[str, str]]) -> str:
        """
        Sends the messages to the LLM and returns the raw JSON text response.
        Retries once on timeout or 5xx errors.
        """
        if not self._headers:
            raise LLMError("LLM_API_KEY is not set. Configure it to enable AI-ranked results.")

        payload = {
            "model": self._settings.llm_model,
            "messages": messages,
            "temperature": 0.1,  # Low temp for deterministic structured output
            "response_format": {"type": "json_object"},
        }

        timeout = httpx.Timeout(self._settings.llm_timeout_sec)
        
        attempts = 2
        for attempt in range(1, attempts + 1):
            try:
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(
                        self._url,
                        headers=self._headers,
                        json=payload,
                    )
                
                # Check for rate limit or server errors (429, 5xx)
                if response.status_code in (429, 500, 502, 503, 504):
                    if attempt < attempts:
                        logging.warning(f"LLM API returned {response.status_code}. Retrying...")
                        continue
                    raise LLMError(f"LLM API failed with status {response.status_code}")

                response.raise_for_status()
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                if not content:
                    raise LLMError("LLM returned empty content")
                
                return str(content)

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                if attempt < attempts:
                    logging.warning(f"LLM API network error: {e}. Retrying...")
                    continue
                raise LLMError(f"LLM API network error after {attempts} attempts: {e}") from e
            except httpx.HTTPStatusError as e:
                # E.g. 401 Unauthorized
                raise LLMError(f"LLM HTTP Error: {e.response.status_code} - {e.response.text}") from e
            except (KeyError, IndexError, ValueError) as e:
                raise LLMError(f"Failed to parse LLM API response structure: {e}") from e

        raise LLMError("LLM API failed unexpectedly.")
