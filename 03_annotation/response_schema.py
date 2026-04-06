"""Compatibility wrapper around 03_generation.response_schema."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TARGET_PATH = PROJECT_ROOT / "03_generation" / "response_schema.py"
for path in (PROJECT_ROOT, TARGET_PATH.parent):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

spec = importlib.util.spec_from_file_location("generation_response_schema_wrapper", TARGET_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load response schema from {TARGET_PATH}.")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

build_google_response_schema = module.build_google_response_schema
build_response_json_schema = module.build_response_json_schema
build_runtime_ontology_context = module.build_runtime_ontology_context
get_annotation_roles = module.get_annotation_roles

__all__ = [
    "build_google_response_schema",
    "build_response_json_schema",
    "build_runtime_ontology_context",
    "get_annotation_roles",
]
