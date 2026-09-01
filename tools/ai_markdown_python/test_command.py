from __future__ import annotations

import configparser
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "apps" / "spl_ai_markdown_python"
BIN = APP / "bin"
LIB = BIN / "lib"


def load_command():
    sys.path[:0] = [str(BIN), str(LIB)]
    spec = importlib.util.spec_from_file_location("aimarkdown", BIN / "aimarkdown.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load aimarkdown")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CommandTests(unittest.TestCase):
    def test_streaming_command_converts_auto_and_explicit_fields(self):
        module = load_command()
        command = module.AiMarkdownCommand()
        command.field = None
        rows = list(command.stream(iter([{"ai_results_1": "# Hello"}])))
        self.assertEqual(rows[0]["ai_markdown_html"], "<h1>Hello</h1>")
        command.field = "answer"
        rows = list(command.stream(iter([{"answer": "**Yes**"}])))
        self.assertEqual(rows[0]["ai_markdown_field"], "answer")

    def test_commands_conf_is_streaming_python3_and_local_only(self):
        parser = configparser.ConfigParser(interpolation=None, strict=True)
        with (APP / "default" / "commands.conf").open(encoding="utf-8") as handle:
            parser.read_file(handle)
        stanza = parser["aimarkdown"]
        self.assertEqual(stanza["filename"], "aimarkdown.py")
        self.assertEqual(stanza["python.version"], "python3")
        self.assertEqual(stanza["streaming"], "true")
        self.assertEqual(stanza["local"], "true")
        self.assertEqual(stanza["supports_getinfo"], "true")


if __name__ == "__main__":
    unittest.main()
