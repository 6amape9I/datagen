# gemini_generate/pipeline.py
from pathlib import Path

import json
import time
import threading
from queue import Queue
from itertools import cycle
from typing import Set, Dict, Any, List

import requests

# 1. Импортируем все настройки и зависимости из config и локальных модулей
from config import (
    API_KEYS,
    MODEL_NAME,
    NUM_WORKERS,
    MAX_RETRIES,
    INITIAL_BACKOFF_DELAY,
    PREPROCESSED_DATA_DIR,
    FIXED_DATA_DIR,
    LOCAL_API_URL,
    REQUEST_STRATEGY,
)
from gemini_client_comp import generate
from local_client import get_local_model_response
from validator import validate_response
from utils.preprocessed_utils import get_legacy_nodes, get_model_input_units

# --- НАСТРОЙКИ ПАЙПЛАЙНА УДАЛЕНЫ, ТЕПЕРЬ ВСЕ В CONFIG ---

# Потокобезопасные замки для записи в файлы
file_locks: Dict[str, threading.Lock] = {}


def get_file_lock(output_filename: str) -> threading.Lock:
    return file_locks.setdefault(output_filename, threading.Lock())


def get_model_response(api_key: str, sentence_data: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    GenAI-клиент для pipeline: напрямую использует функцию generate()
    из gemini_client_comp (армянский промпт/схема).
    """
    if not api_key:
        print("❌ Ошибка: не передан API ключ для GenAI.")
        return None

    try:
        sentence_json_string = json.dumps(sentence_data, ensure_ascii=False, indent=2)
    except (TypeError, AttributeError) as exc:
        print(f"❌ Ошибка при сборке промпта: {exc}")
        return None

    full_response_text = ""
    try:
        full_response_text = generate(
            sentence_json_string,
            api_key=api_key,
            return_text=True,
        )
        if not full_response_text:
            print("  - 🟡 Ответ от GenAI пустой.")
            return None
        return json.loads(full_response_text)
    except json.JSONDecodeError:
        print(f"❌ Ошибка декодирования JSON. Ответ от GenAI:\n{full_response_text}")
        return None
    except Exception as exc:
        print(f"❌ Непредвиденная ошибка во время запроса к GenAI: {exc}")
        return None


def load_processed_ids(output_dir: Path) -> Set[str]:
    """Сканирует .jsonl файлы и возвращает множество уже обработанных sentence_id."""
    processed_ids = set()
    output_dir.mkdir(parents=True, exist_ok=True)
    for filepath in output_dir.glob("*.jsonl"):
        print(f"  - Сканирую файл {filepath.name}...")
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    if 'sentence_id' in record:
                        processed_ids.add(record['sentence_id'])
                except json.JSONDecodeError:
                    print(f"    ⚠️  Обнаружена поврежденная строка в {filepath.name}, игнорируется.")
    return processed_ids


def migrate_data_to_include_model_name(output_dir: Path):
    """
    Проверяет существующие .jsonl файлы и добавляет поле 'model_name': 'unknown',
    если оно отсутствует. Выполняется один раз при старте.
    """
    print("\n--- Шаг 1.5: Проверка и обновление формата данных (миграция)... ---")
    for filepath in output_dir.glob("*.jsonl"):
        if not filepath.is_file(): continue
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except IOError as e:
            print(f"  - ❌ Не удалось прочитать файл для миграции {filepath.name}: {e}")
            continue

        updated_lines = []
        was_migrated = False
        for line in lines:
            try:
                record = json.loads(line)
                if 'model_name' not in record:
                    record['model_name'] = 'unknown'
                    was_migrated = True
                updated_lines.append(json.dumps(record, ensure_ascii=False) + '\n')
            except json.JSONDecodeError:
                updated_lines.append(line)

        if was_migrated:
            print(f"  - Обновляю формат данных в файле {filepath.name}...")
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.writelines(updated_lines)
            except IOError as e:
                print(f"  - ❌ Не удалось записать обновленный файл {filepath.name}: {e}")


def _convert_nodes_for_llm(preprocessed_sentence: Dict[str, Any]) -> Dict[str, Any]:
    """
    Готовит вход для LLM из v2 `units`, а при отсутствии — из legacy nodes.
    """
    llm_nodes = []
    model_units = get_model_input_units(preprocessed_sentence)
    unit_map = {unit.get("unit_id") or unit.get("id"): unit for unit in model_units if isinstance(unit, dict)}

    for unit in model_units:
        if "unit_id" in unit:
            target_id = unit.get("syntactic_link_target_id")
            head_surface = None
            head_lemma = None
            if target_id and isinstance(unit_map.get(target_id), dict):
                head_surface = unit_map[target_id].get("surface")
                head_lemma = unit_map[target_id].get("core_lemma")

            llm_nodes.append(
                {
                    "id": unit.get("unit_id"),
                    "name": unit.get("surface"),
                    "surface": unit.get("surface"),
                    "core_lemma": unit.get("core_lemma"),
                    "pos_universal": unit.get("upos"),
                    "pos_specific": unit.get("xpos"),
                    "features": unit.get("features", {}),
                    "syntactic_link_target_id": target_id,
                    "original_deprel": unit.get("original_deprel"),
                    "introduced_by": unit.get("introduced_by", []),
                    "attached_tokens": unit.get("attached_tokens", []),
                    "ud_semantic_hints": unit.get("ud_semantic_hints", []),
                    "head_surface": head_surface,
                    "head_lemma": head_lemma,
                }
            )
            continue

        llm_nodes.append(
            {
                "id": unit.get("id"),
                "name": unit.get("name"),
                "pos_universal": unit.get("pos_universal"),
                "pos_specific": unit.get("pos_specific"),
                "features": unit.get("features", {}),
                "syntactic_link_target_id": unit.get("syntactic_link_target_id"),
            }
        )

    return {
         #"sentence_id": preprocessed_sentence.get("sentence_id"),
        "text": preprocessed_sentence.get("text"),
        "nodes": llm_nodes,
    }


def _iter_preprocessed_sentences(filepath: Path):
    """Итерирует валидные sentence-record'ы из preprocessed-файла."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"  - ⚠️  Не удалось прочитать {filepath.name}: {e}")
        return

    if not isinstance(data, list):
        print(f"  - ⚠️  Некорректный формат {filepath.name}: ожидается JSON-массив.")
        return

    for item in data:
        if isinstance(item, dict):
            yield item


def _get_validation_nodes(preprocessed_sentence: Dict[str, Any]) -> List[Dict[str, Any]]:
    return get_legacy_nodes(preprocessed_sentence)


def worker(q: Queue, key_cycler):
    """Функция-обработчик для каждого потока."""
    api_key = next(key_cycler)
    thread_name = threading.current_thread().name
    try:
        if REQUEST_STRATEGY == "local":
            session = requests.Session()
            session.trust_env = False
            client = session
            response_fn = get_local_model_response
            print(f"✅ {thread_name} запущен успешно (локальный сервис)")
        elif REQUEST_STRATEGY in {"genai", "google"}:
            if not api_key:
                raise ValueError("API ключ не задан для стратегии genai.")
            client = api_key
            response_fn = get_model_response
            print(f"✅ {thread_name} запущен успешно с ключом ...{api_key[-4:]}")
        else:
            raise ValueError(f"Неизвестная стратегия REQUEST_STRATEGY='{REQUEST_STRATEGY}'.")
    except Exception as e:
        print(f"❌ {thread_name}: Не удалось создать HTTP-клиент. Ошибка: {e}. Воркер останавливается.")
        return

    while not q.empty():
        try:
            # 1. Получаем preprocessed-данные и имя выходного файла из очереди
            original_sentence_data, llm_input_data, output_filename = q.get()
            sentence_id = original_sentence_data.get('sentence_id', 'N/A')
            print(f"-> {thread_name}: Взял в работу ID {sentence_id}")

            success = False
            current_delay = INITIAL_BACKOFF_DELAY

            for attempt in range(MAX_RETRIES):
                # 2. Отправляем в LLM новый компактный JSON
                response_json = response_fn(client, llm_input_data)
                #time.sleep(10)

                # 3. Валидацию проводим с ОРИГИНАЛЬНЫМИ данными, чтобы логировать детали узла
                validation_sentence = dict(original_sentence_data)
                validation_sentence["nodes"] = _get_validation_nodes(original_sentence_data)
                if response_json and 'nodes' in response_json and validate_response(validation_sentence, response_json['nodes']):
                    final_record = {
                        "sentence_id": original_sentence_data['sentence_id'],
                        "text": original_sentence_data['text'],
                        "nodes": response_json['nodes'],
                        "model_name": MODEL_NAME
                    }

                    lock = get_file_lock(output_filename)
                    with lock:
                        output_path = FIXED_DATA_DIR / output_filename
                        with open(output_path, 'a', encoding='utf-8') as f_out:
                            f_out.write(json.dumps(final_record, ensure_ascii=False) + '\n')

                    success = True
                    break # Выходим из цикла повторов в случае успеха

                # Если код дошел сюда, значит была ошибка API или валидации
                print(f"  - 🟡 {thread_name}: Попытка {attempt + 1}/{MAX_RETRIES} для ID {sentence_id} не удалась.")
                if attempt < MAX_RETRIES - 1:
                    print(f"      Пауза на {current_delay} сек. перед следующей попыткой...")
                    time.sleep(current_delay)
                    current_delay *= 2

            if not success:
                print(f"  - ❌ {thread_name}: Все {MAX_RETRIES} попыток для ID {sentence_id} провалены.")

        except Exception as e:
            print(f"  - ❌ {thread_name}: Критическая ошибка при обработке задачи: {e}")
        finally:
            q.task_done()


def build_task_queue_from_preprocessed(processed_ids: Set[str]) -> tuple[Queue, int]:
    task_queue = Queue()
    files_to_process = sorted(list(PREPROCESSED_DATA_DIR.glob("*.json")))
    total_tasks_added = 0

    for filepath in files_to_process:
        output_filename = f"{filepath.stem}.jsonl"

        for preprocessed_sentence in _iter_preprocessed_sentences(filepath):
            sentence_id = preprocessed_sentence.get("sentence_id")
            if not sentence_id or sentence_id in processed_ids:
                continue

            llm_input_data = _convert_nodes_for_llm(preprocessed_sentence)
            task_queue.put((preprocessed_sentence, llm_input_data, output_filename))
            total_tasks_added += 1

    return task_queue, total_tasks_added


def build_task_queue_from_local(processed_ids: Set[str]) -> tuple[Queue, int]:
    """
    Backward-compatible alias для scheduler.py.
    Теперь очередь строится напрямую из PREPROCESSED_DATA_DIR.
    """
    return build_task_queue_from_preprocessed(processed_ids)


def run_pipeline_final():
    """Главная функция для запуска всего пайплайна."""
    if not API_KEYS and REQUEST_STRATEGY in {"genai", "google"}:
        print("⚠️  API ключи не найдены. Для стратегии genai они обязательны.")
        return
    if REQUEST_STRATEGY == "local":
        print(f"⚠️  Использую локальный сервис: {LOCAL_API_URL}")

    # --- Шаг 1: Сканирование прогресса ---
    print("--- Шаг 1: Сканирование прогресса... ---")
    processed_ids = load_processed_ids(FIXED_DATA_DIR)
    if processed_ids:
        print(f"Найдено {len(processed_ids)} уже обработанных предложений. Они будут пропущены.")

    # --- Шаг 1.5: Миграция данных для совместимости ---
    migrate_data_to_include_model_name(FIXED_DATA_DIR)

    # --- Шаг 2: Загрузка НОВЫХ задач в очередь ---
    print("\n--- Шаг 2: Загрузка новых задач в очередь ---")
    task_queue, total_tasks_added = build_task_queue_from_preprocessed(processed_ids)

    if total_tasks_added == 0:
        print("🎉 Вся обработка уже завершена. Новых задач нет.")
        return

    print(f"Загружено {total_tasks_added} новых задач в очередь.")

    # --- Шаг 3: Запуск воркеров ---
    print(f"\n--- Шаг 3: Запуск {NUM_WORKERS} воркеров ---")
    key_cycler = cycle(API_KEYS or [None])
    threads = []
    for i in range(NUM_WORKERS):
        thread = threading.Thread(target=worker, args=(task_queue, key_cycler), name=f"Воркер-{i + 1}")
        thread.start()
        threads.append(thread)

    # Ожидаем завершения всех задач в очереди
    task_queue.join()
    print("\n--- ✅ Все задачи обработаны. Завершение работы. ---")


if __name__ == "__main__":
    run_pipeline_final()
