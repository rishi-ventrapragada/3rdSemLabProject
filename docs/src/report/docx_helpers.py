"""
Formatting primitives for docs/Project_Report.docx, following LAB_PROJECT_FORMAT.docx:
A4, Times New Roman, main heading 16 pt bold uppercase, chapter heading 14 pt bold, section heading
12 pt bold, body 12 pt, 1.5 line spacing, justified, margins L 1.5" R 1" T 1" B 1", Roman page
numbers for preliminary pages and Arabic for chapters. Every figure and table is numbered per
chapter and recorded so the lists of figures and tables can be generated.
"""

import copy
import re
from pathlib import Path

from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image

FONT = "Times New Roman"
TEXT_WIDTH_IN = 8.27 - 1.5 - 1.0          # A4 minus left and right margins
MAX_FIGURE_HEIGHT_IN = 7.4                 # leaves room for the caption and header
ROTATED_MAX_HEIGHT_IN = 8.3
NATIVE_DPI = 170                           # PlantUML renders at this dpi (docs/src/diagrams/_style.iuml)
HEADER_BLUE = RGBColor(0x00, 0x4A, 0xAC)
TABLE_HEAD_FILL = "D9E2F3"

SECTION_ORDER = ["headerReference", "footerReference", "footnotePr", "endnotePr", "type", "pgSz", "pgMar",
                 "paperSrc", "pgBorders", "lnNumType", "pgNumType", "cols", "formProt", "vAlign", "noEndnote",
                 "titlePg", "textDirection", "bidi", "rtlGutter", "docGrid", "printerSettings"]


# ------------------------------------------------------------------------------------------------
# Low-level XML helpers
# ------------------------------------------------------------------------------------------------
def set_section_child(sect_pr, element):
    """Insert or replace a child of w:sectPr while keeping the schema order Word requires."""
    name = element.tag.split("}")[1]
    existing = sect_pr.find(qn(f"w:{name}"))
    if existing is not None:
        sect_pr.replace(existing, element)
        return
    position = SECTION_ORDER.index(name)
    for index, child in enumerate(list(sect_pr)):
        child_name = child.tag.split("}")[1]
        if child_name in SECTION_ORDER and SECTION_ORDER.index(child_name) > position:
            child.addprevious(element)
            return
    sect_pr.append(element)


def page_numbering(section, fmt, start=None):
    element = OxmlElement("w:pgNumType")
    element.set(qn("w:fmt"), fmt)
    if start is not None:
        element.set(qn("w:start"), str(start))
    set_section_child(section._sectPr, element)


def page_border(section):
    borders = OxmlElement("w:pgBorders")
    borders.set(qn("w:offsetFrom"), "page")
    for side in ("top", "left", "bottom", "right"):
        line = OxmlElement(f"w:{side}")
        line.set(qn("w:val"), "single")
        line.set(qn("w:sz"), "6")
        line.set(qn("w:space"), "24")
        line.set(qn("w:color"), "000000")
        borders.append(line)
    set_section_child(section._sectPr, borders)


def report_margins(section):
    section.page_width, section.page_height = Inches(8.27), Inches(11.69)
    section.left_margin, section.right_margin = Inches(1.5), Inches(1.0)
    section.top_margin, section.bottom_margin = Inches(1.0), Inches(1.0)
    section.header_distance, section.footer_distance = Inches(0.4), Inches(0.45)


def add_field(paragraph, instruction):
    """A Word field such as PAGE; LibreOffice and Word both evaluate it."""
    run = paragraph.add_run()
    for kind, text in (("begin", None), (None, instruction), ("separate", None), (None, "1"), ("end", None)):
        if kind:
            element = OxmlElement("w:fldChar")
            element.set(qn("w:fldCharType"), kind)
        elif text == instruction:
            element = OxmlElement("w:instrText")
            element.set(qn("xml:space"), "preserve")
            element.text = f" {instruction} "
        else:
            element = OxmlElement("w:t")
            element.text = text
        run._r.append(element)
    style_run(run, size=11)
    return run


def shade(cell_or_paragraph_pr, fill):
    element = OxmlElement("w:shd")
    element.set(qn("w:val"), "clear")
    element.set(qn("w:color"), "auto")
    element.set(qn("w:fill"), fill)
    cell_or_paragraph_pr.append(element)


def style_run(run, size=12, bold=None, italic=None, font=FONT, color=None):
    run.font.name = font
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), font)
    run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color
    return run


def keep_with_next(paragraph):
    paragraph.paragraph_format.keep_with_next = True


