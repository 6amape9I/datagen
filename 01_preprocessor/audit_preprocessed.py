from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from attachment_policy import classify_attachment_type, decide_attachment
from config import PREPROCESSED_DATA_DIR, RAW_CORPUS_DIR
from reader import detect_split_from_filename, iter_sentences
from schemas import serialize_node
from token_normalizer import normalize_sentence_tokens
from unit_builder import build_nodes


REPRESENTATIVE_TREEBANKS = [
    "UD_English-GUM",
    "UD_German-HDT",
    "UD_French-GSD",
    "UD_Russian-SynTagRus",
    "UD_Finnish-TDT",
    "UD_Japanese-GSD",
    "UD_Chinese-GSD",
    "UD_Hebrew-HTB",
    "UD_Armenian-ArmTDP",
]
FUNCTION_POS = {"ADP", "AUX", "CCONJ", "SCONJ", "PART", "DET", "PRON"}


@dataclass
class AuditSummary:
    treebank: str
    split: str
    sentences: int
    nodes: int
    avg_nodes_per_sentence: float
    introduced_by_ratio: float
    marker_start_ratio: float
    single_function_node_ratio: float
    function_pos_ratio: float
    long_surface_ratio: float
    duplicate_marker_ratio: float
    original_deprel_top: list[tuple[str, int]]
    suspicious_function_surfaces: list[tuple[str, int]]
    suspicious_long_surfaces: list[tuple[str, int]]
    suspicious_duplicate_markers: list[tuple[str, int]]
    decision_actions: list[tuple[str, int]]
    decision_attachment_types: list[tuple[str, int]]
    decision_reasons: list[tuple[str, int]]


def _iter_preprocessed_files(treebanks: list[str], splits: list[str]) -> Iterable[Path]:
    if not PREPROCESSED_DATA_DIR.exists():
        return []
    for path in sorted(PREPROCESSED_DATA_DIR.glob("*.json")):
        treebank, _, split_ext = path.name.rpartition("_")
        split = split_ext.replace(".json", "")
        if treebanks and treebank not in treebanks:
            continue
        if splits and split not in splits:
            continue
        yield path


def _load_records(path: Path, sentence_limit: int | None = None) -> list[dict[str, Any]]:
    if sentence_limit is None:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [item for item in data if isinstance(item, dict)]

    text = path.read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    index = 0
    length = len(text)
    records: list[dict[str, Any]] = []

    while index < length and text[index].isspace():
        index += 1
    if index >= length or text[index] != "[":
        return []
    index += 1

    while index < length and len(records) < sentence_limit:
        while index < length and text[index].isspace():
            index += 1
        if index >= length or text[index] == "]":
            break
        record, index = decoder.raw_decode(text, index)
        if isinstance(record, dict):
            records.append(record)
        while index < length and text[index].isspace():
            index += 1
        if index < length and text[index] == ",":
            index += 1

    return records


def _starts_with_marker(name: str, introduced_by: list[str]) -> bool:
    normalized_name = str(name).strip()
    return any(normalized_name.startswith(str(marker).strip()) for marker in introduced_by)


def _duplicate_marker_in_surface(name: str, introduced_by: list[str]) -> bool:
    normalized_name = str(name)
    for marker in introduced_by:
        cleaned = str(marker).strip()
        if cleaned and normalized_name.count(cleaned) > 1:
            return True
    return False


def _is_long_surface(name: str) -> bool:
    parts = str(name).split()
    if len(parts) >= 5:
        return True
    return len(str(name)) >= 24 and len(parts) >= 3


def _audit_preprocessed_file(path: Path, sentence_limit: int | None = None) -> AuditSummary:
    treebank, _, split_ext = path.name.rpartition("_")
    split = split_ext.replace(".json", "")
    records = _load_records(path, sentence_limit=sentence_limit)
    return _audit_records(treebank, split, records, sentence_limit=sentence_limit)


