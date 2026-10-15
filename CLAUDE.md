# Smart Campus & Academic Suite

One codebase that satisfies four 3rd-semester lab courses. Each lab owns a top-level folder, and the Django and Java code both run against **one MySQL database, `smart_campus_db`**.

| Lab | Folder | Stack | Deliverable |
|---|---|---|---|
| DBMS Lab | `database/` | MySQL 8.0, raw SQL | 3NF schema with PK/FK/CHECK constraints, views, triggers, seed data |
| Java Lab | `java_engine/` | Java 17, Maven, raw JDBC (`mysql-connector-j`) | OOP domain model + DAO layer, packaged as a runnable CLI JAR |
| Django Lab | `campus_portal/` | Django 5.2 LTS, PyMySQL, vanilla HTML5/CSS3 | Role-based web portal for Admin, Faculty and Student |
| SE Lab | `docs/` | Markdown + Mermaid diagrams | SRS, UML/ER diagrams, test plans |

**Status: Phase 1 (scaffolding) is complete.** The folders, build config and conventions are in place. No schema, Java models/DAOs or Django project exist yet. Items marked *(planned)* below show where code goes as later phases build it. Update this file when a phase lands.

## Repository layout

```
3rdSemLabProject/
├── .env.example            # shared DB credentials template → copy to .env (git-ignored)
├── requirements.txt        # Python deps for campus_portal
├── database/               # DBMS Lab: raw MySQL scripts, run in numeric order
│   ├── 01_schema.sql       #   (planned) CREATE DATABASE + 3NF tables and constraints
│   ├── 02_views.sql        #   (planned) vw_* reporting views
│   ├── 03_triggers.sql     #   (planned) trg_* triggers
│   └── 04_seed.sql         #   (planned) demo data
├── java_engine/            # Java Lab: Maven project
│   ├── pom.xml             #   builds target/smart-campus-engine.jar (fat JAR, driver bundled)
│   ├── mvnw, mvnw.cmd      #   Maven Wrapper; downloads Maven 3.9.16 on first run (.mvn/wrapper/)
│   └── src/main/java/com/smartcampus/
│       ├── Main.java       #   CLI entry point (stub: prints usage)
│       ├── config/         #   DB settings loader + JDBC connection factory
│       ├── models/         #   domain entities (abstract bases + subclasses)
│       ├── dao/            #   DAO interfaces + JDBC implementations
│       ├── services/       #   business logic over DAO interfaces
│       └── exceptions/     #   custom exception hierarchy
├── campus_portal/          # Django Lab: empty until `django-admin startproject` runs
│   ├── manage.py           #   (planned)
│   ├── campus_portal/      #   (planned) settings, urls, wsgi; PyMySQL shim in __init__.py
│   ├── accounts/           #   (planned) login/logout, role-based redirect
│   ├── core/               #   (planned) shared helpers, role decorator, Java bridge view
│   ├── admin_portal/       #   (planned) Admin role
│   ├── faculty_portal/     #   (planned) Faculty role
│   ├── student_portal/     #   (planned) Student role
│   ├── templates/          #   (planned) base.html + per-role templates
│   └── static/css/         #   (planned) hand-written CSS
└── docs/                   # SE Lab documentation
```

Create the Django project from the repo root with `django-admin startproject campus_portal campus_portal`. That command puts `manage.py` directly inside `campus_portal/`.

## How Django and Java share `smart_campus_db`

### 1. One set of credentials: the repo-root `.env`

Both stacks read `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` and `DB_PASSWORD`. Never hard-code credentials. When you add a variable, add it to `.env.example` too, and prefix Django-only variables with `DJANGO_`.

- **Django:** `settings.py` calls `load_dotenv(BASE_DIR.parent / ".env")` (`BASE_DIR` is `campus_portal/`) and builds `DATABASES["default"]` with `ENGINE = "django.db.backends.mysql"`. `campus_portal/campus_portal/__init__.py` calls `pymysql.install_as_MySQLdb()` so the MySQL backend runs on PyMySQL. That avoids building `mysqlclient`, which needs a C compiler on Windows.
- **Java:** the `config` package reads real environment variables first. If they're missing, it parses `.env`, searching upward from the working directory. It builds `jdbc:mysql://${DB_HOST}:${DB_PORT}/${DB_NAME}?useSSL=false&allowPublicKeyRetrieval=true&connectionTimeZone=UTC`.

