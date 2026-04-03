from __future__ import annotations

from typing import Dict, List, Optional

from config import ALL_RELATIONS_MAP, HEURISTIC_RULES
from report import get_report
from schemas import RawToken, SemanticUnit


def _check_condition(value: object, condition: object, cond_key: str) -> bool:
    if isinstance(condition, bool):
        return bool(value) == condition
    if isinstance(condition, list):
        if value is None:
            return False
        if cond_key == "deprel" and isinstance(value, str) and ":" in value:
            value = value.split(":")[0]
        return value in condition
    return value == condition


def _build_token_features(
    token: RawToken,
    token_map: Dict[str, RawToken],
    introducer: Optional[Dict[str, str]],
) -> Dict[str, object]:
    token_features: Dict[str, object] = {
        "deprel": token.deprel,
        "pos": token.upos,
        "lemma": token.lemma.lower() if token.lemma else "",
        "case": token.feats.get("Case", [None])[0],
        "number": token.feats.get("Number", [None])[0],
        "animacy": token.feats.get("Animacy", [None])[0],
        "verb_form": token.feats.get("VerbForm", [None])[0],
        "has_marker": introducer is not None,
    }
    if introducer:
        token_features["marker"] = introducer.get("form", "").lower()

    head = token_map.get(token.head_token_id or "")
    if head:
        token_features["head_lemma"] = head.lemma.lower() if head.lemma else ""
        token_features["head_degree"] = head.feats.get("Degree", [None])[0]

    return token_features


def _generate_candidates_from_rules(
    token: RawToken,
    token_map: Dict[str, RawToken],
    introducer: Optional[Dict[str, str]],
) -> List[str]:
    primary_candidates = set()
    fallback_candidates = set()
    any_token_fallback_candidates = set()
    token_features = _build_token_features(token, token_map, introducer)

    for rule in HEURISTIC_RULES:
        conditions = rule.get("conditions", {})
        if not conditions:
            conditions_met = True
        else:
            conditions_met = True
            for cond_key, cond_value in conditions.items():
                value_to_check = token_features.get(cond_key)
                if not _check_condition(value_to_check, cond_value, cond_key):
                    conditions_met = False
                    break

        if not conditions_met:
            continue

        rule_name = str(rule.get("rule_name", ""))
        is_fallback = rule_name.lower().startswith("fallback")
        is_any_fallback = rule_name.strip().lower() == "fallback for any token"
        target_set = any_token_fallback_candidates if is_any_fallback else (
            fallback_candidates if is_fallback else primary_candidates
        )
        for candidate_id in rule.get("candidates", []):
            target_set.add(ALL_RELATIONS_MAP.get(candidate_id, f"UNKNOWN_ID_{candidate_id}"))

    if primary_candidates:
        return sorted(primary_candidates)
    if fallback_candidates:
        return sorted(fallback_candidates)
    if any_token_fallback_candidates:
        return sorted(any_token_fallback_candidates)
    return []


def _unit_introducer(unit: SemanticUnit) -> Optional[Dict[str, str]]:
    if not unit.introduced_by:
        return None
    first = unit.introduced_by[0]
    return {"form": first.form, "deprel": first.relation}


def generate_soft_candidates(
    unit: SemanticUnit,
    token_map: Dict[str, RawToken],
    *,
    include_global_fallback: bool,
) -> List[str]:
    if unit.syntactic_link_target_id is None:
        return ["ROOT"]

    token = token_map.get(unit.head_token_id)
    if token is None:
        return ["ROOT"] if unit.syntactic_link_target_id is None else []

    candidates = _generate_candidates_from_rules(token, token_map, _unit_introducer(unit))
    report = get_report()
    if candidates:
        return candidates

    if include_global_fallback:
        report.legacy_candidate_fallback_count += 1
        return sorted(set(ALL_RELATIONS_MAP.values()) | {"ROOT"})

    report.soft_candidate_empty_count += 1
    return []
