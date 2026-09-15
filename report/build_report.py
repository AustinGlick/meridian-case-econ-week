"""Build the Round 1 submission PDF: four-page narrative plus the exhibit appendix.

Run from the repo root:

    python report/build_report.py            # or: python -m report.build_report

Narrative source format: Markdown (`report/draft.md`). The team writes prose in Markdown and
copies numbers from `outputs/RESULTS.md`, which is also Markdown, so nobody needs to learn
Typst. This script converts the Markdown to Typst with a small hand-written converter
(headings `#`/`##`/`###`, paragraphs, **bold**, *italic*, `code`, bullet and numbered lists,
simple pipe tables, horizontal rules; exhibit references such as "(E12)" are plain text) and
compiles with the `typst` Python package, which bundles the Typst compiler. No pandoc, no
LaTeX, no system fonts (the body font, Libertinus Serif, ships inside Typst).

What the build does
- Reads `report/draft.md` (override with --draft PATH).
- Compiles the narrative alone first and counts its pages with pypdf. More than four pages
  FAILS the build (exit code 1). The appendix never counts.
- Parses the "## Appendix order" list at the bottom of `report/narrative_outline.md` at build
  time (read-only) so the appendix order cannot drift from the outline. Fails if an id in that
  list has neither a PNG in `outputs/exhibits/` nor a table in `outputs/tables/`; warns about
  any PNG/table on disk that the list does not mention.
- For each id: places `outputs/exhibits/E##x_*.png` (fit to page width, aspect kept, capped
  to page height) and its table `outputs/tables/E##x_*.md` underneath; a table-only exhibit
  is placed as a table. Markdown tables are converted to Typst tables; wide tables get a
  smaller font and, past ten columns, a landscape page.
- Writes the assembled Typst source to `build/report.typ` (gitignored) and the PDF to
  `report/Meridian_Round1.pdf` (committed, so teammates can read it without building).
- Prints a build summary: narrative pages, appendix pages, exhibits placed, exhibits missing.

Dependencies: `pip install typst pypdf` (pandas is not needed).
"""
from __future__ import annotations

import argparse
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "report"
OUTLINE = REPORT / "narrative_outline.md"
DRAFT = REPORT / "draft.md"
EXHIBITS = ROOT / "outputs" / "exhibits"
TABLES = ROOT / "outputs" / "tables"
BUILD = ROOT / "build"
PDF_OUT = REPORT / "Meridian_Round1.pdf"

NARRATIVE_MAX_PAGES = 4
PAGE_WIDTH_IN = 8.5 - 2.0        # letter minus 1in margins
PAGE_HEIGHT_IN = 11.0 - 2.0
MAX_FIG_HEIGHT_IN = 6.2          # leaves room for the heading and a few table rows
PORTRAIT_PT = PAGE_WIDTH_IN * 72                 # text width, portrait
LANDSCAPE_PT = (11.0 - 1.5) * 72                 # text width, landscape, 0.75in margins
LANDSCAPE_MIN_COLS = 11

PREAMBLE = """\
#set page(paper: "us-letter", margin: 1in, numbering: "1")
#set text(font: "Libertinus Serif", size: 11pt, lang: "en")
#set par(justify: false, leading: 0.6em)
#set heading(numbering: none)
#show heading.where(level: 1): it => block(above: 1.4em, below: 0.8em, text(size: 14pt, weight: "bold", it.body))
#show heading.where(level: 2): it => block(above: 1.2em, below: 0.6em, text(size: 12pt, weight: "bold", it.body))
#show heading.where(level: 3): it => block(above: 1.0em, below: 0.5em, text(size: 11pt, weight: "bold", it.body))
#set table(stroke: none, inset: (x: 4pt, y: 2.5pt))
#set list(indent: 1em)
#set enum(indent: 1em)
"""

EXHIBIT_ID = re.compile(r"\bE\d{2}[a-z]?\b")


# ---------------------------------------------------------------------------
# Typst text escaping and inline Markdown
# ---------------------------------------------------------------------------
_SPECIAL = "\\#$*_`@<>[]~/'\"-+="   # characters Typst treats as markup at some position


def esc(text: str) -> str:
    """Escape a plain string so Typst renders it literally."""
    out = []
    for ch in text:
        if ch in "\\#$*_`@<>[]~":
            out.append("\\" + ch)
        elif ch == "/":
            out.append("\\/")          # "//" would start a comment
        elif ch in "'\"":
            out.append("\\" + ch)      # smart quotes off
        elif ch in "+-=":
            out.append("\\" + ch)      # "- ", "+ ", "= " at line start are list/heading markers
        else:
            out.append(ch)
    return "".join(out)


_INLINE = re.compile(r"(\*\*.+?\*\*|\*.+?\*|`.+?`)")


