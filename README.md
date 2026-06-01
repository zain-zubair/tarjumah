# Tarjumah (تَرْجَمَة)

A pipeline that ingests an Arabic kitab (PDF) and emits a clean English PDF that reads as one continuous voice.

> Built upon the manhaj of Ahl as-Sunnah wal-Jama'ah, in service of those who study the works of the salaf as-salih and those upon their path. The engine is theologically neutral — it transmits faithfully what the source author wrote. The user picks the source.

## Why this exists

Generic translation tools (DeepL, Google) butcher classical Arabic. They lose footnote anchors, drift in terminology, render the same term three different ways across the same book, and produce page-by-page output that reads disjointed. Translated kitabs published in English are slow, expensive, and many works remain inaccessible.

Tarjumah is a five-stage pipeline that holds the entire book in mind at once: it locks an editorial voice and glossary up front, translates in semantic chunks (never page-by-page) with continuity context, then runs a whole-manuscript coherence pass that smooths transitions, catches glossary drift, and unifies register. The output is a scholarly PDF in clean English with footnotes preserved.

## How it works (5 stages)

1. **Extract** — PDF → structured JSON (`kitab.json`). Auto-detects native vs scanned PDFs. Pages are discarded after this stage; everything downstream works in chapters / sections / paragraphs / footnotes.
2. **Voice & Glossary** — single Opus 1M call reads the whole book, produces a style guide, locked glossary, citation conventions, and translator persona that drive every translation chunk.
3. **Translate** — chunks of 2–4k tokens (semantic boundaries, never mid-paragraph) translated in parallel by chapter, sequential within. Each chunk receives the previous chunk's English (sliding ~1500 tok window) and a preview of what comes next, so voice carries.
4. **Coherence** — entire English manuscript through Opus 1M in one shot. Smooths chunk seams, catches glossary drift, fixes pronoun antecedents that broke across chunks, unifies register. Conservative by default (preserves the translator's voice; doesn't rewrite).
5. **Render** — `kitab.json` → Typst → PDF. Auto-numbered footnotes, auto-built ToC, scholarly typography. Inline Arabic quotations preserved.

All model calls run via `claude -p` (subscription-absorbed), not the API.

## Setup

```bash
git clone https://github.com/zain-zubair/tarjumah.git
cd tarjumah
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
brew install typst   # or: cargo install typst-cli
```

You also need the `claude` CLI on PATH and authenticated (subscription auth — OAuth or keychain). Verify:

```bash
claude -p --model claude-haiku-4-5 "say ok"
```

## Usage

```bash
bin/translate-kitab path/to/kitab.pdf path/to/output.pdf --slug my-book
```

### Flags

- `--slug <name>` — output directory name under `outputs/translations/`. Defaults to input PDF basename.
- `--source ar` / `--target en` — language pair. Defaults Arabic → English.
- `--resume-from {extract,voice,translate,coherence,render}` — skip earlier stages, reuse persisted intermediates. Critical for prompt iteration.
- `--coherence-mode {conservative,balanced,aggressive}` — how invasive the Stage 4 pass is. Defaults to conservative.
- `--dry-run` — run Stage 1 only, print structure summary.

### Intermediates

For `--slug my-book`, intermediates live at:

```
outputs/translations/my-book/
├── 01-extracted.json
├── 02-voice.json
├── 03-translated.json
├── 04-coherent.json
├── 05-render.typ
└── 06-final.pdf
```

Per-call observability lands in `data/runs.jsonl` (timestamps, models, durations, char counts).

## Pipeline at a glance

```
input.pdf
   │
   ▼
[1] extract.py ─────► 01-extracted.json   (kitab.json — Arabic, structured)
   │
   ▼
[2] voice.py ───────► 02-voice.json       (style guide + glossary + persona)
   │
   ▼
[3] translate.py ───► 03-translated.json  (kitab.json — English, chunked)
   │
   ▼
[4] coherence.py ───► 04-coherent.json    (kitab.json — English, unified)
   │
   ▼
[5] render.py ──────► 05-render.typ ──► 06-final.pdf
```

## Notes

- The pipeline is language-pair-agnostic. Arabic → English is the wedge; Urdu, Persian, Turkish, etc. are one prompt change away.
- The translator persona prompt is locked per-book in Stage 2 — re-running Stage 2 produces a fresh persona that flows through every chunk. Fine to iterate.
- Conservative coherence mode is the right default. Balanced/aggressive variants are tunable knobs for after the first book reads well.

— wa billahi at-tawfiq.
