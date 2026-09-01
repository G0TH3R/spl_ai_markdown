from __future__ import annotations

from pathlib import Path
import re
import sys
from typing import Any

LIB_DIR = Path(__file__).resolve().parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import bleach  # type: ignore[import-not-found]
import markdown  # type: ignore[import-not-found]

AUTO_FIELDS = ("ai_result_1", "ai_results_1")
FIELD_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,127}$")
MAX_MARKDOWN_CHARS = 200_000
ALLOWED_TAGS = frozenset(
    {
        "a", "blockquote", "br", "code", "del", "em", "h1", "h2", "h3", "h4", "h5", "h6",
        "hr", "li", "ol", "p", "pre", "strong", "table", "tbody", "td", "th", "thead", "tr", "ul",
    }
)
ALLOWED_PROTOCOLS = frozenset({"http", "https", "mailto"})


def _allowed_attribute(tag: str, name: str, value: str) -> bool:
    if tag == "a" and name in {"href", "title"}:
        return True
    return tag == "code" and name == "class" and bool(re.fullmatch(r"language-[A-Za-z0-9_+-]{1,64}", value))


def select_markdown_field(record: dict[str, object], explicit_field: str | None = None) -> str:
    if explicit_field is not None:
        if not FIELD_PATTERN.fullmatch(explicit_field) or explicit_field.startswith("_"):
            raise ValueError("field must match ^[A-Za-z][A-Za-z0-9_]{0,127}$")
        if explicit_field not in record:
            raise ValueError(f"field is not present in record: {explicit_field}")
        return explicit_field
    for field in AUTO_FIELDS:
        if field in record:
            return field
    raise ValueError("record has neither ai_result_1 nor ai_results_1")


def render_markdown(value: object) -> str:
    source = "" if value is None else str(value)
    if len(source) > MAX_MARKDOWN_CHARS:
        raise ValueError(f"markdown exceeds {MAX_MARKDOWN_CHARS} characters")
    rendered = markdown.markdown(
        source,
        extensions=["fenced_code", "tables", "sane_lists"],
        output_format="html",
    )
    return bleach.clean(
        rendered,
        tags=ALLOWED_TAGS,
        attributes=_allowed_attribute,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        strip_comments=True,
    )


def render_record(record: dict[str, Any], explicit_field: str | None = None) -> dict[str, Any]:
    field = select_markdown_field(record, explicit_field)
    output = dict(record)
    output["ai_markdown_field"] = field
    output["ai_markdown_html"] = render_markdown(record[field])
    return output
