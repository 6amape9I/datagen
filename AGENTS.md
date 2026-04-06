# Repository Guidelines

## Project Structure & Modules
- Stages: `01_preprocessor/`, `02_local_generation/`, `03_annotation/`, `04_postprocessor/`.
- Shared config: `config/` with pure path definitions in `config/paths.py`.
- Utilities: `utils/`.
- Data & logs: `datasets/01_raw_corpus`, `datasets/02_preprocessed`, `datasets/03_local_generated`, `datasets/04_fixed`, `datasets/05_final`, and `logs/`.

## Build, Test, and Dev Commands
- Environment: Python 3.12+. Install deps: `pip install pyconll google-genai tqdm requests pytest`.
- Preprocess corpus: `python 01_preprocessor/main.py` -> writes compact JSON to `datasets/02_preprocessed`.
- Local generation: `python 02_local_generation/pipeline.py` -> writes JSONL to `datasets/03_local_generated`.
- Annotation/fix stage: `python 03_annotation/pipeline.py` -> writes JSONL to `datasets/04_fixed`.
  - Configure API keys via `GEMINI_API_KEYS="key1,key2"` when using Google GenAI.
- Scheduler: `python 03_annotation/scheduler.py`.
- Final dataset: `python 04_postprocessor/prepare_final_dataset.py` -> writes to `datasets/05_final`.
- Optional analysis: `python utils/analyze_dataset.py`.

## Coding Style & Naming
- Python: 4-space indentation, type hints where practical, `snake_case` for functions and variables.
- Keep stage folder prefixes and shared constants in `config/`.
- Do not hardcode paths; import from `config`.
- Do not create directories at import time. Create runtime dirs only inside entrypoints or explicit setup helpers.

## Testing Guidelines
- Use `pytest` under `01_preprocessor/tests/`.
- Prefer smoke checks for compact node export, validator ID parity, and Stage 01/03/04 contract correctness.
- For quick manual verification, run each stage on a tiny subset and inspect outputs.

## Commit & PR Guidelines
- Messages: imperative, scoped, concise, for example `preprocessor: compact stage01 export`.
- PRs: include summary, rationale, commands used, and relevant log snippets from `logs/*.log`.

## Security & Config Tips
- Never commit API keys.
- Large data and logs are gitignored; do not commit corpora.
- Worker limits and retry settings live in `config/pipeline_conf.py`.
- Optional private overrides may live in `config/generate_conf.py`, but the repo must import cleanly without that file.

## Agent-Specific Notes
- Stage 01 production output is compact `nodes[]` only.
- Do not reintroduce compatibility layers such as `legacy_nodes`, schema fallbacks, or debug data into production JSON.
- Keep read/write operations under `datasets/`.
