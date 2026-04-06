from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from config import (
    GENERATION_PROFILE,
    GOOGLE_API_KEYS,
    GOOGLE_ENABLE_SEARCH_TOOL,
    GOOGLE_MODEL_NAME,
    GOOGLE_THINKING_LEVEL,
    MAX_OUTPUT_TOKENS,
    TEMPERATURE,
)
from prompt_builder import PromptPackage
from providers.base import GenerationResult, ProviderMetadata
from response_schema import build_google_response_schema, build_response_json_schema


def normalize_google_thinking_level(level: str) -> str:
    normalized = str(level).strip().upper()
    if normalized in {"OFF", "LOW", "MEDIUM", "HIGH"}:
        return normalized
    return "HIGH"


def build_google_contents(types_module: Any, prompt: PromptPackage) -> list[Any]:
    return [
        types_module.Content(
            role="user",
            parts=[types_module.Part.from_text(text=prompt.user_prompt)],
        )
    ]


def build_google_tools(types_module: Any, *, enable_search_tool: bool) -> list[Any]:
    if not enable_search_tool:
        return []
    return [
        types_module.Tool(
            googleSearch=types_module.GoogleSearch(),
        )
    ]


def build_google_config_kwargs(
    types_module: Any,
    prompt: PromptPackage,
    *,
    max_output_tokens: int,
    temperature: float,
    thinking_level: str,
    enable_search_tool: bool,
) -> dict[str, Any]:
    config_kwargs: dict[str, Any] = {
        "max_output_tokens": max_output_tokens,
        "temperature": temperature,
        "response_mime_type": "application/json",
        "response_schema": build_google_response_schema(types_module),
        "system_instruction": [types_module.Part.from_text(text=prompt.system_prompt)],
    }
    normalized_level = normalize_google_thinking_level(thinking_level)
    if normalized_level != "OFF":
        config_kwargs["thinking_config"] = types_module.ThinkingConfig(
            thinking_level=normalized_level,
        )
    tools = build_google_tools(types_module, enable_search_tool=enable_search_tool)
    if tools:
        config_kwargs["tools"] = tools
    return config_kwargs


def build_google_request_debug_snapshot(
    prompt: PromptPackage,
    *,
    model_name: str,
    max_output_tokens: int,
    temperature: float,
    thinking_level: str,
    enable_search_tool: bool,
) -> dict[str, Any]:
    return {
        "provider": "google_genai",
        "model": model_name,
        "system_prompt": prompt.system_prompt,
        "user_prompt": prompt.user_prompt,
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt.user_prompt,
                    }
                ],
            }
        ],
        "config": {
            "max_output_tokens": max_output_tokens,
            "temperature": temperature,
            "thinking_level": normalize_google_thinking_level(thinking_level),
            "enable_search_tool": enable_search_tool,
            "response_mime_type": "application/json",
            "response_schema": build_response_json_schema(),
            "system_instruction": [prompt.system_prompt],
            "tools": ["googleSearch"] if enable_search_tool else [],
        },
    }


@dataclass(frozen=True)
class GoogleGenAIProvider:
    metadata: ProviderMetadata = ProviderMetadata(
        provider="google_genai",
        model_name=GOOGLE_MODEL_NAME,
        generation_profile=GENERATION_PROFILE,
    )
    max_output_tokens: int = MAX_OUTPUT_TOKENS
    thinking_level: str = GOOGLE_THINKING_LEVEL
    temperature: float = TEMPERATURE
    enable_search_tool: bool = GOOGLE_ENABLE_SEARCH_TOOL

    def worker_tokens(self, requested_workers: int) -> list[str]:
        return list(GOOGLE_API_KEYS)

    def create_client(self, worker_token: str) -> Any:
        if not worker_token:
            raise ValueError("API key is required for Google GenAI provider.")
        try:
            from google import genai
        except ImportError as exc:  # pragma: no cover - depends on optional package
            raise RuntimeError(f"google_genai_import_failed: {exc}") from exc
        return genai.Client(api_key=str(worker_token))

    def generate(self, client: Any, prompt: PromptPackage) -> GenerationResult:
        try:
            from google.genai import types
        except ImportError as exc:  # pragma: no cover - depends on optional package
            return GenerationResult(None, f"google_genai_import_failed: {exc}")

        try:
            response = client.models.generate_content(
                model=self.metadata.model_name,
                contents=build_google_contents(types, prompt),
                config=types.GenerateContentConfig(
                    **build_google_config_kwargs(
                        types,
                        prompt,
                        max_output_tokens=self.max_output_tokens,
                        temperature=self.temperature,
                        thinking_level=self.thinking_level,
                        enable_search_tool=self.enable_search_tool,
                    )
                ),
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
