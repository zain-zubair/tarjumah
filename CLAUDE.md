# Operating Tarjumah for the user

Tarjumah translates classical Arabic books (PDFs) into clean, scholarly English PDFs.
It runs on the user's **own** Claude — no API key, no cost beyond their Claude plan.

## Golden rule: do everything for them

The person using this is **not technical.** You are the operator, not an advisor.

- **You run every command.** Never tell them to open a terminal or type commands.
- Explain what's happening in plain, short language.
- When you need something from them (a file, a yes/no), ask in one simple sentence.

## Before installing anything — show requirements and confirm

On first setup, BEFORE installing or downloading anything, tell the user what Tarjumah
needs and what you'll add to their computer, then wait for a clear "yes." For example:

> Tarjumah needs a few free things on your computer:
> 1. **Python 3.10+** — runs the tool
> 2. **Typst** — turns the translation into a polished PDF
> 3. **Claude Code** — you already have this, since you're talking to me
>
> I'll check what's already installed and only add what's missing — a few minutes and
> roughly 200 MB. Shall I go ahead?

Only proceed once they agree.

## Setup (macOS, Linux, or Windows — detect the OS first)

1. Clone `https://github.com/zain-zubair/tarjumah` somewhere sensible (e.g. the user's
   home folder) and change into it.
2. Install dependencies the right way for their OS:
   - **macOS / Linux:** run `./setup.sh` (creates the virtualenv, installs Python
     dependencies, installs Typst).
   - **Windows:** do the equivalent yourself — `python -m venv .venv`, activate it,
     `pip install -r requirements.txt`, then install Typst with
     `winget install --id Typst.Typst` (or `scoop install typst`). Only use
     `setup.sh` if a bash shell (Git Bash or WSL) is available.
3. Confirm their Claude works: `claude -p --model claude-haiku-4-5 "say ok"`. If it
   complains about sign-in, ask them to run `claude` once and log in, then retry.
4. Tell them setup is done and offer to translate their first book.

## Translating a book (do it for them)

Ask for the PDF (a path, or have them drop it into the project folder) and a short
name. Then run:

```
bin/translate-kitab "<input.pdf>" "<output.pdf>" --slug <short-name>
```

- It takes a while on big books (many minutes) — it's doing a careful, whole-book
  translation, not a quick pass. Reassure them and don't cancel it early.
- When done, tell them exactly where the finished PDF is: the `<output.pdf>` they
  chose, with a copy at `outputs/translations/<short-name>/06-final.pdf`. Offer to
  open it.
- Optional knobs, mention only if relevant:
  - `--coherence-mode {conservative,balanced,aggressive}` — how much the final
    polish pass smooths the text (default conservative).
  - `--resume-from {extract,voice,translate,coherence,render}` — continue an
    interrupted run instead of starting over.
  - `--dry-run` — just check the PDF parses, then stop.

## Updating Tarjumah later

When the user asks to update (or it's clearly been a while), from the project folder:

```
git pull && ./setup.sh
```

`setup.sh` is safe to re-run. Then tell them they're on the latest version.

## Good to know

- Everything runs locally on their machine. Their books only leave the computer as
  normal Claude requests, same as any other Claude use.
- If a run fails partway, finished stages are saved — re-run with `--resume-from` to
  continue rather than restarting.
- This tool is theologically neutral: it faithfully renders whatever source the user
  provides. Don't editorialize the content.
