from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from config import ALL_RELATION_NAMES, VALIDATOR_LOG_PATH


_LOGGER: logging.Logger | None = None


def _get_logger() -> logging.Logger:
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    VALIDATOR_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("validator")
    if not logger.handlers:
        handler = logging.FileHandler(VALIDATOR_LOG_PATH, mode="a", encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.setLevel(logging.WARNING)
        logger.addHandler(handler)
        logger.propagate = False
    _LOGGER = logger
    return logger


def validate_response(original_sentence_data: Dict[str, Any], llm_nodes: List[Dict[str, Any]]) -> bool:
    original_nodes = original_sentence_data.get("nodes", [])
    sentence_text = original_sentence_data.get("text", "N/A")

    original_ids = {node.get("id") for node in original_nodes if node.get("id")}
    llm_ids = {node.get("id") for node in llm_nodes if node.get("id")}

    if len(llm_ids) != len(llm_nodes):
        print("  - ❌ Валидация провалена: в ответе есть дублирующиеся ID.")
        return False
    if original_ids != llm_ids:
        print("  - ❌ Валидация провалена: ID не совпадают.")
        print(f"    - Лишние ID в ответе: {llm_ids - original_ids}")
        print(f"    - Недостающие ID в ответе: {original_ids - llm_ids}")
        return False

    original_nodes_map = {
        str(node["id"]): node
        for node in original_nodes
        if isinstance(node, dict) and node.get("id")
    }
    allowed_relations = set(ALL_RELATION_NAMES)

    for llm_node in llm_nodes:
        node_id = llm_node["id"]
        chosen_link = llm_node.get("syntactic_link_name")
        if chosen_link not in allowed_relations:
            _get_logger().warning(
                "ОШИБКА ВАЛИДАЦИИ: роль вне онтологии.\n%s",
                json.dumps(
                    {
                        "sentence_text": sentence_text,
                        "node_id": node_id,
                        "invalid_role": chosen_link,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
            print(f"  - ❌ Валидация провалена: для id '{node_id}' указана роль вне онтологии: '{chosen_link}'.")
            return False

        original_node = original_nodes_map.get(node_id)
        if not original_node:
            return False

        target_id = original_node.get("syntactic_link_target_id")
        if chosen_link == "ROOT" and target_id is not None:
            print(f"  - ❌ Валидация провалена: для id '{node_id}' ROOT указан не для корневого узла.")
            return False
        if chosen_link != "ROOT" and target_id is None:
            print(f"  - ❌ Валидация провалена: для id '{node_id}' корневой узел должен иметь роль ROOT.")
            return False

    return True
