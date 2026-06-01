"""Stage 3: chunked translation. Parallel chapters, sequential within."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .. import claude_runner, chunking, markup

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "translate_chunk.md"
PREV_ENGLISH_TAIL_CHARS = 6000     # ~1500 tokens
NEXT_PREVIEW_CHARS = 2000
MAX_CHAPTER_WORKERS = 5


def run(extracted: dict, voice: dict) -> dict:
    chunks = chunking.chunk_book(extracted)
    if not chunks:
        raise ValueError("no chunks produced — empty book?")

    by_chapter: dict[int, list[chunking.Chunk]] = {}
    for c in chunks:
        by_chapter.setdefault(c.chapter_idx, []).append(c)
    for ch_idx in by_chapter:
        by_chapter[ch_idx].sort(key=lambda c: c.chunk_idx_in_chapter)

    template = PROMPT_PATH.read_text()
    glossary_lock = threading.Lock()
    running_glossary: dict = dict(voice.get("glossary", {}))
    translated_by_idx: dict[int, list[dict]] = {}

    def process_chapter(ch_idx: int, ch_chunks: list[chunking.Chunk]) -> None:
        prev_english = ""
        for ci, chunk in enumerate(ch_chunks):
            next_preview = ""
            if ci + 1 < len(ch_chunks):
                next_preview = markup.extract_text(ch_chunks[ci + 1].blocks)[:NEXT_PREVIEW_CHARS]
            with glossary_lock:
                gloss_snapshot = dict(running_glossary)
            opening = "[OPENING CHUNK — sets the voice for the entire book]" if (ch_idx == 0 and ci == 0) else ""
            prompt = (template
                .replace("{translator_persona}", voice.get("translator_persona", ""))
                .replace("{style_guide}", voice.get("style_guide", ""))
                .replace("{glossary_json}", markup.to_json(gloss_snapshot))
                .replace("{citation_style_json}", markup.to_json(voice.get("citation_style", {})))
                .replace("{prev_chunk_english}", prev_english if prev_english else "[OPENING CHUNK]")
                .replace("{next_chunk_source_preview}", next_preview if next_preview else "[FINAL CHUNK]")
                .replace("{chunk_idx_in_chapter}", str(chunk.chunk_idx_in_chapter + 1))
                .replace("{chunks_in_chapter}", str(chunk.chunks_in_chapter))
                .replace("{chapter_idx}", str(chunk.chapter_idx + 1))
                .replace("{opening_marker}", opening)
                .replace("{chunk_blocks_json}", markup.to_json(chunk.blocks))
            )
            result = claude_runner.run_claude(
                prompt,
                model=claude_runner.DEFAULT_MODEL,
                timeout=1500,
                expect_json=True,
            )
            translated_blocks = result.get("translated_blocks", []) if isinstance(result, dict) else []
            additions = result.get("glossary_additions", {}) if isinstance(result, dict) else {}
            translated_by_idx[chunk.idx] = translated_blocks
            with glossary_lock:
                for k, v in (additions or {}).items():
                    if k not in running_glossary:
                        running_glossary[k] = v
            prev_english = markup.extract_text(translated_blocks)[-PREV_ENGLISH_TAIL_CHARS:]

    workers = min(MAX_CHAPTER_WORKERS, len(by_chapter))
    print(f"  → {len(chunks)} chunks across {len(by_chapter)} chapters, {workers} parallel workers", flush=True)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(process_chapter, idx, chs) for idx, chs in by_chapter.items()]
        for f in as_completed(futures):
            f.result()

    return _reassemble(extracted, chunks, translated_by_idx, running_glossary)


def _reassemble(
    original: dict,
    chunks: list[chunking.Chunk],
    translated: dict[int, list[dict]],
    glossary: dict,
) -> dict:
    chapters_list = markup.chapters(original)
    if not chapters_list:
        flat: list[dict] = []
        for c in sorted(chunks, key=lambda x: x.idx):
            flat.extend(translated.get(c.idx, []))
        return {**original, "lang": "en", "children": flat, "_glossary": glossary}

    new_chapter_blocks: list[list[dict]] = [[] for _ in chapters_list]
    for c in sorted(chunks, key=lambda x: x.idx):
        new_chapter_blocks[c.chapter_idx].extend(translated.get(c.idx, []))

    new_chapters = []
    for ch, blocks in zip(chapters_list, new_chapter_blocks):
        new_chapters.append({**ch, "children": blocks})

    new_children = []
    chapter_iter = iter(new_chapters)
    for child in original.get("children", []):
        if child.get("type") == "chapter":
            new_children.append(next(chapter_iter))
        else:
            new_children.append(child)

    return {**original, "lang": "en", "children": new_children, "_glossary": glossary}
