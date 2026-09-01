# Security Model

AI Markdown Python treats SPL, model output, and rendered HTML as untrusted.

## Controls

1. Searches execute under the signed-in user's Splunk permissions.
2. Known action-capable SPL commands require browser confirmation.
3. Explicit field names use a strict identifier allowlist.
4. Python-Markdown output passes through a Bleach tag/attribute/protocol allowlist.
5. The browser applies a second DOMPurify allowlist before inserting HTML.
6. Remote images and active/embed content are not allowed.
7. Markdown input is capped at 200,000 characters per record.
8. Browser-rendered rows are bounded, but authors must bound input before model commands.

## Allowed presentation

Headings, paragraphs, emphasis, lists, blockquotes, code, tables, horizontal rules, line breaks, and HTTP/HTTPS/mailto links.

## Reporting

Do not include event payloads, credentials, tokens, cookies, session keys, or private environment identifiers in issues or screenshots.
