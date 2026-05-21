"""
Build AgeCareAI_Full_Report.docx from REPORT.md.
Parses the markdown file directly — edit REPORT.md, re-run this script.
Run: python3 build_report.py
"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import re, os

HERE     = os.path.dirname(__file__)
MD_PATH  = os.path.join(HERE, "REPORT.md")
OUT_PATH = os.path.join(HERE, "AgeCareAI_Full_Report.docx")

NAVY      = RGBColor(0x1E, 0x3A, 0x5F)
BLUE      = RGBColor(0x1F, 0x49, 0x9B)
MID_BLUE  = RGBColor(0x2E, 0x6B, 0xC8)
DARK_GREY = RGBColor(0x2D, 0x2D, 0x2D)
MID_GREY  = RGBColor(0x55, 0x55, 0x55)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_BG  = RGBColor(0xF0, 0xF4, 0xFA)


# ── XML helpers ───────────────────────────────────────────────────────────────

def _set_cell_bg(cell, rgb):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), "{:02X}{:02X}{:02X}".format(rgb[0], rgb[1], rgb[2]))
    tcPr.append(shd)


def _add_divider(doc):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(4)
    pBdr = OxmlElement("w:pBdr")
    bot  = OxmlElement("w:bottom")
    bot.set(qn("w:val"),   "single")
    bot.set(qn("w:sz"),    "6")
    bot.set(qn("w:space"), "1")
    bot.set(qn("w:color"), "1F499B")
    pBdr.append(bot)
    p._p.get_or_add_pPr().append(pBdr)


# ── Inline markup: **bold** and `code` ───────────────────────────────────────

def _add_inline(para, text, size=10.5, color=DARK_GREY, bold=False):
    for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
        if not part:
            continue
        run = para.add_run()
        run.font.size  = Pt(size)
        run.font.color.rgb = color
        if part.startswith("**") and part.endswith("**"):
            run.text = part[2:-2]
            run.bold = True
        elif part.startswith("`") and part.endswith("`"):
            run.text = part[1:-1]
            run.font.name  = "Courier New"
            run.font.size  = Pt(size - 0.5)
            run.font.color.rgb = RGBColor(0xC7, 0x25, 0x4E)
        else:
            run.text = part
            run.bold = bold


# ── Table builder ─────────────────────────────────────────────────────────────

def _build_table(doc, header, rows):
    ncols = len(header)
    tbl = doc.add_table(rows=1 + len(rows), cols=ncols)
    tbl.style     = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT

    for j, txt in enumerate(header):
        cell = tbl.rows[0].cells[j]
        _set_cell_bg(cell, NAVY)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after  = Pt(2)
        run = p.add_run(txt.strip().strip("*"))
        run.bold = True
        run.font.size  = Pt(9)
        run.font.color.rgb = WHITE
        run.font.name  = "Calibri"

    for i, row_data in enumerate(rows):
        bg = LIGHT_BG if i % 2 == 0 else WHITE
        for j, txt in enumerate(row_data):
            cell = tbl.rows[i + 1].cells[j]
            _set_cell_bg(cell, bg)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after  = Pt(1)
            _add_inline(p, txt.strip(), size=9)

    doc.add_paragraph().paragraph_format.space_after = Pt(2)


# ── Code block ────────────────────────────────────────────────────────────────

def _add_code_block(doc, lines):
    for line in lines:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent   = Cm(0.6)
        p.paragraph_format.space_before  = Pt(0)
        p.paragraph_format.space_after   = Pt(0)
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"),   "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"),  "F3F4F6")
        p._p.get_or_add_pPr().append(shd)
        run = p.add_run(line)
        run.font.name  = "Courier New"
        run.font.size  = Pt(8.5)
        run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


# ── Paragraph helpers ─────────────────────────────────────────────────────────

def _add_body(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after  = Pt(5)
    _add_inline(p, text)


def _add_bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent  = Cm(0.4 + level * 0.4)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(2)
    _add_inline(p, text)


def _add_numbered(doc, text):
    p = doc.add_paragraph(style="List Number")
    p.paragraph_format.left_indent  = Cm(0.4)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(2)
    _add_inline(p, text)


def _add_blockquote(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent  = Cm(0.8)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(4)
    _add_inline(p, text, color=MID_GREY)


# ── Style configuration ───────────────────────────────────────────────────────

def _configure_styles(doc):
    n = doc.styles["Normal"]
    n.font.name  = "Calibri"
    n.font.size  = Pt(10.5)
    n.font.color.rgb = DARK_GREY

    specs = [
        (1, 18, NAVY,     True,  12, 3),
        (2, 13, BLUE,     True,  8,  2),
        (3, 11, MID_BLUE, True,  6,  1),
        (4, 10.5, DARK_GREY, True, 4, 1),
    ]
    for lvl, sz, col, bd, sb, sa in specs:
        try:
            h = doc.styles[f"Heading {lvl}"]
        except KeyError:
            continue
        h.font.name  = "Calibri"
        h.font.size  = Pt(sz)
        h.font.color.rgb = col
        h.font.bold  = bd
        h.paragraph_format.space_before    = Pt(sb)
        h.paragraph_format.space_after     = Pt(sa)
        h.paragraph_format.keep_with_next  = True


# ── Cover page ────────────────────────────────────────────────────────────────

def _add_cover(doc):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(72)
    r = p.add_run("AgeCareAI")
    r.font.name  = "Calibri"
    r.font.size  = Pt(36)
    r.font.bold  = True
    r.font.color.rgb = NAVY

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("Autonomous Elder Care Platform — Singapore")
    r2.font.size  = Pt(15)
    r2.font.color.rgb = BLUE
    r2.italic = True

    doc.add_paragraph()

    for label, value in [
        ("Date",        "22 May 2026"),
        ("Prepared by", "AgeCareAI Development Team"),
        ("Repository",  "https://github.com/queenie9216/AgeCareAI-"),
    ]:
        p3 = doc.add_paragraph()
        p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r3 = p3.add_run(f"{label}:  ")
        r3.bold = True
        r3.font.color.rgb = NAVY
        r3.font.size = Pt(10.5)
        r4 = p3.add_run(value)
        r4.font.color.rgb = DARK_GREY
        r4.font.size = Pt(10.5)

    doc.add_page_break()


# ── Markdown parser ───────────────────────────────────────────────────────────

def _parse_md_table(block_lines):
    """Return (header_cells, data_rows) from raw markdown table lines."""
    header, rows = [], []
    for line in block_lines:
        if re.match(r"^\s*\|[-:| ]+\|\s*$", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not header:
            header = cells
        else:
            rows.append(cells)
    return header, rows


def _render_md(doc, md_text):
    lines = md_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]

        # ── Page break marker
        if line.strip() == "<!-- pagebreak -->":
            doc.add_page_break()
            i += 1
            continue

        # ── Headings
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            lvl  = len(m.group(1))
            text = m.group(2).strip()
            doc.add_heading(text, level=lvl)
            if lvl == 1:
                _add_divider(doc)
            i += 1
            continue

        # ── Horizontal rule (--- alone)
        if re.match(r"^---+\s*$", line):
            _add_divider(doc)
            i += 1
            continue

        # ── Fenced code block
        if line.strip().startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            _add_code_block(doc, code_lines)
            i += 1
            continue

        # ── Markdown table
        if line.strip().startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            hdr, rows = _parse_md_table(block)
            if hdr:
                _build_table(doc, hdr, rows)
            continue

        # ── Bullet list
        m = re.match(r"^(\s*)-\s+(.*)", line)
        if m:
            level = len(m.group(1)) // 2
            _add_bullet(doc, m.group(2), level=level)
            i += 1
            continue

        # ── Numbered list
        m = re.match(r"^\d+\.\s+(.*)", line)
        if m:
            _add_numbered(doc, m.group(1))
            i += 1
            continue

        # ── Blockquote
        m = re.match(r"^>\s+(.*)", line)
        if m:
            _add_blockquote(doc, m.group(1))
            i += 1
            continue

        # ── Blank line or metadata header (first 3 lines)
        stripped = line.strip()
        if not stripped or stripped.startswith("**Date:**"):
            i += 1
            continue

        # ── Body paragraph
        _add_body(doc, stripped)
        i += 1


# ── Main ─────────────────────────────────────────────────────────────────────

def build():
    with open(MD_PATH, encoding="utf-8") as f:
        md = f.read()

    doc = Document()
    for sec in doc.sections:
        sec.top_margin    = Cm(2.0)
        sec.bottom_margin = Cm(2.0)
        sec.left_margin   = Cm(2.5)
        sec.right_margin  = Cm(2.5)

    _configure_styles(doc)
    _add_cover(doc)
    _render_md(doc, md)

    doc.save(OUT_PATH)
    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    build()
