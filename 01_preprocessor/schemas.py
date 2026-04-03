from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Dict, List, Optional


PREPROCESSED_SCHEMA_VERSION = 2


@dataclass(slots=True)
class RawToken:
    token_id: str
    form: str
    lemma: Optional[str]
    upos: Optional[str]
    xpos: Optional[str]
    feats: Dict[str, List[str]] = field(default_factory=dict)
    head_token_id: Optional[str] = None
    deprel: Optional[str] = None
    misc: Dict[str, List[str]] = field(default_factory=dict)
    deps: List[Dict[str, Any]] = field(default_factory=list)
    token_index: int = 0
    is_integer_id: bool = False


@dataclass(slots=True)
class AttachmentRecord:
    token_id: str
    relation: str
    attachment_type: str
    form: str
    lemma: Optional[str]
    upos: Optional[str]
    xpos: Optional[str]


@dataclass(slots=True)
class SemanticUnit:
    unit_id: str
    head_token_id: str
    span_token_ids: List[str]
    surface: str
    core_lemma: Optional[str]
    upos: Optional[str]
    xpos: Optional[str]
    features: Dict[str, str] = field(default_factory=dict)
    syntactic_link_target_id: Optional[str] = None
    original_deprel: Optional[str] = None
    attached_tokens: List[AttachmentRecord] = field(default_factory=list)
    introduced_by: List[AttachmentRecord] = field(default_factory=list)
    function_parts: List[AttachmentRecord] = field(default_factory=list)
    ud_semantic_hints: List[str] = field(default_factory=list)
    semantic_candidates_soft: List[str] = field(default_factory=list)


@dataclass(slots=True)
class SentenceRecord:
    sentence_id: str
    text: str
    language_code: str
    split: str
    source_file: str
    tokens: List[RawToken] = field(default_factory=list)
    units: List[SemanticUnit] = field(default_factory=list)
    legacy_nodes: List[Dict[str, Any]] = field(default_factory=list)
    preprocessed_schema_version: int = PREPROCESSED_SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "preprocessed_schema_version": self.preprocessed_schema_version,
            "sentence_id": self.sentence_id,
            "text": self.text,
            "language_code": self.language_code,
            "split": self.split,
            "source_file": self.source_file,
            "tokens": serialize_dataclass_list(self.tokens),
            "units": serialize_dataclass_list(self.units),
            "legacy_nodes": self.legacy_nodes,
        }


def serialize_dataclass_list(items: List[Any]) -> List[Any]:
    return [serialize_dataclass(item) for item in items]


def serialize_dataclass(value: Any) -> Any:
    if is_dataclass(value):
        data = asdict(value)
        return {key: serialize_dataclass(item) for key, item in data.items()}
    if isinstance(value, list):
        return [serialize_dataclass(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize_dataclass(item) for key, item in value.items()}
    return value
