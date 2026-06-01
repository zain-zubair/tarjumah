"""Stage 4: whole-manuscript coherence pass. Opus 1M, single shot."""

from __future__ import annotations

from pathlib import Path

from .. import claude_runner, markup

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "coherence.md"


def run(translated: dict, voice: dict, mode: str = "conservative") -> dict:
    glossary = translated.get("_glossary") or voice.get("glossary", {})
    prompt = (PROMPT_PATH.read_text()
        .replace("{style_guide}", voice.get("style_guide", ""))
        .replace("{glossary_json}", markup.to_json(glossary))
        .replace("{citation_style_json}", markup.to_json(voice.get("citation_style", {})))
        .replace("{mode}", mode)
        .replace("{translated_doc_json}", markup.to_json(translated))
    )
    result = claude_runner.run_claude(
        prompt,
        model=claude_runner.LONG_CONTEXT_MODEL,
        timeout=1500,
        expect_json=True,
    )
    if not isinstance(result, dict):
        raise ValueError(f"coherence expected dict, got {type(result).__name__}")
    markup.validate(result)
    if "_glossary" not in result and glossary:
        result["_glossary"] = glossary
    return result
