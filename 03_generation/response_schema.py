from __future__ import annotations

from typing import Any

from config import ALL_RELATION_NAMES


def get_annotation_roles() -> list[str]:
    seen: set[str] = set()
    roles: list[str] = []
    for role in ALL_RELATION_NAMES:
        if role not in seen:
            seen.add(role)
            roles.append(role)
    return roles


def build_response_json_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["nodes"],
        "properties": {
            "nodes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "syntactic_link_name"],
                    "properties": {
                        "id": {"type": "string"},
                        "syntactic_link_name": {
                            "type": "string",
                            "enum": get_annotation_roles(),
                        },
                    },
                    "additionalProperties": False,
                },
            }
        },
        "additionalProperties": False,
    }


def build_google_response_schema(types_module: Any) -> Any:
    return types_module.Schema(
        type=types_module.Type.OBJECT,
        required=["nodes"],
        properties={
            "nodes": types_module.Schema(
                type=types_module.Type.ARRAY,
                items=types_module.Schema(
                    type=types_module.Type.OBJECT,
                    required=["id", "syntactic_link_name"],
                    properties={
                        "id": types_module.Schema(type=types_module.Type.STRING),
                        "syntactic_link_name": types_module.Schema(
                            type=types_module.Type.STRING,
                            enum=get_annotation_roles(),
                        ),
                    },
                ),
            )
        },
    )
