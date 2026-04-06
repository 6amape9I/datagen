"""Compatibility wrapper around 03_generation.prompt_builder."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TARGET_PATH = PROJECT_ROOT / "03_generation" / "prompt_builder.py"
for path in (PROJECT_ROOT, TARGET_PATH.parent):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

spec = importlib.util.spec_from_file_location("generation_prompt_builder_wrapper", TARGET_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load prompt builder from {TARGET_PATH}.")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

PromptPackage = module.PromptPackage
build_prompt_package = module.build_prompt_package
build_system_prompt = module.build_system_prompt
build_user_prompt = module.build_user_prompt


def build_annotation_request_text(sentence_data):
    return build_user_prompt(sentence_data)


__all__ = [
    "PromptPackage",
    "build_prompt_package",
    "build_system_prompt",
    "build_user_prompt",
    "build_annotation_request_text",
]
