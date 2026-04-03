from __future__ import annotations

from pathlib import Path

from sentence_builder import process_conllu_file


SMOKE_CASES = {
    "eng": """# sent_id = 1
# text = The city in France
1\tThe\tthe\tDET\tDT\tDefinite=Def|PronType=Art\t2\tdet\t_\t_
2\tcity\tcity\tNOUN\tNN\tNumber=Sing\t0\troot\t_\t_
3\tin\tin\tADP\tIN\t_\t4\tcase\t_\t_
4\tFrance\tFrance\tPROPN\tNNP\tNumber=Sing\t2\tnmod\t_\t_
""",
    "rus": """# sent_id = 1
# text = В доме свет
1\tВ\tв\tADP\t_\t_\t2\tcase\t_\t_
2\tдоме\tдом\tNOUN\t_\tCase=Loc|Number=Sing\t3\tobl\t_\t_
3\tсвет\tсвет\tNOUN\t_\tCase=Nom|Number=Sing\t0\troot\t_\t_
""",
    "fra": """# sent_id = 1
# text = Le livre de Marie
1\tLe\tle\tDET\tDET\tDefinite=Def|PronType=Art\t2\tdet\t_\t_
2\tlivre\tlivre\tNOUN\tNOUN\tGender=Masc|Number=Sing\t0\troot\t_\t_
3\tde\tde\tADP\tADP\t_\t4\tcase\t_\t_
4\tMarie\tMarie\tPROPN\tPROPN\tNumber=Sing\t2\tnmod\t_\t_
""",
    "fin": """# sent_id = 1
# text = Talossa on valo
1\tTalossa\ttalo\tNOUN\tNOUN\tCase=Ine|Number=Sing\t3\tobl\t_\t_
2\ton\tolla\tAUX\tAUX\tMood=Ind|Tense=Pres|VerbForm=Fin\t3\tcop\t_\t_
3\tvalo\tvalo\tNOUN\tNOUN\tCase=Nom|Number=Sing\t0\troot\t_\t_
""",
    "zho": """# sent_id = 1
# text = 我 在 学校 学习
1\t我\t我\tPRON\tPRON\t_\t4\tnsubj\t_\t_
2\t在\t在\tADP\tADP\t_\t3\tcase\t_\t_
3\t学校\t学校\tNOUN\tNOUN\t_\t4\tobl\t_\t_
4\t学习\t学习\tVERB\tVERB\t_\t0\troot\t_\t_
""",
    "jpn": """# sent_id = 1
# text = 私 は 学校 で 学ぶ
1\t私\t私\tPRON\tPRON\t_\t5\tnsubj\t_\t_
2\tは\tは\tADP\tADP\t_\t1\tcase\t_\t_
3\t学校\t学校\tNOUN\tNOUN\t_\t5\tobl\t_\t_
4\tで\tで\tADP\tADP\t_\t3\tcase\t_\t_
5\t学ぶ\t学ぶ\tVERB\tVERB\t_\t0\troot\t_\t_
""",
    "heb": """# sent_id = 1
# text = הספר של מריה
1\tהספר\tספר\tNOUN\tNOUN\tDefinite=Def|Number=Sing\t0\troot\t_\t_
2\tשל\tשל\tADP\tADP\t_\t3\tcase\t_\t_
3\tמריה\tמריה\tPROPN\tPROPN\tNumber=Sing\t1\tnmod\t_\t_
""",
}


def test_multilingual_smoke_examples_build_compact_records(tmp_path: Path) -> None:
    for language_code, conllu_text in SMOKE_CASES.items():
        filepath = tmp_path / f"{language_code}-sample-train.conllu"
        filepath.write_text(conllu_text, encoding="utf-8")
        record = process_conllu_file(
            filepath,
            sentence_id_prefix=f"{language_code}_sample-train.conllu",
            language_code=language_code,
            split="train",
            source_file=f"{language_code}_sample-train.conllu",
        )[0]

        assert record["language_code"] == language_code
        assert record["nodes"]
        assert all("id" in node for node in record["nodes"])
        assert all("name" in node for node in record["nodes"])
        assert "tokens" not in record
        assert "units" not in record
        assert "legacy_nodes" not in record
