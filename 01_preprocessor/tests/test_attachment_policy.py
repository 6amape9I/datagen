from __future__ import annotations

from attachment_policy import decide_attachment, get_language_profile
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


def test_attachment_policy_uses_language_profiles_for_determiners() -> None:
    head = _token("2", "livre", "NOUN", "0", "root")
    det = _token("1", "Le", "DET", "2", "det")
    token_map = {"1": det, "2": head}

    article_lang_decision = decide_attachment(det, token_map, language_code="fra")
    articleless_lang_decision = decide_attachment(det, token_map, language_code="rus")

    assert article_lang_decision.action == "attach"
    assert articleless_lang_decision.action == "preserve"


def test_attachment_policy_detects_treebank_name_profiles() -> None:
    assert get_language_profile("UD_English-GUM") == "article_heavy"
    assert get_language_profile("UD_Russian-SynTagRus") == "slavic_rich_inflection"
    assert get_language_profile("UD_Finnish-TDT") == "finnic_rich_case"
    assert get_language_profile("UD_Japanese-GSD") == "cjk_low_morphology"
    assert get_language_profile("UD_Hebrew-HTB") == "semitic"
    assert get_language_profile("UD_Armenian-ArmTDP") == "armenian"


def test_attachment_policy_attaches_case_and_mark_subtypes() -> None:
    head = _token("2", "friend", "NOUN", "0", "root")
    case_token = _token("1", "of", "ADP", "2", "case:gen")
    mark_token = _token("3", "that", "SCONJ", "2", "mark:rel")
    token_map = {"1": case_token, "2": head, "3": mark_token}

    case_decision = decide_attachment(case_token, token_map, language_code="UD_English-GUM")
    mark_decision = decide_attachment(mark_token, token_map, language_code="UD_Chinese-GSD")

    assert case_decision.action == "attach"
    assert case_decision.attachment_type == "adposition"
    assert mark_decision.action == "attach"
    assert mark_decision.attachment_type == "marker"


def test_attachment_policy_attaches_determiners_in_semitic_profile() -> None:
    head = _token("2", "ספר", "NOUN", "0", "root")
    det = _token("1", "ה", "DET", "2", "det")
    token_map = {"1": det, "2": head}

    decision = decide_attachment(det, token_map, language_code="UD_Hebrew-HTB")

    assert decision.action == "attach"
    assert decision.reason == "determiner_attach"


def test_attachment_policy_attaches_aux_subtypes_but_preserves_plain_aux() -> None:
    head = _token("2", "done", "VERB", "0", "root")
    aux_plain = _token("1", "did", "AUX", "2", "aux")
    aux_tense = _token("3", "has", "AUX", "2", "aux:tense")
    token_map = {"1": aux_plain, "2": head, "3": aux_tense}

    plain_decision = decide_attachment(aux_plain, token_map, language_code="UD_English-GUM")
    tense_decision = decide_attachment(aux_tense, token_map, language_code="UD_French-GSD")

    assert plain_decision.action == "preserve"
    assert tense_decision.action == "attach"
