from __future__ import annotations

from typing import Any, Dict, List

from schemas import SentenceRecord


def export_sentence_records(records: List[SentenceRecord]) -> List[Dict[str, Any]]:
    return [record.to_dict() for record in records]
