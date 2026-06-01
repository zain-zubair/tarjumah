"""Semantic chunking. Boundaries at chapter > section > subsection > paragraph.
Never split mid-paragraph. Target 3000 source tokens, hard max 4500."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import markup

TARGET_TOKENS = 1500
MAX_TOKENS = 2500


@dataclass
class Chunk:
    idx: int = 0
    chapter_idx: int = 0
    chunk_idx_in_chapter: int = 0
    chunks_in_chapter: int = 0
    blocks: list[dict] = field(default_factory=list)


def chunk_book(doc: dict) -> list[Chunk]:
    chapters_list = markup.chapters(doc)
    if not chapters_list:
        chapters_list = [{"type": "chapter", "title": "", "children": doc.get("children", [])}]

    out: list[Chunk] = []
    global_idx = 0
    for ch_i, ch in enumerate(chapters_list):
        ch_chunks = _chunk_chapter(ch)
        total = len(ch_chunks)
        for c_i, c in enumerate(ch_chunks):
            c.idx = global_idx
            c.chapter_idx = ch_i
            c.chunk_idx_in_chapter = c_i
            c.chunks_in_chapter = total
            out.append(c)
            global_idx += 1
    return out


def _chunk_chapter(chapter: dict) -> list[Chunk]:
    chunks: list[Chunk] = []
    current: list[dict] = []
    current_tokens = 0
    for block in chapter.get("children", []):
        block_tokens = markup.count_tokens(block, lang="ar")
        if block_tokens > MAX_TOKENS:
            if current:
                chunks.append(Chunk(blocks=current))
                current = []
                current_tokens = 0
            chunks.append(Chunk(blocks=[block]))
            continue
        if current_tokens + block_tokens > MAX_TOKENS and current:
            chunks.append(Chunk(blocks=current))
            current = []
            current_tokens = 0
        current.append(block)
        current_tokens += block_tokens
        if current_tokens >= TARGET_TOKENS and _is_safe_boundary(block):
            chunks.append(Chunk(blocks=current))
            current = []
            current_tokens = 0
    if current:
        chunks.append(Chunk(blocks=current))
    return chunks


def _is_safe_boundary(block: dict) -> bool:
    return block.get("type") in ("section", "subsection", "paragraph", "quotation")
