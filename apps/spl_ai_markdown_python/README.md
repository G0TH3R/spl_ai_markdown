# AI Markdown Python

**Author:** G0TH3R

A Splunk Enterprise 10.4 Classic dashboard that runs arbitrary SPL as the signed-in user, appends the `aimarkdown` streaming command, converts Markdown with vendored Python-Markdown 3.9, sanitizes with Bleach 6.2.0, and sanitizes again with local DOMPurify 3.4.14 before rich HTML insertion.

## Usage

1. Enter bounded SPL returning `ai_result_1` or `ai_results_1` (or provide a safe explicit field name).
2. Choose time bounds and a display cap.
3. Select **Run and render**.

The browser cap does not reduce upstream model calls. Bound data before `| ai`. Searches use the current user's capabilities; action-capable commands require confirmation.

## Security

Allowed HTML is limited to headings, paragraphs, emphasis, lists, blockquotes, code, tables, horizontal rules, and links. Images, scripts, styles, forms, embedded media, SVG, MathML, event handlers, and unsafe protocols are removed. Treat model-generated links as untrusted.

## Local validation

```bash
python3 -m unittest tools.ai_markdown_python.test_core tools.ai_markdown_python.test_command -v
node tools/ai_markdown_python/test_ui.js
python3 tools/ai_markdown_python/verify_and_package.py
```

This app is not installed until deployment is separately verified.
