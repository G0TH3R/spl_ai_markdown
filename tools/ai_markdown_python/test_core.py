from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "apps" / "spl_ai_markdown_python" / "bin" / "ai_markdown_core.py"


def load_core():
    spec = importlib.util.spec_from_file_location("ai_markdown_core", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load ai_markdown_core")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CoreTests(unittest.TestCase):
    def test_auto_field_prefers_ai_result_1_then_plural(self):
        core = load_core()
        self.assertEqual(core.select_markdown_field({"ai_result_1": "one", "ai_results_1": "two"}), "ai_result_1")
        self.assertEqual(core.select_markdown_field({"ai_results_1": "two"}), "ai_results_1")

    def test_explicit_field_must_be_safe_and_present(self):
        core = load_core()
        self.assertEqual(core.select_markdown_field({"answer_2": "ok"}, "answer_2"), "answer_2")
        for invalid in ("bad field", "x|collect", "_raw", "a.b", ""):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                core.select_markdown_field({invalid: "value"}, invalid)
        with self.assertRaises(ValueError):
            core.select_markdown_field({"other": "value"}, "answer")

    def test_markdown_is_rendered_with_required_extensions_and_strict_sanitization(self):
        core = load_core()
        source = """# Safe\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n```python\nprint('ok')\n```\n\n<script>alert(1)</script>\n<img src=x onerror=alert(1)>\n[bad](javascript:alert(1)) [good](https://example.test)\n<style>body{display:none}</style>\n<form><input value=x></form>\n<svg><circle /></svg>\n<math><mi>x</mi></math>"""
        rendered = core.render_markdown(source)
        self.assertIn("<h1>Safe</h1>", rendered)
        self.assertIn("<table>", rendered)
        self.assertIn('<code class="language-python">', rendered)
        self.assertIn('href="https://example.test"', rendered)
        for forbidden in ("<script", "<img", "onerror", "javascript:", "<style", "<form", "<input", "<svg", "<circle", "<math", "<mi"):
            self.assertNotIn(forbidden, rendered.lower())

    def test_render_record_writes_only_bounded_html_output(self):
        core = load_core()
        record = {"ai_result_1": "**hello**", "_raw": "sensitive raw event"}
        converted = core.render_record(record)
        self.assertEqual(converted["ai_markdown_field"], "ai_result_1")
        self.assertEqual(converted["ai_markdown_html"], "<p><strong>hello</strong></p>")
        self.assertEqual(converted["_raw"], "sensitive raw event")
        with self.assertRaises(ValueError):
            core.render_markdown("x" * (core.MAX_MARKDOWN_CHARS + 1))


if __name__ == "__main__":
    unittest.main()
