"""Microstructure library reader: structure-aware search and section reading over references/microstructure/.

Retrieval for *understanding*, not keyword grep: every hit comes back inside its section, with the chapter path
and page numbers, so the reader can open the whole argument (definitions, assumptions, the worked example).

    uv run --with pypdf python .claude/skills/microstructure-library/library.py build        # index all files
    ... library.py books                                    # keys, titles, sizes
    ... library.py toc harris [--depth 2]                   # the book's structure, with section ids
    ... library.py find "adverse selection" [--book harris] [--top 8]
    ... library.py read harris 3.2 [--offset 0] [--max-chars 40000]   # a whole section, page-marked
    ... library.py pages harris 120-124                     # raw pages

The index (full text) lives in references/microstructure/.index/ and is git-ignored: the books are copyrighted.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ROOT = REPO / "references" / "microstructure"
INDEX = ROOT / ".index"
SKIP = ("bookey-summary",)          # superseded or non-source files

# Concept → other phrasings the books use. Searching any one finds all of them.
ALIASES = [
    ("order flow imbalance", "ofi", "order-flow imbalance", "flow imbalance"),
    ("adverse selection", "informed trading", "informed traders", "toxic flow", "toxicity"),
    ("price impact", "market impact", "impact of trades", "kyle's lambda", "kyle lambda"),
    ("square-root impact", "square root law", "square-root law", "concave impact"),
    ("bid-ask spread", "bid–ask spread", "quoted spread", "effective spread", "realized spread", "realised spread"),
    ("queue imbalance", "book imbalance", "order book imbalance", "volume imbalance"),
    ("microprice", "micro-price", "weighted mid", "fair price"),
    ("trade sign", "trade classification", "lee-ready", "lee and ready", "tick rule", "aggressor"),
    ("metaorder", "meta-order", "order splitting", "child orders", "parent order"),
    ("long memory", "long-range correlation", "autocorrelation of order signs", "persistence of order flow"),
    ("stop order", "stop-loss", "stop loss", "stop orders"),
    ("liquidity provider", "market maker", "dealer", "liquidity supplier"),
    ("liquidity taker", "aggressive order", "market order", "marketable order"),
    ("limit order book", "order book", "lob"),
    ("dark pool", "dark pools", "hidden liquidity", "iceberg"),
    ("vpin", "volume-synchronized probability of informed trading", "volume clock"),
    ("optimal execution", "almgren", "implementation shortfall", "twap", "vwap"),
    ("momentum", "trend following", "trend"),
    ("mean reversion", "mean-reverting", "reversal"),
    ("volatility clustering", "volatility", "garch"),
    ("liquidity", "depth", "resilience"),
]
STOP = set("the a an of and or to in on for with by at from as is are be this that it its into how what why when "
           "which who does do vs".split())


# --- pure pieces (unit-tested) -------------------------------------------------------------------

def book_key(path: Path) -> str:
    """'1-harris-trading-and-exchanges.pdf' → 'harris'; '03-cont-price-impact...' (papers) → 'p03-cont'."""
    stem = path.stem
    m = re.match(r"^(\d+)-([a-z]+)", stem)
    if not m:
        return re.sub(r"[^a-z0-9]+", "-", stem.lower())[:24]
    return f"p{m.group(1)}-{m.group(2)}" if path.parent.name == "papers" else m.group(2)


def sections_from_outline(entries: list[tuple[int, str, int]], n_pages: int) -> list[dict]:
    """[(level, title, start_page)] in reading order → sections with ids ('2', '2.3'), end pages and parents.
    A section ends where the next entry at the same or a higher level starts (pages are 1-based)."""
    out, counters = [], []
    for i, (lvl, title, start) in enumerate(entries):
        counters = counters[:lvl + 1] + [0] * max(0, lvl + 1 - len(counters))
        counters[lvl] += 1
        sid = ".".join(str(c) for c in counters[:lvl + 1])
        end = n_pages
        for lvl2, _, start2 in entries[i + 1:]:
            if lvl2 <= lvl:
                end = max(start, start2 - 1) if start2 > start else start
                break
        out.append({"id": sid, "level": lvl, "title": title.strip(), "start": start, "end": end,
                    "parent": sid.rsplit(".", 1)[0] if "." in sid else None})
    for s in out:
        s["leaf"] = not any(o["parent"] == s["id"] for o in out)
    return out


def headings_from_pages(pages: list[str]) -> list[tuple[int, str, int]]:
    """Fallback when a PDF has no outline: a page whose first lines are a chapter number then a title
    (or 'Chapter N Title') starts a chapter."""
    entries = []
    for i, text in enumerate(pages):
        lines = [l.strip() for l in text.splitlines() if l.strip()][:3]
        if not lines:
            continue
        m = re.match(r"^(?:chapter\s+)?(\d{1,2})\s*$", lines[0], re.I)
        if m and len(lines) > 1 and 3 <= len(lines[1]) <= 80 and not lines[1].endswith(".") \
                and not lines[1][0].isdigit() and len(lines[1].split()) <= 7 and "," not in lines[1]:
            entries.append((0, f"{m.group(1)} {lines[1]}", i + 1))
            continue
        m = re.match(r"^chapter\s+(\d{1,2})[.:]?\s+(.{3,80})$", lines[0], re.I)
        if m:
            entries.append((0, f"{m.group(1)} {m.group(2)}", i + 1))
    # keep chapter numbers increasing (drops running headers and cross-references)
    keep, last = [], 0
    for e in entries:
        n = int(e[1].split()[0])
        if n == last + 1:
            keep.append(e)
            last = n
    return keep


def windows(n_pages: int, size: int = 5) -> list[tuple[int, str, int]]:
    """No outline and no detectable headings: fixed page windows, so a hit still points at a few pages."""
    return [(0, f"pp.{a}-{min(a + size - 1, n_pages)}", a) for a in range(1, n_pages + 1, size)]


def expand(query: str) -> tuple[list[str], list[str]]:
    """Query → (phrases incl. aliases, single content words)."""
    q = query.lower().strip()
    phrases = {q}
    for group in ALIASES:
        if any(a == q or a in q or (len(q) > 4 and q in a) for a in group):
            phrases.update(group)
    words = [w for w in re.findall(r"[a-z][a-z'\-]+", q) if w not in STOP and len(w) > 2]
    return sorted(phrases, key=len, reverse=True), words


def score(text: str, title: str, phrases: list[str], words: list[str]) -> tuple[float, int]:
    """Section relevance: phrase hits weigh 3×, words 1× (capped), a heading match +10; long sections are
    discounted (sqrt) so a focused section beats a whole chapter that mentions the term once."""
    t, ti = text.lower(), title.lower()
    ph = sum(len(re.findall(r"(?<![a-z])" + re.escape(p) + r"(?![a-z])", t)) for p in phrases)
    wd = sum(min(t.count(w), 5) for w in words)
    if ph == 0 and (not words or any(w not in t for w in words)):
        return 0.0, 0
    head = 10 if any(p in ti for p in phrases) or (words and all(w in ti for w in words)) else 0
    s = (3 * ph + wd + head) / math.sqrt(1 + len(t) / 20000)
    return s, ph


MATH = re.compile(r"[=∑∫√∂≈≤≥±×→∞^]|\b(?:log|exp|var|cov|E\[)|[α-ωΑ-Ω]")


def math_density(text: str) -> float:
    """Share of non-empty lines that look like equations (math symbols, Greek, or short symbol-heavy
    fragments that pdftotext leaves when it breaks a formula). ≥ 0.15 → render the pages and read them."""
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return 0.0
    mathy = sum(1 for l in lines if MATH.search(l) or (len(l.split()) <= 3 and re.search(r"[()\[\]{}|/+−-]", l)))
    return mathy / len(lines)


def snippet(text: str, phrases: list[str], words: list[str], width: int = 110) -> str:
    t = text.lower()
    for p in phrases + words:
        i = t.find(p)
        if i >= 0:
            a, b = max(0, i - width), min(len(text), i + len(p) + width)
            return ("…" if a else "") + " ".join(text[a:b].split()) + ("…" if b < len(text) else "")
    return ""


# --- extraction ------------------------------------------------------------------------------------

def _pdf(path: Path) -> dict:
    raw = subprocess.run(["pdftotext", str(path), "-"], capture_output=True, text=True).stdout
    pages = raw.split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    entries, source = [], "outline"
    try:
        from pypdf import PdfReader
        r = PdfReader(str(path), strict=False)
        title = (r.metadata.title if r.metadata and r.metadata.title else "") or ""

        def walk(items, lvl):
            for x in items:
                if isinstance(x, list):
                    walk(x, lvl + 1)
                else:
                    try:
                        entries.append((lvl, str(x.title), r.get_destination_page_number(x) + 1))
                    except Exception:
                        pass
        walk(r.outline, 0)
    except Exception:
        title = ""
    entries = [e for e in entries if 1 <= e[2] <= len(pages)]
    if len(entries) < 3:
        entries, source = headings_from_pages(pages), "headings"
    if not entries:
        entries, source = windows(len(pages)), "none"
    return {"kind": "pdf", "title": title or path.stem, "pages": pages, "toc_source": source,
            "sections": sections_from_outline(entries, len(pages))}


def _html_text(s: str) -> str:
    s = re.sub(r"(?is)<(script|style|head).*?</\1>", " ", s)
    s = re.sub(r"(?i)<br\s*/?>|</(p|div|h[1-6]|li|tr|blockquote)>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return "\n".join(" ".join(l.split()) for l in s.splitlines() if l.strip())


def _epub(path: Path) -> dict:
    z = zipfile.ZipFile(path)
    container = z.read("META-INF/container.xml").decode("utf8", "ignore")
    opf_path = re.search(r'full-path="([^"]+)"', container).group(1)
    base = opf_path.rsplit("/", 1)[0] + "/" if "/" in opf_path else ""
    opf = z.read(opf_path).decode("utf8", "ignore")
    title = (re.findall(r"<dc:title[^>]*>(.*?)</dc:title>", opf, re.S) or [path.stem])[0]
    manifest = {m.group(1): m.group(2) for m in re.finditer(r'<item\b[^>]*\bid="([^"]+)"[^>]*\bhref="([^"]+)"', opf)}
    manifest.update({m.group(2): m.group(1) for m in re.finditer(r'<item\b[^>]*\bhref="([^"]+)"[^>]*\bid="([^"]+)"', opf)})
    spine = [manifest[i] for i in re.findall(r'<itemref\b[^>]*\bidref="([^"]+)"', opf) if i in manifest]
    pages = [_html_text(z.read(base + h).decode("utf8", "ignore")) for h in spine]
    index = {h.split("#")[0]: i + 1 for i, h in enumerate(spine)}
    entries = []
    ncx = [n for n in z.namelist() if n.endswith(".ncx")]
    if ncx:
        x = z.read(ncx[0]).decode("utf8", "ignore")
        depth = 0
        for tok in re.finditer(r"<navPoint\b|</navPoint>|<text>(.*?)</text>|<content\b[^>]*src=\"([^\"]+)\"", x, re.S):
            s = tok.group(0)
            if s.startswith("<navPoint"):
                depth += 1
            elif s == "</navPoint>":
                depth -= 1
            elif tok.group(1) is not None:
                pending = html.unescape(tok.group(1)).strip()
            elif tok.group(2):
                href = tok.group(2).split("#")[0]
                if href in index:
                    entries.append((depth - 1, pending, index[href]))
    if not entries:
        entries = [(0, f"Part {i + 1}", i + 1) for i in range(len(pages))]
    return {"kind": "epub", "title": html.unescape(title), "pages": pages, "toc_source": "ncx" if ncx else "spine",
            "sections": sections_from_outline(entries, len(pages))}


def files() -> list[Path]:
    fs = sorted(ROOT.glob("books/*.pdf")) + sorted(ROOT.glob("books/*.epub")) + sorted(ROOT.glob("papers/*.pdf"))
    return [f for f in fs if not any(s in f.name for s in SKIP)]


def build() -> None:
    INDEX.mkdir(parents=True, exist_ok=True)
    for f in files():
        doc = _epub(f) if f.suffix == ".epub" else _pdf(f)
        doc.update({"key": book_key(f), "file": str(f.relative_to(REPO))})
        (INDEX / f"{doc['key']}.json").write_text(json.dumps(doc))
        words = sum(len(p.split()) for p in doc["pages"])
        print(f"{doc['key']:22} {len(doc['pages']):4} {'pp' if doc['kind'] == 'pdf' else 'docs'}  "
              f"{len(doc['sections']):4} sections ({doc['toc_source']})  {words // 1000}k words  {doc['title'][:50]}")


def load(key: str) -> dict:
    p = INDEX / f"{key}.json"
    if not p.exists():
        sys.exit(f"no index for '{key}': run `library.py build`, or see `library.py books`")
    return json.loads(p.read_text())


def all_docs() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(INDEX.glob("*.json"))]


def section_text(doc: dict, s: dict) -> str:
    return "\n".join(f"[p.{i}]\n{doc['pages'][i - 1]}" for i in range(s["start"], s["end"] + 1))


def path_of(doc: dict, s: dict) -> str:
    by = {x["id"]: x for x in doc["sections"]}
    chain, cur = [], s
    while cur:
        chain.append(cur["title"])
        cur = by.get(cur["parent"]) if cur["parent"] else None
    return " › ".join(reversed(chain))


def find(query: str, book: str | None = None, top: int = 8) -> list[dict]:
    phrases, words = expand(query)
    hits = []
    for doc in ([load(book)] if book else all_docs()):
        for s in doc["sections"]:
            if not s["leaf"] and (s["end"] - s["start"]) > 25:
                continue                                    # score focused sections, not whole parts
            text = section_text(doc, s)
            sc, ph = score(text, s["title"], phrases, words)
            if sc > 0:
                hits.append({"key": doc["key"], "id": s["id"], "path": path_of(doc, s), "pages": f"{s['start']}-{s['end']}",
                             "score": round(sc, 1), "phrase_hits": ph, "math": round(math_density(text), 2),
                             "snippet": snippet(text, phrases, words)})
    return sorted(hits, key=lambda h: -h["score"])[:top]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="library.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    sub.add_parser("books")
    t = sub.add_parser("toc"); t.add_argument("book"); t.add_argument("--depth", type=int, default=2)
    f = sub.add_parser("find"); f.add_argument("query"); f.add_argument("--book"); f.add_argument("--top", type=int, default=8)
    r = sub.add_parser("read"); r.add_argument("book"); r.add_argument("section")
    r.add_argument("--offset", type=int, default=0); r.add_argument("--max-chars", type=int, default=40000)
    p = sub.add_parser("pages"); p.add_argument("book"); p.add_argument("range")
    g = sub.add_parser("render", help="page images for reading equations, tables and figures")
    g.add_argument("book"); g.add_argument("range"); g.add_argument("--dpi", type=int, default=110)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        build()
    elif a.cmd == "books":
        for d in all_docs():
            print(f"{d['key']:22} {len(d['pages']):4} {'pp' if d['kind'] == 'pdf' else 'docs'}  {d['title'][:60]}")
    elif a.cmd == "toc":
        d = load(a.book)
        print(f"{d['title']}  (toc from {d['toc_source']})")
        for s in d["sections"]:
            if s["level"] < a.depth:
                print(f"{'  ' * s['level']}{s['id']:8} {s['title'][:70]:70} pp.{s['start']}-{s['end']}")
    elif a.cmd == "find":
        for h in find(a.query, a.book, a.top):
            m = f"  MATH {h['math']:.0%} → render" if h["math"] >= 0.15 else ""
            print(f"{h['key']} {h['id']}  pp.{h['pages']}  score {h['score']} ({h['phrase_hits']} phrase hits){m}\n"
                  f"   {h['path']}\n   {h['snippet']}\n")
    elif a.cmd == "read":
        d = load(a.book)
        s = next((x for x in d["sections"] if x["id"] == a.section), None)
        if s is None:
            sys.exit(f"no section {a.section} in {a.book}: see `library.py toc {a.book}`")
        text = section_text(d, s)
        part = text[a.offset:a.offset + a.max_chars]
        md = math_density(text)
        print(f"## {a.book} {s['id']}: {path_of(d, s)}  (pp.{s['start']}-{s['end']}, chars {a.offset}-"
              f"{a.offset + len(part)} of {len(text)})")
        if md >= 0.15:
            print(f"## MATH-HEAVY ({md:.0%} of lines): equations below are mangled by text extraction. Render the "
                  f"pages and read the images: library.py render {a.book} {s['start']}-{s['end']}")
        print()
        print(part)
        if a.offset + len(part) < len(text):
            print(f"\n[… continues: library.py read {a.book} {s['id']} --offset {a.offset + len(part)}]")
    elif a.cmd == "render":
        d = load(a.book)
        if d["kind"] != "pdf":
            sys.exit("render works on PDFs; EPUB text keeps its formatting (use read)")
        lo, hi = (int(x) for x in a.range.split("-")) if "-" in a.range else (int(a.range),) * 2
        if hi - lo > 11:
            sys.exit("render at most 12 pages at a time")
        out = INDEX / "renders"
        out.mkdir(parents=True, exist_ok=True)
        for i in range(lo, hi + 1):
            png = out / f"{a.book}-p{i:04d}.png"
            if not png.exists():
                subprocess.run(["pdftoppm", "-f", str(i), "-l", str(i), "-r", str(a.dpi), "-gray", "-png",
                                "-singlefile", str(REPO / d["file"]), str(png.with_suffix(""))],
                               capture_output=True)
            print(png)
    elif a.cmd == "pages":
        d = load(a.book)
        lo, hi = (int(x) for x in a.range.split("-"))
        for i in range(max(1, lo), min(len(d["pages"]), hi) + 1):
            print(f"[p.{i}]\n{d['pages'][i - 1]}")


if __name__ == "__main__":
    main()
