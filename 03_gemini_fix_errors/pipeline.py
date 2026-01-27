# gemini_generate/pipeline.py
from pathlib import Path

import json
import time
import threading
from queue import Queue
from itertools import cycle
from typing import Set, Dict, Any

import requests

# 1. Импортируем все настройки и зависимости из config и локальных модулей
from config import (
    API_KEYS, MODEL_NAME, NUM_WORKERS, MAX_RETRIES, INITIAL_BACKOFF_DELAY,
    PREPROCESSED_DATA_DIR, GENERATED_DATA_DIR, LOCAL_API_URL
)
from gemini_client import get_model_response
from validator import validate_response

# --- НАСТРОЙКИ ПАЙПЛАЙНА УДАЛЕНЫ, ТЕПЕРЬ ВСЕ В CONFIG ---

# Потокобезопасные замки для записи в файлы
file_locks = {
    "train.jsonl": threading.Lock(),
    "val.jsonl": threading.Lock(),
    "test.jsonl": threading.Lock(),
}


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


def preprocess_sentence_for_llm(sentence_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Подготавливает данные для LLM: создает поле 'syntactic_link_candidates_names'
    из 'syntactic_link_candidates'. Это обеспечивает обратную совместимость
    и позволяет проводить "слепое" тестирование LLM, не раскрывая внутренние
    эвристические оценки кандидатов.
    """
    if "nodes" in sentence_data:
        for node in sentence_data["nodes"]:
            if "syntactic_link_candidates" in node:
                raw = node.get('syntactic_link_candidates', [])
                if raw and isinstance(raw[0], dict):
                    candidate_names = [c.get('name') for c in raw if isinstance(c, dict) and c.get('name')]
                else:
                    candidate_names = [str(c) for c in raw]
                node['syntactic_link_candidates_names'] = sorted(list(set(candidate_names)))
    return sentence_data


def worker(q: Queue, key_cycler):
    """Функция-обработчик для каждого потока."""
    api_key = next(key_cycler)
    thread_name = threading.current_thread().name
    try:
        session = requests.Session()
        session.trust_env = False
        if api_key:
            print(f"✅ {thread_name} запущен успешно с ключом ...{api_key[-4:]}")
        else:
            print(f"✅ {thread_name} запущен успешно (локальный сервис)")
    except Exception as e:
        print(f"❌ {thread_name}: Не удалось создать HTTP-клиент. Ошибка: {e}. Воркер останавливается.")
        return

    while not q.empty():
        try:
            # 1. Получаем ОРИГИНАЛЬНЫЕ данные из очереди
            original_sentence_data, output_filename = q.get()
            sentence_id = original_sentence_data.get('sentence_id', 'N/A')
            print(f"-> {thread_name}: Взял в работу ID {sentence_id}")

            success = False
            current_delay = INITIAL_BACKOFF_DELAY

            for attempt in range(MAX_RETRIES):
                # 2. Применяем препроцессор для создания "слепой" версии для LLM
                llm_input_data = preprocess_sentence_for_llm(original_sentence_data.copy())
                response_json = get_model_response(session, llm_input_data)

                # 3. Валидацию проводим с ОРИГИНАЛЬНЫМИ данными, чтобы логировать детали узла
                if response_json and 'nodes' in response_json and validate_response(original_sentence_data, response_json['nodes']):
                    final_record = {
                        "sentence_id": original_sentence_data['sentence_id'],
                        "text": original_sentence_data['text'],
                        "nodes": response_json['nodes'],
                        "model_name": MODEL_NAME
                    }

                    lock = file_locks.get(output_filename)
                    if lock:
                        with lock:
                            output_path = GENERATED_DATA_DIR / output_filename
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


def run_pipeline_final():
    """Главная функция для запуска всего пайплайна."""
    if not API_KEYS:
        print(f"⚠️  API ключи не найдены. Использую локальный сервис: {LOCAL_API_URL}")

    # --- Шаг 1: Сканирование прогресса ---
    print("--- Шаг 1: Сканирование прогресса... ---")
    processed_ids = load_processed_ids(GENERATED_DATA_DIR)
    if processed_ids:
        print(f"Найдено {len(processed_ids)} уже обработанных предложений. Они будут пропущены.")

    # --- Шаг 1.5: Миграция данных для совместимости ---
    migrate_data_to_include_model_name(GENERATED_DATA_DIR)

    # --- Шаг 2: Загрузка НОВЫХ задач в очередь ---
    print("\n--- Шаг 2: Загрузка новых задач в очередь ---")
    task_queue = Queue()
    files_to_process = sorted(list(PREPROCESSED_DATA_DIR.glob("*.json")))
    total_tasks_added = 0

    for filepath in files_to_process:
        output_filename = filepath.name.replace(".json", ".jsonl")
        if not output_filename in file_locks:
             print(f"  - ⚠️  Неизвестное имя файла {output_filename}, пропускается. Добавьте его в 'file_locks'.")
             continue
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for sentence_data in data:
                if sentence_data['sentence_id'] not in processed_ids:
                    task_queue.put((sentence_data, output_filename))
                    total_tasks_added += 1

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
