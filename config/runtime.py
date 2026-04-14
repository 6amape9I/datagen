from __future__ import annotations

import importlib
import os
from dataclasses import dataclass
from typing import Any, Mapping

from .defaults import (
    DEFAULT_GENERATION_PROFILE,
    DEFAULT_GOOGLE_API_KEYS_STR,
    DEFAULT_GOOGLE_ENABLE_SEARCH_TOOL,
    DEFAULT_GOOGLE_MODEL_NAME,
    DEFAULT_GOOGLE_SCHEDULER_KEYS_STR,
    DEFAULT_GOOGLE_THINKING_LEVEL,
    DEFAULT_LOCAL_API_URL,
    DEFAULT_LOCAL_MODEL_NAME,
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_MAX_SAMP_PER_JSON,
    DEFAULT_TEMPERATURE,
)


PRIVATE_MODULE_NAME = "config.generate_conf"
PRIVATE_OVERRIDE_FIELDS = (
    "GOOGLE_MODEL_NAME",
    "LOCAL_MODEL_NAME",
    "LOCAL_API_URL",
    "GOOGLE_API_KEYS_STR",
    "GOOGLE_SCHEDULER_KEYS_STR",
    "GOOGLE_THINKING_LEVEL",
    "GOOGLE_ENABLE_SEARCH_TOOL",
    "MAX_OUTPUT_TOKENS",
    "MAX_SAMP_PER_JSON",
    "TEMPERATURE",
    "GENERATION_PROFILE",
)
ENV_TO_FIELD = {
    "GOOGLE_MODEL_NAME": "GOOGLE_MODEL_NAME",
    "LOCAL_MODEL_NAME": "LOCAL_MODEL_NAME",
    "LOCAL_API_URL": "LOCAL_API_URL",
    "GOOGLE_API_KEYS": "GOOGLE_API_KEYS_STR",
    "GOOGLE_SCHEDULER_KEYS": "GOOGLE_SCHEDULER_KEYS_STR",
    "GOOGLE_THINKING_LEVEL": "GOOGLE_THINKING_LEVEL",
    "GOOGLE_ENABLE_SEARCH_TOOL": "GOOGLE_ENABLE_SEARCH_TOOL",
    "GENERATION_MAX_OUTPUT_TOKENS": "MAX_OUTPUT_TOKENS",
    "MAX_SAMP_PER_JSON": "MAX_SAMP_PER_JSON",
    "GENERATION_TEMPERATURE": "TEMPERATURE",
    "GENERATION_PROFILE": "GENERATION_PROFILE",
}

LEGACY_PRIVATE_FIELD_ALIASES = {
    "MODEL_NAME": "GOOGLE_MODEL_NAME",
    "API_KEYS_STR": "GOOGLE_API_KEYS_STR",
    "ALL_KEYS_FOR_SHEDULE": "GOOGLE_SCHEDULER_KEYS_STR",
}


@dataclass(frozen=True)
class RuntimeConfig:
    google_model_name: str
    local_model_name: str
    local_api_url: str
    google_api_keys_str: str
    google_scheduler_keys_str: str
    google_thinking_level: str
    google_enable_search_tool: bool
    max_output_tokens: int
    max_samp_per_json: int
    temperature: float
    generation_profile: str

    @property
    def google_api_keys(self) -> list[str]:
        return [key.strip() for key in self.google_api_keys_str.split(",") if key.strip()]

    @property
    def google_scheduler_keys(self) -> list[str]:
        scheduler_keys = [key.strip() for key in self.google_scheduler_keys_str.split(",") if key.strip()]
        return scheduler_keys or self.google_api_keys


def load_private_overrides(module_name: str = PRIVATE_MODULE_NAME) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name != module_name:
            raise
        return {}

    overrides: dict[str, Any] = {}
    for field_name in PRIVATE_OVERRIDE_FIELDS:
        if hasattr(module, field_name):
            overrides[field_name] = getattr(module, field_name)
    for legacy_name, canonical_name in LEGACY_PRIVATE_FIELD_ALIASES.items():
        if canonical_name not in overrides and hasattr(module, legacy_name):
            overrides[canonical_name] = getattr(module, legacy_name)
    return overrides


