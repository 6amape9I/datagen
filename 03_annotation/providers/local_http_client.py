"""Compatibility wrapper around 03_generation.providers.local_http."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TARGET_PATH = PROJECT_ROOT / "03_generation" / "providers" / "local_http.py"
for path in (PROJECT_ROOT, TARGET_PATH.parent.parent):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

spec = importlib.util.spec_from_file_location("generation_local_provider_wrapper", TARGET_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load provider from {TARGET_PATH}.")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

LocalHTTPProvider = module.LocalHTTPProvider

__all__ = ["LocalHTTPProvider"]
