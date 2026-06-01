#!/usr/bin/env bash
# Tarjumah one-shot setup. Safe to re-run.
set -euo pipefail

say()  { printf '\033[1;32m▸ %s\033[0m\n' "$1"; }
warn() { printf '\033[1;33m! %s\033[0m\n' "$1"; }
err()  { printf '\033[1;31m✗ %s\033[0m\n' "$1"; }

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# 1. Python 3.10+
if ! command -v python3 >/dev/null 2>&1; then
  err "python3 not found. Install Python 3.10+ first: https://www.python.org/downloads/"
  exit 1
fi
say "Python: $(python3 --version)"

# 2. Virtualenv + dependencies
if [ ! -d .venv ]; then
  say "Creating virtual environment (.venv)…"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
say "Installing Python dependencies…"
python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet -r requirements.txt
say "Dependencies installed."

# 3. Typst (renders the final PDF)
if command -v typst >/dev/null 2>&1; then
  say "Typst: $(typst --version)"
else
  warn "Typst not found — it renders the final PDF."
  if command -v brew >/dev/null 2>&1; then
    say "Installing Typst via Homebrew…"
    brew install typst
  elif command -v cargo >/dev/null 2>&1; then
    say "Installing Typst via cargo…"
    cargo install typst-cli
  else
    warn "Install Typst manually, then re-run: https://github.com/typst/typst#installation"
  fi
fi

# 4. Claude CLI — you bring your own Claude (no API key)
if command -v claude >/dev/null 2>&1; then
  say "Claude CLI found: $(command -v claude)"
  warn "Make sure you're signed in — run 'claude' once to log in if you haven't."
else
  warn "The 'claude' CLI is not on your PATH."
  warn "Tarjumah runs on YOUR Claude. Install Claude Code, sign in, then re-run:"
  warn "  https://claude.com/claude-code"
fi

chmod +x bin/translate-kitab 2>/dev/null || true

cat <<'USAGE'

────────────────────────────────────────────────────────
✓ Tarjumah is ready.

Translate a book:
  bin/translate-kitab path/to/kitab.pdf path/to/output.pdf --slug my-book

Handy flags:
  --coherence-mode {conservative,balanced,aggressive}
  --resume-from {extract,voice,translate,coherence,render}
  --dry-run     (parse the PDF and stop after stage 1)

Your finished PDF and all intermediates land in:
  outputs/translations/<slug>/
────────────────────────────────────────────────────────
USAGE
