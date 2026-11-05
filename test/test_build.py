"""Tests for the build script: output shape, links, and the md renderer."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "script"))

import build as build_mod  # noqa: E402

EXPECTED_PAGES = 13  # 12 chapters + index
NO_EXT_LINK = re.compile(r'https?://')


def build_to(tmp_path):
    out = tmp_path / "site"
    pages = build_mod.build_site(out)
    return out, pages


def test_build_creates_all_pages(tmp_path):
    out, pages = build_to(tmp_path)
    assert len(pages) == EXPECTED_PAGES
    assert (out / "index.html").exists()
    chapters = sorted(stem + ".html" for stem in
                      [p.stem for p in build_mod.DOCS.glob("*.md")])
    for ch in chapters:
        assert (out / ch).exists()


def test_every_page_is_complete_self_contained_html(tmp_path):
    out, _ = build_to(tmp_path)
    for page in sorted(out.glob("*.html")):
        text = page.read_text(encoding="utf-8")
        assert text.startswith("<!doctype html>"), page
        assert text.rstrip().endswith("</html>"), page
        assert "<script" not in text.lower(), "site must have no JavaScript"
        assert not NO_EXT_LINK.search(text), f"external link in {page}"
        assert "Copyright (c) 2026 Asdale Dynamics, LLC" in text


def test_internal_links_resolve(tmp_path):
    out, _ = build_to(tmp_path)
    link_re = re.compile(r'href="([^"]+\.html)"')
    for page in sorted(out.glob("*.html")):
        text = page.read_text(encoding="utf-8")
        for href in link_re.findall(text):
            assert (out / href).exists(), f"{page} -> {href} missing"


def test_rebuild_is_fresh_but_stable(tmp_path):
    out, _ = build_to(tmp_path)
    stale = out / "stale.html"
    stale.write_text("leftover", encoding="utf-8")
    pages = build_mod.build_site(out)
    assert not stale.exists()
    assert len(pages) == EXPECTED_PAGES


def test_build_wipes_output_before_rebuild(tmp_path):
    out = tmp_path / "site"
    out.mkdir()
    (out / "junk.css").write_text("old", encoding="utf-8")
    build_mod.build_site(out)
    assert not (out / "junk.css").exists()


def test_read_chapters_ordered():
    chapters = build_mod.sorted_chapters()
    stems = [p.stem for (p, _md, _t) in chapters]
    assert stems == sorted(stems, key=build_mod.chapter_sort_key)
    assert stems[0].startswith("00")
    assert "glossary" in stems[-1]


def test_checklist_page_has_checkboxes(tmp_path):
    out, _ = build_to(tmp_path)
    checklist = next(out.glob("10*checklist*.html"))
    assert "\u2610" in checklist.read_text(encoding="utf-8")


# ------------------------------------------------------------------------
# Renderer unit tests
# ------------------------------------------------------------------------

def md(text):
    got = build_mod.md_to_html(build_mod.unwrap(text))
    return re.sub(r">\s+<", "><", got).strip()


def test_headings():
    assert md("# Big") == "<h1>Big</h1>"
    assert md("## Small") == "<h2>Small</h2>"


def test_paragraph_joins_wrapped_lines():
    got = md("the quick brown\nfox jumps")
    assert got == "<p>the quick brown fox jumps</p>"


def test_bold_italic_code_link():
    assert md("**bold words**") == "<p><strong>bold words</strong></p>"
    assert md("*soft*") == "<p><em>soft</em></p>"
    assert md("`x = 1`") == "<p><code>x = 1</code></p>"
    assert md("[a](b.html)") == '<p><a href="b.html">a</a></p>'
    assert md("**bold with *nested* italics**") == \
        "<p><strong>bold with <em>nested</em> italics</strong></p>"


def test_ordered_and_unordered_lists():
    got = md("1. one\n2. two")
    assert got == "<ol><li>one</li><li>two</li></ol>"
    got = md("- alpha\n- beta")
    assert got == "<ul><li>alpha</li><li>beta</li></ul>"


def test_list_continuations_merge_into_item():
    got = md("- first point\n  more detail here\n")
    assert got == "<ul><li>first point more detail here</li></ul>"


def test_checkbox_items():
    got = md("- [ ] todo\n- [x] done\n")
    assert got.count("\u2610") == 1 and got.count("\u2611") == 1


def test_blockquote_joins_lines_into_one_paragraph():
    got = md("> line one\n> line two\n")
    assert got == "<blockquote><p>line one line two</p></blockquote>"


def test_quote_then_paragraph_stays_separate():
    got = md("> quoted\nafter quote")
    assert got == "<blockquote><p>quoted</p></blockquote><p>after quote</p>"


def test_table_round_trip():
    got = md("| A | B |\n|---|---|\n| 1 | 2 |\n")
    assert "<th>A</th>" in got and "<td>2</td>" in got


def test_special_chars_escaped():
    got = md("a < b & c")
    assert got == "<p>a &lt; b &amp; c</p>"
