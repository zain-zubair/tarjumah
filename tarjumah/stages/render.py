"""Stage 5: kitab.json → Typst → PDF."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from .. import markup

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "kitab.typ"

# Specific Islamic honorific glyphs — NOT all Arabic chars. Stripping arbitrary
# trailing Arabic was wrong: it truncated fully-Arabic chapter titles whose
# names contained internal punctuation (e.g., "أ.د فالح بن إسماعيل مندكار").
_HONORIFIC_GLYPHS = r"ؑ-ؕﷺﷻ"  # ؑ ؒ ؓ ؔ ؕ ﷺ ﷻ
_TRAILING_HONORIFIC = re.compile(rf"\s*([{_HONORIFIC_GLYPHS}]+)\s*$")
_HAS_LTR = re.compile(r"[A-Za-z]")
_ARABIC_FONT_LIST = '("Geeza Pro", "Amiri", "Noto Naskh Arabic")'

# Defensive normalizers applied to every string before escape:
# - LRM injection after honorific glyphs fixes bidi-induced punctuation scrambling
# - Honorific glyphs themselves are wrapped in explicit Arabic-font Typst text
#   blocks at scaled size, so they read clearly in body prose (Geeza Pro renders
#   them small by default, which makes them nearly invisible at 11pt body size)
# - Markdown italic detection converts `*X*` leaks to proper Typst #emph[X]
_HONORIFIC_BIDI_FIX = re.compile(rf"([{_HONORIFIC_GLYPHS}])(?!‎)")
_HONORIFIC_GLYPH_RE = re.compile(rf"[{_HONORIFIC_GLYPHS}]")
_MD_ITALIC = re.compile(r"(?<!\*)\*(?!\s)([^*\n]+?)(?<!\s)\*(?!\*)")
_HONORIFIC_SCALE = "1.3em"


def run(coherent: dict, work_dir: Path, output_pdf: Path) -> Path:
    typ_path = work_dir / "05-render.typ"
    typ_path.write_text(build_typst(coherent))

    pdf_path = work_dir / "06-final.pdf"
    if not shutil.which("typst"):
        raise RuntimeError(
            "`typst` not found on PATH. Install with: brew install typst (macOS) or cargo install typst-cli."
        )
    r = subprocess.run(
        ["typst", "compile", str(typ_path), str(pdf_path)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"Typst compile failed:\n{r.stderr.strip()}\n\nSource: {typ_path}")

    if output_pdf and output_pdf.resolve() != pdf_path.resolve():
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(pdf_path, output_pdf)
    return pdf_path


def build_typst(doc: dict) -> str:
    template = TEMPLATE_PATH.read_text()
    fn_map = _collect_footnotes(doc)
    title = doc.get("title") or "Untitled"
    author = doc.get("author") or "Unknown"
    body = _render_blocks(doc.get("children", []), fn_map)
    return (template
        .replace("{{TITLE}}", _escape(title))
        .replace("{{AUTHOR}}", _escape(author))
        .replace("{{BODY}}", body)
    )


def _collect_footnotes(doc: dict) -> dict[str, list]:
    fn_map: dict[str, list] = {}
    def visit(b: dict) -> None:
        if b.get("type") == "footnote" and b.get("id"):
            fn_map[b["id"]] = b.get("content", [])
    markup.walk(doc, visit)
    return fn_map


def _render_blocks(blocks: list[dict], fn_map: dict[str, list]) -> str:
    return "\n\n".join(s for s in (_render_block(b, fn_map) for b in blocks) if s)


def _render_block(b: dict, fn_map: dict[str, list]) -> str:
    t = b.get("type")
    if t == "chapter":
        return f"= {_render_heading(b.get('title') or '')}\n\n{_render_blocks(b.get('children', []), fn_map)}"
    if t == "section":
        return f"== {_render_heading(b.get('heading') or '')}\n\n{_render_blocks(b.get('children', []), fn_map)}"
    if t == "subsection":
        return f"=== {_render_heading(b.get('heading') or '')}\n\n{_render_blocks(b.get('children', []), fn_map)}"
    if t == "paragraph":
        return _render_inline(b.get("content", []), fn_map)
    if t == "footnote":
        return ""  # rendered inline at footnote_ref site
    if t == "quotation":
        body = _render_inline(b.get("content", []), fn_map)
        attribution = b.get("attribution")
        attr = f"\n\n#align(right)[— {_escape(attribution)}]" if attribution else ""
        return f"#block(inset: (left: 1.5em, right: 1.5em), [_{body}_{attr}])"
    return ""


def _render_text(s: str) -> str:
    """Render a plain text string as Typst content with defensive normalization."""
    s = _HONORIFIC_BIDI_FIX.sub("\\1‎", s)
    parts: list[str] = []
    last = 0
    for m in _HONORIFIC_GLYPH_RE.finditer(s):
        if m.start() > last:
            parts.append(_render_md_italic(s[last:m.start()]))
        parts.append(
            f"#text(font: {_ARABIC_FONT_LIST}, size: {_HONORIFIC_SCALE})[{m.group(0)}]"
        )
        last = m.end()
    if last < len(s):
        parts.append(_render_md_italic(s[last:]))
    return "".join(parts)


def _render_md_italic(s: str) -> str:
    parts: list[str] = []
    last = 0
    for m in _MD_ITALIC.finditer(s):
        if m.start() > last:
            parts.append(_escape(s[last:m.start()]))
        parts.append(f"#emph[{_escape(m.group(1))}]")
        last = m.end()
    if last < len(s):
        parts.append(_escape(s[last:]))
    return "".join(parts)


def _render_inline(items: list, fn_map: dict[str, list]) -> str:
    parts: list[str] = []
    for it in items:
        if isinstance(it, str):
            parts.append(_render_text(it))
        elif isinstance(it, dict):
            t = it.get("type")
            if t == "quran":
                ref = it.get("ref") or ""
                text = it.get("text") or ""
                parts.append(f"_{_escape(text)}_ #h(0.3em) (Q. {_escape(ref)})" if ref else f"_{_escape(text)}_")
            elif t == "hadith":
                source = it.get("source") or ""
                text = it.get("text") or ""
                parts.append(f"_{_escape(text)}_ #h(0.3em) ({_escape(source)})" if source else f"_{_escape(text)}_")
            elif t == "scholar":
                rendered = it.get("rendered") or it.get("name") or ""
                parts.append(_escape(rendered))
            elif t == "work":
                title = it.get("title") or ""
                parts.append(f"_{_escape(title)}_")
            elif t == "footnote_ref":
                fn_id = it.get("id") or ""
                content = fn_map.get(fn_id, [])
                inner = _render_inline(content, fn_map) if content else ""
                if inner:
                    parts.append(f"#footnote[{inner}]")
            elif t == "arabic":
                text = it.get("text") or ""
                parts.append(f'#text(font: ("Amiri", "Noto Naskh Arabic"), lang: "ar")[{_escape(text)}]')
    return "".join(parts)


def _render_heading(h: str) -> str:
    # Only strip a trailing honorific (e.g., ﷺ) when the heading is a
    # mixed-script title (LTR text + trailing honorific glyph). Stripping is
    # required to avoid Typst's outline misplacing page numbers in bidi runs.
    # Fully-Arabic headings render as-is — Typst handles RTL outline entries
    # correctly, and the body font fallback chain renders honorific glyphs.
    if _HAS_LTR.search(h) and _TRAILING_HONORIFIC.search(h):
        m = _TRAILING_HONORIFIC.search(h)
        return _escape(h[:m.start()].rstrip())
    return _escape(h)


def _escape(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return (s
        .replace("\\", "\\\\")
        .replace("#", "\\#")
        .replace("@", "\\@")
        .replace("`", "\\`")
        .replace("$", "\\$")
        .replace("*", "\\*")
        .replace("_", "\\_")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("<", "\\<")
        .replace(">", "\\>")
    )
