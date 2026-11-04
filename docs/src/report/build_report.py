"""
Builds docs/Project_Report.docx from the course templates, the evidence JSON files, the rendered diagrams and
the screenshots, then converts it to PDF with LibreOffice to fill in the page numbers of the table of contents
and the lists of figures and tables (repeated until the numbers are stable).

Run from the repo root:
    .venv\\Scripts\\python.exe docs\\src\\report\\build_report.py --soffice "C:\\path\\to\\soffice.com"
(or set SOFFICE). Without LibreOffice, pass --no-pdf: the lists are then left without page numbers.
"""

import argparse
import copy
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import docx
import pymupdf
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from docx.text.paragraph import Paragraph

sys.path.insert(0, str(Path(__file__).resolve().parent))

import chapters_1_4  # noqa: E402
import chapters_5_10  # noqa: E402
from content_common import REPO, TEAM  # noqa: E402
from docx_helpers import (Report, add_field, page_numbering, rebuild_paragraph, remove_paragraph,  # noqa: E402
                          normalize_order, report_margins, set_table_widths, style_run)

TEMPLATE = REPO / "docs" / "templates" / "LAB_COVERPAGE_FORMAT.docx"
OUTPUT = REPO / "docs" / "Project_Report.docx"
BUILD = REPO / "docs" / "src" / "report" / "build"

TITLE = "Smart Campus & Academic Suite"
GUIDE = "Ms. M. Prasanna Kumari"

ABSTRACT = [
    "Academic records in many college departments are still kept in attendance registers and separate "
    "spreadsheets. The same data is typed several times, grades and attendance percentages are calculated by "
    "hand, students learn that they are short of attendance too late to recover, and nothing prevents "
    "duplicate enrollments or a teacher being booked into two classes at once.",
    "Smart Campus & Academic Suite is a department-level academic management system built to solve these "
    "problems. All data is kept in one normalised (3NF) MySQL 8.0 database of eleven tables. The academic rules "
    "are enforced inside the database itself: CHECK, UNIQUE and foreign-key constraints reject invalid data, "
    "triggers compute totals and grades and record every change of marks in an audit table, views compute "
    "attendance percentages, the below-75% defaulter list and GPA, and a stored procedure declares the "
    "defaulters. Two applications share this database. A Django 5.2 web portal gives Admin, Faculty and Student "
    "users role-based pages in which each user sees and changes only what their role allows. A Java 17 engine, "
    "written with core object-oriented programming and raw JDBC, provides the same reports from the command "
    "line, including a multithreaded dashboard and CSV export, and is called safely from the portal through a "
    "validated subprocess bridge that exchanges JSON.",
    "The system was developed following the software development life cycle: requirements were specified in an "
    "IEEE 830 style SRS, the design was documented with UML, data flow and entity relationship diagrams, and "
    "the implementation was verified with 29 JUnit tests, 71 Django tests and 78 documented unit, integration, "
    "white-box and black-box test cases, all of which pass. Ordinary pages respond in about 50-70 ms and engine "
    "reports in under one second on a laptop. The project shows that placing business rules in a shared "
    "database keeps several applications consistent, and it serves as one worked example for the DBMS, Java, "
    "Django and Software Engineering laboratories.",
    "**Keywords:** academic management system, MySQL, triggers, Django, Java, JDBC, role-based access control, "
    "software engineering.",
]

