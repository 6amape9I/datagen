from __future__ import annotations

from token_normalizer import normalize_sentence_tokens
from unit_builder import build_units


class _FakeToken:
    def __init__(
        self,
        token_id: str,
        form: str,
        lemma: str,
        upos: str,
        xpos: str,
        head: str | None,
        deprel: str,
        feats: dict | None = None,
    ) -> None:
        self.id = token_id
        self.form = form
        self.lemma = lemma
        self.upos = upos
        self.xpos = xpos
        self.head = head
        self.deprel = deprel
        self.feats = feats or {}
        self.misc = {}
        self.deps = {}


def test_unit_builder_preserves_raw_tokens_and_builds_reversible_units() -> None:
    sentence = [
        _FakeToken("1", "The", "the", "DET", "DT", "2", "det", {"Definite": {"Def"}}),
        _FakeToken("2", "city", "city", "NOUN", "NN", "0", "root", {"Number": {"Sing"}}),
        _FakeToken("3", "in", "in", "ADP", "IN", "4", "case"),
        _FakeToken("4", "France", "France", "PROPN", "NNP", "2", "nmod", {"Number": {"Sing"}}),
    ]

    raw_tokens = normalize_sentence_tokens(sentence)
    units, token_map = build_units(raw_tokens, language_code="eng")

    assert [token.token_id for token in raw_tokens] == ["1", "2", "3", "4"]
    assert [unit.unit_id for unit in units] == ["w2", "w4"]

    root_unit = units[0]
    france_unit = units[1]

    assert root_unit.span_token_ids == ["1", "2"]
    assert root_unit.surface == "The city"
    assert root_unit.syntactic_link_target_id is None
    assert root_unit.attached_tokens[0].attachment_type == "determiner"

    assert france_unit.span_token_ids == ["3", "4"]
    assert france_unit.surface == "in France"
    assert france_unit.syntactic_link_target_id == "w2"
    assert france_unit.introduced_by[0].form == "in"
    assert token_map["3"].form == "in"


def test_unit_builder_handles_non_integer_tokens_predictably() -> None:
    sentence = [
        _FakeToken("1-2", "can't", "can't", "X", "X", None, None or "_"),
        _FakeToken("1", "ca", "can", "AUX", "MD", "3", "aux"),
        _FakeToken("2", "n't", "not", "PART", "RB", "3", "advmod"),
        _FakeToken("3", "go", "go", "VERB", "VB", "0", "root"),
    ]

    raw_tokens = normalize_sentence_tokens(sentence)
    units, _ = build_units(raw_tokens, language_code="eng")

    assert raw_tokens[0].is_integer_id is False
    assert [unit.unit_id for unit in units] == ["w3"]
    assert any(token.token_id == "1-2" for token in raw_tokens)
