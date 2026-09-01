#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

BIN_DIR = Path(__file__).resolve().parent
LIB_DIR = BIN_DIR / "lib"
sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(BIN_DIR))

from splunklib.searchcommands import Configuration, Option, StreamingCommand, dispatch, validators  # type: ignore[import-not-found]
from ai_markdown_core import render_record


@Configuration()
class AiMarkdownCommand(StreamingCommand):
    """Render a selected Markdown field to server-sanitized HTML."""

    field = Option(require=False, validate=validators.Fieldname())

    def stream(self, records):
        explicit_field = str(self.field) if self.field else None
        for record in records:
            yield render_record(record, explicit_field)


if __name__ == "__main__":
    dispatch(AiMarkdownCommand, sys.argv, sys.stdin, sys.stdout, __name__)