ABBREVIATIONS = [
    ("AICTE", "All India Council for Technical Education"), ("API", "Application Programming Interface"),
    ("CASE", "Computer-Aided Software Engineering"), ("CGPA", "Cumulative Grade Point Average"),
    ("CLI", "Command-Line Interface"), ("CRUD", "Create, Read, Update, Delete"),
    ("CSE (DS)", "Computer Science and Engineering (Data Science)"), ("CSRF", "Cross-Site Request Forgery"),
    ("CSS", "Cascading Style Sheets"), ("CSV", "Comma-Separated Values"), ("DAO", "Data Access Object"),
    ("DBMS", "Database Management System"), ("DFD", "Data Flow Diagram"),
    ("ERD", "Entity Relationship Diagram"), ("ERP", "Enterprise Resource Planning"),
    ("FD", "Functional Dependency"), ("FK", "Foreign Key"), ("FR", "Functional Requirement"),
    ("GPA", "Grade Point Average"), ("HOD", "Head of the Department"), ("HSTS", "HTTP Strict Transport Security"),
    ("HTML", "HyperText Markup Language"), ("HTTP(S)", "HyperText Transfer Protocol (Secure)"),
    ("IEEE", "Institute of Electrical and Electronics Engineers"), ("JAR", "Java Archive"),
    ("JDBC", "Java Database Connectivity"), ("JDK", "Java Development Kit"),
    ("JNTUH", "Jawaharlal Nehru Technological University Hyderabad"), ("JSON", "JavaScript Object Notation"),
    ("JVM", "Java Virtual Machine"), ("LTS", "Long-Term Support"), ("MVT", "Model-View-Template"),
    ("NFR", "Non-Functional Requirement"), ("OOP", "Object-Oriented Programming"),
    ("ORM", "Object-Relational Mapping"), ("PK", "Primary Key"), ("RBAC", "Role-Based Access Control"),
    ("SCM", "Software Configuration Management"), ("SDLC", "Software Development Life Cycle"),
    ("SQL", "Structured Query Language"), ("SRS", "Software Requirements Specification"),
    ("TLS", "Transport Layer Security"), ("UAT", "User Acceptance Testing"), ("UML", "Unified Modeling Language"),
    ("URL", "Uniform Resource Locator"), ("UTC", "Coordinated Universal Time"),
    ("VJIT", "Vidya Jyothi Institute of Technology"), ("XSS", "Cross-Site Scripting"),
]


# ------------------------------------------------------------------------------------------------
# Front matter: edit the template in place so its colours, images and layout are kept
# ------------------------------------------------------------------------------------------------
def clear(paragraph):
    for run in list(paragraph.runs):
        run._r.getparent().remove(run._r)


def set_run_text(paragraph, index, text):
    paragraph.runs[index].text = text


def clone_after(paragraph):
    """A copy of a template paragraph inserted right after it (keeps its formatting)."""
    element = copy.deepcopy(paragraph._p)
    paragraph._p.addnext(element)
    return Paragraph(element, paragraph._parent)


def column_break_before_text(paragraph):
    run = paragraph.runs[0]._r
    br = OxmlElement("w:br")
    br.set(qn("w:type"), "column")
    first_text = run.find(qn("w:t"))
    first_text.addprevious(br)


def signature_block(paragraph, name_index, tab_index, roll_index, tab_at):
    """Four 'Name<TAB>(Roll)' lines in one template paragraph, separated by line breaks."""
    segments = []
    for i, (name, roll) in enumerate(TEAM):
        last = i == len(TEAM) - 1
        segments += [(name, name_index), ("\t", tab_index), (f"({roll})" + ("" if last else "\n"), roll_index)]
    rebuild_paragraph(paragraph, segments)
    # Replace the template's single tab stop (placed for its two-names-per-line layout).
    tabs = paragraph._p.pPr.find(qn("w:tabs"))
    if tabs is not None:
        paragraph._p.pPr.remove(tabs)
    paragraph.paragraph_format.tab_stops.add_tab_stop(Inches(tab_at))


