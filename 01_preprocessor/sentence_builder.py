from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from exporter import export_sentence_records
from heuristic_candidates import generate_soft_candidates
from reader import iter_sentences
from schemas import SentenceRecord
from token_normalizer import normalize_sentence_tokens
from unit_builder import build_units


EXPORT_MODE_CANONICAL = "canonical"
EXPORT_MODE_CANONICAL_WITH_LEGACY = "canonical+legacy"


def _build_legacy_nodes(
    units,
    token_map,
    *,
    include_candidates: bool,
    allow_global_fallback: bool,
):
    from compat.legacy_export import export_legacy_nodes

    return export_legacy_nodes(
        units,
        token_map,
        include_candidates=include_candidates,
        allow_global_fallback=allow_global_fallback,
    )


def build_sentence_record(
    sentence: Any,
    *,
    sentence_index: int,
    sentence_id_prefix: str,
    language_code: str,
    split: str,
    source_file: str,
    export_mode: str = EXPORT_MODE_CANONICAL,
    enable_soft_candidates: bool = False,
    enable_legacy_candidates: bool = False,
    allow_legacy_candidate_fallback: bool = False,
) -> SentenceRecord:
    sentence_id = f"{sentence_id_prefix}_{sentence_index + 1}"
    raw_tokens = normalize_sentence_tokens(sentence)
    units, token_map = build_units(raw_tokens, language_code=language_code)
    for unit in units:
        unit.semantic_candidates_soft = (
            generate_soft_candidates(
                unit,
                token_map,
                include_global_fallback=False,
            )
            if enable_soft_candidates else []
        )
    legacy_nodes = None
    if export_mode == EXPORT_MODE_CANONICAL_WITH_LEGACY:
        legacy_nodes = _build_legacy_nodes(
            units,
            token_map,
            include_candidates=enable_legacy_candidates,
            allow_global_fallback=allow_legacy_candidate_fallback,
        )
    return SentenceRecord(
        sentence_id=sentence_id,
        text=sentence.text,
        language_code=language_code,
        split=split,
        source_file=source_file,
        tokens=raw_tokens,
        units=units,
        legacy_nodes=legacy_nodes,
    )


def process_conllu_file(
    filepath: Path,
    *,
    sentence_id_prefix: str,
    language_code: str,
    split: str,
    source_file: str,
    sentence_limit: Optional[int] = None,
    export_mode: str = EXPORT_MODE_CANONICAL,
    enable_soft_candidates: bool = False,
    enable_legacy_candidates: bool = False,
    allow_legacy_candidate_fallback: bool = False,
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
                export_mode=export_mode,
                enable_soft_candidates=enable_soft_candidates,
                enable_legacy_candidates=enable_legacy_candidates,
                allow_legacy_candidate_fallback=allow_legacy_candidate_fallback,
            )
        )
    return export_sentence_records(records)
