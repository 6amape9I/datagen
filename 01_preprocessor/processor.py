import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import PROCESSOR_LOG_PATH
from report import get_and_reset_report
from sentence_builder import process_conllu_file


def _build_logger() -> logging.Logger:
    logger = logging.getLogger("stage01_preprocessor")
    if logger.handlers:
        return logger

    handler = logging.FileHandler(PROCESSOR_LOG_PATH, mode="w", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.setLevel(logging.WARNING)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = _build_logger()

def get_and_reset_fallback_any_count() -> int:
    return get_and_reset_report().legacy_candidate_fallback_count


def process_syntagrus_file(
    filepath: Path,
    source_filename: str,
    language_code: Optional[str] = None,
    split_name: Optional[str] = None,
    sentence_limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    print(f"Обработка файла: {filepath.name}...")
    try:
        export_mode = os.environ.get("PREPROCESSOR_EXPORT_MODE", "canonical").strip().lower()
        enable_soft_candidates = os.environ.get("ENABLE_SOFT_CANDIDATES", "").strip().lower() in {"1", "true", "yes"}
        enable_legacy_candidates = os.environ.get("ENABLE_LEGACY_CANDIDATES", "").strip().lower() in {"1", "true", "yes"}
        allow_legacy_candidate_fallback = os.environ.get("ENABLE_LEGACY_CANDIDATE_FALLBACK", "").strip().lower() in {"1", "true", "yes"}
        inferred_language_code = language_code or source_filename.split("_", 1)[0]
        inferred_split_name = split_name or (
            "train" if "train" in filepath.name.lower()
            else "val" if "dev" in filepath.name.lower() or "val" in filepath.name.lower()
            else "test" if "test" in filepath.name.lower()
            else "unknown"
        )
        return process_conllu_file(
            filepath,
            sentence_id_prefix=source_filename,
            language_code=inferred_language_code,
            split=inferred_split_name,
            source_file=source_filename,
            sentence_limit=sentence_limit,
            export_mode=export_mode,
            enable_soft_candidates=enable_soft_candidates,
            enable_legacy_candidates=enable_legacy_candidates,
            allow_legacy_candidate_fallback=allow_legacy_candidate_fallback,
        )
    except Exception as exc:
        logger.exception("Ошибка Stage 01 при обработке файла %s: %s", filepath.name, exc)
        print(f"Ошибка при загрузке файла {filepath.name}: {exc}")
        return []
