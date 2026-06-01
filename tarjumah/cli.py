"""tarjumah CLI — `translate-kitab input.pdf output.pdf`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import pipeline


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="translate-kitab",
        description="Translate an Arabic kitab (PDF) to English (PDF) — one continuous voice.",
    )
    p.add_argument("input_pdf", type=Path, help="path to input PDF")
    p.add_argument("output_pdf", type=Path, help="path to output PDF")
    p.add_argument("--slug", default=None, help="output dir name under outputs/translations/ (defaults to input PDF basename)")
    p.add_argument("--source", default="ar", help="source language (default: ar)")
    p.add_argument("--target", default="en", help="target language (default: en)")
    p.add_argument("--resume-from", choices=pipeline.STAGE_ORDER, default=None,
                   help="skip earlier stages, reuse persisted intermediates")
    p.add_argument("--coherence-mode", choices=["conservative", "balanced", "aggressive"],
                   default="conservative", help="how invasive Stage 4 is")
    p.add_argument("--dry-run", action="store_true", help="run Stage 1 only and stop")
    args = p.parse_args(argv)

    slug = args.slug or args.input_pdf.stem
    if not args.input_pdf.exists():
        print(f"Input PDF not found: {args.input_pdf}", file=sys.stderr)
        return 2

    try:
        pipeline.run(
            input_pdf=args.input_pdf,
            output_pdf=args.output_pdf,
            slug=slug,
            source=args.source,
            target=args.target,
            resume_from=args.resume_from,
            coherence_mode=args.coherence_mode,
            dry_run=args.dry_run,
        )
    except KeyboardInterrupt:
        print("\n^C interrupted.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"\n✗ Pipeline failed: {e}", file=sys.stderr)
        print(f"  Inspect intermediates at: outputs/translations/{slug}/", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
