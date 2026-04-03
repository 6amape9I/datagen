from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_stage02_pipeline():
    module_path = Path(__file__).resolve().parents[2] / "02_local_generation" / "pipeline.py"
    spec = importlib.util.spec_from_file_location("stage02_pipeline_test_module", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_stage02_expected_node_count_uses_compact_nodes(tmp_path: Path, monkeypatch) -> None:
    stage02_pipeline = _load_stage02_pipeline()
    source_path = tmp_path / "eng_train.json"
    output_path = tmp_path / "eng_train.jsonl"
    source_path.write_text(
        json.dumps(
            [
                {
                    "sentence_id": "eng_sample_1",
                    "text": "The city in France",
                    "nodes": [
                        {
                            "id": "w2",
                            "name": "The city",
                            "lemma": "city",
                            "pos_universal": "NOUN",
                            "features": {},
                            "syntactic_link_target_id": None,
                            "original_deprel": "root",
                        }
                    ],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        stage02_pipeline,
        "request_inference",
        lambda sentence_data, retries=3, backoff_sec=1.0: ([{"id": "w2"}], None),
    )

    stage02_pipeline.process_file(source_path, output_path)

    record = json.loads(output_path.read_text(encoding="utf-8").strip())
    assert record["node_error"] is False
    assert record["nodes"] == [{"id": "w2"}]
