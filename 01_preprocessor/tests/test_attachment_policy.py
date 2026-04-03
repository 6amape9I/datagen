from __future__ import annotations

from attachment_policy import decide_attachment
from schemas import RawToken


def _token(
    token_id: str,
    form: str,
    upos: str,
    head_token_id: str | None,
    deprel: str,
) -> RawToken:
    return RawToken(
        token_id=token_id,
        form=form,
        lemma=form.lower(),
        upos=upos,
        xpos=upos,
        head_token_id=head_token_id,
        deprel=deprel,
        token_index=int(token_id) if token_id.isdigit() else 0,
        is_integer_id=token_id.isdigit(),
    )


def test_attachment_policy_attaches_determiners_and_markers() -> None:
    head = _token("2", "city", "NOUN", "0", "root")
    det = _token("1", "The", "DET", "2", "det")
    mark = _token("3", "that", "SCONJ", "2", "mark")
    token_map = {"1": det, "2": head, "3": mark}

    det_decision = decide_attachment(det, token_map, language_code="eng")
    mark_decision = decide_attachment(mark, token_map, language_code="eng")

    assert det_decision.action == "attach"
    assert det_decision.attachment_type == "determiner"
    assert mark_decision.action == "attach"
    assert mark_decision.attachment_type == "marker"


def test_attachment_policy_preserves_semantic_dependents() -> None:
    head = _token("2", "go", "VERB", "0", "root")
    subject = _token("1", "students", "NOUN", "2", "nsubj")
    token_map = {"1": subject, "2": head}

    decision = decide_attachment(subject, token_map, language_code="eng")

    assert decision.action == "preserve"
