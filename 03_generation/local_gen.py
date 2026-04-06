from __future__ import annotations

import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
for path in (PROJECT_ROOT, CURRENT_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from pipeline import run_generation_pipeline
from providers.local_http import LocalHTTPProvider


def main() -> None:
    run_generation_pipeline(LocalHTTPProvider())


if __name__ == "__main__":
    main()
