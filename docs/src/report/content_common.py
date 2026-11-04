"""Shared data loading and small helpers for the report content modules."""

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / "docs" / "src"
EVIDENCE = SRC / "evidence"
DIAGRAMS = SRC / "figures" / "diagrams"
SCREENS = SRC / "figures" / "screens"

# The project team, in the order used everywhere in the report.
TEAM = [
    ("V. Sai Rishi", "25911A67B7"),
    ("Mummadisetty Advyth", "25911A67A3"),
    ("P.V.S Sebareesh", "25911A67C4"),
    ("K. Bharath Reddy", "25911A6784"),
]

DOMAIN_TABLES = ["departments", "faculty", "students", "courses", "enrollments", "attendance_records", "marks",
                 "marks_audit", "rooms", "time_slots", "timetable_entries"]

# Measured on the development machine (Get-CimInstance / --version output, 1 Nov 2026).
MACHINE = {
    "cpu": "AMD Ryzen 5 3550H (4 cores, 8 threads)",
    "ram": "13.9 GB usable RAM",
    "os": "Windows 11 Home Single Language, 64-bit, build 26200",
    "disk": "SSD, 22 GB free at the time of testing",
}
VERSIONS = {
    "mysql": "8.0.42", "java": "OpenJDK 17.0.20.1 (LTS)", "python": "3.13.3", "maven": "3.9.16 (Maven Wrapper)",
    "django": "5.2.18 (LTS)", "pymysql": "1.2.3", "dotenv": "1.2.4", "cryptography": "50.0.2",
    "connector": "mysql-connector-j 9.7.0", "junit": "JUnit 6.1.3 (Jupiter)", "shade": "maven-shade-plugin 3.6.2",
    "plantuml": "PlantUML 1.2026.9", "jacoco": "JaCoCo 0.8.16", "coverage": "coverage.py 7.17.0",
    "playwright": "Playwright for Python 1.64.1 (Chromium)", "docx": "python-docx 1.2.0",
    "libreoffice": "LibreOffice 26.8.2", "git": "Git 2.53.0", "vscode": "Visual Studio Code 1.143.1",
}


def load(name):
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


FACTS = load("facts.json")
TESTS = load("tests.json")
CASES = load("cases.json")
LIVE = load("live.json")


def diagram(name):
    return DIAGRAMS / f"{name}.png"


def diagram_title(name):
    text = (SRC / "diagrams" / f"{name}.puml").read_text(encoding="utf-8")
    return re.search(r"' Figure title: (.+)", text).group(1).strip()


def screen(name):
    return SCREENS / f"{name}.png"


def snippet(path, start, end=None, max_lines=60, include_end=True):
    """Lines of a real source file from the first line containing `start` up to the line containing `end`."""
    lines = (REPO / path).read_text(encoding="utf-8").splitlines()
    first = next(i for i, line in enumerate(lines) if start in line)
    if end is None:
        last = first + max_lines - 1
    else:
        last = next(i for i in range(first + 1, len(lines)) if end in lines[i])
        if not include_end:
            last -= 1
    while not lines[last].strip():
        last -= 1
    return "\n".join(lines[first:last + 1])


def columns(table):
    return [c for c in FACTS["schema"]["columns"] if c["table_name"] == table]


def foreign_keys(table):
    return [f for f in FACTS["schema"]["foreign_keys"] if f["table_name"] == table]


def constraints(kind=None):
    return [c for c in FACTS["schema"]["constraints"]
            if c["table_name"] in DOMAIN_TABLES and (kind is None or c["constraint_type"] == kind)]


def case_rows(cases):
    return [[c["id"], c["module"], c["objective"], c["input"], c["expected"], c["actual"], c["status"]]
            for c in cases]


CASE_HEADERS = ["ID", "Module", "Objective", "Input", "Expected result", "Actual result", "Status"]
CASE_WIDTHS = [0.5, 0.95, 0.92, 0.98, 0.88, 1.0, 0.54]


def case_table(r, cases, caption):
    r.table(CASE_HEADERS, case_rows(cases), CASE_WIDTHS, caption, size=8.5)


def count_status(cases):
    passed = sum(1 for c in cases if c["status"] == "Pass")
    return passed, len(cases) - passed