def _audit_records(
    treebank: str,
    split: str,
    records: list[dict[str, Any]],
    *,
    sentence_limit: int | None = None,
) -> AuditSummary:
    all_nodes = [node for record in records for node in record.get("nodes", []) if isinstance(node, dict)]

    deprel_counter: Counter[str] = Counter()
    suspicious_function: Counter[str] = Counter()
    suspicious_long: Counter[str] = Counter()
    suspicious_duplicate: Counter[str] = Counter()
    introduced_by_count = 0
    marker_start_count = 0
    single_function_count = 0
    function_pos_count = 0
    long_surface_count = 0
    duplicate_marker_count = 0

    for node in all_nodes:
        name = str(node.get("name", "")).strip()
        introduced_by = [str(item) for item in node.get("introduced_by", []) if str(item).strip()]
        pos = node.get("pos_universal")
        deprel = node.get("original_deprel")

        if deprel:
            deprel_counter[str(deprel)] += 1
        if introduced_by:
            introduced_by_count += 1
            if _starts_with_marker(name, introduced_by):
                marker_start_count += 1
            if _duplicate_marker_in_surface(name, introduced_by):
                duplicate_marker_count += 1
                suspicious_duplicate[name] += 1
        if pos in FUNCTION_POS:
            function_pos_count += 1
            if len(name.split()) == 1:
                single_function_count += 1
                suspicious_function[name] += 1
        if _is_long_surface(name):
            long_surface_count += 1
            suspicious_long[name] += 1

    decision_actions, decision_types, decision_reasons = _audit_decisions(treebank, split, sentence_limit=sentence_limit)
    node_count = len(all_nodes)
    sentence_count = len(records)

    return AuditSummary(
        treebank=treebank,
        split=split,
        sentences=sentence_count,
        nodes=node_count,
        avg_nodes_per_sentence=(node_count / sentence_count) if sentence_count else 0.0,
        introduced_by_ratio=(introduced_by_count / node_count) if node_count else 0.0,
        marker_start_ratio=(marker_start_count / node_count) if node_count else 0.0,
        single_function_node_ratio=(single_function_count / node_count) if node_count else 0.0,
        function_pos_ratio=(function_pos_count / node_count) if node_count else 0.0,
        long_surface_ratio=(long_surface_count / node_count) if node_count else 0.0,
        duplicate_marker_ratio=(duplicate_marker_count / node_count) if node_count else 0.0,
        original_deprel_top=deprel_counter.most_common(12),
        suspicious_function_surfaces=suspicious_function.most_common(12),
        suspicious_long_surfaces=suspicious_long.most_common(12),
        suspicious_duplicate_markers=suspicious_duplicate.most_common(12),
        decision_actions=decision_actions,
        decision_attachment_types=decision_types,
        decision_reasons=decision_reasons,
    )


def _audit_decisions(treebank: str, split: str, sentence_limit: int | None = None) -> tuple[list[tuple[str, int]], list[tuple[str, int]], list[tuple[str, int]]]:
    raw_dir = RAW_CORPUS_DIR / treebank
    action_counter: Counter[str] = Counter()
    type_counter: Counter[str] = Counter()
    reason_counter: Counter[str] = Counter()

    if not raw_dir.exists():
        return [], [], []

    sentences_seen = 0
    for conllu_path in sorted(raw_dir.rglob("*.conllu")):
        if detect_split_from_filename(conllu_path.name) != split:
            continue
        for _, sentence in iter_sentences(conllu_path):
            raw_tokens = normalize_sentence_tokens(sentence)
            token_map = {candidate.token_id: candidate for candidate in raw_tokens if candidate.token_id}
            for token in raw_tokens:
                decision = decide_attachment(token, token_map, language_code=treebank)
                action_counter[decision.action] += 1
                if decision.attachment_type:
                    type_counter[decision.attachment_type] += 1
                if decision.reason:
                    reason_counter[decision.reason] += 1
            sentences_seen += 1
            if sentence_limit is not None and sentences_seen >= sentence_limit:
                return action_counter.most_common(), type_counter.most_common(12), reason_counter.most_common(12)

    return action_counter.most_common(), type_counter.most_common(12), reason_counter.most_common(12)


