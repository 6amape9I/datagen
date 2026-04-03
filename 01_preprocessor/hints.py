from __future__ import annotations

from typing import List

from schemas import SemanticUnit


def build_unit_hints(unit: SemanticUnit) -> List[str]:
    hints = set(unit.ud_semantic_hints)

    if unit.syntactic_link_target_id is None:
        hints.add("root_unit")
        if unit.upos in {"VERB", "AUX", "ADJ"}:
            hints.add("root_predicate")
        elif unit.upos in {"NOUN", "PROPN", "PRON"}:
            hints.add("root_nominal")

    if unit.upos in {"NOUN", "PROPN", "PRON"}:
        hints.add("nominal_head")
    if unit.upos in {"VERB", "AUX"}:
        hints.add("verbal_head")
    if unit.original_deprel in {"nmod", "obl"}:
        hints.add("nominal_modifier")
    if unit.original_deprel == "amod":
        hints.add("adjectival_modifier")
    if unit.original_deprel == "conj":
        hints.add("coordination_member")
    if unit.original_deprel == "nummod" or unit.upos == "NUM":
        hints.add("numeric_modifier")

    case_value = unit.features.get("Case")
    if case_value == "Gen":
        hints.add("genitive_modifier")
    if unit.original_deprel == "obl:tmod":
        hints.add("temporal_oblique")
    if case_value in {"Loc", "Ill", "Ela", "Ade", "All", "Abl", "Ess", "Ine"}:
        hints.add("locative_phrase")

    for attachment in unit.attached_tokens:
        if attachment.attachment_type == "determiner":
            hints.add("determiner_attached")
        elif attachment.attachment_type == "adposition":
            hints.add("adpositional_introducer")
            hints.add("adpositional_phrase")
        elif attachment.attachment_type == "marker":
            hints.add("clausal_subordinator")
        elif attachment.attachment_type == "coordinator":
            hints.add("coordination_marker_attached")
        elif attachment.attachment_type == "auxiliary":
            hints.add("auxiliary_attached")
        elif attachment.attachment_type == "copula":
            hints.add("copula_attached")
        elif attachment.attachment_type == "particle":
            hints.add("particle_attached")

    return sorted(hints)