def load_runtime_config(
    *,
    environ: Mapping[str, str] | None = None,
    private_overrides: Mapping[str, Any] | None = None,
) -> RuntimeConfig:
    env = environ or os.environ
    private = dict(private_overrides) if private_overrides is not None else load_private_overrides()

    def _coerce_float(value: Any, default: float) -> float:
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            return default

    def _coerce_int(value: Any, default: int) -> int:
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return default

    def _coerce_positive_int(value: Any, default: int) -> int:
        coerced = _coerce_int(value, default)
        if coerced < 1:
            return default
        return coerced

    def _coerce_bool(value: Any, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        return default

    def _normalize_thinking_level(value: Any) -> str:
        normalized = str(value).strip().upper()
        if normalized in {"OFF", "LOW", "MEDIUM", "HIGH"}:
            return normalized
        return DEFAULT_GOOGLE_THINKING_LEVEL

    config_values: dict[str, str] = {
        "GOOGLE_MODEL_NAME": str(private.get("GOOGLE_MODEL_NAME", DEFAULT_GOOGLE_MODEL_NAME)),
        "LOCAL_MODEL_NAME": str(private.get("LOCAL_MODEL_NAME", DEFAULT_LOCAL_MODEL_NAME)),
        "LOCAL_API_URL": str(private.get("LOCAL_API_URL", DEFAULT_LOCAL_API_URL)),
        "GOOGLE_API_KEYS_STR": str(private.get("GOOGLE_API_KEYS_STR", DEFAULT_GOOGLE_API_KEYS_STR)),
        "GOOGLE_SCHEDULER_KEYS_STR": str(private.get("GOOGLE_SCHEDULER_KEYS_STR", DEFAULT_GOOGLE_SCHEDULER_KEYS_STR)),
        "GOOGLE_THINKING_LEVEL": str(private.get("GOOGLE_THINKING_LEVEL", DEFAULT_GOOGLE_THINKING_LEVEL)),
        "GOOGLE_ENABLE_SEARCH_TOOL": str(private.get("GOOGLE_ENABLE_SEARCH_TOOL", DEFAULT_GOOGLE_ENABLE_SEARCH_TOOL)),
        "MAX_OUTPUT_TOKENS": str(private.get("MAX_OUTPUT_TOKENS", DEFAULT_MAX_OUTPUT_TOKENS)),
        "MAX_SAMP_PER_JSON": str(private.get("MAX_SAMP_PER_JSON", DEFAULT_MAX_SAMP_PER_JSON)),
        "TEMPERATURE": str(private.get("TEMPERATURE", DEFAULT_TEMPERATURE)),
        "GENERATION_PROFILE": str(private.get("GENERATION_PROFILE", DEFAULT_GENERATION_PROFILE)),
    }

    for env_name, field_name in ENV_TO_FIELD.items():
        env_value = env.get(env_name)
        if env_value is not None:
            config_values[field_name] = env_value

    return RuntimeConfig(
        google_model_name=config_values["GOOGLE_MODEL_NAME"].strip() or DEFAULT_GOOGLE_MODEL_NAME,
        local_model_name=config_values["LOCAL_MODEL_NAME"].strip() or DEFAULT_LOCAL_MODEL_NAME,
        local_api_url=config_values["LOCAL_API_URL"].strip() or DEFAULT_LOCAL_API_URL,
        google_api_keys_str=config_values["GOOGLE_API_KEYS_STR"].strip(),
        google_scheduler_keys_str=config_values["GOOGLE_SCHEDULER_KEYS_STR"].strip(),
        google_thinking_level=_normalize_thinking_level(config_values["GOOGLE_THINKING_LEVEL"]),
        google_enable_search_tool=_coerce_bool(
            config_values["GOOGLE_ENABLE_SEARCH_TOOL"],
            DEFAULT_GOOGLE_ENABLE_SEARCH_TOOL,
        ),
        max_output_tokens=_coerce_int(config_values["MAX_OUTPUT_TOKENS"], DEFAULT_MAX_OUTPUT_TOKENS),
        max_samp_per_json=_coerce_positive_int(
            config_values["MAX_SAMP_PER_JSON"],
            DEFAULT_MAX_SAMP_PER_JSON,
        ),
        temperature=_coerce_float(config_values["TEMPERATURE"], DEFAULT_TEMPERATURE),
        generation_profile=config_values["GENERATION_PROFILE"].strip() or DEFAULT_GENERATION_PROFILE,
    )


RUNTIME_CONFIG = load_runtime_config()

GOOGLE_MODEL_NAME = RUNTIME_CONFIG.google_model_name
LOCAL_MODEL_NAME = RUNTIME_CONFIG.local_model_name
LOCAL_API_URL = RUNTIME_CONFIG.local_api_url
GOOGLE_API_KEYS_STR = RUNTIME_CONFIG.google_api_keys_str
GOOGLE_SCHEDULER_KEYS_STR = RUNTIME_CONFIG.google_scheduler_keys_str
GOOGLE_API_KEYS = RUNTIME_CONFIG.google_api_keys
GOOGLE_SCHEDULER_KEYS = RUNTIME_CONFIG.google_scheduler_keys
GOOGLE_THINKING_LEVEL = RUNTIME_CONFIG.google_thinking_level
GOOGLE_ENABLE_SEARCH_TOOL = RUNTIME_CONFIG.google_enable_search_tool
MAX_OUTPUT_TOKENS = RUNTIME_CONFIG.max_output_tokens
MAX_SAMP_PER_JSON = RUNTIME_CONFIG.max_samp_per_json
TEMPERATURE = RUNTIME_CONFIG.temperature
GENERATION_PROFILE = RUNTIME_CONFIG.generation_profile