### 2. Schema ownership: the SQL scripts are the source of truth

- Every domain table, view and trigger is created by `database/*.sql`. Django migrations never create them.
- Django models for those tables and views declare `class Meta: managed = False` and `db_table = "<table>"`. To bootstrap them, run `python manage.py inspectdb` and clean up the output.
- `python manage.py migrate` creates only Django's own tables (`auth_*`, `django_*`) in the same database.
- To change the schema, do all of these in one commit:
  1. Edit and re-run the SQL.
  2. Update the unmanaged Django model.
  3. Update the Java model and DAO.
  4. Update the ER diagram in `docs/`.

### 3. Invariants live in the database

Either application can write, so put the rules that must always hold in the database: FK, UNIQUE and CHECK constraints, plus triggers. Python or Java can repeat a check for friendlier error messages, but it must not be the only enforcement.

### 4. Django → Java bridge

A role-guarded utility view in the `core` app runs the compiled JAR:

```python
subprocess.run(
    [settings.JAVA_BIN, "-jar", str(settings.JAVA_ENGINE_JAR), command, *args],
    capture_output=True, text=True, timeout=60, cwd=settings.REPO_ROOT,
)
```

- `JAVA_ENGINE_JAR` defaults to `REPO_ROOT / "java_engine" / "target" / "smart-campus-engine.jar"`, and `JAVA_BIN` defaults to `"java"`.
- The child process inherits Django's `os.environ`, which python-dotenv has already filled with the `DB_*` variables. The JAR therefore connects with the same credentials and needs no extra configuration.
- The same JAR runs standalone: `java -jar java_engine/target/smart-campus-engine.jar <command> [args]`.
- **CLI contract:** the result goes to stdout and error messages go to stderr. Exit codes are `0` for success, `1` for a runtime or database error and `2` for bad usage. Commands that Django calls must never prompt on stdin.

## Coding standards

### DBMS Lab (`database/`)

- **Target:** MySQL 8.0 (8.0.16+ is needed for CHECK constraints to be enforced). Use InnoDB and `utf8mb4` / `utf8mb4_unicode_ci`.
- **Files are numbered by execution order** (`01_` … `04_`). New kinds of objects take the next number, e.g. `05_procedures.sql`. `01_schema.sql` starts with `CREATE DATABASE IF NOT EXISTS smart_campus_db …`. Every file starts with `USE smart_campus_db;`.
- **Every script must be re-runnable:**
  - Tables: `DROP TABLE IF EXISTS` (children before parents), then `CREATE TABLE`.
  - Views: `CREATE OR REPLACE VIEW`.
  - Triggers: `DROP TRIGGER IF EXISTS`, then `CREATE TRIGGER`.

  Never drop or alter Django's tables (`auth_*`, `django_*`).
- **Explicit 3NF:**
  - Atomic columns with no comma-separated lists or repeating groups (1NF).
  - No attribute depends on only part of a key (2NF).
  - No transitive dependencies (3NF). For example, a student row stores `department_id`, never the department name.
  - Reference data such as departments, programmes and semesters gets its own table.
  - Derived values such as GPA or attendance % are computed in views, not stored. If a trigger maintains a stored copy instead, document why.
  - Write each table's functional dependencies down in `docs/`.
- **Naming:**
  - Tables are plural snake_case (`students`, `course_enrollments`).
  - The PK is `<singular>_id INT AUTO_INCREMENT`, e.g. `student_id`.
  - An FK column has the same name and type as the PK it references.
  - Constraints are named `fk_<table>_<referenced>`, `uq_<table>_<cols>` and `chk_<table>_<rule>`.
- **Single-column surrogate PK on every table**, including junction tables. Enforce the natural key with a `UNIQUE` constraint instead. This keeps Django unmanaged models and Java DAOs simple.
- **Foreign keys:** declare every FK explicitly with `ON DELETE` / `ON UPDATE`. Default to `RESTRICT`. Use `CASCADE` only for rows that cannot exist without their parent.
- **Views:** `vw_<purpose>`. They are read-only reporting surfaces for both Django (unmanaged models, one unique column marked `primary_key=True`) and Java DAOs. Reuse a view rather than re-implementing its join in application code.
- **Triggers:**
  - Name them `trg_<table>_<before|after>_<insert|update|delete>`.
  - Wrap the body in `DELIMITER $$ … $$ DELIMITER ;`.
  - Reject bad data with `SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '…'`. That reaches Java as `SQLException` and Django as `django.db.utils.OperationalError`.
  - Use triggers for cross-row rules and audit trails that CHECK constraints can't express.
