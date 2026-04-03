from __future__ import annotations

from pathlib import Path

from reader import detect_split_from_filename, discover_language_configs
from sentence_builder import process_conllu_file


def test_detect_split_from_filename() -> None:
    assert detect_split_from_filename("sample-train.conllu") == "train"
    assert detect_split_from_filename("sample-dev.conllu") == "val"
    assert detect_split_from_filename("sample-val.conllu") == "val"
    assert detect_split_from_filename("sample-test.conllu") == "test"
    assert detect_split_from_filename("sample.conllu") is None


def test_discover_language_configs(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    (raw_root / "eng").mkdir(parents=True)
    (raw_root / "rus").mkdir(parents=True)
    (raw_root / "eng" / "demo-train.conllu").write_text("", encoding="utf-8")
    (raw_root / "rus" / "demo-dev.conllu").write_text("", encoding="utf-8")

    configs = discover_language_configs(raw_root)

    assert sorted(configs) == ["eng", "rus"]
    assert [path.name for path in configs["eng"]["train"]] == ["demo-train.conllu"]
    assert [path.name for path in configs["rus"]["val"]] == ["demo-dev.conllu"]


def test_process_conllu_file_emits_v2_sentence_metadata(tmp_path: Path) -> None:
    sample = """# sent_id = 1
# text = The city in France
1\tThe\tthe\tDET\tDT\tDefinite=Def|PronType=Art\t2\tdet\t_\t_
2\tcity\tcity\tNOUN\tNN\tNumber=Sing\t0\troot\t_\t_
3\tin\tin\tADP\tIN\t_\t4\tcase\t_\t_
4\tFrance\tFrance\tPROPN\tNNP\tNumber=Sing\t2\tnmod\t_\t_
"""
    filepath = tmp_path / "sample-train.conllu"
    filepath.write_text(sample, encoding="utf-8")

    records = process_conllu_file(
        filepath,
        sentence_id_prefix="eng_sample-train.conllu",
        language_code="eng",
        split="train",
        source_file="eng_sample-train.conllu",
    )

    record = records[0]
    assert record["preprocessed_schema_version"] == 2
    assert record["language_code"] == "eng"
    assert record["split"] == "train"
    assert record["source_file"] == "eng_sample-train.conllu"
    assert record["sentence_id"] == "eng_sample-train.conllu_1"
    assert record["tokens"][0]["token_id"] == "1"
    assert record["units"][0]["unit_id"].startswith("w")
    assert isinstance(record["legacy_nodes"], list)
