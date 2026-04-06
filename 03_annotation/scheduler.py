"""Compatibility wrapper for the canonical 03_generation scheduler."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TARGET_PATH = PROJECT_ROOT / "03_generation" / "scheduler.py"
for path in (PROJECT_ROOT, TARGET_PATH.parent):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def _load_scheduler_entrypoint():
    spec = importlib.util.spec_from_file_location("generation_scheduler_wrapper", TARGET_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load canonical scheduler entrypoint from {TARGET_PATH}.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_scheduler_once() -> None:
    print("⚠️  03_annotation/scheduler.py is deprecated. Redirecting to 03_generation/scheduler.py.")
    _load_scheduler_entrypoint().run_scheduler_once()


if __name__ == "__main__":
    run_scheduler_once()