def edit_front_matter(doc):
    p = list(doc.paragraphs)                      # p[n - 1] is template paragraph Pnnn
    names = ", ".join(name for name, _ in TEAM[:-1]) + " and " + TEAM[-1][0]
    rolls = ", ".join(roll for _, roll in TEAM[:-1]) + " and " + TEAM[-1][1]
    with_rolls = ", ".join(f"{name} ({roll})" for name, roll in TEAM)
    # Cover page: names in the left column, roll numbers in the right, as in the template
    rebuild_paragraph(p[2], [(TITLE, 0)])
    name_paragraphs = [p[12], p[13], p[14], clone_after(p[14])]
    for paragraph, (name, _) in zip(name_paragraphs, TEAM):
        rebuild_paragraph(paragraph, [("                         " + name, 0)])
    roll_paragraphs = [p[15], p[16], p[17], clone_after(p[17])]
    rebuild_paragraph(roll_paragraphs[0], [(TEAM[0][1], 1)])
    for paragraph, (_, roll) in zip(roll_paragraphs[1:], TEAM[1:]):
        rebuild_paragraph(paragraph, [(roll, 0)])
    column_break_before_text(roll_paragraphs[0])
    for paragraph in roll_paragraphs:             # same spacing as the names, so each row lines up
        paragraph.paragraph_format.space_before = p[12].paragraph_format.space_before
        paragraph.paragraph_format.line_spacing = p[12].paragraph_format.line_spacing
    rebuild_paragraph(p[24], [(GUIDE.upper().replace("MS.", "Ms."), 0)])
    # Certificate (plural, as in the template: "carried out by them under my guidance and supervision")
    runs = p[40].runs
    opening, closing = runs[0].text, runs[2].text[-1]
    rebuild_paragraph(p[40], [
        (opening, 0), (TITLE + closing, 1), (" is being submitted by ", 4),
        (with_rolls, 5), (".", 16), (" In partial fulfillment for the award of the Degree of "
                                      "Bachelor of Technology in ", 18),
        ("Computer Science & Engineering (Data Science)", 19),
        (", is a record of Bonafide work carried out by them under my guidance and supervision. These results "
         "embodied in this project report have not been submitted to any other University or Institute for the "
         "award of any degree.", 20)])
    rebuild_paragraph(p[55], [(GUIDE, 2)])
    # Declaration (plural; date left blank, place Hyderabad as in the template)
    runs = p[61].runs
    open_q, close_q = runs[15].text, runs[17].text
    rebuild_paragraph(p[61], [
        ("We, ", 0), (names, 1), (", ", 0), ("bearing Roll Numbers ", 9), (rolls, 10),
        (" hereby declare that the project entitled,", 14), (open_q, 15), (TITLE, 16), (close_q, 17),
        ("submitted for the degree of Bachelor of Technology in ", 18),
        ("Computer Science and Engineering (Data Science)", 19),
        (" is original and has been done by us and this work is not copied and submitted anywhere for the award "
         "of any degree.", 20)])
    signature_block(p[70], 1, 3, 4, tab_at=2.0)
    column_break_before_text(p[70])               # the template's column break was in the removed run 0
    clear(p[72]), clear(p[73])
    # Acknowledgement (plural; guide line added before the HOD line)
    guide = copy.deepcopy(p[78]._p)
    p[78]._p.addprevious(guide)
    guide_paragraph = Paragraph(guide, p[78]._parent)
    rebuild_paragraph(guide_paragraph, [
        ("We express our sincere gratitude to our internal guide ", 0), (GUIDE, 1),
        (", Assistant Professor, Department of Computer Science and Engineering (Data Science), Vidya Jyothi "
         "Institute of Technology, for the valuable guidance, encouragement and constant support given throughout "
         "this project.", 5)])
    set_run_text(p[78], 0, "We are grateful to ")
    set_run_text(p[79], 0, "We whole-heartedly convey our gratitude to Dean of Accreditations ")
    set_run_text(p[80], 0, "We would like to take this opportunity to express our gratitude to our ")
    set_run_text(p[81], 0, "We would like to thank our ")
    signature_block(p[84], 0, 2, 3, tab_at=4.2)   # tab stops count from the margin; the block is indented 2.34"
    p[84].paragraph_format.line_spacing = 1.3
    clear(p[85])
    for paragraph in p[78:82] + [guide_paragraph, p[61]]:
        assert not re.search(r"\b(I|my|me|Mr\.)\b", paragraph.text), paragraph.text

    # Abstract: first template paragraph keeps its style; extra ones are copies of it
    body = p[89]
    clear(body)
    previous = body
    for index, text in enumerate(ABSTRACT):
        target = body if index == 0 else Paragraph(copy.deepcopy(body._p), body._parent)
        if index:
            clear(target)
            previous._p.addnext(target._p)
        from docx_helpers import add_rich_text
        add_rich_text(target, text)
        target.paragraph_format.line_spacing = 1.5
        target.paragraph_format.space_after = Pt(8)
        target.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        previous = target
    for paragraph in p[90:107]:
        remove_paragraph(paragraph)
    # Lists: one heading per page, upper case (main headings are 16 pt bold upper case)
    for index, title in ((107, "TABLE OF CONTENTS"), (119, "LIST OF FIGURES"), (135, "LIST OF TABLES"),
                         (137, "LIST OF ABBREVIATIONS")):
        p[index].runs[0].text = title
        p[index].paragraph_format.page_break_before = True
        p[index].paragraph_format.space_after = Pt(10)
    for paragraph in p[108:119] + p[120:135] + [p[136], p[138]]:
        remove_paragraph(paragraph)

    # Sections: cover and certificate keep the template layout; from the declaration on, report margins.
    # Roman page numbers from the cover (i); the number is printed from the declaration onwards.
    sections = doc.sections
    page_numbering(sections[0], "lowerRoman", start=1)
    for section in sections[1:]:
        page_numbering(section, "lowerRoman")
    for section in sections[:5]:
        section.footer.is_linked_to_previous = False
        for paragraph in section.footer.paragraphs:
            paragraph.text = ""
    footer = sections[5].footer
    footer.is_linked_to_previous = False
    paragraph = footer.paragraphs[0]
    paragraph.text = ""
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_field(paragraph, "PAGE")
    for section in sections[5:]:
        report_margins(section)
    # Two-column signature blocks have explicit column widths for the template's 6.7" text width; fit them
    # to the 5.77" report width (and keep "Place: Hyderabad" on one line in the declaration).
    width = int((8.27 - 2.5) * 1440)
    for index, first_col in ((6, 2600), (7, None)):
        cols = sections[index]._sectPr.find(qn("w:cols")).findall(qn("w:col"))
        if first_col is None:
            total = sum(int(c.get(qn("w:w"))) + int(c.get(qn("w:space"), 0)) for c in cols)
            for c in cols:
                c.set(qn("w:w"), str(int(int(c.get(qn("w:w"))) * width / total)))
        else:
            cols[0].set(qn("w:w"), str(first_col))
            cols[0].set(qn("w:space"), "700")
            cols[1].set(qn("w:w"), str(width - first_col - 700))


