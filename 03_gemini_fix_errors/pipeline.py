# gemini_generate/pipeline.py
from pathlib import Path

import json
import time
import threading
from queue import Queue
from itertools import cycle
from typing import Set, Dict, Any, Optional

import requests

# 1. Импортируем все настройки и зависимости из config и локальных модулей
from config import (
    API_KEYS,
    MODEL_NAME,
    NUM_WORKERS,
    MAX_RETRIES,
    INITIAL_BACKOFF_DELAY,
    PREPROCESSED_DATA_DIR,
    LOCAL_GENERATED_DATA_DIR,
    FIXED_DATA_DIR,
    LOCAL_API_URL,
    REQUEST_STRATEGY,
)
from gemini_client import get_model_response
from local_client import get_local_model_response
from validator import validate_response

# --- НАСТРОЙКИ ПАЙПЛАЙНА УДАЛЕНЫ, ТЕПЕРЬ ВСЕ В CONFIG ---

# Потокобезопасные замки для записи в файлы
file_locks: Dict[str, threading.Lock] = {}


def get_file_lock(output_filename: str) -> threading.Lock:
    return file_locks.setdefault(output_filename, threading.Lock())


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


def _build_preprocessed_index(filepath: Path) -> Dict[str, Dict[str, Any]]:
    """Загружает preprocessed JSON и строит индекс sentence_id -> запись."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["sentence_id"]: item for item in data if "sentence_id" in item}


def _convert_nodes_for_llm(preprocessed_sentence: Dict[str, Any]) -> Dict[str, Any]:
    """
    Готовит вход для LLM в новом формате:
    text + nodes[{id, name, pos_universal, pos_specific, features, syntactic_link_target_id}]
    """
    llm_nodes = []
    for node in preprocessed_sentence.get("nodes", []):
        llm_nodes.append(
            {
                "id": node.get("id"),
                "name": node.get("name"),
                "pos_universal": node.get("pos_universal"),
                "pos_specific": node.get("pos_specific"),
                "features": node.get("features", {}),
                "syntactic_link_target_id": node.get("syntactic_link_target_id"),
            }
        )

    return {
         #"sentence_id": preprocessed_sentence.get("sentence_id"),
        "text": preprocessed_sentence.get("text"),
        "nodes": llm_nodes,
    }


def _get_preprocessed_sentence(
    sentence_id: str,
    preprocessed_path: Path,
    cache: Dict[Path, Dict[str, Dict[str, Any]]],
) -> Optional[Dict[str, Any]]:
    """Достает preprocessed-запись по sentence_id с кэшем по файлу."""
    if preprocessed_path not in cache:
        if not preprocessed_path.exists():
            return None
        cache[preprocessed_path] = _build_preprocessed_index(preprocessed_path)
    return cache[preprocessed_path].get(sentence_id)


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
                if response_json and 'nodes' in response_json and validate_response(original_sentence_data, response_json['nodes']):
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


def build_task_queue_from_local(processed_ids: Set[str]) -> tuple[Queue, int]:
    task_queue = Queue()
    files_to_process = sorted(list(LOCAL_GENERATED_DATA_DIR.glob("*.jsonl")))
    preprocessed_cache: Dict[Path, Dict[str, Dict[str, Any]]] = {}
    total_tasks_added = 0

    for filepath in files_to_process:
        output_filename = filepath.name
        preprocessed_path = PREPROCESSED_DATA_DIR / f"{filepath.stem}.json"

        if not preprocessed_path.exists():
            print(
                f"  - ⚠️  Не найден соответствующий preprocessed-файл {preprocessed_path.name} для {filepath.name}."
            )
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    local_record = json.loads(line)
                except json.JSONDecodeError:
                    print(f"  - ⚠️  Поврежденная строка в {filepath.name}, пропускается.")
                    continue

                sentence_id = local_record.get("sentence_id")
                if not sentence_id or sentence_id in processed_ids:
                    continue

                preprocessed_sentence = _get_preprocessed_sentence(
                    sentence_id=sentence_id,
                    preprocessed_path=preprocessed_path,
                    cache=preprocessed_cache,
                )

                if not preprocessed_sentence:
                    print(
                        f"  - ⚠️  Не найдена preprocessed-запись для sentence_id={sentence_id} "
                        f"в файле {preprocessed_path.name}."
                    )
                    continue

                llm_input_data = _convert_nodes_for_llm(preprocessed_sentence)
                print(llm_input_data)

                task_queue.put((preprocessed_sentence, llm_input_data, output_filename))
                total_tasks_added += 1

    return task_queue, total_tasks_added


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
    task_queue, total_tasks_added = build_task_queue_from_local(processed_ids)

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
