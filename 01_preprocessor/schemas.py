from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Dict, List, Optional


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
class InternalAttachment:
    token_id: str
    form: str
    attachment_type: str


@dataclass(slots=True)
class CompactNode:
    id: str
    name: str
    lemma: Optional[str]
    pos_universal: Optional[str]
    features: Dict[str, str] = field(default_factory=dict)
    syntactic_link_target_id: Optional[str] = None
    original_deprel: Optional[str] = None
    introduced_by: List[str] = field(default_factory=list)


@dataclass(slots=True)
class SentenceRecord:
    sentence_id: str
    text: str
    language_code: str
    split: str
    source_file: str
    nodes: List[CompactNode] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sentence_id": self.sentence_id,
            "text": self.text,
            "language_code": self.language_code,
            "split": self.split,
            "source_file": self.source_file,
            "nodes": [serialize_node(node) for node in self.nodes],
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


def serialize_node(node: CompactNode) -> Dict[str, Any]:
    data = serialize_dataclass(node)
    if not data.get("introduced_by"):
        data.pop("introduced_by", None)
    return data
