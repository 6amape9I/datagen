from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from prompt_builder import PromptPackage


@dataclass(frozen=True)
class ProviderMetadata:
    provider: str
    model_name: str
    generation_profile: str | None = None


@dataclass(frozen=True)
class GenerationResult:
    payload: dict[str, Any] | None
    error: str | None = None


class GenerationProvider(Protocol):
    metadata: ProviderMetadata

    def worker_tokens(self, requested_workers: int) -> list[str]:
        ...

    def create_client(self, worker_token: str) -> Any:
        ...

    def generate(self, client: Any, prompt: PromptPackage) -> GenerationResult:
        ...

    def is_quota_error(self, error_text: str | None) -> bool:
        ...
