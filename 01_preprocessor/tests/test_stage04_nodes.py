from __future__ import annotations

import json

from prepare_final_dataset import prepare_final_dataset


def test_stage04_builds_final_dataset_from_compact_nodes(tmp_path: Path, monkeypatch) -> None:
    source_dir = tmp_path / "preprocessed"
    fixed_dir = tmp_path / "fixed"
    final_dir = tmp_path / "final"
    source_dir.mkdir()
    fixed_dir.mkdir()
    final_dir.mkdir()

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
                    "features": {"Case": "Nom"},
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
    (fixed_dir / "eng_train.jsonl").write_text(
        json.dumps(
            {
                "sentence_id": "eng_sample_1",
                "text": "The city in France",
                "nodes": [
                    {"id": "w2", "syntactic_link_name": "ROOT"},
                    {"id": "w4", "syntactic_link_name": "Content_Theme"},
                ],
            },
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("prepare_final_dataset.PREPROCESSED_DATA_DIR", source_dir)
    monkeypatch.setattr("prepare_final_dataset.FIXED_DATA_DIR", fixed_dir)
    monkeypatch.setattr("prepare_final_dataset.FINAL_DATASET_DIR", final_dir)

    prepare_final_dataset()

    result = json.loads((final_dir / "eng_train.json").read_text(encoding="utf-8"))
    assert result[0]["output"][0]["id"] == "w2"
    assert result[0]["output"][0]["name"] == "The city"
    assert result[0]["output"][1]["id"] == "w4"
    assert result[0]["output"][1]["name"] == "in France"
