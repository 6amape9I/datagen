from __future__ import annotations

from typing import Any


def build_model_input(preprocessed_sentence: dict[str, Any]) -> dict[str, Any]:
    compact_nodes = preprocessed_sentence.get("nodes", [])
    node_map = {
        str(node["id"]): node
        for node in compact_nodes
        if isinstance(node, dict) and node.get("id")
    }

    payload_nodes: list[dict[str, Any]] = []
    for node in compact_nodes:
        if not isinstance(node, dict) or not node.get("id"):
            continue

        target_id = node.get("syntactic_link_target_id")
        head_lemma = None
        if target_id:
            head_node = node_map.get(str(target_id))
            if isinstance(head_node, dict):
                head_lemma = head_node.get("lemma")

        payload_node = {
            "id": node.get("id"),
            "name": node.get("name"),
            "lemma": node.get("lemma"),
            "pos_universal": node.get("pos_universal"),
            "features": node.get("features", {}),
            "syntactic_link_target_id": target_id,
            "original_deprel": node.get("original_deprel"),
        }

        introduced_by = node.get("introduced_by") or []
        if introduced_by:
            payload_node["introduced_by"] = introduced_by
        if head_lemma:
            payload_node["head_lemma"] = head_lemma

        payload_nodes.append(payload_node)

    return {
        "text": preprocessed_sentence.get("text", ""),
        "nodes": payload_nodes,
    }
