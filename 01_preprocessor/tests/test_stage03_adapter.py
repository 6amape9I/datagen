from __future__ import annotations

from pathlib import Path

from pipeline import _convert_nodes_for_llm
from sentence_builder import process_conllu_file
from validator import validate_response


def test_stage03_adapter_uses_compact_nodes(tmp_path: Path) -> None:
    sample = """# sent_id = 1
# text = The city in France
1\tThe\tthe\tDET\tDT\tDefinite=Def|PronType=Art\t2\tdet\t_\t_
2\tcity\tcity\tNOUN\tNN\tNumber=Sing\t0\troot\t_\t_
3\tin\tin\tADP\tIN\t_\t4\tcase\t_\t_
4\tFrance\tFrance\tPROPN\tNNP\tNumber=Sing\t2\tnmod\t_\t_
"""
    filepath = tmp_path / "sample-test.conllu"
    filepath.write_text(sample, encoding="utf-8")

    record = process_conllu_file(
        filepath,
        sentence_id_prefix="eng_sample-test.conllu",
        language_code="eng",
        split="test",
        source_file="eng_sample-test.conllu",
    )[0]

    llm_payload = _convert_nodes_for_llm(record)
    assert llm_payload["nodes"][0]["name"] == "The city"
    assert llm_payload["nodes"][1]["introduced_by"] == ["in"]
    assert llm_payload["nodes"][1]["head_lemma"] == "city"

    response_nodes = [
        {"id": "w2", "syntactic_link_name": "ROOT"},
        {"id": "w4", "syntactic_link_name": "Content_Theme"},
    ]
    assert validate_response(record, response_nodes) is True


def test_validator_rejects_role_outside_ontology(tmp_path: Path) -> None:
    sample = """# sent_id = 1
# text = The city in France
1\tThe\tthe\tDET\tDT\tDefinite=Def|PronType=Art\t2\tdet\t_\t_
2\tcity\tcity\tNOUN\tNN\tNumber=Sing\t0\troot\t_\t_
3\tin\tin\tADP\tIN\t_\t4\tcase\t_\t_
4\tFrance\tFrance\tPROPN\tNNP\tNumber=Sing\t2\tnmod\t_\t_
"""
    filepath = tmp_path / "sample-ontology.conllu"
    filepath.write_text(sample, encoding="utf-8")
    record = process_conllu_file(
        filepath,
        sentence_id_prefix="eng_sample-ontology.conllu",
        language_code="eng",
        split="test",
        source_file="eng_sample-ontology.conllu",
    )[0]

    response_nodes = [
        {"id": "w2", "syntactic_link_name": "ROOT"},
        {"id": "w4", "syntactic_link_name": "NotARole"},
    ]
    assert validate_response(record, response_nodes) is False


def test_validator_rejects_duplicate_ids_and_bad_root(tmp_path: Path) -> None:
    sample = """# sent_id = 1
# text = The city in France
1\tThe\tthe\tDET\tDT\tDefinite=Def|PronType=Art\t2\tdet\t_\t_
2\tcity\tcity\tNOUN\tNN\tNumber=Sing\t0\troot\t_\t_
3\tin\tin\tADP\tIN\t_\t4\tcase\t_\t_
4\tFrance\tFrance\tPROPN\tNNP\tNumber=Sing\t2\tnmod\t_\t_
"""
    filepath = tmp_path / "sample-invalid-root.conllu"
    filepath.write_text(sample, encoding="utf-8")
    record = process_conllu_file(
        filepath,
        sentence_id_prefix="eng_sample-invalid-root.conllu",
        language_code="eng",
        split="test",
        source_file="eng_sample-invalid-root.conllu",
    )[0]

    duplicate_response = [
        {"id": "w2", "syntactic_link_name": "ROOT"},
        {"id": "w2", "syntactic_link_name": "Content_Theme"},
    ]
    bad_root_response = [
        {"id": "w2", "syntactic_link_name": "ROOT"},
        {"id": "w4", "syntactic_link_name": "ROOT"},
    ]

    assert validate_response(record, duplicate_response) is False
    assert validate_response(record, bad_root_response) is False
