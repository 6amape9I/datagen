# gemini_generate/validator.py
import logging
import json
from typing import List, Dict, Any

# --- Импортируем путь к лог-файлу из config ---
from config import VALIDATOR_LOG_PATH

# --- Настраиваем логгер с использованием пути из config ---
logging.basicConfig(
    level=logging.WARNING,
    filename=VALIDATOR_LOG_PATH,  # <-- ИСПОЛЬЗУЕМ КОНСТАНТУ
    filemode='w',
    encoding='utf-8',
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def validate_response(original_sentence_data: Dict[str, Any], llm_nodes: List[Dict[str, Any]]) -> bool:
    """
    Проверяет, что ответ от LLM соответствует требованиям:
    1. Набор ID совпадает с исходным (фатальная ошибка).
    2. Выбранная связь была в списке кандидатов (фатальная ошибка, логируется).
    """
    original_nodes = original_sentence_data.get("nodes", [])
    sentence_text = original_sentence_data.get("text", "N/A")

    original_ids = {node['id'] for node in original_nodes}
    llm_ids = {node.get('id') for node in llm_nodes}

    if original_ids != llm_ids:
        print(f"  - ❌ Валидация провалена: ID не совпадают.")
        print(f"    - Лишние ID в ответе: {llm_ids - original_ids}")
        print(f"    - Недостающие ID в ответе: {original_ids - llm_ids}")
        return False

    original_nodes_map = {node['id']: node for node in original_nodes}

    for llm_node in llm_nodes:
        node_id = llm_node['id']
        chosen_link = llm_node.get('syntactic_link_name')

        if chosen_link == "ROOT":
            continue

        original_node = original_nodes_map.get(node_id)
        if not original_node:
            continue

        # Поддержка обоих форматов кандидатов: список объектов или список имен
        raw_candidates = original_node.get('syntactic_link_candidates', [])
        if raw_candidates and isinstance(raw_candidates[0], dict):
            candidate_names = {c.get('name') for c in raw_candidates if isinstance(c, dict) and c.get('name')}
        else:
            candidate_names = set(str(c) for c in raw_candidates)

        # ИЗМЕНЕНО: Строгая проверка
        if chosen_link not in candidate_names:
            print(f"  - ❌ Валидация провалена: для id '{node_id}', ответ '{chosen_link}' не в списке кандидатов.")

            # Логируем детали инцидента
            error_info = {
                "sentence_text": sentence_text,
                "node_info": {
                    "id": node_id,
                    "name": original_node.get("name"),
                    "lemma": original_node.get("lemma"),
                    "deprel": original_node.get("original_deprel"),
                    "features": original_node.get("features"),
                },
                "heuristic_candidates": candidates_with_conf,
                "llm_invalid_choice": chosen_link
            }
            log_message = (
                f"ОШИБКА ВАЛИДАЦИИ: LLM выбрала роль, отсутствующую в списке кандидатов.\n"
                f"{json.dumps(error_info, ensure_ascii=False, indent=2)}"
            )
            logging.warning(log_message)

            # Возвращаем False, чтобы запустить retry
            return False

    return True
