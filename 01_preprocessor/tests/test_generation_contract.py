from __future__ import annotations

import json
from pathlib import Path

from input_builder import build_model_input
from prompt_builder import PROMPT_ASSET_PATH, build_prompt_package
from providers.google_genai import (
    build_google_request_debug_snapshot,
    build_google_tools,
    normalize_google_thinking_level,
)
from response_schema import build_response_json_schema, get_annotation_roles
from sentence_builder import process_conllu_file
from validator import validate_response


def _build_sample_record(tmp_path: Path):
    sample = """# sent_id = 1
# text = The city in France
1\tThe\tthe\tDET\tDT\tDefinite=Def|PronType=Art\t2\tdet\t_\t_
2\tcity\tcity\tNOUN\tNN\tNumber=Sing\t0\troot\t_\t_
3\tin\tin\tADP\tIN\t_\t4\tcase\t_\t_
4\tFrance\tFrance\tPROPN\tNNP\tNumber=Sing\t2\tnmod\t_\t_
"""
    filepath = tmp_path / "sample-test.conllu"
    filepath.write_text(sample, encoding="utf-8")
    return process_conllu_file(
        filepath,
        sentence_id_prefix="eng_sample-test.conllu",
        language_code="eng",
        split="test",
        source_file="eng_sample-test.conllu",
    )[0]


def test_generation_input_builder_uses_compact_nodes_only(tmp_path: Path) -> None:
    record = _build_sample_record(tmp_path)

    llm_payload = build_model_input(record)

    assert set(llm_payload.keys()) == {"text", "nodes"}
    assert llm_payload["nodes"][0]["name"] == "The city"
    assert "sentence_id" not in llm_payload
    assert "language_code" not in llm_payload
    assert llm_payload["nodes"][1]["introduced_by"] == ["in"]
    assert llm_payload["nodes"][1]["head_lemma"] == "city"


def test_generation_prompt_builder_uses_canonical_prompt_asset(tmp_path: Path) -> None:
    record = _build_sample_record(tmp_path)
    prompt = build_prompt_package(build_model_input(record))

    assert PROMPT_ASSET_PATH.exists()
    assert "Allowed labels:" in prompt.system_prompt
    assert "{{ALLOWED_LABELS}}" not in prompt.system_prompt
    assert "Payload:" in prompt.user_prompt
    assert '"text":"The city in France"' in prompt.user_prompt
    assert "sentence_id" not in prompt.user_prompt


def test_generation_validator_accepts_minimal_valid_output(tmp_path: Path) -> None:
    record = _build_sample_record(tmp_path)
    response_nodes = [
        {"id": "w2", "syntactic_link_name": "ROOT"},
        {"id": "w4", "syntactic_link_name": "Content_Theme"},
    ]

    assert validate_response(record, response_nodes) is True


def test_generation_validator_rejects_invalid_role_duplicate_id_and_bad_root(tmp_path: Path) -> None:
    record = _build_sample_record(tmp_path)

    assert validate_response(
        record,
        [
            {"id": "w2", "syntactic_link_name": "ROOT"},
            {"id": "w4", "syntactic_link_name": "NotARole"},
        ],
    ) is False
    assert validate_response(
        record,
        [
            {"id": "w2", "syntactic_link_name": "ROOT"},
            {"id": "w2", "syntactic_link_name": "Content_Theme"},
        ],
    ) is False
    assert validate_response(
        record,
        [
            {"id": "w2", "syntactic_link_name": "ROOT"},
            {"id": "w4", "syntactic_link_name": "ROOT"},
        ],
    ) is False


def test_generation_response_schema_matches_shared_ontology() -> None:
    roles = get_annotation_roles()
    schema = build_response_json_schema()

    assert len(roles) == len(set(roles))
    assert schema["properties"]["nodes"]["items"]["properties"]["syntactic_link_name"]["enum"] == roles


def test_google_provider_helpers_disable_search_by_default() -> None:
    class DummyTypes:
        class GoogleSearch:
            def __init__(self):
                self.kind = "search"

        class Tool:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

    assert build_google_tools(DummyTypes, enable_search_tool=False) == []
    tools = build_google_tools(DummyTypes, enable_search_tool=True)
    assert len(tools) == 1
    assert "googleSearch" in tools[0].kwargs
    assert normalize_google_thinking_level("medium") == "MEDIUM"
    assert normalize_google_thinking_level("unknown") == "HIGH"


def test_google_provider_debug_dump_prints_full_request_bundle(tmp_path: Path) -> None:
    record = _build_sample_record(tmp_path)
    model_input = build_model_input(record)
    prompt = build_prompt_package(model_input)

    snapshot = build_google_request_debug_snapshot(
        prompt,
        model_name="gemma-4-31b-it",
        max_output_tokens=32760,
        temperature=0.0,
        thinking_level="HIGH",
        enable_search_tool=True,
    )

    print(json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True))

    assert snapshot["provider"] == "google_genai"
    assert snapshot["model"] == "gemma-4-31b-it"
    assert snapshot["config"]["thinking_level"] == "HIGH"
    assert snapshot["config"]["tools"] == ["googleSearch"]
    assert snapshot["config"]["response_schema"] == build_response_json_schema()
    assert "Allowed labels:" in snapshot["system_prompt"]
    assert '"text":"The city in France"' in snapshot["user_prompt"]
