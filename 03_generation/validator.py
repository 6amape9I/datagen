from __future__ import annotations

from typing import Any

from response_schema import get_annotation_roles


def validate_response_with_reason(
    original_sentence_data: dict[str, Any],
    llm_nodes: list[dict[str, Any]],
) -> tuple[bool, str | None]:
    original_nodes = original_sentence_data.get("nodes", [])
    original_ids = [str(node.get("id")) for node in original_nodes if isinstance(node, dict) and node.get("id")]
    response_ids = [str(node.get("id")) for node in llm_nodes if isinstance(node, dict) and node.get("id")]

    if len(response_ids) != len(llm_nodes):
        return False, "response contains node entries without valid id"
    if set(original_ids) != set(response_ids):
        missing_ids = sorted(set(original_ids) - set(response_ids))
        extra_ids = sorted(set(response_ids) - set(original_ids))
        return False, f"id mismatch: missing={missing_ids} extra={extra_ids}"
    if len(response_ids) != len(set(response_ids)):
        return False, "response contains duplicate node ids"

    original_nodes_map = {
        str(node["id"]): node
        for node in original_nodes
        if isinstance(node, dict) and node.get("id")
    }
    allowed_relations = set(get_annotation_roles())

    for llm_node in llm_nodes:
        if not isinstance(llm_node, dict):
            return False, "response node is not an object"
        if set(llm_node.keys()) != {"id", "syntactic_link_name"}:
            return False, f"response node has unexpected keys: {sorted(llm_node.keys())}"

        node_id = str(llm_node.get("id"))
        chosen_link = llm_node.get("syntactic_link_name")

        if chosen_link not in allowed_relations:
            return False, f"invalid relation '{chosen_link}' for node {node_id}"

        original_node = original_nodes_map.get(node_id)
        if original_node is None:
            return False, f"node {node_id} is not present in source sentence"

        target_id = original_node.get("syntactic_link_target_id")
        if target_id is None and chosen_link != "ROOT":
            return False, f"node {node_id} must be ROOT because it has no syntactic head"
        if target_id is not None and chosen_link == "ROOT":
            return False, f"node {node_id} cannot be ROOT because its head is {target_id}"

    return True, None


def validate_response(original_sentence_data: dict[str, Any], llm_nodes: list[dict[str, Any]]) -> bool:
    is_valid, _ = validate_response_with_reason(original_sentence_data, llm_nodes)
    return is_valid
