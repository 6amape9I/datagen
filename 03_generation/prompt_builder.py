from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from response_schema import build_runtime_ontology_context


@dataclass(frozen=True)
class PromptPackage:
    system_prompt: str
    user_prompt: str

    def as_text(self) -> str:
        return f"{self.system_prompt}\n\n{self.user_prompt}".strip()


def build_system_prompt() -> str:
    rules = [
        "You are a semantic relation annotator for compact nodes inside a single sentence.",
        "Choose exactly one syntactic_link_name for every node.",
        "Return only JSON with shape {\"nodes\":[{\"id\":\"...\",\"syntactic_link_name\":\"...\"}]} and no extra text.",
        "If syntactic_link_target_id is null, choose ROOT. Otherwise ROOT is forbidden.",
        "Use only the allowed ontology labels below.",
    ]
    return "\n".join(rules) + "\n\n" + build_runtime_ontology_context()


def build_user_prompt(model_input: dict[str, Any]) -> str:
    payload = json.dumps(model_input, ensure_ascii=False, separators=(",", ":"))
    return (
        "Annotate each node in the JSON payload.\n"
        "Return only the compact JSON object described in the system instructions.\n"
        f"Payload:\n{payload}"
    )


def build_prompt_package(model_input: dict[str, Any]) -> PromptPackage:
    return PromptPackage(
        system_prompt=build_system_prompt(),
        user_prompt=build_user_prompt(model_input),
    )
