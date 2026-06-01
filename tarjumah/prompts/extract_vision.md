You are reading a single page of a scanned Arabic kitab. The image is at the path below. Read it carefully (full classical Arabic OCR, including diacritics where present), then identify structure and emit a partial kitab.json for THIS page only. We will merge across pages later.

# Image path

{image_path}

# Output schema (partial — just blocks for this page)

Return JSON of shape:

```
{
  "page_blocks": [Block, ...],
  "trailing_unfinished": bool,
  "leading_unfinished": bool
}
```

Where Block types:
- `{"type": "chapter", "title": str, "children": [...]}` — only if a chapter clearly starts on this page
- `{"type": "section", "heading": str, "children": [...]}`
- `{"type": "subsection", "heading": str, "children": [...]}`
- `{"type": "paragraph", "content": [str | inline, ...]}`
- `{"type": "footnote", "id": "page-{page_num}-fn{n}", "content": [...]}` — IDs scoped to this page; the merger renumbers globally
- `{"type": "quotation", "content": [...], "attribution": str | null}`

Inline items:
- plain string
- `{"type": "quran", "ref": str | null, "text": str}`
- `{"type": "hadith", "source": str | null, "text": str}`
- `{"type": "scholar", "name": str, "rendered": null}`
- `{"type": "work", "author": str, "title": str}`
- `{"type": "footnote_ref", "id": str}` — refer to local footnote id

# Rules

1. **OCR accurately.** Preserve diacritics where they exist. Do not translate. Output is in Arabic.
2. **Detect footnotes** — usually smaller font at the bottom of the page, often separated by a horizontal rule. Insert `footnote_ref` inline where the marker appeared in the main text.
3. **Stitch hint flags:**
   - `trailing_unfinished: true` if the last paragraph on this page does NOT end in terminal punctuation (`.`, `؟`, `!`, `:`, `۔`)
   - `leading_unfinished: true` if the first paragraph appears mid-thought (no capital, no clear sentence start)
4. **Do not invent content** that isn't on the page. If you can't read a word, write `[…]` and continue.
5. **Page number context:** this is page {page_num}.

# Output

Return STRICT JSON only — begin with `{`. No prose, no code fences.
