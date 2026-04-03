from __future__ import annotations

from config import HEURISTIC_RULES
from heuristic_candidates import _build_token_features, _check_condition
from schemas import RawToken


def test_heuristic_rule_matching_uses_and_not_or() -> None:
    token = RawToken(
        token_id="1",
        form="city",
        lemma="city",
        upos="NOUN",
        xpos="NN",
        feats={"Case": ["Nom"]},
        head_token_id="2",
        deprel="nsubj",
        token_index=0,
        is_integer_id=True,
    )
    head = RawToken(
        token_id="2",
        form="goes",
        lemma="go",
        upos="VERB",
        xpos="VBZ",
        feats={},
        head_token_id="0",
        deprel="root",
        token_index=1,
        is_integer_id=True,
    )

    features = _build_token_features(token, {"1": token, "2": head}, None)
    rule = next(rule for rule in HEURISTIC_RULES if rule["rule_name"] == "Patient (direct object)")

    conditions_met = True
    for cond_key, cond_value in rule["conditions"].items():
        if not _check_condition(features.get(cond_key), cond_value, cond_key):
            conditions_met = False
            break

    assert conditions_met is False