def fill_list_table(table, rows, widths, bold_rows=()):
    """Keep the template's header row, clone its first data row for every entry."""
    prototype = copy.deepcopy(table.rows[1]._tr)
    for element in list(prototype.iter(qn("w:numPr"))) + list(prototype.iter(qn("w:trHeight"))):
        element.getparent().remove(element)
    for row in list(table.rows)[1:]:
        table._tbl.remove(row._tr)
    for index, values in enumerate(rows):
        tr = copy.deepcopy(prototype)
        table._tbl.append(tr)
        row = table.rows[-1]
        for col, (cell, value) in enumerate(zip(row.cells, values)):
            cell.width = Inches(widths[col])
            paragraph = cell.paragraphs[0]
            for extra in cell.paragraphs[1:]:
                remove_paragraph(extra)
            clear(paragraph)
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.line_spacing = 1.15
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT if col == 1 else WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.left_indent = Inches(0)
            paragraph.paragraph_format.first_line_indent = Inches(0)
            style_run(paragraph.add_run(str(value)), size=11, bold=index in bold_rows)
    set_table_widths(table, widths)


def fill_front_lists(doc, report, pages):
    toc, lof, lot, abbr = doc.tables[:4]
    widths = [0.65, 4.22, 0.9]
    rows, bold, chapter_no = [], [], 0
    for index, (level, text) in enumerate(report.toc):
        number = pages.get(("toc", index), "") if pages else ""
        if level == 1:
            chapter_no += 1
            bold.append(len(rows))
            rows.append([str(chapter_no), text, number])
        else:
            rows.append(["", "      " + text, number])
    fill_list_table(toc, rows, widths, bold_rows=bold)
    fill_list_table(lof, [[i, text, pages.get(("fig", i - 1), "") if pages else ""]
                          for i, text in enumerate(report.figures, 1)], widths)
    fill_list_table(lot, [[i, text, pages.get(("tab", i - 1), "") if pages else ""]
                          for i, text in enumerate(report.tables, 1)], widths)
    fill_list_table(abbr, [[i, a, d] for i, (a, d) in enumerate(ABBREVIATIONS, 1)], [0.65, 1.3, 3.82])
    for table in (toc, lof, lot, abbr):  # header row repeats on every page
        from docx_helpers import Report as _R
        _R._repeat_header(table.rows[0])


