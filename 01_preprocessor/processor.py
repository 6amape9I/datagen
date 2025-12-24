# preprocessor/processor.py

import pyconll
import logging
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import ALL_RELATIONS_MAP, HEURISTIC_RULES, PROCESSOR_LOG_PATH

# --- ИЗМЕНЕНИЕ: Настраиваем логирование с использованием пути из config ---
logging.basicConfig(
    level=logging.WARNING,
    filename=PROCESSOR_LOG_PATH, # <-- ИСПОЛЬЗУЕМ КОНСТАНТУ
    filemode='w',
    encoding='utf-8',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Счетчик случаев, когда сработал самый общий фолбэк (ANY token)
_FALLBACK_ANY_COUNT = 0
_VALID_TOKEN_ID_PATTERN = re.compile(r"^\d+$")


def _is_valid_token_id(raw_id: Optional[str]) -> bool:
    """Допускаются только целочисленные идентификаторы (без точек и других символов)."""
    if not raw_id:
        return False
    return bool(_VALID_TOKEN_ID_PATTERN.match(str(raw_id)))

def get_and_reset_fallback_any_count() -> int:
    global _FALLBACK_ANY_COUNT
    c = _FALLBACK_ANY_COUNT
    _FALLBACK_ANY_COUNT = 0
    return c


# Функция _check_condition
def _check_condition(value: Any, condition: Any, cond_key: str) -> bool:
    if isinstance(condition, bool): return bool(value) == condition
    if isinstance(condition, list):
        if value is None: return False
        if cond_key == 'deprel' and isinstance(value, str) and ':' in value: value = value.split(':')[0]
        return value in condition
    return value == condition


# Функция generate_candidates_from_rules
def generate_candidates_from_rules(token: pyconll.unit.token.Token, sentence: pyconll.unit.sentence.Sentence,
                                   marker_info: Optional[Dict[str, str]]) -> List[str]:
    global _FALLBACK_ANY_COUNT
    primary_candidates = set()
    fallback_candidates = set()
    any_token_fallback_candidates = set()
    features = token.feats
    token_features = {
        "deprel": token.deprel, "pos": token.upos, "lemma": token.lemma.lower() if token.lemma else "",
        "case": list(features['Case'])[0] if 'Case' in features else None,
        "number": list(features['Number'])[0] if 'Number' in features else None,
        "animacy": list(features['Animacy'])[0] if 'Animacy' in features else None,
        "verb_form": list(features['VerbForm'])[0] if 'VerbForm' in features else None,
        "has_marker": marker_info is not None
    }
    if marker_info: token_features["marker"] = marker_info.get("form", "").lower()
    head_word = sentence[token.head] if token.head and token.head != '0' and token.head in sentence else None
    if head_word:
        head_features = head_word.feats
        token_features["head_lemma"] = head_word.lemma.lower() if head_word.lemma else ""
        token_features["head_degree"] = list(head_features['Degree'])[0] if 'Degree' in head_features else None
    for rule in HEURISTIC_RULES:
        conditions = rule.get("conditions", {})
        if not conditions:
            conditions_met = True
        else:
            conditions_met = False
            for cond_key, cond_value in conditions.items():
                value_to_check = token_features.get(cond_key)
                if _check_condition(value_to_check, cond_value, cond_key):
                    conditions_met = True
                    break
        if conditions_met:
            rule_name = str(rule.get("rule_name", ""))
            is_fallback = rule_name.lower().startswith("fallback")
            is_any_fallback = rule_name.strip().lower() == "fallback for any token"
            target_set = any_token_fallback_candidates if is_any_fallback else (fallback_candidates if is_fallback else primary_candidates)
            for candidate_id in rule["candidates"]:
                candidate_name = ALL_RELATIONS_MAP.get(candidate_id, f"UNKNOWN_ID_{candidate_id}")
                target_set.add(candidate_name)

    if primary_candidates:
        return sorted(primary_candidates)
    if fallback_candidates:
        return sorted(fallback_candidates)
    if any_token_fallback_candidates:
        _FALLBACK_ANY_COUNT += 1
        try:
            node_debug_info = {
                "id": token.id,
                "form": token.form,
                "lemma": token.lemma,
                "upos": token.upos,
                "deprel": token.deprel,
                "head_id": token.head,
                "feats": dict(token.feats),
                "marker_info": marker_info
            }
            logging.warning(
                "FALLBACK_ANY_ACTIVATED: Все остальные fallback-правила не сработали.\n"
                f"  - ПРЕДЛОЖЕНИЕ: {sentence.text}\n"
                f"  - УЗЕЛ (JSON): {json.dumps(node_debug_info, ensure_ascii=False, indent=2)}"
            )
        except Exception:
            pass
        return sorted(any_token_fallback_candidates)
    return []


# Функция process_syntagrus_file
def process_syntagrus_file(filepath: Path, source_filename: str, sentence_limit: int = None) -> List[Dict[str, Any]]:
    print(f"Обработка файла: {filepath.name}...")
    try:
        corpus = pyconll.load_from_file(str(filepath))
    except Exception as e:
        print(f"Ошибка при загрузке файла {filepath.name}: {e}")
        return []
    all_sentences_data = []
    for sent_idx, sentence in enumerate(corpus):
        if sentence_limit and sent_idx >= sentence_limit: break
        internal_sentence_id = str(sent_idx + 1)
        global_sentence_id = f"{source_filename}_{internal_sentence_id}"
        markers_to_merge = {}
        marker_ids_to_remove = set()
        function_parts_to_merge = {}
        function_ids_to_remove = set()

        def find_fixed_chain(start_token):
            if not _is_valid_token_id(start_token.id):
                return []
            chain = [start_token]
            for t in sentence:
                if not _is_valid_token_id(t.id):
                    continue
                if t.head == start_token.id and t.deprel == 'fixed':
                    chain.extend(find_fixed_chain(t))
            return chain

        for token in sentence:
            if not _is_valid_token_id(token.id):
                continue
            if token.id in marker_ids_to_remove: continue
            if token.deprel in ['case', 'cc', 'mark']:
                head_id = token.head
                if head_id and head_id != '0' and _is_valid_token_id(head_id):
                    marker_chain = find_fixed_chain(token)
                    marker_chain.sort(key=lambda t: int(t.id))
                    full_marker_form = "-".join([t.form for t in marker_chain])
                    markers_to_merge[head_id] = {'form': full_marker_form, 'deprel': token.deprel}
                    for part in marker_chain: marker_ids_to_remove.add(part.id)

        # 2) Объединяем прочие служебные элементы (частицы, вводные, фиксированные части выражений, flat/compound)
        FUNCTION_ROOT_DEPRELS = {
            'discourse', 'expl', 'flat', 'flat:name', 'flat:foreign', 'compound', 'list',
            'dislocated', 'dep'
        }
        for token in sentence:
            if not _is_valid_token_id(token.id):
                continue
            if token.id in marker_ids_to_remove or token.id in function_ids_to_remove: continue
            if token.deprel in FUNCTION_ROOT_DEPRELS:
                head_id = token.head
                if head_id and head_id != '0' and _is_valid_token_id(head_id):
                    chain = find_fixed_chain(token)
                    chain.sort(key=lambda t: int(t.id))
                    full_form = "-".join([t.form for t in chain])
                    acc = function_parts_to_merge.setdefault(head_id, [])
                    acc.append(full_form)
                    for part in chain: function_ids_to_remove.add(part.id)
            elif token.deprel == 'fixed':
                # Оставшиеся fixed, не попавшие в маркерные или служебные цепочки — присоединим к их head напрямую
                head_id = token.head
                if head_id and head_id != '0' and _is_valid_token_id(head_id) and token.id not in function_ids_to_remove and token.id not in marker_ids_to_remove:
                    acc = function_parts_to_merge.setdefault(head_id, [])
                    acc.append(token.form)
                    function_ids_to_remove.add(token.id)
            # Дополнительно: сливаем SYM, а также некоторые PART/ADP в нетипичных deprel
            elif token.upos == 'SYM':
                head_id = token.head
                if head_id and head_id != '0' and _is_valid_token_id(head_id):
                    acc = function_parts_to_merge.setdefault(head_id, [])
                    acc.append(token.form)
                    function_ids_to_remove.add(token.id)
            elif token.upos == 'PART' and token.deprel in {'appos', 'orphan', 'dep', 'dislocated'}:
                head_id = token.head
                if head_id and head_id != '0' and _is_valid_token_id(head_id):
                    acc = function_parts_to_merge.setdefault(head_id, [])
                    acc.append(token.form)
                    function_ids_to_remove.add(token.id)
            elif token.upos == 'ADP' and token.deprel in {'appos', 'dislocated', 'dep'}:
                head_id = token.head
                if head_id and head_id != '0' and _is_valid_token_id(head_id):
                    acc = function_parts_to_merge.setdefault(head_id, [])
                    acc.append(token.form)
                    function_ids_to_remove.add(token.id)
        processed_tokens = []
        for token in sentence:
            if (
                token.upos == 'PUNCT'
                or token.id in marker_ids_to_remove
                or token.id in function_ids_to_remove
                or not _is_valid_token_id(token.id)
            ):
                continue
            word_form = token.form
            link_intro_info = None
            marker_info_for_token = markers_to_merge.get(token.id)
            if marker_info_for_token:
                word_form = f"{marker_info_for_token['form']}_{word_form}"
                if marker_info_for_token['deprel'] in ['mark', 'cc']: link_intro_info = {
                    "marker_word": marker_info_for_token['form'], "marker_deprel": marker_info_for_token['deprel']}
            # Добавляем прочие служебные части в конец через дефис
            function_parts = function_parts_to_merge.get(token.id)
            if function_parts:
                word_form = f"{word_form}-" + "-".join(function_parts)
            if token.head is None or token.head == '0' or not _is_valid_token_id(token.head):
                generated_candidates = ["ROOT"]
            else:
                generated_candidates = generate_candidates_from_rules(token, sentence, marker_info_for_token)
                if not generated_candidates:
                    node_debug_info = {"id": token.id, "form": token.form, "lemma": token.lemma, "upos": token.upos,
                                       "deprel": token.deprel, "head_id": token.head, "feats": dict(token.feats),
                                       "marker_info": marker_info_for_token}
                    log_message = (
                        f"Ни одно правило не сработало. Применен глобальный fallback (все роли).\n"
                        f"  - ПРЕДЛОЖЕНИЕ: {sentence.text}\n"
                        f"  - УЗЕЛ (JSON): {json.dumps(node_debug_info, ensure_ascii=False, indent=2)}")
                    logging.warning(log_message)
                    generated_candidates = sorted(ALL_RELATIONS_MAP.values())
            target_id = token.head
            if target_id == '0' or not _is_valid_token_id(target_id):
                target_id = None
            else:
                target_id = f"w{token.head}"
            token_data = {
                "id": f"w{token.id}", "name": word_form, "lemma": token.lemma, "pos_universal": token.upos,
                "pos_specific": token.xpos,
                "features": {k: list(v)[0] for k, v in token.feats.items() if v},
                "syntactic_link_candidates": generated_candidates,
                "syntactic_link_target_id": target_id, "original_deprel": token.deprel
            }
            if link_intro_info: token_data["link_introduction_info"] = link_intro_info
            if function_parts:
                token_data["function_parts"] = function_parts
            processed_tokens.append(token_data)
        if not processed_tokens: continue
        all_sentences_data.append({"sentence_id": global_sentence_id, "text": sentence.text, "nodes": processed_tokens})
    return all_sentences_data
