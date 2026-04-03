from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from exporter import export_sentence_records
from reader import iter_sentences
from schemas import SentenceRecord
from token_normalizer import normalize_sentence_tokens
from unit_builder import build_nodes


def build_sentence_record(
    sentence: Any,
    *,
    sentence_index: int,
    sentence_id_prefix: str,
    language_code: str,
    split: str,
    source_file: str,
) -> SentenceRecord:
    sentence_id = f"{sentence_id_prefix}_{sentence_index + 1}"
    raw_tokens = normalize_sentence_tokens(sentence)
    nodes = build_nodes(raw_tokens, language_code=language_code)
    return SentenceRecord(
        sentence_id=sentence_id,
        text=sentence.text,
        language_code=language_code,
        split=split,
        source_file=source_file,
        nodes=nodes,
    )


def process_conllu_file(
    filepath: Path,
    *,
    sentence_id_prefix: str,
    language_code: str,
    split: str,
    source_file: str,
    sentence_limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    records: List[SentenceRecord] = []
    for sentence_index, sentence in iter_sentences(filepath, sentence_limit=sentence_limit):
        records.append(
            build_sentence_record(
                sentence,
                sentence_index=sentence_index,
                sentence_id_prefix=sentence_id_prefix,
                language_code=language_code,
                split=split,
                source_file=source_file,
            )
        )
    return export_sentence_records(records)