def _rebuild_records(treebank: str, split: str, sentence_limit: int | None = None) -> list[dict[str, Any]]:
    raw_dir = RAW_CORPUS_DIR / treebank
    records: list[dict[str, Any]] = []
    if not raw_dir.exists():
        return records

    for conllu_path in sorted(raw_dir.rglob("*.conllu")):
        if detect_split_from_filename(conllu_path.name) != split:
            continue
        rel_name = str(conllu_path.relative_to(raw_dir)).replace("\\", "/").replace("/", "__")
        source_file = f"{treebank}_{rel_name}"
        for sentence_index, sentence in iter_sentences(conllu_path, sentence_limit=sentence_limit):
            raw_tokens = normalize_sentence_tokens(sentence)
            nodes = [serialize_node(node) for node in build_nodes(raw_tokens, language_code=treebank)]
            records.append(
                {
                    "sentence_id": f"{source_file}_{sentence_index + 1}",
                    "text": sentence.text,
                    "language_code": treebank,
                    "split": split,
                    "source_file": source_file,
                    "nodes": nodes,
                }
            )
        break
    return records


def _audit_rebuilt_treebank(treebank: str, split: str, sentence_limit: int | None = None) -> AuditSummary:
    records = _rebuild_records(treebank, split, sentence_limit=sentence_limit)
    return _audit_records(treebank, split, records, sentence_limit=sentence_limit)


def _summary_to_markdown(summary: AuditSummary) -> str:
    return "\n".join(
        [
            f"### {summary.treebank} `{summary.split}`",
            f"- sentences: {summary.sentences}",
            f"- nodes: {summary.nodes}",
            f"- avg nodes/sentence: {summary.avg_nodes_per_sentence:.2f}",
            f"- introduced_by ratio: {summary.introduced_by_ratio:.2%}",
            f"- marker-start ratio: {summary.marker_start_ratio:.2%}",
            f"- single function-word node ratio: {summary.single_function_node_ratio:.2%}",
            f"- function POS ratio: {summary.function_pos_ratio:.2%}",
            f"- long-surface ratio: {summary.long_surface_ratio:.2%}",
            f"- duplicate-marker ratio: {summary.duplicate_marker_ratio:.2%}",
            f"- top deprels: {summary.original_deprel_top}",
            f"- top single function surfaces: {summary.suspicious_function_surfaces}",
            f"- top long surfaces: {summary.suspicious_long_surfaces}",
            f"- top duplicate markers: {summary.suspicious_duplicate_markers}",
            f"- decision actions: {summary.decision_actions}",
            f"- decision attachment types: {summary.decision_attachment_types}",
            f"- decision reasons: {summary.decision_reasons}",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit compact Stage 01 preprocessed outputs.")
    parser.add_argument("--treebanks", nargs="*", default=REPRESENTATIVE_TREEBANKS)
    parser.add_argument("--splits", nargs="*", default=["train"])
    parser.add_argument("--sentence-limit", type=int, default=400)
    parser.add_argument("--mode", choices=["preprocessed", "rebuild"], default="preprocessed")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    summaries: list[AuditSummary] = []
    if args.mode == "preprocessed":
        for path in _iter_preprocessed_files(args.treebanks, args.splits):
            summaries.append(_audit_preprocessed_file(path, sentence_limit=args.sentence_limit))
    else:
        for treebank in args.treebanks:
            for split in args.splits:
                summaries.append(_audit_rebuilt_treebank(treebank, split, sentence_limit=args.sentence_limit))

    if args.output_json:
        args.output_json.write_text(
            json.dumps([summary.__dict__ for summary in summaries], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    markdown = "# Stage 01 Audit\n\n" + "\n\n".join(_summary_to_markdown(summary) for summary in summaries)
    if args.output_md:
        args.output_md.write_text(markdown, encoding="utf-8")
    print(markdown)


if __name__ == "__main__":
    main()
