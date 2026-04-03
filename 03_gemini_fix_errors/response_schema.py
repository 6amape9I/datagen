from __future__ import annotations

from typing import List

from config import ALL_RELATION_NAMES


def get_annotation_roles() -> List[str]:
    seen = set()
    roles: List[str] = []
    for role in ALL_RELATION_NAMES:
        if role not in seen:
            seen.add(role)
            roles.append(role)
    return roles
