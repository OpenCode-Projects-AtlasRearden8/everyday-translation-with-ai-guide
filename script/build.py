#!/usr/bin/env python3
"""Build the static HTML site from the Markdown manual in docs/.

Local-first: pure Python standard library, no network access, no
dependencies. Run from the project root:

    python3 script/build.py            # build into site/
    python3 script/build.py --out html # build elsewhere if you like

Every built page needs no JavaScript and works offline.
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
from pathlib import Path
from typing import Callable, List, Optional

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SITE_TITLE = "AI Translation for Everyday Life"
SITE_SUBTITLE = "A manual for multilingual households"
TOC_LEAD = "Contents"
GOLDEN_RULE = (
    "<strong>Golden rule:</strong> AI drafts, you verify, and humans decide "
    "anything signed, medical, or court-related."
)
FOOTER = (
    "Part of the Asdale Dynamics beginner AI manual series &middot; "
    "Copyright (c) 2026 Asdale Dynamics, LLC &middot; MIT License &middot; "
    "Education only; never a substitute for a human professional&rsquo;s advice."
)


def esc(text: str) -> str:
    return html.escape(text, quote=True)


# --------------------------------------------------------------------------
# Tiny Markdown subset renderer: headings, ordered/unordered lists (including
# checkbox items), blockquotes, tables, bold, italics, inline code, links,
# horizontal rules. Honest about being small and purpose-built.
# --------------------------------------------------------------------------

def _inline(text: str) -> str:
    out: List[str] = []
    # Process with a single left-to-right scanner so nesting is predictable:
    # `code`, then [links], **bold**, *italic*.
    pos = 0
    patterns = (
        ("code", re.compile(r"`([^`]+)`")),
        ("link", re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")),
        ("bold", re.compile(r"\*\*((?:[^*\n]|\*(?!\*))+)\*\*")),
        ("italic", re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")),
    )

    def next_match(start: int):
        best = None
        for kind, pat in patterns:
            m = pat.search(text, start)
            if m and (best is None or m.start() < best[0].start()):
                best = (m, kind)
        return best

    while pos < len(text):
        hit = next_match(pos)
        if hit is None:
            out.append(esc(text[pos:]))
            break
        m, kind = hit
        out.append(esc(text[pos:m.start()]))
        if kind == "code":
            out.append(f"<code>{esc(m.group(1))}</code>")
        elif kind == "link":
            out.append(f'<a href="{esc(m.group(2))}">{esc(m.group(1))}</a>')
        elif kind == "bold":
            out.append(f"<strong>{_inline(m.group(1))}</strong>")
        else:
            out.append(f"<em>{_inline(m.group(1))}</em>")
        pos = m.end()
    return "".join(out)


CHECK_BOX = {" ": "\u2610", "x": "\u2611", "X": "\u2611"}

# Lines that *start* a structural block. Anything else after a non-blank line
# is a soft-wrapped continuation of it.
STARTER = re.compile(
    r"^\s*(?:[-*]\s+|\d+[.)]\s+|>\s?|#{1,6}\s+|\||-{3,}\s*$)"
)


def unwrap(md: str) -> str:
    """Join soft-wrapped lines into single structural units.

    A line that starts a new block (list item, heading, quote, table, rule)
    always opens a fresh line. Otherwise:
      - a plain line after a blockquote paragraph starts a new paragraph,
      - a plain wrapped line after any other block (list item, paragraph)
        continues that block,
      - a ">"-prefixed line after a ">"-prefixed line extends the quote.
    """
    out: List[str] = []
    heading_or_rule = re.compile(r"^\s*(#{1,6}\s+|-{3,}\s*$)")
    for line in md.splitlines():
        if not line.strip():
            out.append(line)
            continue
        prev = out[-1] if out else ""
        is_starter = bool(STARTER.match(line))
        prev_is_quote = prev.lstrip().startswith(">")

        if not prev or prev == "" or not prev.strip():
            out.append(line)
        elif prev_is_quote and line.lstrip().startswith(">"):
            # Consecutive quote lines extend one quotation.
            out[-1] = prev.rstrip() + " " + line.lstrip("> ").strip()
        elif is_starter:
            out.append(line)
        elif prev_is_quote:
            out.append(line)
        elif heading_or_rule.match(prev):
            out.append(line)
        else:
            out[-1] = prev.rstrip() + " " + line.strip()
    return "\n".join(out)


def md_to_html(md: str) -> str:
    out: List[str] = []
    list_tag: Optional[str] = None  # "ul" | "ol" while inside one
    in_quote = False
    quote_list: bool = False
    in_table = False

    def close_list() -> None:
        nonlocal list_tag
        if list_tag:
            out.append(f"</{list_tag}>")
            list_tag = None

    def close_quote() -> None:
        nonlocal in_quote, quote_list
        if quote_list:
            out.append("</ul>")
            quote_list = False
        if in_quote:
            out.append("</blockquote>")
            in_quote = False

    def close_table() -> None:
        nonlocal in_table
        if in_table:
            out.append("</tbody></table>")
            in_table = False

    def close_all() -> None:
        close_table()
        close_list()
        close_quote()

    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            close_list()
            if in_quote:
                close_quote()
            i += 1
            continue

        # Table row.
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped[1:-1].split("|")]
            separator_next = (
                i + 1 < len(lines)
                and re.match(r"^\s*\|[\s:\-|]+\|\s*$", lines[i + 1]) is not None
            )
            if not in_table:
                close_list()
                close_quote()
                out.append("<table><thead><tr>")
                out.append("".join(f"<th>{_inline(c)}</th>" for c in cells))
                out.append("</tr></thead><tbody>")
                in_table = True
                if separator_next:
                    i += 2
                else:
                    i += 1
                continue
            out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in cells) + "</tr>")
            i += 1
            continue
        close_table()

        # Heading or rule.
        if m := re.match(r"^(#{1,6})\s+(.*)$", stripped):
            close_all()
            level, content = len(m.group(1)), m.group(2).strip()
            out.append(f"<h{level}>{_inline(content)}</h{level}>")
            i += 1
            continue
        if re.match(r"^-{3,}$", stripped):
            close_all()
            out.append("<hr>")
            i += 1
            continue

        # Blockquote (supports simple bullet lists inside).
        if stripped.startswith(">"):
            if not in_quote:
                close_list()
                out.append("<blockquote>")
                in_quote = True
            body = stripped.lstrip("> ").strip()
            bullet = re.match(r"^(?:[-*]|\d+[.)])\s+(.*)$", body)
            if bullet:
                if not quote_list:
                    out.append("<ul>")
                    quote_list = True
                out.append(f"<li>{_inline(bullet.group(1))}</li>")
            else:
                if quote_list:
                    out.append("</ul>")
                    quote_list = False
                out.append(f"<p>{_inline(body)}</p>")
            i += 1
            continue
        close_quote()

        # Checkbox item ("- [ ] task") and its bare "[ ] task" form.
        if m := re.match(r"^(?:[-*]\s+)?\[( |x|X)\]\s+(.*)$", stripped):
            if list_tag != "ul":
                close_list()
                out.append("<ul>")
                list_tag = "ul"
            box = CHECK_BOX[m.group(1)]
            out.append(f'<li class="cb">{box} {_inline(m.group(2))}</li>')
            i += 1
            continue

        if m := re.match(r"^[-*]\s+(.*)$", stripped):
            if list_tag != "ul":
                close_list()
                out.append("<ul>")
                list_tag = "ul"
            out.append(f"<li>{_inline(m.group(1))}</li>")
            i += 1
            continue

        if m := re.match(r"^\d+[.)]\s+(.*)$", stripped):
            if list_tag != "ol":
                close_list()
                out.append("<ol>")
                list_tag = "ol"
            out.append(f"<li>{_inline(m.group(1))}</li>")
            i += 1
            continue

        close_list()
        out.append(f"<p>{_inline(stripped)}</p>")
        i += 1

    close_all()
    return "\n".join(out)


# --------------------------------------------------------------------------
# Site assembly
# --------------------------------------------------------------------------

def chapter_title(md: str, stem: str) -> str:
    """First H1 in the markdown, else a tidied filename."""
    if m := re.search(r"^#\s+(.+)$", md, re.M):
        return m.group(1).strip()
    return stem.replace("-", " ").title()


def chapter_label(stem: str) -> str:
    """Numbered stems get a 'Chapter N:' label; the welcome page gets none."""
    if stem.startswith("00"):
        return ""
    if m := re.match(r"^(\d+)-", stem):
        return f"Chapter {int(m.group(1))}: "
    return ""


BACKMATTER_RANK = {"checklist": 1, "glossary": 2}


def chapter_sort_key(stem: str) -> tuple:
    """Reading order: numbered chapters, then checklist, then glossary."""
    if m := re.match(r"^(\d+)", stem):
        return (0, int(m.group(1)), stem)
    return (1, BACKMATTER_RANK.get(stem, 9), stem)


def sorted_chapters() -> List[tuple]:
    """Chapters in reading order: numbered chapters, then checklist, glossary."""
    files = []
    for path in DOCS.glob("*.md"):
        md = path.read_text(encoding="utf-8")
        files.append((path, md, chapter_title(md, path.stem)))
    files.sort(key=lambda t: chapter_sort_key(t[0].stem))
    return files


def make_page(title: str, nav_html: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{esc(SITE_TITLE + ' - ' + SITE_SUBTITLE)}">
<title>{esc(title)} | {esc(SITE_TITLE)}</title>
<style>
body {{ margin: 0; background: #f6f3ee; color: #2b2b2b; line-height: 1.65;
  font-family: Georgia, serif; }}
header.site {{ background: #274156; color: #fff; padding: 1.4rem 1rem; text-align: center; }}
header.site h1 {{ margin: 0; font-size: 1.6rem; }}
header.site p {{ margin: .3rem 0 0 0; color: #cdd9e5; font-style: italic; }}
main {{ max-width: 46rem; margin: 0 auto; padding: 1rem 1.2rem 0 1.2rem; }}
nav.toc {{ background: #fffdf8; border: 1px solid #e4dccc; border-radius: 8px;
  padding: 1rem 1.4rem; margin: 1rem 0 1.4rem 0; font-family: system-ui, sans-serif;
  font-size: .95rem; }}
nav.toc div {{ font-weight: 600; margin-bottom: .4rem; }}
nav.toc ol {{ margin: 0; padding-left: 1.4rem; }}
nav.toc a {{ color: #274156; text-decoration: none; }}
nav.toc a:hover {{ text-decoration: underline; }}
h1, h2, h3, h4 {{ color: #274156; line-height: 1.3; }}
h1 {{ font-size: 1.9rem; margin-top: .6rem; }}
blockquote {{ margin: 1.2rem 0; padding: .7rem 1.1rem; background: #fffdf8;
  border-left: 4px solid #b08968; border-radius: 4px; }}
blockquote p {{ margin: 0 0 .6rem 0; }}
blockquote p:last-child {{ margin-bottom: 0; }}
code {{ background: #eee7da; padding: .1rem .35rem; border-radius: 4px;
  font-size: .92em; }}
li.cb {{ list-style: none; margin-left: -1.2rem; }}
table {{ border-collapse: collapse; margin: 1rem 0; width: 100%;
  font-family: system-ui, sans-serif; font-size: .95rem; }}
th, td {{ border: 1px solid #d8cfbc; padding: .45rem .7rem; text-align: left;
  vertical-align: top; }}
th {{ background: #efe6d6; }}
html {{ scroll-behavior: smooth; }}
footer {{ text-align: center; color: #6f6a5f; font-size: .85rem;
  padding: 1.5rem 1rem 2.5rem 1rem; font-family: system-ui, sans-serif; }}
nav.pager {{ display: flex; justify-content: space-between; gap: 1rem;
  margin-top: 2.5rem; font-family: system-ui, sans-serif; }}
nav.pager a {{ color: #274156; text-decoration: none; font-weight: 600; }}
nav.pager a:hover {{ text-decoration: underline; }}
.kicker {{ color: #8a7452; font-family: system-ui, sans-serif;
  letter-spacing: .08em; font-size: .8rem; margin-bottom: 0; }}
.rail {{ margin: 0 0 1.6rem 0; padding: 1rem 1.2rem; background: #faf3e8;
  border: 1px solid #e4d0b4; border-radius: 8px;
  font-family: system-ui, sans-serif; font-size: .95rem; }}
.rail strong {{ color: #7a4a1e; }}
</style>
</head>
<body>
<header class="site">
<h1>{esc(SITE_TITLE)}</h1>
<p>{esc(SITE_SUBTITLE)}</p>
</header>
<main>
<nav class="toc"><div>{TOC_LEAD}</div>{nav_html}</nav>
<div class="rail">{GOLDEN_RULE}</div>
{body}
</main>
<footer>{FOOTER}</footer>
</body>
</html>
"""


