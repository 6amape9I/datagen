from __future__ import annotations

from typing import Any, Dict, List


def is_preprocessed_v2(sentence_record: Dict[str, Any]) -> bool:
    try:
        return int(sentence_record.get("preprocessed_schema_version", 0)) >= 2
    except (TypeError, ValueError):
        return False


def get_legacy_nodes(sentence_record: Dict[str, Any]) -> List[Dict[str, Any]]:
    legacy_nodes = sentence_record.get("legacy_nodes")
    if isinstance(legacy_nodes, list):
        return [node for node in legacy_nodes if isinstance(node, dict)]

    nodes = sentence_record.get("nodes")
    if isinstance(nodes, list):
        return [node for node in nodes if isinstance(node, dict)]

    return []


def get_units(sentence_record: Dict[str, Any]) -> List[Dict[str, Any]]:
    units = sentence_record.get("units")
    if isinstance(units, list):
        return [unit for unit in units if isinstance(unit, dict)]
    legacy_nodes = get_legacy_nodes(sentence_record)
    if not legacy_nodes:
        return []

    canonical_units: List[Dict[str, Any]] = []
    for node in legacy_nodes:
        canonical_units.append(
            {
                "unit_id": node.get("id"),
                "head_token_id": None,
                "span_token_ids": [],
                "surface": node.get("name"),
                "core_lemma": node.get("lemma"),
                "upos": node.get("pos_universal"),
                "xpos": node.get("pos_specific"),
                "features": node.get("features", {}),
                "syntactic_link_target_id": node.get("syntactic_link_target_id"),
                "original_deprel": node.get("original_deprel"),
                "attached_tokens": [],
                "introduced_by": [],
                "function_parts": [],
                "ud_semantic_hints": [],
                "semantic_candidates_soft": node.get("syntactic_link_candidates", []),
            }
        )
    return canonical_units


def get_unit_map(sentence_record: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    units = get_units(sentence_record)
    return {
        str(unit.get("unit_id")): unit
        for unit in units
        if isinstance(unit, dict) and unit.get("unit_id")
    }


def get_model_input_units(sentence_record: Dict[str, Any]) -> List[Dict[str, Any]]:
    return get_units(sentence_record)
