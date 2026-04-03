import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import PROCESSOR_LOG_PATH
from report import get_and_reset_report
from sentence_builder import process_conllu_file

logging.basicConfig(
    level=logging.WARNING,
    filename=PROCESSOR_LOG_PATH,
    filemode="w",
    encoding="utf-8",
    format="%(asctime)s - %(levelname)s - %(message)s",
)

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
            enable_legacy_candidates=True,
        )
    except Exception as exc:
        logging.exception("Ошибка Stage 01 при обработке файла %s: %s", filepath.name, exc)
        print(f"Ошибка при загрузке файла {filepath.name}: {exc}")
        return []
