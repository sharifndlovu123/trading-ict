---
name: microstructure-library
description: Read the order-flow / market-microstructure books and papers in references/microstructure/ in context: find a concept across the library, open the whole section around it (chapter path, pages), render equation pages as images and work the maths properly, then map it to the ICT engine. Use whenever a question, rule or feature touches order flow, liquidity, spreads, price impact, adverse selection, stops, market makers, OFI, microprice, VPIN, execution, or the quant models behind them. Also use when citing these books.
---

# Microstructure library

The library is the evidence base behind `references/orderflow.md`. It holds 7 books (Harris, Bouchaud et al.,
Hasbrouck, Cartea et al., Lehalle & Laruelle, López de Prado, Patterson) and the free papers (`p01`–`p17`). The
tool is `library.py` in this folder. **Read for meaning, not for words.** A keyword hit is only a pointer: the
answer is in the section's argument, its definitions, its assumptions and its maths.

```bash
L="uv run --with pypdf python .claude/skills/microstructure-library/library.py"
$L books                                   # keys (harris, bouchaud, hasbrouck, cartea, lehalle, lopez, patterson, p03-cont …)
$L toc bouchaud --depth 2                  # structure + section ids (ids are positional, not chapter numbers)
$L find "adverse selection" [--book harris] [--top 8]   # ranked sections, with path, pages, MATH flag
$L read bouchaud 21.3                      # the whole section, page-marked ([p.N]); --offset to continue
$L render bouchaud 252-258                 # page images → Read them (equations, tables, figures)
$L pages harris 120-124                    # raw page text
$L build                                   # re-index after adding or replacing a file (≈7 s)
```

## Method (every time)

1. **Orient.** Run `toc` for the book you'll lean on. Know where the section sits in the book's argument (which
   part, what comes before it) before reading it.
2. **Find across the library.** `find` expands synonyms (e.g. OFI ↔ order flow imbalance; adverse selection ↔
   informed trading ↔ toxicity). Prefer focused subsections over whole chapters. Look at **2+ sources** when
   they exist: a textbook (theory and definitions) and a paper (the empirical result).
3. **Read the whole section, plus its context.**
   - Read the full section with `read`, not the snippet.
   - Read the parent chapter's opening pages when terms are defined there.
   - Read the next section when the argument continues ("Conclusion", "Discussion", "Limitations").
   - If a term is used but not defined, find where it is defined (`find "<term>" --book X` → the earliest section).
4. **Work the maths properly.** When `find` or `read` flags **MATH** (≥ 15% equation lines), the extracted text
   has broken formulas, so `render` the pages and Read the images. Then:
   - Transcribe each equation you rely on into LaTeX, in your own notes.
   - List every symbol: its meaning, units, and which variable is estimated vs observed.
   - State the assumptions: the market model, the data level (L1/L2/L3/trades), the horizon and the regime.
   - Record the empirical values with their ranges and the sample they came from (e.g. an exponent ≈ 0.5–0.6 on
     futures for 2007–2010). A parameter has no meaning without its sample.
   - Check dimensions and limiting cases (what happens as Q → 0, or at large depth).
   - Before using an equation in the engine: implement it as a pure function with a unit test on hand-computed
     numbers (the CLAUDE.md testing rule), and note the book's equation number and page beside the code.
5. **Judge it in context.**
   - Which market and instrument was it shown on (equities, futures, FX, crypto)? Our feed is a CFD.
   - Theory or measurement? Is it contested (e.g. VPIN)? Do the books disagree with each other?
   - What horizon? Microstructure effects decay in seconds to minutes, while our trades last minutes to hours.
6. **Map it to the engine.** Use `references/orderflow.md` §10 for the data limits: Dukascopy gives quotes, not
   trades, so delta, VPIN and Kyle's λ need futures data. Use the four layers for placement (concept / pattern /
   strategy / model). ICT concepts are still settled by ictindex.io; these books settle microstructure facts.
7. **Record with citations, in your own words.** Cite as `bouchaud §12.3, pp.252-258` (book key, the book's own
   section number, PDF pages). Paraphrase. Quote at most a sentence or two. Never paste long passages into repo
   files, artifacts or chat: the books are copyrighted and stay local (`books/`, `papers/` and `.index/` are
   git-ignored). Put lasting findings in `references/orderflow.md` with their citations.

## Notes

- Pages are **PDF page numbers** (what `read`, `pages` and `render` use). The book's printed page numbers differ,
  so give both when quoting.
- Hasbrouck's book has no outline: its chapters come from heading detection (15 chapters, checked). Papers without
  an outline are split into 5-page windows.
- `patterson` is an EPUB. Its "pages" are chapters, and `render` doesn't apply.
- `references/microstructure/README.md` is the checklist of what's in the library and what's missing.
