from __future__ import annotations

from typing import Any, Dict, List, Optional

from heuristic_candidates import generate_soft_candidates
from schemas import RawToken, SemanticUnit


def _legacy_name(unit: SemanticUnit, token_map: Dict[str, RawToken]) -> str:
    head = token_map[unit.head_token_id]
    name = head.form
    if unit.introduced_by:
        prefix = "-".join(attachment.form for attachment in unit.introduced_by)
        name = f"{prefix}_{name}"
    if unit.function_parts:
        suffix = "-".join(attachment.form for attachment in unit.function_parts)
        name = f"{name}-{suffix}"
    return name


def _legacy_link_introduction_info(unit: SemanticUnit) -> Optional[Dict[str, str]]:
    for attachment in unit.introduced_by:
        if attachment.attachment_type in {"marker", "coordinator", "adposition"}:
            return {
                "marker_word": attachment.form,
                "marker_deprel": attachment.relation,
            }
    return None


def export_legacy_nodes(
    units: List[SemanticUnit],
    token_map: Dict[str, RawToken],
    *,
    include_candidates: bool = True,
) -> List[Dict[str, Any]]:
    legacy_nodes: List[Dict[str, Any]] = []
    for unit in units:
        candidates = generate_soft_candidates(
            unit,
            token_map,
            include_global_fallback=include_candidates,
        )
        node = {
            "id": unit.unit_id,
            "name": _legacy_name(unit, token_map),
            "lemma": unit.core_lemma,
            "pos_universal": unit.upos,
            "pos_specific": unit.xpos,
            "features": unit.features,
            "syntactic_link_candidates": candidates,
            "syntactic_link_target_id": unit.syntactic_link_target_id,
            "original_deprel": unit.original_deprel,
        }
        link_info = _legacy_link_introduction_info(unit)
        if link_info:
            node["link_introduction_info"] = link_info
        if unit.function_parts:
            node["function_parts"] = [attachment.form for attachment in unit.function_parts]
        legacy_nodes.append(node)
    return legacy_nodes
