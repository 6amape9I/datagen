from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
DATASETS_ROOT = PROJECT_ROOT / "datasets"

RAW_CORPUS_DIR = DATASETS_ROOT / "01_raw_corpus"
PREPROCESSED_DATA_DIR = DATASETS_ROOT / "02_preprocessed"
LOCAL_GENERATED_DATA_DIR = DATASETS_ROOT / "03_local_generated"
FIXED_DATA_DIR = DATASETS_ROOT / "04_fixed"
FINAL_DATASET_DIR = DATASETS_ROOT / "05_final"

LOGS_DIR = PROJECT_ROOT / "logs"

PROCESSOR_LOG_PATH = LOGS_DIR / "processor.log"
VALIDATOR_LOG_PATH = LOGS_DIR / "validator_errors.log"
SCHEDULER_LOG_PATH = LOGS_DIR / "scheduler_summary.log"
LOCAL_GENERATION_LOG_PATH = LOGS_DIR / "local_generation_errors.log"


def ensure_runtime_dirs(*paths: Path) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def ensure_stage01_runtime_dirs() -> None:
    ensure_runtime_dirs(PREPROCESSED_DATA_DIR, LOGS_DIR)


def ensure_stage02_runtime_dirs() -> None:
    ensure_runtime_dirs(LOCAL_GENERATED_DATA_DIR, LOGS_DIR)


def ensure_stage03_runtime_dirs() -> None:
    ensure_runtime_dirs(FIXED_DATA_DIR, LOGS_DIR)


def ensure_stage04_runtime_dirs() -> None:
    ensure_runtime_dirs(FINAL_DATASET_DIR)
