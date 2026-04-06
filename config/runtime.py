from __future__ import annotations

import importlib
import os
from dataclasses import dataclass
from typing import Any, Mapping

from .defaults import (
    DEFAULT_ALL_KEYS_FOR_SHEDULE,
    DEFAULT_API_KEYS_STR,
    DEFAULT_LOCAL_API_URL,
    DEFAULT_LOCAL_INFER_URL,
    DEFAULT_MODEL_NAME,
    DEFAULT_REQUEST_STRATEGY,
)


PRIVATE_MODULE_NAME = "config.generate_conf"
PRIVATE_OVERRIDE_FIELDS = (
    "MODEL_NAME",
    "LOCAL_API_URL",
    "LOCAL_INFER_URL",
    "API_KEYS_STR",
    "ALL_KEYS_FOR_SHEDULE",
)
ENV_TO_FIELD = {
    "GEMINI_MODEL_NAME": "MODEL_NAME",
    "LOCAL_API_URL": "LOCAL_API_URL",
    "LOCAL_INFER_URL": "LOCAL_INFER_URL",
    "GEMINI_API_KEYS": "API_KEYS_STR",
    "GEMINI_SCHEDULER_KEYS": "ALL_KEYS_FOR_SHEDULE",
    "GEMINI_REQUEST_STRATEGY": "REQUEST_STRATEGY",
}


@dataclass(frozen=True)
class RuntimeConfig:
    model_name: str
    local_api_url: str
    local_infer_url: str
    api_keys_str: str
    all_keys_for_schedule: str
    request_strategy: str

    @property
    def api_keys(self) -> list[str]:
        return [key.strip() for key in self.api_keys_str.split(",") if key.strip()]

    @property
    def scheduler_keys(self) -> list[str]:
        return [key.strip() for key in self.all_keys_for_schedule.split(",") if key.strip()]


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
    return overrides


def load_runtime_config(
    *,
    environ: Mapping[str, str] | None = None,
    private_overrides: Mapping[str, Any] | None = None,
) -> RuntimeConfig:
    env = environ or os.environ
    private = dict(private_overrides) if private_overrides is not None else load_private_overrides()

    config_values: dict[str, str] = {
        "MODEL_NAME": str(private.get("MODEL_NAME", DEFAULT_MODEL_NAME)),
        "LOCAL_API_URL": str(private.get("LOCAL_API_URL", DEFAULT_LOCAL_API_URL)),
        "LOCAL_INFER_URL": str(private.get("LOCAL_INFER_URL", DEFAULT_LOCAL_INFER_URL)),
        "API_KEYS_STR": str(private.get("API_KEYS_STR", DEFAULT_API_KEYS_STR)),
        "ALL_KEYS_FOR_SHEDULE": str(private.get("ALL_KEYS_FOR_SHEDULE", DEFAULT_ALL_KEYS_FOR_SHEDULE)),
        "REQUEST_STRATEGY": str(private.get("REQUEST_STRATEGY", DEFAULT_REQUEST_STRATEGY)),
    }

    for env_name, field_name in ENV_TO_FIELD.items():
        env_value = env.get(env_name)
        if env_value is not None:
            config_values[field_name] = env_value

    request_strategy = config_values["REQUEST_STRATEGY"].strip().lower() or DEFAULT_REQUEST_STRATEGY

    return RuntimeConfig(
        model_name=config_values["MODEL_NAME"].strip() or DEFAULT_MODEL_NAME,
        local_api_url=config_values["LOCAL_API_URL"].strip() or DEFAULT_LOCAL_API_URL,
        local_infer_url=config_values["LOCAL_INFER_URL"].strip() or DEFAULT_LOCAL_INFER_URL,
        api_keys_str=config_values["API_KEYS_STR"].strip(),
        all_keys_for_schedule=config_values["ALL_KEYS_FOR_SHEDULE"].strip(),
        request_strategy=request_strategy,
    )


RUNTIME_CONFIG = load_runtime_config()

MODEL_NAME = RUNTIME_CONFIG.model_name
LOCAL_API_URL = RUNTIME_CONFIG.local_api_url
LOCAL_INFER_URL = RUNTIME_CONFIG.local_infer_url
API_KEYS_STR = RUNTIME_CONFIG.api_keys_str
ALL_KEYS_FOR_SHEDULE = RUNTIME_CONFIG.all_keys_for_schedule
REQUEST_STRATEGY = RUNTIME_CONFIG.request_strategy
API_KEYS = RUNTIME_CONFIG.api_keys
ALL_SCHEDULER_KEYS = RUNTIME_CONFIG.scheduler_keys

