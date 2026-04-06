from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from config import API_KEYS, GENERATION_PROFILE, MAX_OUTPUT_TOKENS, MODEL_NAME, TEMPERATURE, THINKING_BUDGET
from prompt_builder import PromptPackage
from providers.base import GenerationResult, ProviderMetadata
from response_schema import build_google_response_schema


@dataclass(frozen=True)
class GoogleGenAIProvider:
    metadata: ProviderMetadata = ProviderMetadata(
        provider="google_genai",
        model_name=MODEL_NAME,
        generation_profile=GENERATION_PROFILE,
    )
    max_output_tokens: int = MAX_OUTPUT_TOKENS
    thinking_budget: int = THINKING_BUDGET
    temperature: float = TEMPERATURE

    def worker_tokens(self, requested_workers: int) -> list[str]:
        return list(API_KEYS)

    def create_client(self, worker_token: str) -> Any:
        if not worker_token:
            raise ValueError("API key is required for Google GenAI provider.")
        return worker_token

    def generate(self, client: Any, prompt: PromptPackage) -> GenerationResult:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:  # pragma: no cover - depends on optional package
            return GenerationResult(None, f"google_genai_import_failed: {exc}")

        try:
            genai_client = genai.Client(api_key=str(client))
            config_kwargs: dict[str, Any] = {
                "response_mime_type": "application/json",
                "response_schema": build_google_response_schema(types),
                "system_instruction": [types.Part.from_text(text=prompt.system_prompt)],
                "max_output_tokens": self.max_output_tokens,
                "temperature": self.temperature,
            }
            if self.thinking_budget >= 0:
                config_kwargs["thinking_config"] = types.ThinkingConfig(
                    thinking_budget=self.thinking_budget
                )

            response = genai_client.models.generate_content(
                model=self.metadata.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=prompt.user_prompt)],
                    )
                ],
                config=types.GenerateContentConfig(**config_kwargs),
            )
            response_text = getattr(response, "text", "") or ""
            if not response_text:
                return GenerationResult(None, "empty_google_response")
            return GenerationResult(json.loads(response_text), None)
        except json.JSONDecodeError as exc:
            return GenerationResult(None, f"google_response_json_decode_failed: {exc}")
        except Exception as exc:  # pragma: no cover - network/provider code
            return GenerationResult(None, f"google_generation_failed: {exc}")

    def is_quota_error(self, error_text: str | None) -> bool:
        if not error_text:
            return False
        lowered = error_text.lower()
        return "quota" in lowered or "limit" in lowered or "resource_exhausted" in lowered