def outline_level(paragraph, level):
    element = OxmlElement("w:outlineLvl")
    element.set(qn("w:val"), str(level))
    paragraph._p.get_or_add_pPr().append(element)


# ------------------------------------------------------------------------------------------------
# Inline markup: **bold**, `code`
# ------------------------------------------------------------------------------------------------
TOKEN = re.compile(r"(\*\*.+?\*\*|`[^`]+`)")


def add_rich_text(paragraph, text, size=12, base_bold=False):
    for part in TOKEN.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            style_run(paragraph.add_run(part[2:-2]), size=size, bold=True)
        elif part.startswith("`") and part.endswith("`"):
            style_run(paragraph.add_run(part[1:-1]), size=size - 1, font="Consolas", bold=base_bold)
        else:
            style_run(paragraph.add_run(part), size=size, bold=base_bold)


# ------------------------------------------------------------------------------------------------
# The report builder
# ------------------------------------------------------------------------------------------------
class Report:
    def __init__(self, doc, build_dir):
        self.doc = doc
        self.build_dir = Path(build_dir)
        self.build_dir.mkdir(parents=True, exist_ok=True)
        self.chapter_no = 0
        self.figure_no = 0
        self.table_no = 0
        self.toc = []            # (level, text)  level 1 = chapter, 2 = section
        self.figures = []        # "Figure 4.1: ..."
        self.tables = []         # "Table 3.1: ..."

    # -- structure ------------------------------------------------------------------------------
    def start_chapters(self, header_logo):
        """New section for the chapters: Arabic numbering from 1, VJIT header, page border."""
        section = self.doc.add_section(WD_SECTION.NEW_PAGE)
        report_margins(section)
        page_numbering(section, "decimal", start=1)
        page_border(section)
        self._header(section, header_logo)
        footer = section.footer
        footer.is_linked_to_previous = False
        paragraph = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        paragraph.text = ""
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_field(paragraph, "PAGE")
        self.first_chapter = True

    def _header(self, section, logo):
        header = section.header
        header.is_linked_to_previous = False
        for paragraph in header.paragraphs:
            paragraph.text = ""
        table = header.add_table(rows=1, cols=2, width=Inches(TEXT_WIDTH_IN))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.columns[0].width = Inches(0.75)
        table.columns[1].width = Inches(TEXT_WIDTH_IN - 0.75)
        logo_cell, text_cell = table.rows[0].cells
        logo_cell.width, text_cell.width = Inches(0.75), Inches(TEXT_WIDTH_IN - 0.75)
        logo_cell.paragraphs[0].add_run().add_picture(str(logo), height=Inches(0.62))
        first = text_cell.paragraphs[0]
        first.alignment = WD_ALIGN_PARAGRAPH.CENTER
        style_run(first.add_run("VIDYA JYOTHI INSTITUTE OF TECHNOLOGY"), size=15, bold=True)
        for line in ("Department of Computer Science & Engineering", "(Data Science)"):
            paragraph = text_cell.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            style_run(paragraph.add_run(line), size=11, bold=True, italic=True)
        for cell in (logo_cell, text_cell):
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.space_before = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.0
        rule = header.add_paragraph()
        bottom = OxmlElement("w:pBdr")
        line = OxmlElement("w:bottom")
        for key, value in (("val", "single"), ("sz", "8"), ("space", "1"), ("color", "000000")):
            line.set(qn(f"w:{key}"), value)
        bottom.append(line)
        rule._p.get_or_add_pPr().append(bottom)
        rule.paragraph_format.space_after = Pt(0)

    def chapter(self, number, title):
        self.chapter_no, self.figure_no, self.table_no = number, 0, 0
        paragraph = self.doc.add_paragraph()
        if not getattr(self, "first_chapter", False):
            paragraph.paragraph_format.page_break_before = True
        self.first_chapter = False
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_after = Pt(18)
        text = f"CHAPTER {number}: {title.upper()}" if number else title.upper()
        style_run(paragraph.add_run(text), size=16, bold=True)
        outline_level(paragraph, 0)
        keep_with_next(paragraph)
        self.toc.append((1, f"Chapter {number}: {title}" if number else title))

    def unnumbered_main(self, title):
        """References and appendices: a 16 pt main heading on a new page."""
        letter = title.split()[1][0] if title.startswith("Appendix") else title[:1]
        self.chapter_no, self.figure_no, self.table_no = letter, 0, 0
        paragraph = self.doc.add_paragraph()
        paragraph.paragraph_format.page_break_before = True
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_after = Pt(18)
        style_run(paragraph.add_run(title.upper()), size=16, bold=True)
        outline_level(paragraph, 0)
        keep_with_next(paragraph)
        self.toc.append((1, title))

    def h2(self, text, toc=True, new_page=False):
        paragraph = self.doc.add_paragraph()
        paragraph.paragraph_format.page_break_before = new_page
        paragraph.paragraph_format.space_before = Pt(14)
        paragraph.paragraph_format.space_after = Pt(6)
        style_run(paragraph.add_run(text), size=14, bold=True)
        outline_level(paragraph, 1)
        keep_with_next(paragraph)
        if toc:
            self.toc.append((2, text))

    def h3(self, text, new_page=False):
        paragraph = self.doc.add_paragraph()
        paragraph.paragraph_format.page_break_before = new_page
        paragraph.paragraph_format.space_before = Pt(10)
        paragraph.paragraph_format.space_after = Pt(4)
        style_run(paragraph.add_run(text), size=12, bold=True)
        outline_level(paragraph, 2)
        keep_with_next(paragraph)

    # -- text -----------------------------------------------------------------------------------
    def p(self, text, align="justify", size=12, keep=False, space_after=6):
        paragraph = self.doc.add_paragraph()
        fmt = paragraph.paragraph_format
        fmt.line_spacing = 1.5
        fmt.space_after = Pt(space_after)
        fmt.alignment = {"justify": WD_ALIGN_PARAGRAPH.JUSTIFY, "center": WD_ALIGN_PARAGRAPH.CENTER,
                         "left": WD_ALIGN_PARAGRAPH.LEFT}[align]
        add_rich_text(paragraph, text, size=size)
        if keep:
            keep_with_next(paragraph)
        return paragraph

    def bullets(self, items, numbered=False, size=12):
        for index, item in enumerate(items, 1):
            paragraph = self.doc.add_paragraph()
            fmt = paragraph.paragraph_format
            fmt.left_indent = Inches(0.4)
            fmt.first_line_indent = Inches(-0.25)
            fmt.line_spacing = 1.5
            fmt.space_after = Pt(0)
            fmt.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            style_run(paragraph.add_run(f"{index}." if numbered else "•"), size=size)
            style_run(paragraph.add_run("\t"), size=size)
            fmt.tab_stops.add_tab_stop(Inches(0.4))
            add_rich_text(paragraph, item, size=size)
        if items:
            self.doc.paragraphs[-1].paragraph_format.space_after = Pt(6)

    def code(self, text, size=9):
        """A shaded block of real source code (single spacing, Consolas)."""
        lines = text.rstrip("\n").split("\n")
        for index, line in enumerate(lines):
            paragraph = self.doc.add_paragraph()
            fmt = paragraph.paragraph_format
            fmt.line_spacing = 1.0
            fmt.space_after = Pt(0)
            fmt.space_before = Pt(4) if index == 0 else Pt(0)
            fmt.left_indent = Inches(0.1)
            fmt.alignment = WD_ALIGN_PARAGRAPH.LEFT
            fmt.keep_together = True
            if index < len(lines) - 1:
                keep_with_next(paragraph)
            shade(paragraph._p.get_or_add_pPr(), "F2F4F7")
            style_run(paragraph.add_run(line if line else " "), size=size, font="Consolas")
        self.doc.paragraphs[-1].paragraph_format.space_after = Pt(8)

    # -- captions, tables, figures ----------------------------------------------------------------
    def _caption(self, kind, title, before):
        if kind == "Figure":
            self.figure_no += 1
            label = f"Figure {self.chapter_no}.{self.figure_no}: {title}"
            self.figures.append(label)
        else:
            self.table_no += 1
            label = f"Table {self.chapter_no}.{self.table_no}: {title}"
            self.tables.append(label)
        paragraph = self.doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_before = Pt(4)
        paragraph.paragraph_format.space_after = Pt(10 if kind == "Figure" else 4)
        paragraph.paragraph_format.line_spacing = 1.15
        style_run(paragraph.add_run(label), size=11, bold=True)
        if before:
            keep_with_next(paragraph)
        return paragraph

    def table(self, headers, rows, widths, caption, size=10, header_fill=TABLE_HEAD_FILL, bold_first_col=False):
        self._caption("Table", caption, before=True)
        table = self.doc.add_table(rows=1, cols=len(headers))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        self._borders(table)
        total = sum(widths)
        scale = min(1.0, TEXT_WIDTH_IN / total)
        widths = [Inches(w * scale) for w in widths]
        for cell, text, width in zip(table.rows[0].cells, headers, widths):
            self._cell(cell, text, size, bold=True, width=width)
            shade(cell._tc.get_or_add_tcPr(), header_fill)
        self._repeat_header(table.rows[0])
        for row_values in rows:
            cells = table.add_row().cells
            for index, (cell, value, width) in enumerate(zip(cells, row_values, widths)):
                self._cell(cell, "" if value is None else str(value), size,
                           bold=bold_first_col and index == 0, width=width)
        set_table_widths(table, widths)
        for row in table.rows:
            no_split = OxmlElement("w:cantSplit")
            row._tr.get_or_add_trPr().append(no_split)
        spacer = self.doc.add_paragraph()
        spacer.paragraph_format.space_after = Pt(4)
        spacer.paragraph_format.line_spacing = 1.0
        return table

    def kv_table(self, pairs, caption, widths=(1.6, 4.1), size=10.5):
        """Two-column 'field | value' table, as used for each use case and test case in the sample."""
        return self.table(["Field", "Description"], pairs, list(widths), caption, size=size, bold_first_col=True)

    @staticmethod
    def _borders(table):
        borders = OxmlElement("w:tblBorders")
        for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
            line = OxmlElement(f"w:{side}")
            line.set(qn("w:val"), "single")
            line.set(qn("w:sz"), "4")
            line.set(qn("w:space"), "0")
            line.set(qn("w:color"), "808080")
            borders.append(line)
        set_tbl_pr_child(table._tbl.tblPr, borders)

    @staticmethod
    def _repeat_header(row):
        element = OxmlElement("w:tblHeader")
        element.set(qn("w:val"), "true")
        row._tr.get_or_add_trPr().append(element)

    @staticmethod
    def _cell(cell, text, size, bold=False, width=None):
        if width is not None:
            cell.width = width
        paragraph = cell.paragraphs[0]
        paragraph.paragraph_format.space_after = Pt(1)
        paragraph.paragraph_format.space_before = Pt(1)
        paragraph.paragraph_format.line_spacing = 1.0
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        lines = text.split("\n")
        for index, line in enumerate(lines):
            if index:
                paragraph = cell.add_paragraph()
                paragraph.paragraph_format.space_after = Pt(1)
                paragraph.paragraph_format.line_spacing = 1.0
            add_rich_text(paragraph, line, size=size, base_bold=bold)

    def figure(self, image_path, caption, max_width_in=TEXT_WIDTH_IN, max_height_in=MAX_FIGURE_HEIGHT_IN,
               native_dpi=None, rotate_if_wide=True):
        """
        Inserts an image scaled to fit the text area. A wide diagram that would shrink below 60% of its
        native size is rotated 90 degrees onto its own page when that makes it noticeably larger.
        """
        image_path = Path(image_path)
        with Image.open(image_path) as image:
            width_px, height_px = image.size
            dpi = native_dpi or 96
            w_in, h_in = width_px / dpi, height_px / dpi
            cap = 1.0 if native_dpi else 99
            upright = min(max_width_in / w_in, max_height_in / h_in, cap)
            turned = min(max_width_in / h_in, ROTATED_MAX_HEIGHT_IN / w_in, cap)
            # Rotate a wide diagram onto its own page when that makes it at least 25% larger and it would
            # otherwise be printed below 60% of its native size (text would be too small to read).
            rotate = rotate_if_wide and w_in > h_in and upright < 0.6 and turned >= 1.25 * upright
            if rotate:
                rotated = self.build_dir / f"rot_{image_path.name}"
                image.rotate(90, expand=True).save(rotated)
                image_path, (width_px, height_px) = rotated, (height_px, width_px)
        if rotate:
            max_height_in = ROTATED_MAX_HEIGHT_IN
        width_in = width_px / (native_dpi or 96)
        height_in = height_px / (native_dpi or 96)
        scale = min(max_width_in / width_in, max_height_in / height_in, 1.0 if native_dpi else 99)
        width_in, height_in = width_in * scale, height_in * scale
        if not native_dpi:  # screenshots: always use the full text width (they are 1280 px wide)
            scale = min(max_width_in / (width_px / 96), max_height_in / (height_px / 96))
            width_in, height_in = width_px / 96 * scale, height_px / 96 * scale
        paragraph = self.doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_before = Pt(6)
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph.paragraph_format.keep_with_next = True
        if rotate:
            paragraph.paragraph_format.page_break_before = True
        paragraph.add_run().add_picture(str(image_path), width=Inches(width_in), height=Inches(height_in))
        caption_paragraph = self._caption("Figure", caption + (" (rotated to fit the page)" if rotate else ""),
                                          before=False)
        if rotate:
            caption_paragraph.add_run().add_break(WD_BREAK.PAGE)
        return paragraph


