You are extracting structure from an Arabic book. Below is the raw text content extracted from a native PDF (with optional positional/font hints). Your task: produce a kitab.json document.

# kitab.json schema (concise)

Root: `{"type": "book", "title": str, "author": str | null, "lang": "ar", "children": [Block...]}`

Block types:
- `{"type": "chapter", "title": str, "children": [Section | Paragraph | Footnote | Quotation, ...]}`
- `{"type": "section", "heading": str, "children": [...]}`
- `{"type": "subsection", "heading": str, "children": [...]}`
- `{"type": "paragraph", "content": [str | inline, ...]}`
- `{"type": "footnote", "id": "fn1", "content": [str | inline, ...]}`
- `{"type": "quotation", "content": [...], "attribution": str | null}`

Inline items inside `content` arrays:
- plain string
- `{"type": "quran", "ref": "2:255", "text": "<the Arabic verse>"}`
- `{"type": "hadith", "source": "<short attribution>", "text": "<Arabic>"}`
- `{"type": "scholar", "name": "<Arabic name>", "rendered": null}`
- `{"type": "work", "author": "<Arabic>", "title": "<Arabic>"}`
- `{"type": "footnote_ref", "id": "fn1"}`

# Rules

1. **Detect chapters and sections** from font-size jumps, leading whitespace, and conventional Arabic structure markers (الباب، الفصل، المقدمة، الخاتمة، etc.).
2. **Detect footnotes** — typically smaller font near the page bottom, often separated by a horizontal rule. Number them globally as `fn1`, `fn2`, ... across the WHOLE book (not per page). Insert `{"type": "footnote_ref", "id": "fnN"}` at the position in the main text where the marker appeared (often a superscript number or `(N)`).
3. **Stitch sentences across page breaks.** If the last paragraph on one page does not end in `.`, `؟`, `!`, `:`, `۔`, then merge it with the first paragraph on the next page.
4. **Identify Quran citations** — when you see وَقَالَ تَعَالَى, قَوْلُهُ تَعَالَى, etc. followed by a Quranic verse, wrap as a `quran` inline. If the surah/ayah ref isn't given but you can identify it confidently from the text, include `ref`. If unsure, use `"ref": null`.
5. **Identify hadith citations** — when introduced by رَوَى، أَخْرَجَ، عَنِ النَّبِيِّ ﷺ, etc., wrap as `hadith` with `source` if given (e.g., "البخاري", "مسلم").
6. **Preserve all Arabic text exactly** — including diacritics. Do not translate. Do not paraphrase. Do not omit. The output `content` strings are Arabic.
7. **Keep paragraph breaks meaningful** — don't merge unrelated paragraphs, don't split a single thought.

# Output

Return STRICT JSON only — no prose, no code fences. Begin with `{`. The root object MUST be the book.

# Source content

```
{source_content}
```
