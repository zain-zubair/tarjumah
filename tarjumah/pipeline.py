"""Top-level orchestrator. Runs all 5 stages, manages intermediates."""

from __future__ import annotations

import json
import time
from pathlib import Path

from . import markup
from .stages import coherence, extract, render, translate, voice

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRANSLATIONS_ROOT = PROJECT_ROOT / "outputs" / "translations"

STAGE_ORDER = ["extract", "voice", "translate", "coherence", "render"]


def run(
    input_pdf: Path,
    output_pdf: Path,
    slug: str,
    source: str = "ar",
    target: str = "en",
    resume_from: str | None = None,
    coherence_mode: str = "conservative",
    dry_run: bool = False,
) -> Path:
    work_dir = TRANSLATIONS_ROOT / slug
    work_dir.mkdir(parents=True, exist_ok=True)

    extracted_path = work_dir / "01-extracted.json"
    voice_path = work_dir / "02-voice.json"
    translated_path = work_dir / "03-translated.json"
    coherent_path = work_dir / "04-coherent.json"

    skip_until = STAGE_ORDER.index(resume_from) if resume_from else 0

    # Stage 1
    if skip_until <= 0:
        print("[1/5] Extracting structure from PDF...", flush=True)
        t = time.time()
        extracted = extract.run(input_pdf, work_dir)
        markup.validate(extracted)
        extracted_path.write_text(markup.to_json(extracted))
        chs = len(markup.chapters(extracted))
        toks = markup.count_tokens(extracted, lang="ar")
        print(f"  ✓ {chs} chapters, ~{toks:,} ar tokens   ({time.time()-t:.1f}s)", flush=True)
    else:
        if not extracted_path.exists():
            raise FileNotFoundError(f"--resume-from requires {extracted_path} to exist")
        extracted = json.loads(extracted_path.read_text())

    if dry_run:
        print("Dry run: stopping after Stage 1.")
        return extracted_path

    # Stage 2
    if skip_until <= 1:
        print("[2/5] Locking voice & glossary...", flush=True)
        t = time.time()
        v = voice.run(extracted)
        voice_path.write_text(json.dumps(v, ensure_ascii=False, indent=2))
        print(f"  ✓ glossary: {len(v.get('glossary', {}))} terms   ({time.time()-t:.1f}s)", flush=True)
    else:
        if not voice_path.exists():
            raise FileNotFoundError(f"--resume-from requires {voice_path} to exist")
        v = json.loads(voice_path.read_text())

    # Stage 3
    if skip_until <= 2:
        print("[3/5] Translating chunks (parallel by chapter)...", flush=True)
        t = time.time()
        translated = translate.run(extracted, v)
        markup.validate(translated)
        translated_path.write_text(markup.to_json(translated))
        print(f"  ✓ ({time.time()-t:.1f}s)", flush=True)
    else:
        if not translated_path.exists():
            raise FileNotFoundError(f"--resume-from requires {translated_path} to exist")
        translated = json.loads(translated_path.read_text())

    # Stage 4
    if skip_until <= 3:
        print(f"[4/5] Coherence pass ({coherence_mode})...", flush=True)
        t = time.time()
        coherent = coherence.run(translated, v, mode=coherence_mode)
        markup.validate(coherent)
        coherent_path.write_text(markup.to_json(coherent))
        print(f"  ✓ ({time.time()-t:.1f}s)", flush=True)
    else:
        if not coherent_path.exists():
            raise FileNotFoundError(f"--resume-from requires {coherent_path} to exist")
        coherent = json.loads(coherent_path.read_text())

    # Stage 5
    print("[5/5] Rendering PDF...", flush=True)
    t = time.time()
    pdf_path = render.run(coherent, work_dir, output_pdf)
    print(f"  ✓ {output_pdf}   ({time.time()-t:.1f}s)", flush=True)
    return pdf_path