def inline(text: str) -> str:
    """Convert **bold**, *italic* and `code` in one line; escape everything else."""
    parts = []
    for tok in _INLINE.split(text):
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            parts.append("#strong[" + inline(tok[2:-2]) + "]")
        elif tok.startswith("`") and tok.endswith("`") and len(tok) > 2:
            parts.append("#raw(" + typst_str(tok[1:-1]) + ")")
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            parts.append("#emph[" + inline(tok[1:-1]) + "]")
        else:
            parts.append(esc(tok))
    return "".join(parts)


def typst_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


# ---------------------------------------------------------------------------
# Markdown block conversion
# ---------------------------------------------------------------------------
def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    cells = re.split(r"(?<!\\)\|", line)
    return [c.replace("\\|", "|").strip() for c in cells]


def is_sep_row(line: str) -> bool:
    return bool(re.fullmatch(r"\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?", line.strip()))


def parse_md_table(lines: list[str]) -> tuple[list[str], list[str], list[list[str]]]:
    """Return (header, aligns, rows). aligns: 'l' | 'r' | 'c'."""
    header = split_row(lines[0])
    aligns = []
    for cell in split_row(lines[1]):
        c = cell.strip()
        if c.startswith(":") and c.endswith(":"):
            aligns.append("c")
        elif c.endswith(":"):
            aligns.append("r")
        else:
            aligns.append("l")
    rows = [split_row(ln) for ln in lines[2:]]
    n = len(header)
    aligns = (aligns + ["l"] * n)[:n]
    rows = [(r + [""] * n)[:n] for r in rows]
    return header, aligns, rows


def drop_pandas_index(header, aligns, rows):
    """to_markdown() writes the DataFrame index as a first, unnamed column. Drop it when it is
    the default 0..n-1 RangeIndex; keep it when it carries labels (e.g. E17a)."""
    if header and header[0] == "" and rows and all(re.fullmatch(r"\d+", r[0]) for r in rows):
        return header[1:], aligns[1:], [r[1:] for r in rows]
    return header, aligns, rows


def cell_text(s: str) -> str:
    s = s.strip()
    if s.lower() in {"nan", "none"}:
        s = "\u2014"                 # em dash for missing
    # allow long snake_case headers/labels to break at underscores
    return esc(s).replace("\\_", "\\_#sym.zws;")


CHAR_EM = 0.55                     # average glyph width as a fraction of the font size
TEXT_COL_CAP = 42                  # max "character units" a text column claims before wrapping


def _numeric(cells: list[str]) -> bool:
    return all(re.fullmatch(r"[-+]?[\d,.]+%?|nan|", c.strip()) for c in cells)


def _units(header: str, cells: list[str], numeric: bool) -> float:
    """Approximate natural width of a column in characters. Headers break at underscores,
    so a header counts as its longest underscore-separated piece (bold: +10%)."""
    hdr = max((len(seg) for seg in header.split("_")), default=0) * 1.1
    val = max((len(c) for c in cells), default=0)
    if numeric:
        val *= 0.85                    # digits are narrower than letters
    else:
        val = min(val, TEXT_COL_CAP)
    return max(hdr, val, 3) + 1.5      # + cell inset


def table_to_typst(header, aligns, rows, font_pt: float, avail_pt: float) -> str:
    ncol = len(header)
    amap = {"l": "left", "r": "right", "c": "center"}
    align = "(" + ", ".join(amap[a] for a in aligns) + ("," if ncol == 1 else "") + ")"
    cols = [[r[j] for r in rows] for j in range(ncol)]
    numeric = [_numeric(c) for c in cols]
    units = [_units(header[j], cols[j], numeric[j]) for j in range(ncol)]
    total = sum(units)
    if total * CHAR_EM * font_pt <= avail_pt:
        columns = str(ncol)                       # fits: let Typst size to content
    else:
        # shrink the font until the proportional layout fits, but not below 6.5pt
        font_pt = max(6.5, min(font_pt, avail_pt / (total * CHAR_EM)))
        columns = "(" + ", ".join(f"{u:.1f}fr" for u in units) + ("," if ncol == 1 else "") + ")"
    hdr = ", ".join("[*" + cell_text(h) + "*]" for h in header)
    body = ",\n    ".join(", ".join("[" + cell_text(c) + "]" for c in r) for r in rows)
    return (
        f"#block(breakable: true, width: 100%)[\n"
        f"#set text(size: {font_pt:.1f}pt)\n"
        f"#table(\n  columns: {columns},\n  align: {align},\n"
        f"  stroke: (x, y) => if y == 0 {{ (bottom: 0.5pt + black) }} else {{ none }},\n"
        f"  table.header({hdr}),\n"
        f"    {body}\n)\n]\n"
    )


