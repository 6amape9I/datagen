from __future__ import annotations

from typing import Any

from response_schema import get_annotation_roles


def validate_response(original_sentence_data: dict[str, Any], llm_nodes: list[dict[str, Any]]) -> bool:
    original_nodes = original_sentence_data.get("nodes", [])
    original_ids = [str(node.get("id")) for node in original_nodes if isinstance(node, dict) and node.get("id")]
    response_ids = [str(node.get("id")) for node in llm_nodes if isinstance(node, dict) and node.get("id")]

    if len(response_ids) != len(llm_nodes):
        return False
    if set(original_ids) != set(response_ids):
        return False

    original_nodes_map = {
        str(node["id"]): node
        for node in original_nodes
        if isinstance(node, dict) and node.get("id")
    }
    allowed_relations = set(get_annotation_roles())

    for llm_node in llm_nodes:
        if not isinstance(llm_node, dict):
            return False
        if set(llm_node.keys()) != {"id", "syntactic_link_name"}:
            return False

        node_id = str(llm_node.get("id"))
        chosen_link = llm_node.get("syntactic_link_name")

        if chosen_link not in allowed_relations:
            return False

        original_node = original_nodes_map.get(node_id)
        if original_node is None:
            return False

        target_id = original_node.get("syntactic_link_target_id")
        if target_id is None and chosen_link != "ROOT":
            return False
        if target_id is not None and chosen_link == "ROOT":
            return False

    return True
