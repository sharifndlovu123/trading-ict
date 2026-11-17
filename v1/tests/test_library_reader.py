"""Microstructure library reader (.claude/skills/microstructure-library/library.py) on hand-built inputs.

The books themselves are local-only, so these tests use synthetic outlines, pages and a tiny EPUB.
A real-data check runs only when the index exists (a skip is not a pass).
"""

import importlib.util
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("library", ROOT / ".claude/skills/microstructure-library/library.py")
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)


def test_book_key_for_books_and_papers():
    assert lib.book_key(Path("books/1-harris-trading-and-exchanges.pdf")) == "harris"
    assert lib.book_key(Path("papers/03-cont-price-impact.pdf")) == "p03-cont"
    assert lib.book_key(Path("books/7-patterson-dark-pools.epub")) == "patterson"


def test_sections_from_outline_ids_end_pages_parents_and_leaves():
    entries = [(0, "1 Intro", 1), (0, "2 Impact", 5), (1, "2.1 Linear", 5), (1, "2.2 Square root", 8), (0, "3 End", 12)]
    s = {x["id"]: x for x in lib.sections_from_outline(entries, n_pages=15)}
    assert (s["1"]["start"], s["1"]["end"]) == (1, 4)
    assert (s["2"]["start"], s["2"]["end"]) == (5, 11)          # a chapter spans its subsections
    assert (s["2.2"]["start"], s["2.2"]["end"], s["2.2"]["parent"]) == (8, 11, "2")
    assert (s["3"]["end"]) == 15                                 # the last section runs to the last page
    assert not s["2"]["leaf"] and s["2.1"]["leaf"] and s["1"]["leaf"]


def test_heading_fallback_keeps_increasing_chapters_and_skips_front_matter():
    pages = ["Oxford University Press\n1\nOxford University Press, Inc., publishes works that further\n",
             "1\nIntroduction\ntext", "body", "2\nTrading Mechanisms\ntext", "see chapter\n7\nfoo\n",
             "Chapter 3 The Roll Model\ntext"]
    assert lib.headings_from_pages(pages) == [(0, "1 Introduction", 2), (0, "2 Trading Mechanisms", 4),
                                              (0, "3 The Roll Model", 6)]


def test_windows_cover_every_page():
    w = lib.windows(12, size=5)
    assert [e[2] for e in w] == [1, 6, 11] and w[-1][1] == "pp.11-12"


def test_expand_adds_aliases_and_content_words():
    phrases, words = lib.expand("OFI")
    assert "order flow imbalance" in phrases and "ofi" in phrases
    _, words = lib.expand("how do stop orders work")
    assert words == ["stop", "orders", "work"]


def test_score_prefers_focused_phrase_hits_and_heading_matches():
    phrases, words = lib.expand("price impact")
    focused = "price impact " * 5
    diluted = "price impact " * 5 + "filler " * 20000
    assert lib.score(focused, "Other", phrases, words)[0] > lib.score(diluted, "Other", phrases, words)[0]
    assert lib.score(focused, "Price impact", phrases, words)[0] > lib.score(focused, "Other", phrases, words)[0]
    assert lib.score("nothing relevant here", "x", phrases, words) == (0.0, 0)


def test_math_density_flags_broken_equations():
    prose = "\n".join(["The market maker quotes both sides of the book every day."] * 10)
    maths = "\n".join(["δ ≈ 0.5", "Q/V", "(12.6)", "σ√(Q/V)"] * 3 + ["Some words in a sentence here."])
    assert lib.math_density(prose) < 0.15 <= lib.math_density(maths)


def test_epub_toc_and_spine(tmp_path):
    p = tmp_path / "7-test-book.epub"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("META-INF/container.xml", '<rootfile full-path="OEBPS/content.opf"/>')
        z.writestr("OEBPS/content.opf",
                   '<dc:title>Test Book</dc:title><item id="c1" href="c1.xhtml"/><item id="c2" href="c2.xhtml"/>'
                   '<itemref idref="c1"/><itemref idref="c2"/>')
        z.writestr("OEBPS/toc.ncx", '<navPoint><text>One</text><content src="c1.xhtml"/>'
                   '<navPoint><text>One A</text><content src="c1.xhtml#a"/></navPoint></navPoint>'
                   '<navPoint><text>Two</text><content src="c2.xhtml"/></navPoint>')
        z.writestr("OEBPS/c1.xhtml", "<html><body><p>Market makers &amp; dealers.</p></body></html>")
        z.writestr("OEBPS/c2.xhtml", "<html><body><p>Dark pools.</p></body></html>")
    d = lib._epub(p)
    assert d["title"] == "Test Book" and d["pages"] == ["Market makers & dealers.", "Dark pools."]
    assert [(s["id"], s["title"], s["start"]) for s in d["sections"]] == [("1", "One", 1), ("1.1", "One A", 1),
                                                                          ("2", "Two", 2)]


def test_real_library_finds_the_square_root_law():
    if not (lib.INDEX / "bouchaud.json").exists():
        pytest.skip("library index not built (books are local-only): run library.py build")
    hits = lib.find("square-root impact", book="bouchaud", top=3)
    assert any("Square-Root Law" in h["path"] for h in hits)
