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
    return []


def get_model_input_units(sentence_record: Dict[str, Any]) -> List[Dict[str, Any]]:
    units = get_units(sentence_record)
    if units:
        return units
    return get_legacy_nodes(sentence_record)
