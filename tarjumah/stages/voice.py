"""Stage 2: produce style guide + glossary + citation style + translator persona."""

from __future__ import annotations

from pathlib import Path

from .. import claude_runner, markup

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "voice_glossary.md"
SAMPLE_THRESHOLD_TOKENS = 150_000


def run(extracted: dict) -> dict:
    total = markup.count_tokens(extracted, lang="ar")
    payload = extracted if total <= SAMPLE_THRESHOLD_TOKENS else _sample(extracted)
    prompt = PROMPT_PATH.read_text().replace("{kitab_json}", markup.to_json(payload))
    result = claude_runner.run_claude(
        prompt,
        model=claude_runner.LONG_CONTEXT_MODEL,
        timeout=900,
        expect_json=True,
    )
    if not isinstance(result, dict):
        raise ValueError(f"voice expected dict, got {type(result).__name__}")
    _validate(result)
    return result


def _sample(doc: dict) -> dict:
    chs = markup.chapters(doc)
    if len(chs) < 3:
        return doc
    samples = [chs[0], chs[len(chs) // 2], chs[-1]]
    return {
        "type": "book",
        "title": doc.get("title"),
        "author": doc.get("author"),
        "lang": doc.get("lang", "ar"),
        "_note": "sampled (first/middle/last chapter; full ToC of titles below)",
        "_chapter_titles": [c.get("title", "") for c in chs],
        "children": samples,
    }


def _validate(v: dict) -> None:
    required = {"book_meta", "style_guide", "glossary", "citation_style", "translator_persona"}
    missing = required - set(v.keys())
    if missing:
        raise ValueError(f"voice artifact missing keys: {missing}")
    if not isinstance(v["glossary"], dict):
        raise ValueError("glossary must be dict")