- **Seed data** (`04_seed.sql`): insert parents before children with realistic demo data. Login accounts are created through Django, not SQL, because Django hashes passwords.

### Java Lab (`java_engine/`)

- **Toolchain:** Java 17 (`maven.compiler.release`) and Maven. Use no frameworks: no Spring, Hibernate/JPA or connection pools. The lab assesses raw JDBC and core OOP.
- **Package responsibilities:**
  - `config`: loads DB settings (environment variables, then `.env`) and hands out `Connection`s via `DriverManager`.
  - `models`: plain domain classes. No SQL.
  - `dao`: one interface per entity plus a JDBC implementation (e.g. `StudentDao` / `JdbcStudentDao`). Only `dao` and `config` import `java.sql`.
  - `services`: business rules and orchestration. They depend on DAO *interfaces*, never on implementations.
  - `exceptions`: the project's exception hierarchy.
- **OOP requirements** (each must be visibly present):
  - *Abstraction:* abstract base classes hold shared state and declare abstract behaviour (e.g. `Person` → `Student`, `Faculty`).
  - *Inheritance and polymorphism:* subclasses override base behaviour, and services work with base types and interfaces.
  - *Interfaces:* a generic `CrudDao<T, ID>` is extended by entity DAOs, and services are coded against the interfaces.
  - *Encapsulation:* private fields, with validation in constructors and setters. Override `equals`/`hashCode`/`toString` on models.
  - *Custom exceptions:* a root `SmartCampusException` with specific subclasses (`DataAccessException`, `EntityNotFoundException`, `ValidationException`). DAOs catch `SQLException` and rethrow it wrapped, keeping the cause. Never swallow an exception or `printStackTrace()` and carry on.
  - *Collections:* use `List`/`Set`/`Map` (and streams) for in-memory processing. Declare variables by interface type (`List<Student> s = new ArrayList<>()`). Return empty collections, never `null`.
- **JDBC rules:**
  - Always use `PreparedStatement` with `?` placeholders. Never concatenate values into SQL.
  - Open `Connection`, `PreparedStatement` and `ResultSet` in try-with-resources.
  - For multi-statement writes, call `setAutoCommit(false)`, then `commit()`, and `rollback()` in the `catch`.
  - Map rows to objects in one private `mapRow(ResultSet)` helper per DAO.
  - Column names must match `database/01_schema.sql` exactly.
- **CLI:** `Main` parses `<command> [args]` and dispatches to services, following the stdout/stderr/exit-code contract above. An interactive menu is fine for standalone demos, but only behind an explicit command such as `menu`.

### Django Lab (`campus_portal/`)

- **MVT, kept clean:**
  - *Models:* unmanaged mirrors of the SQL tables and views (see Schema ownership).
  - *Views:* thin. They handle requests, call an app-level `services.py` for non-trivial logic, and render templates.
  - *Templates:* presentation only.
  - All user input goes through Django Forms. Give each app's URLs a namespace (`app_name = "faculty"`) and always use `{% url %}` / `reverse()`, never hard-coded paths.
- **Templates and static files:**
  - Vanilla HTML5 + hand-written CSS3 only. **No Tailwind, Bootstrap or any other CSS framework or CDN stylesheet.** No JS frameworks; small vanilla JS only where unavoidable.
  - Use semantic elements (`header`, `nav`, `main`, `section`, `table`, `form`/`label`).
  - Keep one `templates/base.html` with `{% block %}`s, and have each role's layout extend it.
  - Put CSS in `static/css/`, with colours and spacing as custom properties in one place. Lay out with Flexbox/Grid and make it responsive with media queries.
  - Include `{% csrf_token %}` in every POST form.
- **Role-based portals:**
  - Admin, Faculty and Student are Django Groups with exactly those names. After login, `accounts` redirects users to their role's dashboard.
  - Prefixes: `/admin-portal/`, `/faculty/`, `/student/`. Django's built-in admin is a developer tool, not the Admin portal; mount it at `/django-admin/`.
  - Enforce access in **every** view with `@login_required` plus a role decorator from `core` (e.g. `@role_required("Faculty")`). Hiding links in a template is not access control.
  - Students and faculty see only their own records. Filter querysets by the logged-in user; never trust an ID from the URL or form on its own.
  - How an `auth_user` row maps to its `students`/`faculty` row is decided when the schema is written. Record that decision here.
