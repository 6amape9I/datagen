from __future__ import annotations

import json
from typing import Any, Dict


def build_annotation_request_text(sentence_data: Dict[str, Any]) -> str:
    return json.dumps(sentence_data, ensure_ascii=False, indent=2)
