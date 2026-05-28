"""JSON serialization helpers for list fields stored as text."""

import json


def to_json_list(items: list[str] | None) -> str:
    return json.dumps(items or [], ensure_ascii=False)


def from_json_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return [str(x) for x in data] if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []
