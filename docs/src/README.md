# Report sources (`docs/src/`)

Everything needed to regenerate `docs/Project_Report.docx` (and its PDF) from the real project.

| Path | What it is |
|---|---|
| `diagrams/*.puml` | PlantUML sources of all 21 report diagrams (UML, ERD, DFD). `_style.iuml` holds the shared style. Edit these. |
| `render_diagrams.py` | Renders `diagrams/*.puml` to `figures/diagrams/*.png` with PlantUML 1.2026.9 (downloaded to `tools/` on first run, SHA-1 checked; Smetana layout, so no Graphviz). |
| `figures/screens/*.png` | Screenshots of the running portal (Playwright, Chromium) and terminal output. |
| `evidence/collect_facts.py` → `facts.json` | Schema, constraints, triggers, row counts (from MySQL's `information_schema`), git history and line counts. |
| `evidence/collect_tests.py` → `tests.json` | Runs `mvnw clean package` with JaCoCo and `manage.py test` under coverage.py, and records every test result. |
| `evidence/collect_cases.py` → `cases.json` | Executes the 78 documented test cases (UT, IT, WB, BB) against the real database, JAR and Django client, plus CLI timings. Writes are rolled back. |
| `evidence/capture_live.py` → `live.json` | Starts the dev server, logs in as each demo role, captures the screenshots and page timings, then rebuilds the database from the seed. |
| `report/build_report.py` | Builds the .docx from the course templates, the JSON evidence, the figures and the chapter modules (`report/chapters_*.py`), then paginates it with LibreOffice. |

## Regenerate (Windows, from the repo root)

Prerequisites: the normal project setup (README.md), plus `pip install -r docs/requirements-docs.txt`,
`python -m playwright install chromium` (only for `capture_live.py`) and LibreOffice (only for page numbers).
The course templates must be in `docs/templates/` (they are git-ignored).

```powershell
.venv\Scripts\python.exe docs\src\render_diagrams.py
.venv\Scripts\python.exe docs\src\evidence\collect_facts.py
.venv\Scripts\python.exe docs\src\evidence\collect_tests.py
.venv\Scripts\python.exe docs\src\evidence\collect_cases.py
.venv\Scripts\python.exe docs\src\evidence\capture_live.py      # needs a free port 8000
.venv\Scripts\python.exe docs\src\report\build_report.py --soffice "C:\Program Files\LibreOffice\program\soffice.com"
```

`build_report.py` converts the document to PDF, finds every heading and caption, fills the page numbers of the
table of contents and the lists of figures and tables, and repeats until they are stable. With `--no-pdf` it
only writes the .docx (lists without page numbers).

Notes:
- `collect_cases.py` and `capture_live.py` write to `smart_campus_db`; both restore it (rollback, or
  `init_db.py --yes` at the end). Run them only against the local demo database.
- The demo password is never printed in screenshots or in the report.
- Wide diagrams are rotated onto their own page automatically when that makes them at least 25% larger.
