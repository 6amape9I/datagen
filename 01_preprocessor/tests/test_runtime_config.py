from __future__ import annotations

import importlib
from types import SimpleNamespace

from config.runtime import load_private_overrides, load_runtime_config


def test_runtime_config_uses_defaults_without_private_file(monkeypatch) -> None:
    def _raise_missing(module_name: str):
        raise ModuleNotFoundError(name=module_name)

    monkeypatch.setattr(importlib, "import_module", _raise_missing)

    private = load_private_overrides()
    config = load_runtime_config(environ={}, private_overrides=private)

    assert private == {}
    assert config.google_model_name == "gemma-4-31b-it"
    assert config.local_model_name == "local_http"
    assert config.local_api_url == "http://127.0.0.1:8080/generate"
    assert config.google_api_keys == []
    assert config.google_scheduler_keys == []
    assert config.google_thinking_level == "HIGH"
    assert config.google_enable_search_tool is False
    assert config.max_output_tokens == 32760
    assert config.max_samp_per_json == 2000
    assert config.temperature == 0.0
    assert config.generation_profile == "standard"


def test_runtime_config_uses_env_over_private_and_defaults() -> None:
    config = load_runtime_config(
        environ={
            "GOOGLE_MODEL_NAME": "env-google-model",
            "LOCAL_MODEL_NAME": "env-local-model",
            "GOOGLE_API_KEYS": "env-key-1, env-key-2",
            "GOOGLE_SCHEDULER_KEYS": "env-scheduler",
            "LOCAL_API_URL": "http://env.local/generate",
            "GOOGLE_THINKING_LEVEL": "medium",
            "GOOGLE_ENABLE_SEARCH_TOOL": "true",
            "GENERATION_MAX_OUTPUT_TOKENS": "2048",
            "MAX_SAMP_PER_JSON": "1500",
            "GENERATION_TEMPERATURE": "0.2",
            "GENERATION_PROFILE": "review",
        },
        private_overrides={
            "GOOGLE_MODEL_NAME": "private-google-model",
            "LOCAL_MODEL_NAME": "private-local-model",
            "GOOGLE_API_KEYS_STR": "private-key",
            "GOOGLE_SCHEDULER_KEYS_STR": "private-scheduler",
            "LOCAL_API_URL": "http://private.local/generate",
            "GOOGLE_THINKING_LEVEL": "low",
            "GOOGLE_ENABLE_SEARCH_TOOL": False,
            "MAX_OUTPUT_TOKENS": "1024",
            "MAX_SAMP_PER_JSON": "900",
            "TEMPERATURE": "0.1",
            "GENERATION_PROFILE": "bulk",
        },
    )

    assert config.google_model_name == "env-google-model"
    assert config.local_model_name == "env-local-model"
    assert config.google_api_keys == ["env-key-1", "env-key-2"]
    assert config.google_scheduler_keys == ["env-scheduler"]
    assert config.local_api_url == "http://env.local/generate"
    assert config.google_thinking_level == "MEDIUM"
    assert config.google_enable_search_tool is True
    assert config.max_output_tokens == 2048
    assert config.max_samp_per_json == 1500
    assert config.temperature == 0.2
    assert config.generation_profile == "review"


def test_runtime_config_uses_private_overrides_when_env_missing() -> None:
    config = load_runtime_config(
        environ={},
        private_overrides={
            "GOOGLE_MODEL_NAME": "private-google-model",
            "LOCAL_MODEL_NAME": "private-local-model",
            "GOOGLE_API_KEYS_STR": "private-key",
            "LOCAL_API_URL": "http://private.local/generate",
            "GOOGLE_THINKING_LEVEL": "off",
            "GOOGLE_ENABLE_SEARCH_TOOL": "no",
            "MAX_OUTPUT_TOKENS": "8192",
            "MAX_SAMP_PER_JSON": "777",
            "TEMPERATURE": "0.4",
            "GENERATION_PROFILE": "hard-cases",
        },
    )

    assert config.google_model_name == "private-google-model"
    assert config.local_model_name == "private-local-model"
    assert config.google_api_keys == ["private-key"]
    assert config.google_scheduler_keys == ["private-key"]
    assert config.local_api_url == "http://private.local/generate"
    assert config.google_thinking_level == "OFF"
    assert config.google_enable_search_tool is False
    assert config.max_output_tokens == 8192
    assert config.max_samp_per_json == 777
    assert config.temperature == 0.4
    assert config.generation_profile == "hard-cases"


def test_runtime_config_falls_back_to_default_for_invalid_max_samp_per_json() -> None:
    config = load_runtime_config(
        environ={"MAX_SAMP_PER_JSON": "0"},
        private_overrides={},
    )

    assert config.max_samp_per_json == 2000


def test_load_private_overrides_accepts_legacy_private_field_names(monkeypatch) -> None:
    fake_module = SimpleNamespace(
        MODEL_NAME="legacy-model",
        API_KEYS_STR="legacy-key",
        ALL_KEYS_FOR_SHEDULE="legacy-scheduler",
    )

    monkeypatch.setattr(importlib, "import_module", lambda module_name: fake_module)

    private = load_private_overrides()

    assert private["GOOGLE_MODEL_NAME"] == "legacy-model"
    assert private["GOOGLE_API_KEYS_STR"] == "legacy-key"
    assert private["GOOGLE_SCHEDULER_KEYS_STR"] == "legacy-scheduler"
