from __future__ import annotations

from hints import build_unit_hints
from schemas import AttachmentRecord, SemanticUnit


def test_hints_are_descriptive_and_non_binding() -> None:
    unit = SemanticUnit(
        unit_id="w4",
        head_token_id="4",
        span_token_ids=["3", "4"],
        surface="in France",
        core_lemma="France",
        upos="PROPN",
        xpos="NNP",
        features={"Case": "Loc"},
        syntactic_link_target_id="w2",
        original_deprel="obl:tmod",
        attached_tokens=[
            AttachmentRecord(
                token_id="3",
                relation="case",
                attachment_type="adposition",
                form="in",
                lemma="in",
                upos="ADP",
                xpos="IN",
            )
        ],
    )

    hints = build_unit_hints(unit)

    assert "adpositional_introducer" in hints
    assert "locative_phrase" in hints
    assert "temporal_oblique" in hints
    assert "nominal_head" in hints
