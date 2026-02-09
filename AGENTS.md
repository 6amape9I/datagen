# Repository Guidelines

## Project Structure & Modules
- Stages: `01_preprocessor/`, `02_local_generation/`, `03_gemini_fix_errors/`, `04_postprocessor/`.
- Shared config: `config/` (see `config/paths.py` for dataset/log paths).
- Utilities: `utils/` (helpers and analysis scripts).
- Data & logs: `datasets/01_raw_corpus`, `datasets/02_preprocessed`, `datasets/03_local_generated`, `datasets/04_fixed`, `datasets/05_final`, and `logs/`.
- Example raw file: `datasets/01_raw_corpus/ru_syntagrus-ud-train-a.conllu`.

## Build, Test, and Dev Commands
- Environment: Python 3.12+. Create a venv and install deps: `pip install pyconll google-genai tqdm`.
- Preprocess SynTagRus: `python 01_preprocessor/main.py` → writes JSON to `datasets/02_preprocessed`.
- Local generation (LLM): `python 02_local_generation/pipeline.py` → writes JSONL to `datasets/03_local_generated`.
- Gemini fix errors: `python 03_gemini_fix_errors/pipeline.py` → writes JSONL to `datasets/04_fixed`.
  - Configure API keys via `GEMINI_API_KEYS="key1,key2"` (overrides `config/generate_conf.py`).
- Postprocess final dataset: `python 04_postprocessor/prepare_final_dataset.py` → writes to `datasets/05_final`.
- Optional analysis: `python utils/analyze_dataset.py`.

## Coding Style & Naming
- Python: 4-space indentation, type hints where practical, `snake_case` for functions/vars.
- Keep stage folder prefixes (`01_`, `02_`, `03_`) and place shared constants in `config/`.
- Do not hardcode paths; import from `config` (e.g., `from config import PREPROCESSED_DATA_DIR`).
- Use logging to files under `logs/` (see `PROCESSOR_LOG_PATH`, `VALIDATOR_LOG_PATH`).

## Testing Guidelines
- No formal suite yet. Prefer `pytest` for new tests under `tests/`.
- Add smoke checks for: candidate generation, validator ID parity, and pipeline I/O.
- For quick manual verification, run each stage on a tiny subset and inspect outputs.

## Commit & PR Guidelines
- Messages: imperative, scoped, concise (e.g., `preprocessor: fix candidate sorting`).
- PRs: include summary, rationale, sample commands used, and relevant log snippets from `logs/*.log`.
- Link issues and note data/compute implications.

## Security & Config Tips
- Never commit API keys. Prefer `GEMINI_API_KEYS` env var; multiple keys comma-separated.
- Large data and logs are gitignored; do not commit corpora.
- Rate limits: worker counts and quotas live in `config/pipeline_conf.py`. Adjust carefully.

## Agent-Specific Notes
- Reuse centralized config and dataset layout; avoid introducing ad-hoc folders.
- If adding paths, update `config/paths.py` and keep read/write under `datasets/`.
