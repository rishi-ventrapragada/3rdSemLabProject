# Smart Campus & Academic Suite

A 3rd-semester college project that covers four lab courses with one codebase. A MySQL database holds attendance, marks, timetables and results. A Java engine and a Django web portal both work on that same database, and the design is documented for the Software Engineering lab.

| Lab | Folder | What it shows |
|---|---|---|
| **DBMS** | [`database/`](database/) | 3NF schema (11 tables), PK/FK/UNIQUE/CHECK constraints, 4 views, 9 triggers (BEFORE and AFTER/audit), 2 stored functions, a stored procedure, seed data, and [`queries.sql`](database/queries.sql) with joins, subqueries, window functions and transactions |
| **Java** | [`java_engine/`](java_engine/) | Java 17 + raw JDBC: abstract classes, inheritance, interfaces with default methods, generics, custom checked exceptions, collections and streams, a multithreaded dashboard, CSV file export, and a Scanner menu. Builds to one runnable JAR. |
| **Django** | [`campus_portal/`](campus_portal/) | Login with Student / Faculty / Admin portals, role checks on every page, CRUD, forms, plain HTML5 + CSS3, Django admin, and a page that runs the Java engine |
| **Software Engineering** | [`docs/`](docs/) | ER diagram and functional dependencies, URL/role matrix, sequence diagram ([`database_design.md`](docs/database_design.md), [`django_portal.md`](docs/django_portal.md)) |

## Setup (Windows PowerShell, from the repo root)

Needs MySQL 8.0, JDK 17+ and Python 3.10+. Maven is downloaded automatically by the wrapper.

```powershell
Copy-Item .env.example .env                                     # 1. then set DB_PASSWORD in .env
python -m venv .venv; .venv\Scripts\python.exe -m pip install -r requirements.txt   # 2.
.venv\Scripts\python.exe database\init_db.py --yes              # 3. builds smart_campus_db
cd java_engine; .\mvnw.cmd clean package; cd ..                 # 4. builds the engine JAR (runs its tests)
cd campus_portal; ..\.venv\Scripts\python.exe manage.py migrate; ..\.venv\Scripts\python.exe manage.py seed_demo_users   # 5.
..\.venv\Scripts\python.exe manage.py runserver                 # 6. open http://127.0.0.1:8000/
```

On macOS/Linux, use `cp`, `.venv/bin/python` and `./mvnw`. Step 3 drops and recreates the project's tables but never touches Django's login tables. [`CLAUDE.md`](CLAUDE.md) has the full guide, conventions and troubleshooting.

## Demo logins (demo only)

All demo accounts share the password **`campus-demo-2026`**. Never use it outside a local demo.

| Role | Username | Notes |
|---|---|---|
| Admin | `admin` | Admin portal, Java engine page, Django admin |
| Faculty | `ananya.rao` | Teaches CS301 (others: `kiran.kumar`, `meera.iyer`, `arjun.reddy`, `suresh.babu`) |
| Student | `25cse001` | Good standing (`25cse002` … `25cse010` also exist) |
| Student | `25cse004` | Below 75% attendance: sees the defaulter warning |

## Pages worth a screenshot

| Page | Log in as | Shows |
|---|---|---|
| `/student/` | `25cse004` | Defaulter warning, per-course attendance and grades, CGPA, timetable |
| `/faculty/` | `ananya.rao` | Own courses and weekly timetable |
| `/faculty/courses/CS301/attendance/` | `ananya.rao` | Attendance sheet for a date |
| `/faculty/courses/CS301/marks/` | `ananya.rao` | Marks entry; the database computes totals and grades and logs changes |
| `/admin-portal/` | `admin` | Dashboard: counts, average attendance, defaulters, top GPAs |
| `/admin-portal/students/` | `admin` | Search, pagination, add / edit / delete |
| `/admin-portal/timetable/` | `admin` | Add an entry; try double-booking a teacher to see the trigger's message |
| `/admin-portal/defaulters/` | `admin` | Live defaulter list plus "declare" (stored procedure) |
| `/admin-portal/gpa-report/` | `admin` | Weighted GPA vs official CGPA |
| `/admin-portal/marks-audit/` | `admin` | History written by the AFTER UPDATE trigger |
| `/engine/` | `admin` | Runs the Java JAR (defaulters, GPA, dashboard with thread names, enroll) |
| `/django-admin/` | `admin` | Django's built-in admin over every table and view |

The Java engine also runs on its own: `java -jar java_engine/target/smart-campus-engine.jar help` (try `dashboard`, `defaulters`, `export gpa-report gpa.csv`, or `menu`).

## Tests

- `cd java_engine; .\mvnw.cmd test`: 29 JUnit tests, no database needed.
- `cd campus_portal; ..\.venv\Scripts\python.exe manage.py test --noinput`: 71 Django tests on a throwaway `test_smart_campus_db` built from the real SQL scripts.
