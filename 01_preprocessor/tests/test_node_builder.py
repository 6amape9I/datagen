from __future__ import annotations

from token_normalizer import normalize_sentence_tokens
from unit_builder import build_nodes


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


def test_node_builder_builds_compact_nodes() -> None:
    sentence = [
        _FakeToken("1", "The", "the", "DET", "DT", "2", "det", {"Definite": {"Def"}}),
        _FakeToken("2", "city", "city", "NOUN", "NN", "0", "root", {"Number": {"Sing"}}),
        _FakeToken("3", "in", "in", "ADP", "IN", "4", "case"),
        _FakeToken("4", "France", "France", "PROPN", "NNP", "2", "nmod", {"Case": {"Loc"}}),
    ]

    raw_tokens = normalize_sentence_tokens(sentence)
    nodes = build_nodes(raw_tokens, language_code="eng")

    assert [node.id for node in nodes] == ["w2", "w4"]
    assert nodes[0].name == "The city"
    assert nodes[0].lemma == "city"
    assert nodes[0].syntactic_link_target_id is None
    assert nodes[0].introduced_by == []
    assert nodes[1].name == "in France"
    assert nodes[1].introduced_by == ["in"]
    assert nodes[1].syntactic_link_target_id == "w2"


def test_node_builder_handles_non_integer_tokens_predictably() -> None:
    sentence = [
        _FakeToken("1-2", "can't", "can't", "X", "X", None, None or "_"),
        _FakeToken("1", "ca", "can", "AUX", "MD", "3", "aux"),
        _FakeToken("2", "n't", "not", "PART", "RB", "3", "advmod"),
        _FakeToken("3", "go", "go", "VERB", "VB", "0", "root"),
    ]

    raw_tokens = normalize_sentence_tokens(sentence)
    nodes = build_nodes(raw_tokens, language_code="eng")

    assert raw_tokens[0].is_integer_id is False
    assert [node.id for node in nodes] == ["w1", "w3"]
