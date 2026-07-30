#!/usr/bin/env python3
"""
The small template engine tools/shots-to-html.py renders preview.html.tpl with.

Only the subset the template actually uses is implemented, deliberately: variable
substitution, a loop, and a truthiness block. It exists so the CLI and the
storyboard-html-preview skill render the same structural template instead of two
hand-maintained copies that drift apart.

Supported syntax:
    {{name}}            HTML-escaped substitution
    {{{name}}}          raw substitution, for pre-built markup such as inlined CSS
    {{#each items}}     iterate a list of dicts; inside the block, keys resolve
    {{/each}}           against the item first, then the enclosing context
    {{#if name}}        render when the value is truthy
    {{/if}}

Unknown names render empty rather than raising, which keeps a partially populated
context from producing a traceback in front of a client.
"""

from __future__ import annotations

import html
import re

BLOCK_RE = re.compile(r"\{\{#(each|if)\s+([A-Za-z0-9_]+)\s*\}\}")
RAW_VAR_RE = re.compile(r"\{\{\{\s*([A-Za-z0-9_]+)\s*\}\}\}")
VAR_RE = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")


def escape(value) -> str:
    """HTML-escape a value for text and attribute contexts, including quotes."""
    if value is None or value is False:
        return ""
    if value is True:
        return "true"
    return html.escape(str(value), quote=True)


def _find_block_end(text: str, kind: str, start: int) -> int:
    """Index of the closing tag matching the block opened before `start`."""
    open_re = re.compile(r"\{\{#" + kind + r"\s+[A-Za-z0-9_]+\s*\}\}")
    close_tag = "{{/" + kind + "}}"
    depth = 1
    pos = start
    while depth:
        next_close = text.find(close_tag, pos)
        if next_close == -1:
            raise ValueError(f"unclosed {{{{#{kind}}}}} block")
        next_open = open_re.search(text, pos, next_close)
        if next_open:
            depth += 1
            pos = next_open.end()
            continue
        depth -= 1
        pos = next_close + len(close_tag)
    return pos


def render(template: str, context: dict) -> str:
    """Render `template` against `context`."""
    out: list[str] = []
    pos = 0

    while pos < len(template):
        block = BLOCK_RE.search(template, pos)
        if not block:
            out.append(_render_leaf(template[pos:], context))
            break

        out.append(_render_leaf(template[pos : block.start()], context))
        kind, name = block.group(1), block.group(2)
        body_start = block.end()
        block_end = _find_block_end(template, kind, body_start)
        close_len = len("{{/" + kind + "}}")
        body = template[body_start : block_end - close_len]

        value = context.get(name)
        if kind == "each":
            for item in value or []:
                scoped = dict(context)
                if isinstance(item, dict):
                    scoped.update(item)
                else:
                    scoped["this"] = item
                out.append(render(body, scoped))
        else:
            if value:
                out.append(render(body, context))

        pos = block_end

    return "".join(out)


def _render_leaf(text: str, context: dict) -> str:
    """Substitute variables in a chunk with no block tags left in it."""
    text = RAW_VAR_RE.sub(lambda m: str(context.get(m.group(1), "") or ""), text)
    return VAR_RE.sub(lambda m: escape(context.get(m.group(1))), text)