TBL_PR_ORDER = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize", "tblStyleColBandSize",
                "tblW", "jc", "tblCellSpacing", "tblInd", "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook",
                "tblCaption", "tblDescription"]


def set_tbl_pr_child(tbl_pr, element):
    """Insert or replace a child of w:tblPr in the order the schema requires (Word rejects other orders)."""
    name = element.tag.split("}")[1]
    existing = tbl_pr.find(qn(f"w:{name}"))
    if existing is not None:
        tbl_pr.replace(existing, element)
        return
    position = TBL_PR_ORDER.index(name)
    for child in list(tbl_pr):
        child_name = child.tag.split("}")[1]
        if child_name in TBL_PR_ORDER and TBL_PR_ORDER.index(child_name) > position:
            child.addprevious(element)
            return
    tbl_pr.append(element)


def set_table_widths(table, widths):
    """Fixed layout with explicit grid columns, so Word and LibreOffice both honour the column widths."""
    tbl_pr = table._tbl.tblPr
    total = OxmlElement("w:tblW")
    total.set(qn("w:w"), str(sum(int(w.inches * 1440) if hasattr(w, "inches") else int(w * 1440)
                                 for w in widths)))
    total.set(qn("w:type"), "dxa")
    set_tbl_pr_child(tbl_pr, total)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    set_tbl_pr_child(tbl_pr, layout)
    grid = table._tbl.tblGrid
    for col in list(grid):
        grid.remove(col)
    for width in widths:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(int(width.inches * 1440) if hasattr(width, "inches") else int(width * 1440)))
        grid.append(col)
    for row in table.rows:
        for cell, width in zip(row.cells, widths):
            cell.width = width if hasattr(width, "inches") else Inches(width)