def md_to_typst(md: str, avail_pt: float = PORTRAIT_PT) -> str:
    """Small Markdown-to-Typst converter for the narrative and table files."""
    lines = md.splitlines()
    out: list[str] = []
    para: list[str] = []
    i = 0

    def flush_para():
        if para:
            out.append(" ".join(inline(ln.strip()) for ln in para) + "\n")
            para.clear()

    while i < len(lines):
        ln = lines[i]
        stripped = ln.strip()
        if not stripped:
            flush_para()
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            flush_para()
            out.append("=" * len(m.group(1)) + " " + inline(m.group(2).strip()) + "\n")
            i += 1
            continue
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            flush_para()
            out.append("#v(0.5em)\n")
            i += 1
            continue
        if stripped.startswith("|") and i + 1 < len(lines) and is_sep_row(lines[i + 1]):
            flush_para()
            j = i
            while j < len(lines) and lines[j].strip().startswith("|"):
                j += 1
            header, aligns, rows = drop_pandas_index(*parse_md_table(lines[i:j]))
            out.append(table_to_typst(header, aligns, rows, table_font_pt(len(header)), avail_pt))
            i = j
            continue
        m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", ln)
        if m:
            flush_para()
            while i < len(lines):
                m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", lines[i])
                if not m:
                    break
                depth = len(m.group(1).expandtabs(4)) // 2
                marker = "-" if m.group(2) in "-*+" else "+"
                item = [m.group(3)]
                i += 1
                # continuation lines of the same item (indented, not a new marker)
                while i < len(lines) and lines[i].strip() and lines[i].startswith(" ") \
                        and not re.match(r"^\s*([-*+]|\d+[.)])\s+", lines[i]):
                    item.append(lines[i].strip())
                    i += 1
                out.append("  " * depth + marker + " " + inline(" ".join(item)) + "\n")
            out.append("\n")
            continue
        para.append(ln)
        i += 1
    flush_para()
    return "\n".join(out)


def table_font_pt(ncols: int) -> float:
    if ncols <= 7:
        return 9
    if ncols <= 10:
        return 8
    return 7


