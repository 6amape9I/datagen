"""Ежедневный шедулер для этапа 02_gemini_generate.

Использует большой пул ключей и поддерживает ограниченное число воркеров,
которые последовательно перебирают ключи, пока очередь предложений не опустеет
или пока не закончится запас ключей.
"""

from __future__ import annotations

import importlib.util
import json
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue
from typing import List, Optional, Tuple

import requests

from config import (
    PREPROCESSED_DATA_DIR,
    GENERATED_DATA_DIR,
    INITIAL_BACKOFF_DELAY,
    MAX_RETRIES,
    MODEL_NAME,
    ALL_SCHEDULER_KEYS,
    SCHEDULER_MAX_CONCURRENT_WORKERS,
    SCHEDULER_CONSECUTIVE_ERROR_LIMIT,
    SCHEDULER_DAILY_QUOTA,
    SCHEDULER_LOG_PATH,
)
from gemini_client import get_model_response
from validator import validate_response


def _load_pipeline_helpers():
    """Динамически загружает pipeline.py, чтобы переиспользовать утилиты."""
    pipeline_path = Path(__file__).resolve().parent / "pipeline.py"
    spec = importlib.util.spec_from_file_location("gemini_pipeline_for_scheduler", pipeline_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Не удалось загрузить модуль pipeline.py для шедулера.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_PIPELINE = _load_pipeline_helpers()
load_processed_ids = _PIPELINE.load_processed_ids
migrate_data_to_include_model_name = _PIPELINE.migrate_data_to_include_model_name
preprocess_sentence_for_llm = _PIPELINE.preprocess_sentence_for_llm
file_locks = _PIPELINE.file_locks


class ThreadSafeCounter:
    """Простейший потокобезопасный счётчик."""

    def __init__(self) -> None:
        self._value = 0
        self._lock = threading.Lock()

    def increment(self, delta: int = 1) -> None:
        with self._lock:
            self._value += delta

    def value(self) -> int:
        with self._lock:
            return self._value


class KeyPool:
    """Выдаёт ключи по очереди. Используется всеми воркерами."""

    def __init__(self, keys: List[str]) -> None:
        self._keys = keys
        self._index = 0
        self._lock = threading.Lock()

    def acquire(self) -> Optional[str]:
        with self._lock:
            if self._index >= len(self._keys):
                return None
            key = self._keys[self._index]
            self._index += 1
            return key


@dataclass
class WorkerMetrics:
    worker_name: str
    api_key: str
    successes: int = 0
    stop_reason: str = ""
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    quota_exceeded: bool = False


def _print_worker(msg: str, worker_name: str, key: Optional[str] = None) -> None:
    suffix = f"...{key[-4:]}" if key else ""
    print(f"[{worker_name}{suffix}] {msg}")


def _write_result(output_filename: str, record: dict) -> None:
    lock = file_locks.get(output_filename)
    if not lock:
        print(f"⚠️  Нет file_lock для файла {output_filename}, пропускаю запись.")
        return
    with lock:
        output_path = GENERATED_DATA_DIR / output_filename
        with open(output_path, "a", encoding="utf-8") as f_out:
            f_out.write(json.dumps(record, ensure_ascii=False) + "\n")


def _build_task_queue(processed_ids) -> Tuple[Queue, int]:
    """Формирует очередь задач аналогично pipeline.run_pipeline_final."""
    task_queue: Queue = Queue()
    files_to_process = sorted(list(PREPROCESSED_DATA_DIR.glob("*.json")))
    total_tasks = 0

    for filepath in files_to_process:
        output_filename = filepath.name.replace(".json", ".jsonl")
        if output_filename not in file_locks:
            print(f"  - ⚠️  Неизвестное имя файла {output_filename}, пропускается.")
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as exc:
                print(f"  - ❌ Не удалось прочитать {filepath.name}: {exc}")
                continue
            for sentence_data in data:
                if sentence_data["sentence_id"] not in processed_ids:
                    task_queue.put((sentence_data, output_filename))
                    total_tasks += 1
    return task_queue, total_tasks


def _log_summary(total_successes: int, used_keys: List[str], reports: List[WorkerMetrics], remaining_tasks: int) -> None:
    log_path = Path(SCHEDULER_LOG_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().isoformat() + "Z"
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] Scheduler finished\n")
        log_file.write(f"  Successful requests: {total_successes}\n")
        if remaining_tasks:
            log_file.write(f"  Remaining tasks in queue: {remaining_tasks}\n")
        if used_keys:
            masked = ", ".join(f"...{key[-4:]}" if key else "<empty>" for key in used_keys)
            log_file.write(f"  Used keys ({len(used_keys)}): {masked}\n")
        for report in reports:
            log_file.write(
                f"    {report.worker_name} key ...{report.api_key[-4:]} -> "
                f"{report.successes} requests, reason: {report.stop_reason}, "
                f"last_error: {report.last_error}\n"
            )
        log_file.write("\n")


def _should_stop_due_to_quota(error_text: Optional[str]) -> bool:
    if not error_text:
        return False
    lowered = error_text.lower()
    return "quota" in lowered or "limit" in lowered or "exceed" in lowered


def _process_with_key(
    worker_name: str,
    api_key: str,
    task_queue: Queue,
    success_counter: ThreadSafeCounter,
    metrics: WorkerMetrics,
) -> None:
    try:
        session = requests.Session()
        session.trust_env = False
        _print_worker("запущен (локальный сервис)", worker_name, api_key)
    except Exception as exc:  # pragma: no cover - сетевой код
        metrics.stop_reason = "client_init_failed"
        metrics.last_error = str(exc)
        _print_worker(f"не удалось создать HTTP-клиент: {exc}", worker_name, api_key)
        return

    while True:
        if metrics.successes >= SCHEDULER_DAILY_QUOTA:
            metrics.stop_reason = "daily_quota_reached"
            return
        try:
            task = task_queue.get(timeout=2)
        except Empty:
            metrics.stop_reason = "no_tasks_available"
            return

        original_sentence_data, output_filename = task
        requeue_task = False
        should_break = False

        try:
            success = False
            current_delay = INITIAL_BACKOFF_DELAY
            for attempt in range(MAX_RETRIES):
                llm_input_data = preprocess_sentence_for_llm(original_sentence_data.copy())
                response_json, error_info = get_model_response(
                    session, llm_input_data, return_error=True
                )
                response = response_json
                error_text = error_info

                if response and "nodes" in response and validate_response(original_sentence_data, response["nodes"]):
                    final_record = {
                        "sentence_id": original_sentence_data["sentence_id"],
                        "text": original_sentence_data["text"],
                        "nodes": response["nodes"],
                        "model_name": MODEL_NAME,
                    }
                    _write_result(output_filename, final_record)
                    success_counter.increment()
                    metrics.successes += 1
                    metrics.consecutive_failures = 0
                    success = True
                    break

                metrics.last_error = error_text or "validation_failed"
                if _should_stop_due_to_quota(error_text):
                    metrics.stop_reason = "api_quota_exceeded"
                    metrics.quota_exceeded = True
                    requeue_task = True
                    should_break = True
                    break

                if attempt < MAX_RETRIES - 1:
                    time.sleep(current_delay)
                    current_delay *= 2

            if not success:
                metrics.consecutive_failures += 1
                if should_break:
                    break
                if metrics.consecutive_failures >= SCHEDULER_CONSECUTIVE_ERROR_LIMIT:
                    metrics.stop_reason = "error_threshold"
                    requeue_task = True
                    should_break = True
        finally:
            task_queue.task_done()
            if requeue_task:
                task_queue.put((original_sentence_data, output_filename))

        if should_break:
            return


def _scheduler_worker(
    worker_id: int,
    key_pool: KeyPool,
    task_queue: Queue,
    success_counter: ThreadSafeCounter,
    used_keys: List[str],
    used_keys_lock: threading.Lock,
    reports: List[WorkerMetrics],
    reports_lock: threading.Lock,
) -> None:
    worker_name = f"SchedulerWorker-{worker_id}"
    while True:
        api_key = key_pool.acquire()
        if not api_key:
            _print_worker("ключи закончились, выходим", worker_name)
            return

        metrics = WorkerMetrics(worker_name=worker_name, api_key=api_key)
        _process_with_key(worker_name, api_key, task_queue, success_counter, metrics)

        with used_keys_lock:
            used_keys.append(api_key)
        with reports_lock:
            reports.append(metrics)

        if metrics.stop_reason == "no_tasks_available":
            _print_worker("очередь пуста, завершаю", worker_name, api_key)
            return


def run_scheduler_once() -> None:
    """Запуск задачи сбора данных один раз (расчёт на выполнение ~1 раз в день)."""
    if not ALL_SCHEDULER_KEYS:
        print("❌ В config.generate_conf.ALL_KEYS_FOR_SHEDULE не заданы ключи для шедулера.")
        return

    print("=== Gemini Scheduler: подготовка ===")
    processed_ids = load_processed_ids(GENERATED_DATA_DIR)
    if processed_ids:
        print(f"  Пропустим {len(processed_ids)} предложений — уже обработаны.")

    migrate_data_to_include_model_name(GENERATED_DATA_DIR)

    task_queue, total_tasks = _build_task_queue(processed_ids)
    if total_tasks == 0:
        print("🎉 Новых задач нет — шедулер завершает работу.")
        return

    worker_slots = max(1, min(SCHEDULER_MAX_CONCURRENT_WORKERS, len(ALL_SCHEDULER_KEYS)))
    print(
        f"  Всего задач: {total_tasks}. "
        f"Активных воркеров: {worker_slots}. "
        f"Доступных ключей: {len(ALL_SCHEDULER_KEYS)}."
    )

    key_pool = KeyPool(ALL_SCHEDULER_KEYS)
    success_counter = ThreadSafeCounter()
    used_keys: List[str] = []
    reports: List[WorkerMetrics] = []
    used_keys_lock = threading.Lock()
    reports_lock = threading.Lock()

    workers: List[threading.Thread] = []
    for idx in range(worker_slots):
        thread = threading.Thread(
            target=_scheduler_worker,
            args=(idx + 1, key_pool, task_queue, success_counter, used_keys, used_keys_lock, reports, reports_lock),
            name=f"SchedulerThread-{idx + 1}",
        )
        thread.start()
        workers.append(thread)

    for thread in workers:
        thread.join()

    remaining_tasks = task_queue.qsize()
    if remaining_tasks:
        print(f"⚠️  Осталось задач в очереди: {remaining_tasks}. Проверьте лимиты ключей.")
    else:
        print("✅ Все доступные задачи шедулера обработаны.")

    _log_summary(success_counter.value(), used_keys, reports, remaining_tasks)
    used_keys.clear()


if __name__ == "__main__":
    run_scheduler_once()