def build(out_dir: Path) -> List[Path]:
    chapters = sorted_chapters()
    if not chapters:
        sys.exit("build.py: no Markdown chapters found in docs/.")

    nav_parts = ["<ol>"]
    for (path, _md, title) in chapters:
        nav_parts.append(
            f'<li><a href="{esc(path.stem + ".html")}">'
            f'{esc(chapter_label(path.stem))}{esc(title)}</a></li>'
        )
    nav_parts.append("</ol>")
    nav_html = "".join(nav_parts)

    # Backlinks helper outside f-strings for clarity.
    def pager(idx: int, count: int) -> str:
        prev_link = ""
        next_link = ""
        if idx > 0:
            prev_stem = chapters[idx - 1][0].stem
            prev_link = (
                f'<a class="prev" href="{esc(prev_stem)}.html">'
                f'&larr; {esc(chapter_label(prev_stem) or "")}'
                f'{esc(chapters[idx - 1][2])}</a>'
            )
        if idx < count - 1:
            next_stem = chapters[idx + 1][0].stem
            next_link = (
                f'<a class="next" href="{esc(next_stem)}.html">'
                f'{esc(chapter_label(next_stem) or "")}'
                f'{esc(chapters[idx + 1][2])} &rarr;</a>'
            )
        return f'<nav class="pager">{prev_link}{next_link}</nav>'

    built: List[Path] = []
    for idx, (path, md, title) in enumerate(chapters):
        body = md_to_html(unwrap(md))
        body += pager(idx, len(chapters))
        page = make_page(title, nav_html, body)
        target = out_dir / f"{path.stem}.html"
        target.write_text(page, encoding="utf-8")
        built.append(target)

    # index.html: short front page linking to chapter one and the checklist.
    def stem_of(prefix: str) -> str:
        for (path, _md, _title) in chapters:
            if path.stem == prefix or path.stem.startswith(prefix + "-"):
                return path.stem
        raise SystemExit(f"build.py: no chapter found for {prefix!r}")

    first_stem = chapters[0][0].stem
    checklist_stem = stem_of("10")
    glossary_stem = stem_of("11")
    home_body = (
        "<h1>Start here</h1>"
        "<p>Welcome. This manual is for multilingual households who use AI "
        "to translate the daily stuff &mdash; school notices, utility "
        "letters, medical and rental paperwork, government forms.</p>"
        "<p>It is deliberately <em>not</em> a language guide (no vocabulary "
        "drills, no conjugations). It is about understanding today&rsquo;s "
        "document safely: read the structure first, keep personal details "
        "out of cloud tools, verify before you act, and know when the right "
        "move is talking to a human office instead of translating.</p>"
        "<ul>"
        f'<li><a href="{esc(first_stem)}.html">Read the whole manual &rarr;</a></li>'
        f'<li><a href="{esc(checklist_stem)}.html">The one-page Verification Checklist &rarr;</a></li>'
        f'<li><a href="{esc(glossary_stem)}.html">Plain-English Glossary &rarr;</a></li>'
        "</ul>"
        "<p>No JavaScript, no tracking, works offline. Print anything you "
        "like.</p>"
    )
    index_target = out_dir / "index.html"
    index_target.write_text(make_page(SITE_TITLE, nav_html, home_body), encoding="utf-8")
    built.append(index_target)
    return built


def build_site(out_dir: Path) -> List[Path]:
    """Fresh build: wipe the directory, then build."""
    if out_dir.exists():
        for child in sorted(out_dir.iterdir()):
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    else:
        out_dir.mkdir(parents=True)
    return build(out_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(ROOT / "site"),
        help="Output directory (default: site/)",
    )
    args = parser.parse_args()
    pages = build_site(Path(args.out).resolve())
    print(f"Built {len(pages)} HTML pages into {args.out}")


if __name__ == "__main__":
    main()
