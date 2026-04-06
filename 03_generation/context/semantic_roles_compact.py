from __future__ import annotations

from config import ALL_RELATION_NAMES


ROLE_SHORT_DEFINITIONS = {
    "ROOT": "sentence root; use only when syntactic_link_target_id is null",
    "Agent": "volitional initiator or controller of an event",
    "Patient": "entity affected, changed, or acted upon",
    "Recipient": "animate or address-like receiver of transfer",
    "Instrument": "means, tool, material, or mechanism for an event",
    "Inclusion_Containment": "inside a container, space, or bounded area",
    "Exteriority": "outside the boundaries of the landmark",
    "Support": "on a supporting surface",
    "Subjacency": "below the landmark",
    "Covering_Superadjacency": "above or over the landmark",
    "Proximity": "near the landmark without contact",
    "Contact_Adjacency": "touching or directly adjacent without support/containment",
    "Attachment": "firmly attached or functionally joined",
    "Functional_Proximity": "institutional or functional association rather than physical location",
    "Source_as_Origin": "origin or source of emergence or transfer",
    "Goal_as_Recipient": "animate endpoint or addressee of movement/transfer",
    "Duration": "how long an event lasts",
    "Point_in_Time": "when an event happens",
    "Frequency": "how often an event happens",
    "Quality": "attribute or property",
    "Possession": "ownership or belonging",
    "Content_Theme": "topic, subject matter, or informational content",
    "Addition_Conjunction": "additive coordination or conjunction",
    "Disjunction": "alternative or choice relation",
    "Contrast": "contrast between coordinated facts",
    "Concession": "fact that holds despite another fact",
    "Clarification": "content or explanation clause",
    "Goal": "purpose or intended result",
    "Condition": "condition on which another fact depends",
    "Comparison": "comparative relation",
    "Specification_which": "restrictive or descriptive specification of a referent",
    "Specification_that_is": "rephrasing or explanatory restatement",
    "Addition": "additional included element or extension",
}


ROLE_DISAMBIGUATION_RULES = (
    "Agent vs Patient: Agent controls or initiates; Patient is affected or undergoes change.",
    "Recipient vs Patient: Recipient receives transfer; Patient is acted upon.",
    "Inclusion_Containment vs Support vs Contact_Adjacency: inside vs on a supporting surface vs simple contact.",
    "Quality vs Possession vs Content_Theme: property vs ownership/belonging vs topic/content.",
    "Duration vs Point_in_Time vs Frequency: how long vs when vs how often.",
    "ROOT: if syntactic_link_target_id is null, choose ROOT; otherwise ROOT is forbidden.",
)


def _fallback_definition(role_name: str) -> str:
    return role_name.replace("_", " ")


def build_compact_ontology_text() -> str:
    lines = ["Allowed labels and compact cues:"]
    for role_name in ALL_RELATION_NAMES:
        lines.append(f"- {role_name}: {ROLE_SHORT_DEFINITIONS.get(role_name, _fallback_definition(role_name))}")

    lines.append("")
    lines.append("Key disambiguation rules:")
    for rule in ROLE_DISAMBIGUATION_RULES:
        lines.append(f"- {rule}")
    return "\n".join(lines)