- **Java bridge view** (`core`):
  - Pass arguments as a list and **never use `shell=True`**.
  - Accept only commands from an allow-list, and validate their arguments with a Form.
  - Always set a `timeout`.
  - Handle `FileNotFoundError` (Java missing or JAR not built), `subprocess.TimeoutExpired` and a non-zero `returncode` by showing stderr as a user-facing error. The page must never return a 500 because the JAR is absent.

### SE Lab (`docs/`)

- Write documents in Markdown and diagrams as Mermaid code blocks, so they render on GitHub/VS Code and diff cleanly.
- Expected artifacts:
  - SRS (IEEE 830-style)
  - Use-case diagram
  - ER diagram (must match `01_schema.sql`)
  - Class diagram (must match `java_engine` models/dao)
  - DFD level 0/1
  - Sequence diagram for the Django → Java bridge
  - Test plan and test cases
- Update a diagram in the same commit as the code change that affects it.

## Setup, build and run

**Prerequisites:**
- MySQL Server 8.0.16+. The default Windows install is at `C:\Program Files\MySQL\MySQL Server 8.0\bin`; add it to PATH.
- JDK 17+ (`JAVA_HOME` set, or `java` on PATH).
- Python 3.10+.
- No global Maven install is needed. `java_engine/mvnw` (macOS/Linux) and `java_engine\mvnw.cmd` (Windows) download the pinned Maven version into `~/.m2/wrapper` on first run.

Run every command from the repo root unless a step says to `cd`. For a fresh machine, go in this order: `.env` → SQL scripts → Maven build → Django migrate → runserver.

```powershell
# 1. Shared config
Copy-Item .env.example .env          # bash: cp .env.example .env — then set DB_PASSWORD

# 2. Database (MySQL client, started from the repo root)
mysql -u root -p
#   mysql> source database/01_schema.sql
#   mysql> source database/02_views.sql
#   mysql> source database/03_triggers.sql
#   mysql> source database/04_seed.sql

# 3. Java engine
cd java_engine
.\mvnw.cmd clean package             # bash: ./mvnw clean package  -> target/smart-campus-engine.jar
java -jar target/smart-campus-engine.jar <command> [args]
cd ..

# 4. Django portal
python -m venv .venv
.venv\Scripts\Activate.ps1           # bash: source .venv/bin/activate
pip install -r requirements.txt
cd campus_portal
python manage.py migrate             # Django's own tables only
python manage.py createsuperuser
python manage.py runserver           # http://127.0.0.1:8000/
```

## Gotchas

- **Stay on Django 5.2 LTS.** Django 6.1 requires MySQL 8.4+, and this project targets MySQL 8.0. 5.2 LTS is supported until April 2028.
- **PowerShell has no `<` redirection,** so `mysql -u root -p < database\01_schema.sql` fails there. Use `source` inside the client as shown above, or wrap the command in `cmd /c "…"`.
- **Keep `cryptography` in requirements.txt.** PyMySQL needs it to authenticate against MySQL 8's default `caching_sha2_password`.
- **The JDBC URL needs `allowPublicKeyRetrieval=true`** when `useSSL=false`. Without it, Connector/J fails with "Public Key Retrieval is not allowed". This setting is for local development only.
- **Timestamps are UTC.** Django (`USE_TZ = True`) writes `DATETIME` values in UTC. Java therefore uses `connectionTimeZone=UTC`, and SQL scripts use `UTC_TIMESTAMP()`, not `NOW()`.
- **`.env` must be plain `KEY=value`.** python-dotenv strips quotes, but the Java parser doesn't, so a quoted password works in Django and fails in Java.
- **`migrate` never creates domain tables.** If Django reports a missing table, re-run the SQL scripts.
- **Triggers change rows behind the ORM.** Call `obj.refresh_from_db()` after `save()` when a trigger modifies that row.
- **Django runs the last *built* JAR.** Re-run `.\mvnw.cmd clean package` (or `./mvnw clean package`) after any Java change.
- **Keep `mvnw` on LF line endings.** `.gitattributes` enforces this. A CRLF `mvnw` fails on macOS/Linux with `/bin/sh^M: bad interpreter`.
- **Trigger and procedure scripts need `DELIMITER $$`** when run through the `mysql` client.
