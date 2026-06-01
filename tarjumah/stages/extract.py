"""Stage 1: PDF → kitab.json. Auto-detects native vs scanned."""

from __future__ import annotations

from pathlib import Path

import fitz  # pymupdf

from .. import claude_runner, markup

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

SCAN_DETECTION_PAGES = 5
SCAN_TEXT_DENSITY_THRESHOLD = 0.5  # chars per cm² — below this, treat as scan


def run(pdf_path: Path, work_dir: Path) -> dict:
    if is_scanned(pdf_path):
        print(f"  → scanned PDF detected; routing through vision OCR", flush=True)
        return extract_scanned(pdf_path, work_dir)
    print(f"  → native PDF detected; routing through text extraction", flush=True)
    return extract_native(pdf_path)


def is_scanned(pdf_path: Path) -> bool:
    doc = fitz.open(pdf_path)
    try:
        pages_to_check = min(SCAN_DETECTION_PAGES, doc.page_count)
        if pages_to_check == 0:
            return True
        total_chars = 0
        total_area_cm2 = 0.0
        for i in range(pages_to_check):
            page = doc[i]
            total_chars += len(page.get_text("text"))
            r = page.rect
            total_area_cm2 += (r.width * r.height) / (28.35 * 28.35)
        if total_area_cm2 == 0:
            return True
        return (total_chars / total_area_cm2) < SCAN_TEXT_DENSITY_THRESHOLD
    finally:
        doc.close()


def extract_native(pdf_path: Path) -> dict:
    doc = fitz.open(pdf_path)
    try:
        pages: list[str] = []
        for i in range(doc.page_count):
            pages.append(f"\n\n=== PAGE {i+1} ===\n\n{doc[i].get_text('text')}")
    finally:
        doc.close()
    source_content = "".join(pages)
    template = (PROMPTS_DIR / "extract_native.md").read_text()
    prompt = template.replace("{source_content}", source_content)
    result = claude_runner.run_claude(
        prompt,
        model=claude_runner.LONG_CONTEXT_MODEL,
        timeout=900,
        expect_json=True,
    )
    if not isinstance(result, dict):
        raise ValueError(f"extract_native expected dict, got {type(result).__name__}")
    markup.validate(result)
    return result


def extract_scanned(pdf_path: Path, work_dir: Path) -> dict:
    images_dir = work_dir / "page-images"
    images_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    image_paths: list[Path] = []
    try:
        for i in range(doc.page_count):
            pix = doc[i].get_pixmap(dpi=200)
            img = images_dir / f"page-{i+1:04d}.png"
            pix.save(str(img))
            image_paths.append(img)
    finally:
        doc.close()

    template = (PROMPTS_DIR / "extract_vision.md").read_text()
    prompts = [
        template
            .replace("{image_path}", str(p.resolve()))
            .replace("{page_num}", str(i + 1))
        for i, p in enumerate(image_paths)
    ]
    page_results = claude_runner.run_claude_parallel(
        prompts,
        model=claude_runner.DEFAULT_MODEL,
        max_workers=4,
        timeout=300,
        expect_json=True,
    )
    return _merge_pages(page_results, pdf_path.stem)


def _merge_pages(pages: list[dict], book_title: str) -> dict:
    all_blocks: list[dict] = []
    for p in pages:
        page_blocks = list(p.get("page_blocks", []))
        if p.get("leading_unfinished") and all_blocks:
            last_para = _find_last_paragraph(all_blocks)
            first_para = _find_first_paragraph(page_blocks)
            if last_para is not None and first_para is not None:
                last_para["content"] = list(last_para.get("content", [])) + list(first_para.get("content", []))
                page_blocks = _without_first_paragraph(page_blocks)
        all_blocks.extend(page_blocks)

    id_remap: dict[str, str] = {}
    counter = [0]

    def renumber(b: dict) -> None:
        if b.get("type") == "footnote" and b.get("id"):
            counter[0] += 1
            new_id = f"fn{counter[0]}"
            id_remap[b["id"]] = new_id
            b["id"] = new_id
        for c in b.get("children", []) or []:
            renumber(c)
    for b in all_blocks:
        renumber(b)

    def rewrite_refs(b: dict) -> None:
        if isinstance(b.get("content"), list):
            for item in b["content"]:
                if isinstance(item, dict) and item.get("type") == "footnote_ref":
                    old = item.get("id")
                    if old in id_remap:
                        item["id"] = id_remap[old]
        for c in b.get("children", []) or []:
            rewrite_refs(c)
    for b in all_blocks:
        rewrite_refs(b)

    return {
        "type": "book",
        "title": book_title,
        "author": None,
        "lang": "ar",
        "children": all_blocks,
    }


def _find_last_paragraph(blocks: list[dict]) -> dict | None:
    for b in reversed(blocks):
        if b.get("type") == "paragraph":
            return b
        if b.get("children"):
            r = _find_last_paragraph(b["children"])
            if r is not None:
                return r
    return None


def _find_first_paragraph(blocks: list[dict]) -> dict | None:
    for b in blocks:
        if b.get("type") == "paragraph":
            return b
        if b.get("children"):
            r = _find_first_paragraph(b["children"])
            if r is not None:
                return r
    return None


def _without_first_paragraph(blocks: list[dict]) -> list[dict]:
    out: list[dict] = []
    removed = False
    for b in blocks:
        if removed:
            out.append(b)
            continue
        if b.get("type") == "paragraph":
            removed = True
            continue
        if b.get("children"):
            new_children = _without_first_paragraph(b["children"])
            if len(new_children) != len(b["children"]):
                removed = True
                out.append({**b, "children": new_children})
                continue
        out.append(b)
    return out
