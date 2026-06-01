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

## Get started — no terminal needed

Tarjumah is run *by* Claude. You don't type commands — you talk to Claude and it does the work for you.

**Step 1 — Get Claude Code.** The one thing you install yourself; it works on macOS, Windows, and Linux → https://claude.com/claude-code

**Step 2 — Paste this to Claude.** It tells you what it needs, installs only what's missing (after you say yes), then translates books for you:

```text
I'd like to use "Tarjumah" — an open-source tool that translates classical Arabic
books (PDFs) into clean English PDFs. It runs on you (my own Claude), so there's no
API key and no cost beyond my Claude plan.

Please set it up and run it FOR me — I don't want to use the terminal myself:

1. First, before installing anything, tell me in plain words what Tarjumah needs on
   my computer and what you'll install, then wait for me to say yes.
2. Detect my operating system and install the right way for it.
3. Clone https://github.com/zain-zubair/tarjumah, then open its CLAUDE.md and follow
   those instructions exactly.
4. When it's ready, just ask me for a PDF and translate it for me — you run every
   command; I'll only hand you files and say yes or no.

Keep everything simple and do the work yourself.
```

Claude handles the rest: it clones Tarjumah, checks what's already on your computer, installs only the missing pieces (with your OK), and then waits for you to hand it a PDF.

## Using it — just ask

Once it's set up you never touch the terminal. Tell Claude things like:

- *"Translate this book for me."* — then give it the PDF.
- *"Make the translation more polished."* — it raises the coherence pass.
- *"Continue the one that got interrupted."* — it resumes where it stopped.

When it finishes, Claude tells you where your English PDF is — by default `outputs/translations/<name>/06-final.pdf`, plus anywhere you asked it to save a copy.

## Getting updates

Tarjumah improves over time. To get the latest, just tell Claude:

> *"Update Tarjumah to the latest version."*

It pulls the newest code and re-runs setup (safe to repeat), so you stay current with one sentence.

## Advanced — run it yourself

Prefer the terminal? Set up manually:

```bash
git clone https://github.com/zain-zubair/tarjumah.git
cd tarjumah
./setup.sh                                     # venv + dependencies + Typst (safe to re-run)
claude -p --model claude-haiku-4-5 "say ok"    # confirm your own Claude is signed in
```

Then translate a book directly:

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
