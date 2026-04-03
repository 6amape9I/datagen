from __future__ import annotations

import os
from typing import Optional

from google import genai
from google.genai import types

from config import SYSTEM_PROMPT
from response_schema import get_annotation_roles


def request_google_genai_response(
    prompt_text: str,
    *,
    model_name: str,
    api_key: Optional[str] = None,
    return_text: bool = False,
) -> str:
    client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))
    response_schema = genai.types.Schema(
        type=genai.types.Type.OBJECT,
        properties={
            "nodes": genai.types.Schema(
                type=genai.types.Type.ARRAY,
                items=genai.types.Schema(
                    type=genai.types.Type.OBJECT,
                    properties={
                        "id": genai.types.Schema(type=genai.types.Type.STRING),
                        "syntactic_link_name": genai.types.Schema(
                            type=genai.types.Type.STRING,
                            enum=get_annotation_roles(),
                        ),
                    },
                ),
            ),
        },
    )
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt_text)],
        )
    ]
    config = types.GenerateContentConfig(
        max_output_tokens=15000,
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
        response_mime_type="application/json",
        response_schema=response_schema,
        system_instruction=[types.Part.from_text(text=SYSTEM_PROMPT)],
    )
    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=config,
    )
    return response.text if return_text else str(response)
