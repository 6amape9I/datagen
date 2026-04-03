from __future__ import annotations

from pathlib import Path

from sentence_builder import EXPORT_MODE_CANONICAL_WITH_LEGACY, process_conllu_file


def test_legacy_export_keeps_stage03_contract(tmp_path: Path) -> None:
    sample = """# sent_id = 1
# text = The city in France
1\tThe\tthe\tDET\tDT\tDefinite=Def|PronType=Art\t2\tdet\t_\t_
2\tcity\tcity\tNOUN\tNN\tNumber=Sing\t0\troot\t_\t_
3\tin\tin\tADP\tIN\t_\t4\tcase\t_\t_
4\tFrance\tFrance\tPROPN\tNNP\tNumber=Sing\t2\tnmod\t_\t_
"""
    filepath = tmp_path / "sample-dev.conllu"
    filepath.write_text(sample, encoding="utf-8")

    record = process_conllu_file(
        filepath,
        sentence_id_prefix="eng_sample-dev.conllu",
        language_code="eng",
        split="val",
        source_file="eng_sample-dev.conllu",
        export_mode=EXPORT_MODE_CANONICAL_WITH_LEGACY,
        enable_legacy_candidates=True,
    )[0]

    nodes = record["legacy_nodes"]
    assert [node["id"] for node in nodes] == ["w2", "w4"]
    assert nodes[0]["syntactic_link_target_id"] is None
    assert nodes[1]["syntactic_link_target_id"] == "w2"
    assert "syntactic_link_candidates" in nodes[0]
    assert isinstance(nodes[0]["syntactic_link_candidates"], list)
    assert nodes[1]["link_introduction_info"]["marker_word"] == "in"
