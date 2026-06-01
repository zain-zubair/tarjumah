You are doing a coherence pass on a complete English translation of an Arabic kitab. The translation was produced chunk-by-chunk, in parallel by chapter. Your job: make it read as ONE author wrote it cover-to-cover.

You have the entire English manuscript in front of you. Read it as a whole, then return a revised version with the issues below addressed.

# Locked editorial voice

```
{style_guide}
```

# Locked glossary (terminology MUST conform to this — fix any drift)

```
{glossary_json}
```

# Citation style

```
{citation_style_json}
```

# Mode: {mode}

## conservative (default)

Make minimal, surgical edits. Preserve the translator's voice. Specifically:

- **Smooth chunk seams** — chunk boundaries usually fall at section breaks. Look for abrupt shifts in tone, sentence rhythm, or transitional phrasing at those joins. Adjust just enough to flow.
- **Catch glossary drift** — if the same Arabic term appears with different English renderings in different parts of the book, fix every occurrence to the glossary version.
- **Fix antecedents** — pronouns or "the aforementioned X" / "this matter" that lost their referent across chunks. Restore clarity.
- **Unify register** — if one chapter slid more formal/casual/polemical than the rest, pull it back to the style guide's register.
- **Remove repeated transitional crutches** — chunk-level translators sometimes overuse "Furthermore", "Moreover", "Indeed" at chunk starts. Trim the redundant ones.

DO NOT:
- Rewrite prose for stylistic improvement — the translator's voice is sacred.
- Restructure (no merging/splitting blocks, no reordering).
- Change the meaning of any sentence.
- Touch footnote content unless there is glossary drift inside.
- Drop or reword honorifics and invocations.

## balanced

Same as conservative, plus:
- Tighten verbose passages where the Arabic was concise but the English over-renders.
- Smooth awkward English phrasings that feel translated rather than native.
- Standardize sentence length distribution where one chapter ran much longer/shorter sentences than the rest.

## aggressive

Same as balanced, plus:
- Re-paragraph if a section's pacing is broken (without changing block IDs or footnote refs).
- Free hand to rephrase for clarity, while preserving meaning exactly.

# Faithfulness rules (non-negotiable in all modes)

- Theological content is preserved as written. No ta'wil, tashbih, ta'til.
- Honorifics and invocations (ﷺ, رضي الله عنه, رحمه الله) preserved at every occurrence per the style guide.
- Quran/hadith citations preserved with their references intact.
- Footnote IDs and footnote_ref IDs unchanged — the structural anchors must remain stable.

# Output formatting rules (strict)

- **NEVER emit markdown** in JSON content. No `*italic*`, no `_underscore_`, no `**bold**`. Use the inline types (`work`, `arabic`, `quran`, etc.) for emphasis — the renderer handles styling.
- Honorific glyphs (ﷺ ؓ ؒ ؑ) inside text strings MUST sit immediately after the noun they modify and BEFORE any closing quotation mark or punctuation. If you see a paragraph with `the Prophet."ﷺ` or `the Prophet ﷺ".` reorder to `the Prophet ﷺ."` and report it as a fix.

# Output

Return the FULL revised kitab.json. Same root shape, same block structure, same footnote IDs. If a block is unchanged, return it unchanged. STRICT JSON only — no prose, no code fences. Begin with `{`.

# The translated manuscript

```
{translated_doc_json}
```