def copy_run_format(source_run, target_run):
    """Give target_run exactly the formatting (rPr) of source_run."""
    source_pr = source_run._r.find(qn("w:rPr"))
    target_pr = target_run._r.find(qn("w:rPr"))
    if target_pr is not None:
        target_run._r.remove(target_pr)
    if source_pr is not None:
        target_run._r.insert(0, copy.deepcopy(source_pr))


def rebuild_paragraph(paragraph, segments):
    """
    Replace a template paragraph's runs. segments = [(text, template_run_index), ...]; each new run
    copies the colour/bold/size of the template run at that index, so the template look is kept.
    """
    template_runs = list(paragraph.runs)
    for run in template_runs:
        run._r.getparent().remove(run._r)
    for text, index in segments:
        run = paragraph.add_run(text)
        copy_run_format(template_runs[index], run)
    return paragraph


def remove_paragraph(paragraph):
    paragraph._p.getparent().remove(paragraph._p)


def line_spacing_exact(paragraph, value=1.5):
    paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    paragraph.paragraph_format.line_spacing = value


SCHEMA_ORDER = {
    "pPr": ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr",
            "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap",
            "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd", "snapToGrid",
            "spacing", "ind", "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc", "textDirection",
            "textAlignment", "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr", "pPrChange"],
    "trPr": ["cnfStyle", "divId", "gridBefore", "gridAfter", "wBefore", "wAfter", "cantSplit", "trHeight",
             "tblHeader", "tblCellSpacing", "jc", "hidden", "ins", "del", "trPrChange"],
    "tcPr": ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap", "tcMar",
             "textDirection", "tcFitText", "vAlign", "hideMark"],
    "rPr": ["rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike", "dstrike", "outline",
            "shadow", "emboss", "imprint", "noProof", "snapToGrid", "vanish", "webHidden", "color", "spacing", "w",
            "kern", "position", "sz", "szCs", "highlight", "u", "effect", "bdr", "shd", "fitText", "vertAlign",
            "rtl", "cs", "em", "lang", "eastAsianLayout", "specVanish", "oMath"],
}


def normalize_order(root):
    """Re-sort property children into schema order; keeps unknown children in place at the end."""
    for tag, order in SCHEMA_ORDER.items():
        rank = {name: i for i, name in enumerate(order)}
        for element in root.iter(qn(f"w:{tag}")):
            children = list(element)
            keyed = sorted(enumerate(children),
                           key=lambda item: (rank.get(item[1].tag.split("}")[1], len(order)), item[0]))
            if [c for _, c in keyed] != children:
                for child in children:
                    element.remove(child)
                for _, child in keyed:
                    element.append(child)
