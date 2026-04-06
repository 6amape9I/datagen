from __future__ import annotations

import json
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
for path in (PROJECT_ROOT, CURRENT_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from config import (
    FIXED_DATA_DIR,
    INITIAL_BACKOFF_DELAY,
    MAX_RETRIES,
    REQUEST_STRATEGY,
    SCHEDULER_CONSECUTIVE_ERROR_LIMIT,
    SCHEDULER_DAILY_QUOTA,
    SCHEDULER_LOG_PATH,
    SCHEDULER_MAX_CONCURRENT_WORKERS,
    ensure_stage03_runtime_dirs,
)
from pipeline import (
    GenerationTask,
    build_output_record,
    build_task_queue,
    load_processed_ids,
    validate_response,
    write_output_record,
)
from providers.google_genai import GoogleGenAIProvider
from providers.local_http import LocalHTTPProvider


class KeyPool:
    def __init__(self, keys: list[str]) -> None:
        self._keys = keys
        self._index = 0
        self._lock = threading.Lock()

    def acquire(self) -> str | None:
        with self._lock:
            if self._index >= len(self._keys):
                return None
            key = self._keys[self._index]
            self._index += 1
            return key


class ThreadSafeCounter:
    def __init__(self) -> None:
        self._value = 0
        self._lock = threading.Lock()

    def increment(self) -> None:
        with self._lock:
            self._value += 1

    def value(self) -> int:
        with self._lock:
            return self._value


@dataclass
class WorkerMetrics:
    worker_name: str
    token: str
    successes: int = 0
    stop_reason: str = ""
    last_error: str | None = None
    consecutive_failures: int = 0


def _select_provider():
    if REQUEST_STRATEGY in {"google", "genai"}:
        return GoogleGenAIProvider()
    return LocalHTTPProvider()


def _log_summary(
    total_successes: int,
    provider_name: str,
    reports: list[WorkerMetrics],
    remaining_tasks: int,
) -> None:
    log_path = Path(SCHEDULER_LOG_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().isoformat() + "Z"
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] Scheduler finished for {provider_name}\n")
        log_file.write(f"  Successful requests: {total_successes}\n")
        if remaining_tasks:
            log_file.write(f"  Remaining tasks in queue: {remaining_tasks}\n")
        for report in reports:
            log_file.write(
                f"  {report.worker_name} token={report.token} successes={report.successes} "
                f"stop_reason={report.stop_reason} last_error={report.last_error}\n"
            )
        log_file.write("\n")


def _scheduler_worker(
    worker_id: int,
    provider,
    key_pool: KeyPool,
    task_queue: Queue,
    success_counter: ThreadSafeCounter,
    reports: list[WorkerMetrics],
    reports_lock: threading.Lock,
) -> None:
    token = key_pool.acquire()
    if not token:
        return

    worker_name = f"SchedulerWorker-{worker_id}"
    metrics = WorkerMetrics(worker_name=worker_name, token=token)
    with reports_lock:
        reports.append(metrics)

    try:
        client = provider.create_client(token)
    except Exception as exc:
        metrics.stop_reason = "client_init_failed"
        metrics.last_error = str(exc)
        return

    while True:
        if metrics.successes >= SCHEDULER_DAILY_QUOTA:
            metrics.stop_reason = "daily_quota_reached"
            return

        try:
            task: GenerationTask = task_queue.get(timeout=1)
        except Empty:
            metrics.stop_reason = "queue_empty"
            return

        should_break = False
        requeue_task = False
        try:
            current_delay = INITIAL_BACKOFF_DELAY
            success = False
            for attempt in range(MAX_RETRIES):
                result = provider.generate(client, task.prompt)
                payload = result.payload or {}
                nodes = payload.get("nodes") if isinstance(payload, dict) else None

                if isinstance(nodes, list) and validate_response(task.sentence_data, nodes):
                    record = build_output_record(
                        task.sentence_data,
                        nodes,
                        provider_name=provider.metadata.provider,
                        model_name=provider.metadata.model_name,
                        generation_profile=provider.metadata.generation_profile,
                    )
                    write_output_record(FIXED_DATA_DIR, task.output_filename, record)
                    success_counter.increment()
                    metrics.successes += 1
                    metrics.consecutive_failures = 0
                    success = True
                    break

                metrics.last_error = result.error or "validation_failed"
                if provider.is_quota_error(result.error):
                    metrics.stop_reason = "quota_error"
                    requeue_task = True
                    should_break = True
                    break

                if attempt < MAX_RETRIES - 1:
                    time.sleep(current_delay)
                    current_delay *= 2

            if not success:
                metrics.consecutive_failures += 1
                if metrics.consecutive_failures >= SCHEDULER_CONSECUTIVE_ERROR_LIMIT:
                    metrics.stop_reason = "error_threshold"
                    requeue_task = True
                    should_break = True
        finally:
            task_queue.task_done()
            if requeue_task:
                task_queue.put(task)

        if should_break:
            return


def run_scheduler_once() -> None:
    ensure_stage03_runtime_dirs()
    provider = _select_provider()
    processed_ids = load_processed_ids(FIXED_DATA_DIR)
    task_queue, total_tasks = build_task_queue(processed_ids)
    if total_tasks == 0:
        print("✅ No new generation tasks for scheduler.")
        return

    tokens = provider.worker_tokens(SCHEDULER_MAX_CONCURRENT_WORKERS)
    if not tokens:
        print(f"⚠️ No credentials available for scheduler provider {provider.metadata.provider}.")
        return

    key_pool = KeyPool(tokens[:SCHEDULER_MAX_CONCURRENT_WORKERS])
    success_counter = ThreadSafeCounter()
    reports: list[WorkerMetrics] = []
    reports_lock = threading.Lock()
    workers: list[threading.Thread] = []

    for worker_id in range(min(len(tokens), SCHEDULER_MAX_CONCURRENT_WORKERS)):
        thread = threading.Thread(
            target=_scheduler_worker,
            args=(worker_id + 1, provider, key_pool, task_queue, success_counter, reports, reports_lock),
            name=f"SchedulerWorker-{worker_id + 1}",
        )
        thread.start()
        workers.append(thread)

    for thread in workers:
        thread.join()

    _log_summary(success_counter.value(), provider.metadata.provider, reports, task_queue.qsize())
    print(f"✅ Scheduler finished with {success_counter.value()} successful requests.")


if __name__ == "__main__":
    run_scheduler_once()
