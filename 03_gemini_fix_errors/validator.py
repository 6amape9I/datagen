# gemini_generate/validator.py
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# --- Импортируем путь к лог-файлу из config ---
from config import VALIDATOR_LOG_PATH, ALL_RELATION_NAMES
from utils.preprocessed_utils import get_units, get_unit_map


def _build_logger() -> logging.Logger:
    """Создает отдельный логгер, чтобы другие basicConfig не мешали."""
    logger = logging.getLogger("validator")
    if logger.handlers:
        return logger

    log_path = Path(VALIDATOR_LOG_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logger.setLevel(logging.WARNING)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = _build_logger()


def validate_response(original_sentence_data: Dict[str, Any], llm_nodes: List[Dict[str, Any]]) -> bool:
    """
    Проверяет, что ответ от LLM соответствует требованиям:
    1. Набор ID совпадает с canonical units.
    2. Роль входит в общую онтологию.
    3. ROOT разрешен только для unit с syntactic_link_target_id == null.
    """
    original_nodes = get_units(original_sentence_data)
    sentence_text = original_sentence_data.get("text", "N/A")

    original_ids = {node["unit_id"] for node in original_nodes if node.get("unit_id")}
    llm_ids = {node.get('id') for node in llm_nodes}
    if len(llm_ids) != len(llm_nodes):
        print("  - ❌ Валидация провалена: в ответе есть дублирующиеся ID.")
        return False

    if original_ids != llm_ids:
        print(f"  - ❌ Валидация провалена: ID не совпадают.")
        print(f"    - Лишние ID в ответе: {llm_ids - original_ids}")
        print(f"    - Недостающие ID в ответе: {original_ids - llm_ids}")
        return False

    original_nodes_map = get_unit_map(original_sentence_data)
    allowed_relations = set(ALL_RELATION_NAMES)

    for llm_node in llm_nodes:
        node_id = llm_node['id']
        chosen_link = llm_node.get('syntactic_link_name')
        if chosen_link not in allowed_relations:
            logger.warning(
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
            continue

        target_id = original_node.get("syntactic_link_target_id")
        if chosen_link == "ROOT" and target_id is not None:
            print(f"  - ❌ Валидация провалена: для id '{node_id}' ROOT указан не для корневого unit.")
            return False
        if chosen_link != "ROOT" and target_id is None:
            print(f"  - ❌ Валидация провалена: для id '{node_id}' корневой unit должен иметь роль ROOT.")
            return False

    return True
