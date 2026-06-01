"""kitab.json — language-agnostic AST for structured book content.

Top-level shape:
    {"type": "book", "title": str, "author": str | None, "lang": str, "children": [Block, ...]}

Block types (each is a dict with `type`):
    - book        : root, has `children`
    - chapter     : has `title` and `children`
    - section     : has `heading` and `children`
    - subsection  : has `heading` and `children`
    - paragraph   : has `content` (list of inline items)
    - footnote    : has `id` (globally unique) and `content`
    - quotation   : has `content`, optional `attribution`

Inline items (appear inside `content` arrays):
    - plain string
    - {"type": "quran",        "ref": str, "text": str}
    - {"type": "hadith",       "source": str, "text": str}
    - {"type": "scholar",      "name": str, "rendered": str | None}
    - {"type": "work",         "author": str, "title": str}
    - {"type": "footnote_ref", "id": str}
    - {"type": "arabic",       "text": str}    # inline Arabic preserved in English output
"""

from __future__ import annotations

import json
from typing import Any, Callable

BLOCK_TYPES = {"book", "chapter", "section", "subsection", "paragraph", "footnote", "quotation"}
INLINE_TYPES = {"quran", "hadith", "scholar", "work", "footnote_ref", "arabic"}


def validate(doc: dict) -> None:
    if not isinstance(doc, dict):
        raise ValueError("doc must be dict")
    if doc.get("type") != "book":
        raise ValueError("root must have type='book'")
    if not isinstance(doc.get("children"), list):
        raise ValueError("root must have children list")
    seen_fn_ids: set[str] = set()
    for i, child in enumerate(doc["children"]):
        _validate_block(child, f"book[{i}]", seen_fn_ids)


def _validate_block(b: Any, path: str, seen_fn_ids: set[str]) -> None:
    if not isinstance(b, dict):
        raise ValueError(f"{path}: block must be dict")
    t = b.get("type")
    if t not in BLOCK_TYPES:
        raise ValueError(f"{path}: unknown block type {t!r}")
    if t in ("paragraph", "footnote", "quotation"):
        content = b.get("content")
        if not isinstance(content, list):
            raise ValueError(f"{path}.{t}: content must be list")
        for i, item in enumerate(content):
            _validate_inline(item, f"{path}.{t}[{i}]")
    if "children" in b:
        if not isinstance(b["children"], list):
            raise ValueError(f"{path}.{t}: children must be list")
        for i, c in enumerate(b["children"]):
            _validate_block(c, f"{path}.{t}[{i}]", seen_fn_ids)
    if t == "footnote":
        fid = b.get("id")
        if not fid:
            raise ValueError(f"{path}.footnote: id required")
        if fid in seen_fn_ids:
            raise ValueError(f"{path}.footnote: duplicate id {fid!r}")
        seen_fn_ids.add(fid)


def _validate_inline(item: Any, path: str) -> None:
    if isinstance(item, str):
        return
    if not isinstance(item, dict):
        raise ValueError(f"{path}: inline must be str or dict")
    if item.get("type") not in INLINE_TYPES:
        raise ValueError(f"{path}: unknown inline type {item.get('type')!r}")


def walk(doc: dict, fn: Callable[[dict], None]) -> None:
    fn(doc)
    for c in doc.get("children", []) or []:
        _walk_block(c, fn)


def _walk_block(b: dict, fn: Callable[[dict], None]) -> None:
    fn(b)
    for c in b.get("children", []) or []:
        _walk_block(c, fn)


def chapters(doc: dict) -> list[dict]:
    return [b for b in doc.get("children", []) if b.get("type") == "chapter"]


def extract_text(node: Any) -> str:
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return " ".join(extract_text(x) for x in node)
    if not isinstance(node, dict):
        return ""
    parts: list[str] = []
    if node.get("type") in ("paragraph", "footnote", "quotation"):
        parts.append(extract_text(node.get("content", [])))
    elif "text" in node and isinstance(node["text"], str):
        parts.append(node["text"])
    for key in ("title", "heading", "attribution"):
        v = node.get(key)
        if isinstance(v, str):
            parts.append(v)
    for c in node.get("children", []) or []:
        parts.append(extract_text(c))
    return " ".join(p for p in parts if p)


def count_tokens(node: Any, lang: str = "ar") -> int:
    text = extract_text(node) if not isinstance(node, str) else node
    cpt = 3.5 if lang == "ar" else 4.0
    return int(len(text) / cpt) if text else 0


def footnote_ids(doc: dict) -> set[str]:
    ids: set[str] = set()
    walk(doc, lambda b: ids.add(b["id"]) if b.get("type") == "footnote" and b.get("id") else None)
    return ids


def to_json(doc: Any, indent: int = 2) -> str:
    return json.dumps(doc, ensure_ascii=False, indent=indent)


def from_json(s: str) -> dict:
    return json.loads(s)
