from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import requests

from config import GENERATION_PROFILE, LOCAL_API_URL, LOCAL_MODEL_NAME
from prompt_builder import PromptPackage
from providers.base import GenerationResult, ProviderMetadata


@dataclass(frozen=True)
class LocalHTTPProvider:
    metadata: ProviderMetadata = ProviderMetadata(
        provider="local_http",
        model_name=LOCAL_MODEL_NAME,
        generation_profile=GENERATION_PROFILE,
    )
    endpoint_url: str = LOCAL_API_URL

    def worker_tokens(self, requested_workers: int) -> list[str]:
        count = max(1, requested_workers)
        return [f"local-worker-{index + 1}" for index in range(count)]

    def create_client(self, worker_token: str) -> Any:
        session = requests.Session()
        session.trust_env = False
        return session

    def generate(self, client: Any, prompt: PromptPackage) -> GenerationResult:
        if not isinstance(client, requests.Session):
            return GenerationResult(None, "local_http_client_missing")

        try:
            response = client.post(
                self.endpoint_url,
                json={"text": prompt.as_text()},
                timeout=12000,
            )
            if response.status_code != 200:
                return GenerationResult(
                    None,
                    f"local_http_status_{response.status_code}: {response.text}",
                )

            response_json = response.json()
            if isinstance(response_json, dict) and isinstance(response_json.get("nodes"), list):
                return GenerationResult(response_json, None)

            full_response_text = str(response_json.get("response", "")).strip()
            if not full_response_text:
                return GenerationResult(None, "local_http_empty_response")

            return GenerationResult(json.loads(full_response_text), None)
        except json.JSONDecodeError as exc:
            return GenerationResult(None, f"local_http_json_decode_failed: {exc}")
        except requests.RequestException as exc:  # pragma: no cover - network/provider code
            return GenerationResult(None, f"local_http_request_failed: {exc}")
        except Exception as exc:  # pragma: no cover - network/provider code
            return GenerationResult(None, f"local_http_unexpected_error: {exc}")

    def is_quota_error(self, error_text: str | None) -> bool:
        return False
