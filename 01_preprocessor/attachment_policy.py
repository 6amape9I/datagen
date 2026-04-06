from __future__ import annotations

from dataclasses import dataclass
import re
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
ARTICLE_HEAVY_KEYWORDS = {
    "english", "german", "french", "italian", "dutch", "norwegian", "swedish", "portuguese", "spanish", "danish",
}
SLAVIC_KEYWORDS = {
    "russian", "czech", "croatian", "bulgarian", "belarusian", "slovak", "ukrainian", "polish", "slovene",
}
FINNIC_KEYWORDS = {"finnish", "estonian"}
CJK_KEYWORDS = {"japanese", "chinese", "classical chinese", "classical_chinese", "korean"}
SEMITIC_KEYWORDS = {"hebrew", "ancient hebrew", "ancient_hebrew"}
ARMENIAN_KEYWORDS = {"armenian", "western armenian", "western_armenian", "classical armenian", "classical_armenian"}

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


@dataclass(slots=True)
class AttachmentDecision:
    action: str
    attachment_type: Optional[str] = None
    reason: Optional[str] = None


def get_language_profile(language_code: str) -> str:
    code = (language_code or "").strip().lower()
    normalized = _NON_ALNUM_RE.sub(" ", code).strip()
    normalized_underscore = normalized.replace(" ", "_")

    def _matches(keywords: set[str]) -> bool:
        return (
            code in keywords
            or normalized in keywords
            or normalized_underscore in keywords
            or any(keyword in normalized for keyword in keywords)
        )

    if code in ARTICLE_HEAVY_LANGUAGES:
        return "article_heavy"
    if _matches(ARTICLE_HEAVY_KEYWORDS):
        return "article_heavy"
    if code in SLAVIC_RICH_INFLECTION_LANGUAGES:
        return "slavic_rich_inflection"
    if _matches(SLAVIC_KEYWORDS):
        return "slavic_rich_inflection"
    if code in FINNIC_LANGUAGES:
        return "finnic_rich_case"
    if _matches(FINNIC_KEYWORDS):
        return "finnic_rich_case"
    if code in CJK_LANGUAGES:
        return "cjk_low_morphology"
    if _matches(CJK_KEYWORDS):
        return "cjk_low_morphology"
    if code in SEMITIC_LANGUAGES:
        return "semitic"
    if _matches(SEMITIC_KEYWORDS):
        return "semitic"
    if code in ARMENIAN_LANGUAGES:
        return "armenian"
    if _matches(ARMENIAN_KEYWORDS):
        return "armenian"
    return "base"


def classify_attachment_type(token: RawToken) -> str:
    deprel = token.deprel or ""
    if deprel == "case" or deprel.startswith("case:"):
        return "adposition"
    if deprel == "mark" or deprel.startswith("mark:"):
        return "marker"
    if deprel == "det" or deprel.startswith("det:"):
        return "determiner"
    if deprel == "cc" or deprel.startswith("cc:"):
        return "coordinator"
    if deprel == "cop" or deprel.startswith("cop:"):
        return "copula"
    if deprel == "aux" or deprel.startswith("aux:"):
        return "auxiliary"
    if deprel == "clf" or deprel.startswith("clf:"):
        return "classifier"
    if deprel == "fixed" or deprel.startswith("fixed:"):
        return "fixed"
    if token.upos == "PART":
        return "particle"
    if token.upos == "SYM":
        return "symbol"
    if deprel.startswith("flat"):
        return "flat"
    if deprel == "compound:prt":
        return "phrasal_particle"
    if deprel == "compound" or deprel.startswith("compound:"):
        return "compound"
    if deprel == "discourse" or deprel.startswith("discourse:"):
        return "discourse"
    return "function_word"


def decide_attachment(
    token: RawToken,
    token_map: Dict[str, RawToken],
    *,
    language_code: str,
) -> AttachmentDecision:
    profile = get_language_profile(language_code)
    deprel = token.deprel or ""
    deprel_base = deprel.split(":", 1)[0]

    if not token.is_integer_id:
        return AttachmentDecision(action="skip", reason="non_integer_token_id")
    if token.upos == "PUNCT":
        return AttachmentDecision(action="skip", reason="punctuation")
    if token.head_token_id in {None, "", "0"} or token.deprel == "root":
        return AttachmentDecision(action="preserve", reason="root_or_headless")

    head = token_map.get(token.head_token_id)
    if head is None:
        return AttachmentDecision(action="preserve", reason="missing_head")

    if deprel in SAFE_ATTACH_DEPRELS or deprel in SAFE_ATTACH_FLAT:
        return AttachmentDecision(action="attach", attachment_type=classify_attachment_type(token), reason="safe_attach")
    if deprel.startswith("case:") or deprel.startswith("mark:") or deprel.startswith("flat:") or deprel.startswith("fixed:"):
        return AttachmentDecision(action="attach", attachment_type=classify_attachment_type(token), reason="safe_attach_subtype")

    if deprel == "det" or deprel.startswith("det:"):
        if profile in {"article_heavy", "base", "semitic"}:
            return AttachmentDecision(action="attach", attachment_type="determiner", reason="determiner_attach")
        return AttachmentDecision(action="preserve", attachment_type="determiner", reason="determiner_preserve")

    if deprel_base in CONTEXTUAL_ATTACH_DEPRELS:
        if deprel.startswith("aux:"):
            return AttachmentDecision(action="attach", attachment_type="auxiliary", reason="auxiliary_subtype_attach")
        if deprel in {"aux", "cop"} or deprel.startswith("cop:"):
            return AttachmentDecision(action="preserve", attachment_type=classify_attachment_type(token), reason="predicate_structure")
        if deprel_base == "compound" and profile in {"slavic_rich_inflection", "finnic_rich_case"}:
            return AttachmentDecision(action="preserve", attachment_type=classify_attachment_type(token), reason="compound_preserve")
        return AttachmentDecision(action="attach", attachment_type=classify_attachment_type(token), reason="contextual_attach")

    if token.upos == "PART":
        if profile in {"cjk_low_morphology", "article_heavy"}:
            return AttachmentDecision(action="attach", attachment_type="particle", reason="particle_attach")
        if deprel in {"advmod", "mark"} or deprel.startswith("mark:") or deprel == "advmod:emph":
            return AttachmentDecision(action="attach", attachment_type="particle", reason="particle_attach")
        return AttachmentDecision(action="preserve", attachment_type="particle", reason="particle_preserve")

    if token.upos == "ADP" and deprel_base == "case" and profile == "cjk_low_morphology":
        return AttachmentDecision(action="attach", attachment_type="particle", reason="particle_attach")

    if token.upos == "SYM" and deprel_base in {"dep", "discourse", "compound"}:
        return AttachmentDecision(action="attach", attachment_type="symbol", reason="symbol_attach")

    if deprel == "flat:name" and head.upos == "PROPN":
        return AttachmentDecision(action="attach", attachment_type="flat", reason="proper_name_flat")

    if deprel_base == "compound" and token.upos in {"PART", "ADP", "ADV"}:
        return AttachmentDecision(action="attach", attachment_type="compound", reason="function_compound")

    if token.upos in {"PART", "CCONJ"} and deprel == "advmod:emph":
        return AttachmentDecision(action="attach", attachment_type="particle", reason="emphasis_particle_attach")

    if deprel in PRESERVE_DEPRELS:
        return AttachmentDecision(action="preserve", reason="semantic_structure")

    return AttachmentDecision(action="preserve", reason="default_preserve")