# ---------------------------------------------------------------------------
# Appendix assembly
# ---------------------------------------------------------------------------
def appendix_order() -> list[str]:
    text = OUTLINE.read_text(encoding="utf-8")
    m = re.search(r"^## Appendix order\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        sys.exit(f"ERROR: no '## Appendix order' section in {OUTLINE}")
    ids = EXHIBIT_ID.findall(m.group(1))
    seen, ordered = set(), []
    for e in ids:
        if e not in seen:
            seen.add(e)
            ordered.append(e)
    if not ordered:
        sys.exit("ERROR: the '## Appendix order' list is empty")
    return ordered


def exhibit_files(folder: Path, suffix: str) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for p in sorted(folder.glob(f"E*{suffix}")):
        m = re.match(r"(E\d{2}[a-z]?)_", p.name)
        if m:
            if m.group(1) in found:
                print(f"WARNING: two {suffix} files for {m.group(1)}: {found[m.group(1)].name} "
                      f"and {p.name}; using the first")
                continue
            found[m.group(1)] = p
    return found


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return (1600, 1000)
    w, h = struct.unpack(">II", head[16:24])
    return w, h


def figure_block(png: Path) -> str:
    w, h = png_size(png)
    rel = "/" + png.relative_to(ROOT).as_posix()
    natural_h = PAGE_WIDTH_IN * h / max(w, 1)
    if natural_h <= MAX_FIG_HEIGHT_IN:
        return f"#image({typst_str(rel)}, width: 100%)\n"
    return (f"#align(center)[#image({typst_str(rel)}, width: 100%, "
            f"height: {MAX_FIG_HEIGHT_IN}in, fit: \"contain\")]\n")


def table_block(md_path: Path, promote_title: bool = False) -> tuple[str, int, int]:
    """Convert one outputs/tables/*.md file. Returns (typst, ncols, nrows). With promote_title
    the table's own "### E##. title" line becomes the exhibit's level-2 heading."""
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    ncols = nrows = 0
    for k, ln in enumerate(lines):
        if ln.strip().startswith("|") and k + 1 < len(lines) and is_sep_row(lines[k + 1]):
            header, _, rows = drop_pandas_index(*parse_md_table(
                [l for l in lines[k:] if l.strip().startswith("|")]))
            ncols, nrows = len(header), len(rows)
            break
    landscape = ncols >= LANDSCAPE_MIN_COLS
    body = md_to_typst(text, LANDSCAPE_PT if landscape else PORTRAIT_PT)
    if promote_title and body.startswith("=== "):
        body = "==" + body[3:]
    return body, ncols, nrows


def build_appendix(order: list[str]) -> tuple[str, list[str], list[str], list[str]]:
    pngs = exhibit_files(EXHIBITS, ".png")
    tables = exhibit_files(TABLES, ".md")
    placed, missing, warnings = [], [], []
    for extra in sorted(set(pngs) | set(tables)):
        if extra not in order:
            kinds = [k for k, d in (("PNG", pngs), ("table", tables)) if extra in d]
            warnings.append(f"{extra} ({'+'.join(kinds)}) is in outputs/ but not in the "
                            f"outline's Appendix order list")
    parts = ["#pagebreak()\n= Appendix: exhibits\n",
             "Exhibits appear in the order listed in the narrative outline. Each figure carries "
             "its own title, sample statement and source note; each table is reproduced from "
             "#raw(\"outputs/tables/\") as written by the analysis scripts.\n"]
    for eid in order:
        png, tbl = pngs.get(eid), tables.get(eid)
        if png is None and tbl is None:
            missing.append(eid)
            continue
        # figure exhibits get a "== E##" heading (the PNG carries its own title); table-only
        # exhibits use the table's "E##. title" line as the heading instead
        block = [f"== {eid}\n"] if png is not None else []
        ncols = nrows = 0
        if png is not None:
            block.append(figure_block(png))
        if tbl is not None:
            tb, ncols, nrows = table_block(tbl, promote_title=png is None)
            block.append(tb)
        body = "".join(block)
        if ncols >= LANDSCAPE_MIN_COLS:
            body = ('#page(flipped: true, margin: 0.75in)[\n' + body + ']\n')
        else:
            # a short table-only exhibit stays on one page with its notes; anything that
            # might exceed a page (a figure plus table, or a long table) is allowed to break
            keep = "false" if (png is None and nrows <= 15) else "true"
            body = f"#block(breakable: {keep})[\n" + body + "]\n#v(1em)\n"
        parts.append(body)
        placed.append(eid + ("" if png is None else " fig") + ("" if tbl is None else " tbl"))
    return "\n".join(parts), placed, missing, warnings


# ---------------------------------------------------------------------------
# Compile and count pages
# ---------------------------------------------------------------------------
def compile_typ(typ_path: Path, pdf_path: Path) -> None:
    import typst
    typst.compile(str(typ_path), output=str(pdf_path), root=str(ROOT))


def pdf_pages(pdf_path: Path) -> int:
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(pdf_path)).pages)
    except ImportError:
        data = pdf_path.read_bytes()
        return len(re.findall(rb"/Type\s*/Page[^s]", data))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--draft", type=Path, default=DRAFT, help="narrative Markdown file")
    ap.add_argument("--out", type=Path, default=PDF_OUT, help="output PDF path")
    ap.add_argument("--max-pages", type=int, default=NARRATIVE_MAX_PAGES)
    args = ap.parse_args(argv)

    if not args.draft.exists():
        sys.exit(f"ERROR: narrative source {args.draft} not found")
    BUILD.mkdir(exist_ok=True)

    narrative = md_to_typst(args.draft.read_text(encoding="utf-8"))
    order = appendix_order()
    appendix, placed, missing, warnings = build_appendix(order)

    # 1. narrative alone -> page count
    narr_typ = BUILD / "narrative_only.typ"
    narr_pdf = BUILD / "narrative_only.pdf"
    narr_typ.write_text(PREAMBLE + "\n" + narrative, encoding="utf-8")
    compile_typ(narr_typ, narr_pdf)
    n_narr = pdf_pages(narr_pdf)

    # 2. full document
    full_typ = BUILD / "report.typ"
    full_typ.write_text(PREAMBLE + "\n" + narrative + "\n" + appendix, encoding="utf-8")
    compile_typ(full_typ, args.out)
    n_total = pdf_pages(args.out)

    print("=== Build summary ===")
    print(f"Narrative source : {args.draft}")
    print(f"Narrative pages  : {n_narr} (maximum {args.max_pages})")
    print(f"Appendix pages   : {n_total - n_narr}")
    print(f"Total pages      : {n_total}")
    print(f"Exhibits placed  : {len(placed)} of {len(order)} in the outline list")
    print("  " + ", ".join(placed))
    print(f"Exhibits missing : {len(missing)}" + (" - " + ", ".join(missing) if missing else ""))
    for w in warnings:
        print("WARNING: " + w)
    print(f"Typst source     : {full_typ}")
    print(f"PDF              : {args.out}")

    failed = False
    if missing:
        print(f"ERROR: {len(missing)} exhibit id(s) in the outline list have neither a PNG nor "
              f"a table on disk: {', '.join(missing)}")
        failed = True
    if n_narr > args.max_pages:
        print(f"ERROR: the narrative runs to {n_narr} pages; the prompt allows at most "
              f"{args.max_pages}. Cut {args.draft.name} and rebuild.")
        failed = True
    if failed:
        print("BUILD FAILED")
        return 1
    print("BUILD OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
