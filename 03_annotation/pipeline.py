from __future__ import annotations

import json
import sys
import threading
import time
from itertools import cycle
from pathlib import Path
from queue import Queue
from typing import Any, Dict, List, Set

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    API_KEYS,
    FIXED_DATA_DIR,
    INITIAL_BACKOFF_DELAY,
    MAX_RETRIES,
    MODEL_NAME,
    NUM_WORKERS,
    PREPROCESSED_DATA_DIR,
    REQUEST_STRATEGY,
    ensure_stage03_runtime_dirs,
)
from gemini_client import get_model_response
from local_client import get_local_model_response
from validator import validate_response


file_locks: Dict[str, threading.Lock] = {}


def get_file_lock(output_filename: str) -> threading.Lock:
    return file_locks.setdefault(output_filename, threading.Lock())


def load_processed_ids(output_dir: Path) -> Set[str]:
    processed_ids: Set[str] = set()
    if not output_dir.exists():
        return processed_ids

    for filepath in output_dir.glob("*.jsonl"):
        print(f"  - Сканирую файл {filepath.name}...")
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    print(f"    ⚠️  Обнаружена поврежденная строка в {filepath.name}, игнорируется.")
                    continue
                sentence_id = record.get("sentence_id")
                if sentence_id:
                    processed_ids.add(sentence_id)
    return processed_ids


def _convert_nodes_for_llm(preprocessed_sentence: Dict[str, Any]) -> Dict[str, Any]:
    llm_nodes: List[Dict[str, Any]] = []
    compact_nodes = preprocessed_sentence.get("nodes", [])
    node_map = {
        str(node["id"]): node
        for node in compact_nodes
        if isinstance(node, dict) and node.get("id")
    }

    for node in compact_nodes:
        target_id = node.get("syntactic_link_target_id")
        head_lemma = None
        if target_id and target_id in node_map:
            head_lemma = node_map[target_id].get("lemma")
        llm_node = {
            "id": node.get("id"),
            "name": node.get("name"),
            "lemma": node.get("lemma"),
            "pos_universal": node.get("pos_universal"),
            "features": node.get("features", {}),
            "syntactic_link_target_id": target_id,
            "original_deprel": node.get("original_deprel"),
        }
        if node.get("introduced_by"):
            llm_node["introduced_by"] = node["introduced_by"]
        if head_lemma:
            llm_node["head_lemma"] = head_lemma
        llm_nodes.append(llm_node)

    return {
        "text": preprocessed_sentence.get("text"),
        "nodes": llm_nodes,
    }


def _iter_preprocessed_sentences(filepath: Path):
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


def worker(q: Queue, key_cycler) -> None:
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
            original_sentence_data, llm_input_data, output_filename = q.get()
            sentence_id = original_sentence_data.get("sentence_id", "N/A")
            print(f"-> {thread_name}: Взял в работу ID {sentence_id}")

            success = False
            current_delay = INITIAL_BACKOFF_DELAY

            for attempt in range(MAX_RETRIES):
                response_json = response_fn(client, llm_input_data)

                if response_json and "nodes" in response_json and validate_response(original_sentence_data, response_json["nodes"]):
                    final_record = {
                        "sentence_id": original_sentence_data["sentence_id"],
                        "text": original_sentence_data["text"],
                        "nodes": response_json["nodes"],
                        "model_name": MODEL_NAME,
                    }

                    lock = get_file_lock(output_filename)
                    with lock:
                        output_path = FIXED_DATA_DIR / output_filename
                        with open(output_path, "a", encoding="utf-8") as f_out:
                            f_out.write(json.dumps(final_record, ensure_ascii=False) + "\n")

                    success = True
                    break

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
    files_to_process = sorted(PREPROCESSED_DATA_DIR.glob("*.json"))
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
    return build_task_queue_from_preprocessed(processed_ids)


def run_pipeline_final() -> None:
    ensure_stage03_runtime_dirs()

    if not API_KEYS and REQUEST_STRATEGY in {"genai", "google"}:
        print("⚠️  API ключи не найдены. Для стратегии genai они обязательны.")
        return

    print("--- Шаг 1: Сканирование прогресса... ---")
    processed_ids = load_processed_ids(FIXED_DATA_DIR)
    if processed_ids:
        print(f"Найдено {len(processed_ids)} уже обработанных предложений. Они будут пропущены.")

    print("\n--- Шаг 2: Формирование очереди задач напрямую из preprocessed-файлов... ---")
    task_queue, total_tasks = build_task_queue_from_preprocessed(processed_ids)
    if total_tasks == 0:
        print("✅ Нет новых задач для обработки.")
        return
    print(f"  - В очередь добавлено {total_tasks} новых предложений.")

    if REQUEST_STRATEGY == "local":
        keys_for_cycle = ["local-worker"] * max(1, NUM_WORKERS)
    else:
        keys_for_cycle = API_KEYS
    key_cycler = cycle(keys_for_cycle)

    print(f"\n--- Шаг 3: Запуск {NUM_WORKERS} воркеров... ---")
    workers = []
    for i in range(NUM_WORKERS):
        t = threading.Thread(target=worker, args=(task_queue, key_cycler), name=f"Worker-{i + 1}")
        t.start()
        workers.append(t)

    print("\n--- Ожидание завершения всех задач в очереди... ---")
    task_queue.join()

    print("--- Ожидание завершения всех потоков... ---")
    for t in workers:
        t.join()

    print("\n--- ✅ Пайплайн Stage 03 успешно завершён! ---")


if __name__ == "__main__":
    run_pipeline_final()
