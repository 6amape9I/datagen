from __future__ import annotations

import json
from pathlib import Path

from pipeline import run_generation_pipeline
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


def test_generation_pipeline_writes_minimal_jsonl_output(tmp_path: Path) -> None:
    source_dir = tmp_path / "preprocessed"
    output_dir = tmp_path / "fixed"
    source_dir.mkdir()
    output_dir.mkdir()

    source_record = [
        {
            "sentence_id": "eng_sample_1",
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
    ]
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
