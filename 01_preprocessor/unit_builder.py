from __future__ import annotations

import re
from typing import Dict, List, Optional, Set

from attachment_policy import AttachmentDecision, classify_attachment_type, decide_attachment, get_language_profile
from schemas import CompactNode, InternalAttachment, RawToken
from token_normalizer import collapse_single_value_map, is_integer_token_id


_CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff]")


def _build_attachment(token: RawToken, attachment_type: str) -> InternalAttachment:
    return InternalAttachment(
        token_id=token.token_id,
        form=_clean_surface_piece(token.form),
        attachment_type=attachment_type,
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


def _clean_surface_piece(form: str) -> str:
    cleaned = (form or "").replace("_", "").strip()
    return " ".join(cleaned.split())


def _join_surface_pieces(pieces: List[str], *, language_code: str) -> str:
    profile = get_language_profile(language_code)
    cleaned = [piece for piece in (_clean_surface_piece(piece) for piece in pieces) if piece]
    if not cleaned:
        return ""

    if profile == "cjk_low_morphology" and all(_CJK_RE.search(piece) for piece in cleaned):
        return "".join(cleaned)

    return " ".join(cleaned)


def _extract_introducers(attachments: List[InternalAttachment]) -> List[str]:
    introducers: List[str] = []
    seen = set()
    for attachment in attachments:
        if attachment.attachment_type not in {"adposition", "marker"}:
            continue
        if attachment.form in seen:
            continue
        seen.add(attachment.form)
        introducers.append(attachment.form)
    return introducers


def build_nodes(
    raw_tokens: List[RawToken],
    *,
    language_code: str,
) -> List[CompactNode]:
    token_map = {token.token_id: token for token in raw_tokens if token.token_id}
    integer_tokens = [token for token in raw_tokens if token.is_integer_id]
    decisions = {
        token.token_id: decide_attachment(token, token_map, language_code=language_code)
        for token in integer_tokens
    }
    host_cache: Dict[str, Optional[str]] = {}

    node_head_ids: List[str] = []
    attachments_by_host: Dict[str, List[InternalAttachment]] = {}

    for token in integer_tokens:
        decision = decisions[token.token_id]
        if decision.action == "skip":
            continue

        resolved_host = _resolve_host_token_id(token.token_id, decisions, token_map, host_cache)
        if decision.action == "attach" and resolved_host and resolved_host != token.token_id:
            attachments_by_host.setdefault(resolved_host, []).append(
                _build_attachment(token, decision.attachment_type or classify_attachment_type(token))
            )
            continue

        node_head_ids.append(token.token_id)

    nodes: List[CompactNode] = []
    for head_token_id in _ordered_unique_token_ids(node_head_ids, token_map):
        head = token_map[head_token_id]
        if head.upos == "PUNCT":
            continue

        attachments = sorted(
            attachments_by_host.get(head_token_id, []),
            key=lambda item: token_map[item.token_id].token_index,
        )
        span_token_ids = _ordered_unique_token_ids(
            [head_token_id] + [attachment.token_id for attachment in attachments],
            token_map,
        )

        target_host_id = None
        if head.head_token_id and head.head_token_id not in {"0", ""}:
            target_host_id = _resolve_host_token_id(head.head_token_id, decisions, token_map, host_cache)
        target_node_id = f"w{target_host_id}" if target_host_id and target_host_id != head_token_id else None

        nodes.append(
            CompactNode(
                id=f"w{head_token_id}",
                name=_join_surface_pieces([token_map[token_id].form for token_id in span_token_ids if token_id in token_map], language_code=language_code),
                lemma=head.lemma,
                pos_universal=head.upos,
                features=collapse_single_value_map(head.feats),
                syntactic_link_target_id=target_node_id,
                original_deprel=head.deprel,
                introduced_by=_extract_introducers(attachments),
            )
        )

    return nodes
