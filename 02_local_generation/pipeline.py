"""Compatibility wrapper for the canonical 03_generation local entrypoint."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TARGET_PATH = PROJECT_ROOT / "03_generation" / "local_gen.py"
for path in (PROJECT_ROOT, TARGET_PATH.parent):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def _load_local_entrypoint():
    spec = importlib.util.spec_from_file_location("generation_local_gen_wrapper", TARGET_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load canonical local generation entrypoint from {TARGET_PATH}.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_pipeline() -> None:
    print("⚠️  02_local_generation/pipeline.py is deprecated. Redirecting to 03_generation/local_gen.py.")
    _load_local_entrypoint().main()


if __name__ == "__main__":
    run_pipeline()
