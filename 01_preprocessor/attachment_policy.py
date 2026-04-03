from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from schemas import RawToken


SAFE_ATTACH_DEPRELS = {"case", "mark", "fixed", "compound:prt", "goeswith"}
SAFE_ATTACH_FLAT = {"flat", "flat:name", "flat:foreign"}
CONTEXTUAL_ATTACH_DEPRELS = {"cc", "cop", "aux", "clf", "compound", "discourse"}
PRESERVE_DEPRELS = {
    "root",
    "conj",
    "parataxis",
    "appos",
    "acl",
    "acl:relcl",
    "ccomp",
    "csubj",
    "advcl",
    "xcomp",
    "obj",
    "iobj",
    "obl",
    "nsubj",
    "nsubj:pass",
    "vocative",
}

ARTICLE_HEAVY_LANGUAGES = {
    "dan", "deu", "eng", "fra", "ita", "nld", "nor", "por", "spa", "swe",
}
SLAVIC_RICH_INFLECTION_LANGUAGES = {
    "bel", "bul", "ces", "hrv", "pol", "rus", "slk", "slv", "ukr",
}
FINNIC_LANGUAGES = {"est", "fin"}
CJK_LANGUAGES = {"jpn", "kor", "lzh", "zho"}
SEMITIC_LANGUAGES = {"heb"}
ARMENIAN_LANGUAGES = {"arm", "hye", "hy"}


@dataclass(slots=True)
class AttachmentDecision:
    action: str
    attachment_type: Optional[str] = None
    reason: Optional[str] = None


def get_language_profile(language_code: str) -> str:
    code = (language_code or "").strip().lower()
    if code in ARTICLE_HEAVY_LANGUAGES:
        return "article_heavy"
    if code in SLAVIC_RICH_INFLECTION_LANGUAGES:
        return "slavic_rich_inflection"
    if code in FINNIC_LANGUAGES:
        return "finnic_rich_case"
    if code in CJK_LANGUAGES:
        return "cjk_low_morphology"
    if code in SEMITIC_LANGUAGES:
        return "semitic"
    if code in ARMENIAN_LANGUAGES:
        return "armenian"
    return "base"


def classify_attachment_type(token: RawToken) -> str:
    if token.deprel == "case":
        return "adposition"
    if token.deprel == "mark":
        return "marker"
    if token.deprel == "det":
        return "determiner"
    if token.deprel == "cc":
        return "coordinator"
    if token.deprel == "cop":
        return "copula"
    if token.deprel == "aux":
        return "auxiliary"
    if token.deprel == "clf":
        return "classifier"
    if token.deprel == "fixed":
        return "fixed"
    if token.upos == "PART":
        return "particle"
    if token.upos == "SYM":
        return "symbol"
    if token.deprel and token.deprel.startswith("flat"):
        return "flat"
    if token.deprel == "compound:prt":
        return "phrasal_particle"
    if token.deprel == "compound":
        return "compound"
    if token.deprel == "discourse":
        return "discourse"
    return "function_word"


def decide_attachment(
    token: RawToken,
    token_map: Dict[str, RawToken],
    *,
    language_code: str,
) -> AttachmentDecision:
    profile = get_language_profile(language_code)

    if not token.is_integer_id:
        return AttachmentDecision(action="skip", reason="non_integer_token_id")
    if token.upos == "PUNCT":
        return AttachmentDecision(action="skip", reason="punctuation")
    if token.head_token_id in {None, "", "0"} or token.deprel == "root":
        return AttachmentDecision(action="preserve", reason="root_or_headless")

    head = token_map.get(token.head_token_id)
    if head is None:
        return AttachmentDecision(action="preserve", reason="missing_head")

    if token.deprel in SAFE_ATTACH_DEPRELS or token.deprel in SAFE_ATTACH_FLAT:
        return AttachmentDecision(action="attach", attachment_type=classify_attachment_type(token), reason="safe_attach")

    if token.deprel == "det":
        if profile in {"article_heavy", "base"}:
            return AttachmentDecision(action="attach", attachment_type="determiner", reason="determiner_attach")
        return AttachmentDecision(action="preserve", attachment_type="determiner", reason="determiner_preserve")

    if token.deprel in CONTEXTUAL_ATTACH_DEPRELS:
        if token.deprel in {"aux", "cop"}:
            return AttachmentDecision(action="preserve", attachment_type=classify_attachment_type(token), reason="predicate_structure")
        if token.deprel == "compound" and profile in {"slavic_rich_inflection", "finnic_rich_case"}:
            return AttachmentDecision(action="preserve", attachment_type=classify_attachment_type(token), reason="compound_preserve")
        return AttachmentDecision(action="attach", attachment_type=classify_attachment_type(token), reason="contextual_attach")

    if token.upos == "PART":
        if profile in {"cjk_low_morphology", "article_heavy"}:
            return AttachmentDecision(action="attach", attachment_type="particle", reason="particle_attach")
        if token.deprel in {"advmod", "mark"}:
            return AttachmentDecision(action="attach", attachment_type="particle", reason="particle_attach")
        return AttachmentDecision(action="preserve", attachment_type="particle", reason="particle_preserve")

    if token.upos == "ADP" and token.deprel == "case" and profile == "cjk_low_morphology":
        return AttachmentDecision(action="attach", attachment_type="particle", reason="particle_attach")

    if token.upos == "SYM" and token.deprel in {"dep", "discourse", "compound"}:
        return AttachmentDecision(action="attach", attachment_type="symbol", reason="symbol_attach")

    if token.deprel == "flat:name" and head.upos == "PROPN":
        return AttachmentDecision(action="attach", attachment_type="flat", reason="proper_name_flat")

    if token.deprel == "compound" and token.upos in {"PART", "ADP", "ADV"}:
        return AttachmentDecision(action="attach", attachment_type="compound", reason="function_compound")

    if token.deprel in PRESERVE_DEPRELS:
        return AttachmentDecision(action="preserve", reason="semantic_structure")

    return AttachmentDecision(action="preserve", reason="default_preserve")
