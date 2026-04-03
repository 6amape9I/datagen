"""Compatibility wrapper around the provider-neutral Google GenAI client."""

from __future__ import annotations

from typing import Optional

from config import MODEL_NAME
from providers.google_genai_client import request_google_genai_response


def generate(
    input_text: str = "INSERT_INPUT_HERE",
    *,
    api_key: Optional[str] = None,
    return_text: bool = False,
    model_name: Optional[str] = None,
):
    return request_google_genai_response(
        input_text,
        model_name=model_name or MODEL_NAME,
        api_key=api_key,
        return_text=return_text,
    )
