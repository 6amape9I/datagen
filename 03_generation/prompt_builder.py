from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from response_schema import get_annotation_roles


PROMPT_ASSET_PATH = Path(__file__).resolve().parent / "prompt_assets" / "node_level_system_prompt.md"


@dataclass(frozen=True)
class PromptPackage:
    system_prompt: str
    user_prompt: str

    def as_text(self) -> str:
        return f"{self.system_prompt}\n\n{self.user_prompt}".strip()


@lru_cache(maxsize=1)
def _load_system_prompt_template() -> str:
    return PROMPT_ASSET_PATH.read_text(encoding="utf-8").strip()


def build_system_prompt() -> str:
    allowed_labels = ", ".join(get_annotation_roles())
    return _load_system_prompt_template().replace("{{ALLOWED_LABELS}}", allowed_labels)


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
