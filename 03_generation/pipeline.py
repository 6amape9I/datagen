from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from typing import Any, Iterable

from config import (
    FIXED_DATA_DIR,
    INITIAL_BACKOFF_DELAY,
    MAX_RETRIES,
    NUM_WORKERS,
    PREPROCESSED_DATA_DIR,
    ensure_stage03_runtime_dirs,
)
from input_builder import build_model_input
from prompt_builder import PromptPackage, build_prompt_package
from providers.base import GenerationProvider
from validator import validate_response


_FILE_LOCKS: dict[str, threading.Lock] = {}


@dataclass(frozen=True)
class GenerationTask:
    sentence_data: dict[str, Any]
    prompt: PromptPackage
    output_filename: str


def get_file_lock(output_filename: str) -> threading.Lock:
    return _FILE_LOCKS.setdefault(output_filename, threading.Lock())


def load_processed_ids(output_dir: Path) -> set[str]:
    processed_ids: set[str] = set()
    if not output_dir.exists():
        return processed_ids

    for filepath in output_dir.glob("*.jsonl"):
        with open(filepath, "r", encoding="utf-8") as file_obj:
            for line in file_obj:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                sentence_id = record.get("sentence_id")
                if sentence_id:
                    processed_ids.add(str(sentence_id))
    return processed_ids


def iter_preprocessed_sentences(filepath: Path) -> Iterable[dict[str, Any]]:
    with open(filepath, "r", encoding="utf-8") as file_obj:
        data = json.load(file_obj)

    if not isinstance(data, list):
        return

    for item in data:
        if isinstance(item, dict):
            yield item


def prepare_task(sentence_data: dict[str, Any], output_filename: str) -> GenerationTask:
    model_input = build_model_input(sentence_data)
    prompt = build_prompt_package(model_input)
    return GenerationTask(
        sentence_data=sentence_data,
        prompt=prompt,
        output_filename=output_filename,
    )


def build_task_queue(
    processed_ids: set[str],
    *,
    input_dir: Path = PREPROCESSED_DATA_DIR,
) -> tuple[Queue, int]:
    task_queue: Queue = Queue()
    total_tasks = 0

    for filepath in sorted(input_dir.glob("*.json")):
        output_filename = f"{filepath.stem}.jsonl"
        for sentence_data in iter_preprocessed_sentences(filepath):
            sentence_id = sentence_data.get("sentence_id")
            if not sentence_id or str(sentence_id) in processed_ids:
                continue
            task_queue.put(prepare_task(sentence_data, output_filename))
            total_tasks += 1

    return task_queue, total_tasks


def build_output_record(
    sentence_data: dict[str, Any],
    response_nodes: list[dict[str, Any]],
    *,
    provider_name: str,
    model_name: str,
    generation_profile: str | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "sentence_id": sentence_data.get("sentence_id"),
        "text": sentence_data.get("text"),
        "nodes": response_nodes,
        "model_name": model_name,
        "provider": provider_name,
    }
    if generation_profile:
        record["generation_profile"] = generation_profile
    return record


def write_output_record(output_dir: Path, output_filename: str, record: dict[str, Any]) -> None:
    lock = get_file_lock(output_filename)
    with lock:
        output_path = output_dir / output_filename
        with open(output_path, "a", encoding="utf-8") as file_obj:
            file_obj.write(json.dumps(record, ensure_ascii=False) + "\n")


def _run_task_with_retries(
    task: GenerationTask,
    *,
    provider: GenerationProvider,
    client: Any,
    output_dir: Path,
    max_retries: int,
    initial_backoff_delay: int,
) -> bool:
    current_delay = initial_backoff_delay
    for attempt in range(max_retries):
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
            write_output_record(output_dir, task.output_filename, record)
            return True

        if attempt < max_retries - 1:
            time.sleep(current_delay)
            current_delay *= 2

    return False


def _worker(
    task_queue: Queue,
    *,
    provider: GenerationProvider,
    worker_token: str,
    output_dir: Path,
    max_retries: int,
    initial_backoff_delay: int,
) -> None:
    try:
        client = provider.create_client(worker_token)
    except Exception as exc:
        print(f"❌ Worker init failed for provider {provider.metadata.provider}: {exc}")
        return

    while not task_queue.empty():
        try:
            task = task_queue.get_nowait()
        except Exception:
            break

        try:
            sentence_id = task.sentence_data.get("sentence_id", "N/A")
            success = _run_task_with_retries(
                task,
                provider=provider,
                client=client,
                output_dir=output_dir,
                max_retries=max_retries,
                initial_backoff_delay=initial_backoff_delay,
            )
            if not success:
                print(f"❌ Generation failed for sentence_id={sentence_id}")
        finally:
            task_queue.task_done()


def run_generation_pipeline(
    provider: GenerationProvider,
    *,
    input_dir: Path = PREPROCESSED_DATA_DIR,
    output_dir: Path = FIXED_DATA_DIR,
    num_workers: int = NUM_WORKERS,
    max_retries: int = MAX_RETRIES,
    initial_backoff_delay: int = INITIAL_BACKOFF_DELAY,
) -> None:
    ensure_stage03_runtime_dirs()

    processed_ids = load_processed_ids(output_dir)
    task_queue, total_tasks = build_task_queue(processed_ids, input_dir=input_dir)
    if total_tasks == 0:
        print("✅ No new generation tasks found.")
        return

    worker_tokens = provider.worker_tokens(max(1, num_workers))
    if not worker_tokens:
        print(f"⚠️ No provider credentials available for {provider.metadata.provider}.")
        return

    print(f"=== Generation: {provider.metadata.provider} ===")
    print(f"Model: {provider.metadata.model_name}")
    print(f"Queued sentences: {total_tasks}")

    workers: list[threading.Thread] = []
    for index, worker_token in enumerate(worker_tokens[: max(1, num_workers)]):
        worker = threading.Thread(
            target=_worker,
            kwargs={
                "task_queue": task_queue,
                "provider": provider,
                "worker_token": worker_token,
                "output_dir": output_dir,
                "max_retries": max_retries,
                "initial_backoff_delay": initial_backoff_delay,
            },
            name=f"GenerationWorker-{index + 1}",
        )
        worker.start()
        workers.append(worker)

    task_queue.join()
    for worker in workers:
        worker.join()

    print("✅ Generation finished.")