# ------------------------------------------------------------------------------------------------
# Build and paginate
# ------------------------------------------------------------------------------------------------
def build(pages):
    BUILD.mkdir(parents=True, exist_ok=True)
    doc = docx.Document(str(TEMPLATE))
    edit_front_matter(doc)
    logo = BUILD / "vjit_emblem.jpeg"
    with zipfile.ZipFile(TEMPLATE) as z:
        logo.write_bytes(z.read("word/media/image1.jpeg"))
    r = Report(doc, BUILD)
    r.start_chapters(logo)
    for chapter in (chapters_1_4.chapter1, chapters_1_4.chapter2, chapters_1_4.chapter3, chapters_1_4.chapter4,
                    chapters_5_10.chapter5, chapters_5_10.chapter6, chapters_5_10.chapter7,
                    chapters_5_10.chapter8, chapters_5_10.chapter9, chapters_5_10.chapter10,
                    chapters_5_10.references, chapters_5_10.appendix_a, chapters_5_10.appendix_b,
                    chapters_5_10.appendix_c):
        chapter(r)
    fill_front_lists(doc, r, pages)
    normalize_order(doc.element.body)
    for section in doc.sections:
        for part in (section.header, section.footer):
            if not part.is_linked_to_previous:
                normalize_order(part._element)
    doc.core_properties.title = TITLE
    doc.core_properties.author = "; ".join(name for name, _ in TEAM)
    doc.core_properties.last_modified_by = doc.core_properties.author   # the template carries its own name here
    doc.core_properties.subject = "Software Engineering Lab project report"
    doc.save(str(OUTPUT))
    return r


def to_pdf(soffice, docx_path, out_dir):
    profile = Path(tempfile.mkdtemp(prefix="lo_profile_"))
    try:
        subprocess.run([str(soffice), f"-env:UserInstallation={profile.as_uri()}", "--headless", "--convert-to",
                        "pdf", "--outdir", str(out_dir), str(docx_path)], check=True, capture_output=True,
                       timeout=900)
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    return out_dir / (docx_path.stem + ".pdf")


def roman(n):
    out = ""
    for value, letters in ((10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")):
        while n >= value:
            out, n = out + letters, n - value
    return out


def norm(text):
    return re.sub(r"\s+", " ", text.replace("\u2019", "'")).strip()


def page_map(pdf_path, report):
    pdf = pymupdf.open(pdf_path)
    lines = [[norm(line) for line in page.get_text().splitlines() if line.strip()] for page in pdf]
    first = next(i for i, page in enumerate(lines) if any(l.startswith("CHAPTER 1: INTRODUCTION") for l in page))

    def label(i):
        return roman(i + 1) if i < first else str(i - first + 1)

    def scan(kind, targets):
        found, cursor = {}, first
        for index, target in enumerate(targets):
            key = norm(target)[:40]
            for i in range(cursor, len(lines)):
                page = lines[i]
                if any(" ".join(page[j:j + 3]).startswith(key) for j in range(len(page))):
                    found[(kind, index)], cursor = label(i), i
                    break
            else:
                print(f"  not found in PDF: {kind} {target!r}")
        return found

    toc_targets = [text.upper() if level == 1 else text for level, text in report.toc]
    pages = {**scan("toc", toc_targets), **scan("fig", report.figures), **scan("tab", report.tables)}
    return pages, pdf.page_count, first


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--soffice", default=os.environ.get("SOFFICE", "soffice"))
    parser.add_argument("--no-pdf", action="store_true")
    args = parser.parse_args()
    report = build(pages=None)
    print(f"built {OUTPUT.name}: {len(report.toc)} contents entries, {len(report.figures)} figures, "
          f"{len(report.tables)} tables")
    if args.no_pdf:
        return
    pages = None
    for attempt in range(1, 5):
        pdf = to_pdf(args.soffice, OUTPUT, BUILD)
        new_pages, count, first = page_map(pdf, report)
        print(f"pass {attempt}: {count} PDF pages, chapter 1 starts on PDF page {first + 1}")
        if new_pages == pages:
            break
        pages = new_pages
        report = build(pages)
    shutil.copy(pdf, OUTPUT.with_suffix(".pdf"))
    print(f"final: {OUTPUT} and {OUTPUT.with_suffix('.pdf')}")


if __name__ == "__main__":
    main()
