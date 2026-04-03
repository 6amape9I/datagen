from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from config import PROCESSOR_LOG_PATH
from sentence_builder import process_conllu_file


_LOGGER: logging.Logger | None = None


def _get_logger() -> logging.Logger:
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    PROCESSOR_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("stage01_preprocessor")
    if not logger.handlers:
        handler = logging.FileHandler(PROCESSOR_LOG_PATH, mode="w", encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.setLevel(logging.WARNING)
        logger.addHandler(handler)
        logger.propagate = False
    _LOGGER = logger
    return logger


def process_syntagrus_file(
    filepath: Path,
    source_filename: str,
    language_code: Optional[str] = None,
    split_name: Optional[str] = None,
    sentence_limit: Optional[int] = None,
) -> List[Dict[str, object]]:
    print(f"Обработка файла: {filepath.name}...")
    try:
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
        )
    except Exception as exc:
        _get_logger().exception("Ошибка Stage 01 при обработке файла %s: %s", filepath.name, exc)
        print(f"Ошибка при загрузке файла {filepath.name}: {exc}")
        return []
