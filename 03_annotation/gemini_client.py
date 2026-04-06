"""Compatibility wrapper around 03_generation Google provider."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPT_BUILDER_PATH = PROJECT_ROOT / "03_generation" / "prompt_builder.py"
PROVIDER_PATH = PROJECT_ROOT / "03_generation" / "providers" / "google_genai.py"
for path in (PROJECT_ROOT, PROMPT_BUILDER_PATH.parent, PROVIDER_PATH.parent.parent):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_PROMPTS = _load_module(PROMPT_BUILDER_PATH, "generation_prompt_builder_compat")
_PROVIDER = _load_module(PROVIDER_PATH, "generation_google_provider_compat")


def get_model_response(api_key, sentence_data, *, return_error=False):
    provider = _PROVIDER.GoogleGenAIProvider()
    prompt = _PROMPTS.build_prompt_package(sentence_data)
    result = provider.generate(api_key, prompt)
    if return_error:
        return result.payload, result.error
    return result.payload


__all__ = ["get_model_response"]
