from __future__ import annotations

import json
from pathlib import Path

from pipeline import build_task_queue, run_generation_pipeline
from providers.base import GenerationResult, ProviderMetadata


class DummyProvider:
    metadata = ProviderMetadata(provider="dummy", model_name="dummy-model", generation_profile="test")

    def worker_tokens(self, requested_workers: int) -> list[str]:
        return ["dummy-token"]

    def create_client(self, worker_token: str):
        return object()

    def generate(self, client, prompt):
        return GenerationResult(
            payload={
                "nodes": [
                    {"id": "w2", "syntactic_link_name": "ROOT"},
                    {"id": "w4", "syntactic_link_name": "Content_Theme"},
                ]
            },
            error=None,
        )

    def is_quota_error(self, error_text: str | None) -> bool:
        return False


def _make_source_record(sentence_id: str) -> dict:
    return {
        "sentence_id": sentence_id,
        "text": "The city in France",
        "language_code": "eng",
        "split": "train",
        "source_file": "eng_sample.conllu",
        "nodes": [
            {
                "id": "w2",
                "name": "The city",
                "lemma": "city",
                "pos_universal": "NOUN",
                "features": {},
                "syntactic_link_target_id": None,
                "original_deprel": "root",
            },
            {
                "id": "w4",
                "name": "in France",
                "lemma": "France",
                "pos_universal": "PROPN",
                "features": {"Case": "Loc"},
                "syntactic_link_target_id": "w2",
                "original_deprel": "nmod",
                "introduced_by": ["in"],
            },
        ],
    }


def test_generation_pipeline_writes_minimal_jsonl_output(tmp_path: Path) -> None:
    source_dir = tmp_path / "preprocessed"
    output_dir = tmp_path / "fixed"
    source_dir.mkdir()
    output_dir.mkdir()

    source_record = [_make_source_record("eng_sample_1")]
    (source_dir / "eng_train.json").write_text(json.dumps(source_record, ensure_ascii=False), encoding="utf-8")

    run_generation_pipeline(
        DummyProvider(),
        input_dir=source_dir,
        output_dir=output_dir,
        num_workers=1,
        max_retries=1,
        initial_backoff_delay=0,
    )

    written = json.loads((output_dir / "eng_train.jsonl").read_text(encoding="utf-8").strip())
    assert written["sentence_id"] == "eng_sample_1"
    assert written["provider"] == "dummy"
    assert written["model_name"] == "dummy-model"
    assert written["generation_profile"] == "test"
    assert written["nodes"] == [
        {"id": "w2", "syntactic_link_name": "ROOT"},
        {"id": "w4", "syntactic_link_name": "Content_Theme"},
    ]


def test_generation_pipeline_prints_worker_and_sentence_progress(
    tmp_path: Path,
    capsys,
) -> None:
    source_dir = tmp_path / "preprocessed"
    output_dir = tmp_path / "fixed"
    source_dir.mkdir()
    output_dir.mkdir()

    source_record = [_make_source_record("eng_sample_2")]
    (source_dir / "eng_train.json").write_text(json.dumps(source_record, ensure_ascii=False), encoding="utf-8")

    run_generation_pipeline(
        DummyProvider(),
        input_dir=source_dir,
        output_dir=output_dir,
        num_workers=1,
        max_retries=1,
        initial_backoff_delay=0,
    )

    captured = capsys.readouterr().out
    assert "Started workers: 1" in captured
    assert "Max samples per json: 2000" in captured
    assert "[GenerationWorker-1] assigned token=dummy-...oken" in captured
    assert "[GenerationWorker-1] picked sentence_id=eng_sample_2" in captured
    assert "[GenerationWorker-1] request success sentence_id=eng_sample_2 attempt=1/1" in captured


def test_build_task_queue_caps_each_json_after_processed_filter(tmp_path: Path, capsys) -> None:
    source_dir = tmp_path / "preprocessed"
    source_dir.mkdir()

    file_a_records = [_make_source_record(f"eng_a_{index}") for index in range(5)]
    file_b_records = [_make_source_record(f"eng_b_{index}") for index in range(4)]
    (source_dir / "eng_a.json").write_text(json.dumps(file_a_records, ensure_ascii=False), encoding="utf-8")
    (source_dir / "eng_b.json").write_text(json.dumps(file_b_records, ensure_ascii=False), encoding="utf-8")

    processed_ids = {"eng_a_0", "eng_a_1"}
    task_queue, total_tasks = build_task_queue(
        processed_ids,
        input_dir=source_dir,
        max_samp_per_json=2,
    )

    queued_ids = []
    while not task_queue.empty():
        queued_ids.append(task_queue.get_nowait().sentence_data["sentence_id"])

    captured = capsys.readouterr().out
    assert total_tasks == 4
    assert queued_ids == ["eng_a_2", "eng_a_3", "eng_b_0", "eng_b_1"]
    assert "[build_task_queue] capped file=eng_a.json queued=2 max_samp_per_json=2" in captured
    assert "[build_task_queue] capped file=eng_b.json queued=2 max_samp_per_json=2" in captured
