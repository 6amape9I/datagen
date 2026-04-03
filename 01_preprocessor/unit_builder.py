from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from attachment_policy import AttachmentDecision, classify_attachment_type, decide_attachment
from hints import build_unit_hints
from schemas import AttachmentRecord, RawToken, SemanticUnit
from token_normalizer import collapse_single_value_map, is_integer_token_id


def _build_attachment_record(token: RawToken, attachment_type: str) -> AttachmentRecord:
    return AttachmentRecord(
        token_id=token.token_id,
        relation=token.deprel or "",
        attachment_type=attachment_type,
        form=token.form,
        lemma=token.lemma,
        upos=token.upos,
        xpos=token.xpos,
    )


def _resolve_host_token_id(
    token_id: str,
    decisions: Dict[str, AttachmentDecision],
    token_map: Dict[str, RawToken],
    cache: Dict[str, Optional[str]],
    trail: Optional[Set[str]] = None,
) -> Optional[str]:
    if token_id in cache:
        return cache[token_id]

    trail = trail or set()
    if token_id in trail:
        cache[token_id] = None
        return None
    trail.add(token_id)

    token = token_map.get(token_id)
    decision = decisions.get(token_id)
    if token is None or decision is None:
        cache[token_id] = None
        return None
    if decision.action != "attach":
        cache[token_id] = token_id
        return token_id

    head_token_id = token.head_token_id
    if not head_token_id or not is_integer_token_id(head_token_id):
        cache[token_id] = None
        return None

    host = _resolve_host_token_id(head_token_id, decisions, token_map, cache, trail)
    cache[token_id] = host
    return host


def _ordered_unique_token_ids(token_ids: List[str], token_map: Dict[str, RawToken]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for token_id in sorted(token_ids, key=lambda item: token_map[item].token_index):
        if token_id not in seen:
            seen.add(token_id)
            ordered.append(token_id)
    return ordered


def _build_unit_surface(span_token_ids: List[str], token_map: Dict[str, RawToken]) -> str:
    return " ".join(token_map[token_id].form for token_id in span_token_ids if token_id in token_map)


def _split_attachment_views(
    attachments: List[AttachmentRecord],
) -> Tuple[List[AttachmentRecord], List[AttachmentRecord]]:
    introducers: List[AttachmentRecord] = []
    function_parts: List[AttachmentRecord] = []
    for attachment in attachments:
        if attachment.attachment_type in {"adposition", "marker"}:
            introducers.append(attachment)
        elif attachment.attachment_type not in {"determiner"}:
            function_parts.append(attachment)
    return introducers, function_parts


def build_units(
    raw_tokens: List[RawToken],
    *,
    language_code: str,
) -> tuple[List[SemanticUnit], Dict[str, RawToken]]:
    token_map = {token.token_id: token for token in raw_tokens if token.token_id}
    integer_tokens = [token for token in raw_tokens if token.is_integer_id]
    decisions = {
        token.token_id: decide_attachment(token, token_map, language_code=language_code)
        for token in integer_tokens
    }
    host_cache: Dict[str, Optional[str]] = {}

    unit_head_ids: List[str] = []
    attachments_by_host: Dict[str, List[AttachmentRecord]] = {}

    for token in integer_tokens:
        decision = decisions[token.token_id]
        if decision.action == "skip":
            continue

        resolved_host = _resolve_host_token_id(token.token_id, decisions, token_map, host_cache)
        if decision.action == "attach" and resolved_host and resolved_host != token.token_id:
            attachments_by_host.setdefault(resolved_host, []).append(
                _build_attachment_record(token, decision.attachment_type or classify_attachment_type(token))
            )
            continue

        unit_head_ids.append(token.token_id)

    units: List[SemanticUnit] = []
    for head_token_id in _ordered_unique_token_ids(unit_head_ids, token_map):
        head = token_map[head_token_id]
        if head.upos == "PUNCT":
            continue

        attachments = sorted(
            attachments_by_host.get(head_token_id, []),
            key=lambda item: token_map[item.token_id].token_index,
        )
        introducers, function_parts = _split_attachment_views(attachments)
        span_token_ids = _ordered_unique_token_ids(
            [head_token_id] + [attachment.token_id for attachment in attachments],
            token_map,
        )

        target_host_id = None
        if head.head_token_id and head.head_token_id not in {"0", ""}:
            target_host_id = _resolve_host_token_id(head.head_token_id, decisions, token_map, host_cache)
        target_unit_id = f"w{target_host_id}" if target_host_id and target_host_id != head_token_id else None

        unit = SemanticUnit(
            unit_id=f"w{head_token_id}",
            head_token_id=head_token_id,
            span_token_ids=span_token_ids,
            surface=_build_unit_surface(span_token_ids, token_map),
            core_lemma=head.lemma,
            upos=head.upos,
            xpos=head.xpos,
            features=collapse_single_value_map(head.feats),
            syntactic_link_target_id=target_unit_id,
            original_deprel=head.deprel,
            attached_tokens=attachments,
            introduced_by=introducers,
            function_parts=function_parts,
        )
        unit.ud_semantic_hints = build_unit_hints(unit)
        units.append(unit)

    return units, token_map
