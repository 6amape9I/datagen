from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from schemas import RawToken


_INTEGER_TOKEN_ID_PATTERN = re.compile(r"^\d+$")


def is_integer_token_id(raw_id: Optional[str]) -> bool:
    if not raw_id:
        return False
    return bool(_INTEGER_TOKEN_ID_PATTERN.match(str(raw_id)))


def collapse_single_value_map(values: Dict[str, List[str]]) -> Dict[str, str]:
    collapsed: Dict[str, str] = {}
    for key, items in values.items():
        if items:
            collapsed[key] = items[0]
    return collapsed


def normalize_feature_map(raw_map: Any) -> Dict[str, List[str]]:
    normalized: Dict[str, List[str]] = {}
    try:
        items = dict(raw_map).items()
    except Exception:
        return normalized

    for key, value in items:
        if value is None:
            normalized[key] = []
        else:
            normalized[key] = sorted(str(item) for item in value)
    return normalized


def normalize_deps(raw_deps: Any) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    try:
        items = dict(raw_deps).items()
    except Exception:
        return normalized

    for head_token_id, payload in items:
        relation = None
        extras: List[str] = []
        if isinstance(payload, tuple):
            relation = payload[0] if payload else None
            extras = [str(item) for item in payload[1:] if item is not None]
        elif payload is not None:
            relation = str(payload)

        normalized.append(
            {
                "head_token_id": str(head_token_id),
                "relation": relation,
                "extras": extras,
            }
        )
    return normalized


def normalize_sentence_tokens(sentence: Any) -> List[RawToken]:
    normalized: List[RawToken] = []
    for token_index, token in enumerate(sentence):
        token_id = str(token.id) if token.id is not None else ""
        normalized.append(
            RawToken(
                token_id=token_id,
                form=token.form or "",
                lemma=token.lemma,
                upos=token.upos,
                xpos=token.xpos,
                feats=normalize_feature_map(token.feats),
                head_token_id=str(token.head) if token.head is not None else None,
                deprel=token.deprel,
                misc=normalize_feature_map(token.misc),
                deps=normalize_deps(token.deps),
                token_index=token_index,
                is_integer_id=is_integer_token_id(token_id),
            )
        )
    return normalized
