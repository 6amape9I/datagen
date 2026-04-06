from __future__ import annotations

import importlib

from config.runtime import load_private_overrides, load_runtime_config


def test_runtime_config_uses_defaults_without_private_file(monkeypatch) -> None:
    def _raise_missing(module_name: str):
        raise ModuleNotFoundError(name=module_name)

    monkeypatch.setattr(importlib, "import_module", _raise_missing)

    private = load_private_overrides()
    config = load_runtime_config(environ={}, private_overrides=private)

    assert private == {}
    assert config.model_name == "gemini-flash-latest"
    assert config.local_api_url == "http://127.0.0.1:8080/generate"
    assert config.local_infer_url == "http://127.0.0.1:8000/infer"
    assert config.api_keys == []
    assert config.scheduler_keys == []
    assert config.request_strategy == "genai"
    assert config.thinking_budget == 256
    assert config.max_output_tokens == 4096
    assert config.temperature == 0.0
    assert config.generation_profile == "standard"


def test_runtime_config_uses_env_over_private_and_defaults() -> None:
    config = load_runtime_config(
        environ={
            "GEMINI_MODEL_NAME": "env-model",
            "GEMINI_API_KEYS": "env-key-1, env-key-2",
            "GEMINI_SCHEDULER_KEYS": "env-scheduler",
            "GEMINI_REQUEST_STRATEGY": "local",
            "LOCAL_API_URL": "http://env.local/generate",
            "LOCAL_INFER_URL": "http://env.local/infer",
            "GEMINI_THINKING_BUDGET": "512",
            "GENERATION_MAX_OUTPUT_TOKENS": "2048",
            "GENERATION_TEMPERATURE": "0.2",
            "GENERATION_PROFILE": "review",
        },
        private_overrides={
            "MODEL_NAME": "private-model",
            "API_KEYS_STR": "private-key",
            "ALL_KEYS_FOR_SHEDULE": "private-scheduler",
            "LOCAL_API_URL": "http://private.local/generate",
            "LOCAL_INFER_URL": "http://private.local/infer",
            "THINKING_BUDGET": "128",
            "MAX_OUTPUT_TOKENS": "1024",
            "TEMPERATURE": "0.1",
            "GENERATION_PROFILE": "bulk",
        },
    )

    assert config.model_name == "env-model"
    assert config.api_keys == ["env-key-1", "env-key-2"]
    assert config.scheduler_keys == ["env-scheduler"]
    assert config.request_strategy == "local"
    assert config.local_api_url == "http://env.local/generate"
    assert config.local_infer_url == "http://env.local/infer"
    assert config.thinking_budget == 512
    assert config.max_output_tokens == 2048
    assert config.temperature == 0.2
    assert config.generation_profile == "review"


def test_runtime_config_uses_private_overrides_when_env_missing() -> None:
    config = load_runtime_config(
        environ={},
        private_overrides={
            "MODEL_NAME": "private-model",
            "API_KEYS_STR": "private-key",
            "ALL_KEYS_FOR_SHEDULE": "private-scheduler-1, private-scheduler-2",
            "LOCAL_API_URL": "http://private.local/generate",
            "LOCAL_INFER_URL": "http://private.local/infer",
            "THINKING_BUDGET": "768",
            "MAX_OUTPUT_TOKENS": "8192",
            "TEMPERATURE": "0.4",
            "GENERATION_PROFILE": "hard-cases",
        },
    )

    assert config.model_name == "private-model"
    assert config.api_keys == ["private-key"]
    assert config.scheduler_keys == ["private-scheduler-1", "private-scheduler-2"]
    assert config.local_api_url == "http://private.local/generate"
    assert config.local_infer_url == "http://private.local/infer"
    assert config.thinking_budget == 768
    assert config.max_output_tokens == 8192
    assert config.temperature == 0.4
    assert config.generation_profile == "hard-cases"
