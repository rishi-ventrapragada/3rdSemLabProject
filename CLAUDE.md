# Smart Campus & Academic Suite

One codebase that satisfies four 3rd-semester lab courses. Each lab owns a top-level folder, and the Django and Java code both run against **one MySQL database, `smart_campus_db`**.

| Lab | Folder | Stack | Deliverable |
|---|---|---|---|
| DBMS Lab | `database/` | MySQL 8.0, raw SQL | 3NF schema with PK/FK/CHECK constraints, views, triggers, seed data |
| Java Lab | `java_engine/` | Java 17, Maven, raw JDBC (`mysql-connector-j`) | OOP domain model + DAO layer, packaged as a runnable CLI JAR |
| Django Lab | `campus_portal/` | Django 5.2 LTS, PyMySQL, vanilla HTML5/CSS3 | Role-based web portal for Admin, Faculty and Student |
| SE Lab | `docs/` | Markdown + Mermaid diagrams | SRS, UML/ER diagrams, test plans |

**Status: Phase 4 (Django Lab) is complete.**
- Phase 1: scaffolding and build config.
- Phase 2: the MySQL schema, views, triggers, seed data, `init_db.py`, and the ER/FD write-up in `docs/database_design.md`.
- Phase 3: the Java engine (config, models, DAOs, services, exceptions, CLI with `--json`) and its tests.
- Phase 4: the Django portal (unmanaged models, role-based Student/Faculty/Admin portals, the Java bridge page, `seed_demo_users`) and its tests. See `docs/django_portal.md`.

**Open item:** a known database bug, case-insensitive `REGEXP` CHECKs; see Gotchas. The fix in `database/` is waiting for approval.

The SE Lab documents (SRS, UML, test plan) are still to come. Update this file when a phase lands.

## Repository layout

```
3rdSemLabProject/
├── .env.example            # shared DB credentials template → copy to .env (git-ignored)
├── requirements.txt        # Python deps for campus_portal
├── database/               # DBMS Lab: raw MySQL scripts, run in this order:
│   ├── schema.sql          #   1. CREATE DATABASE + 10 3NF tables and constraints
│   ├── views_triggers.sql  #   2. fn_* functions, v_* views, trg_* triggers, sp_* procedures
│   ├── seed_data.sql       #   3. demo data: 3rd-sem CSE, 2026-27
│   └── init_db.py          #   runs 1-3 via PyMySQL using .env, then prints row counts
├── java_engine/            # Java Lab: Maven project
│   ├── pom.xml             #   builds target/smart-campus-engine.jar (fat JAR, driver bundled)
│   ├── mvnw, mvnw.cmd      #   Maven Wrapper; downloads Maven 3.9.16 on first run (.mvn/wrapper/)
│   ├── src/main/java/com/smartcampus/
│   │   ├── Main.java       #   entry point: delegates to cli.Cli, then System.exit(code)
│   │   ├── config/         #   DatabaseConfig (env vars, then .env), ConnectionFactory
│   │   ├── models/         #   Person -> Student/Faculty, Course, Enrollment, AttendanceRecord,
│   │   │                   #   Marks; records for view rows (AttendanceSummary, GpaReportRow, ...)
│   │   ├── dao/            #   CrudDao<T,ID> + entity DAO interfaces, Jdbc*Dao, ReportDao (views/procedure)
│   │   ├── services/       #   StudentService, ReportService (incl. concurrent dashboard)
│   │   ├── exceptions/     #   SmartCampusException hierarchy (all checked)
│   │   └── cli/            #   command registry, arg parsing, text tables, JsonWriter
│   └── src/test/java/      #   JUnit 6 tests; no database needed
├── campus_portal/          # Django Lab (run manage.py from inside this folder)
│   ├── manage.py
│   ├── campus_portal/      #   settings (reads ../.env), urls; __init__.py installs PyMySQL as MySQLdb
│   ├── core/               #   unmanaged models, roles.py (role_required / RoleRequiredMixin),
│   │                       #   services.py (all writes), db_errors.py (friendly DB errors),
│   │                       #   java_bridge.py + /engine/ view, test_runner.py, tests/
│   ├── accounts/           #   login/logout, "/" role redirect, seed_demo_users command
│   ├── student_portal/     #   /student/        own profile, attendance, marks, CGPA, warning
│   ├── faculty_portal/     #   /faculty/        own courses, timetable, roster, attendance, marks
│   ├── admin_portal/       #   /admin-portal/   dashboards, CRUD, enrollments, timetable, reports
│   ├── templates/          #   base.html, 403/404, per-app folders, includes/form_fields.html
│   └── static/css/         #   campus.css (hand-written)
└── docs/                   # SE Lab documentation
    ├── database_design.md  #   ER diagram, functional dependencies, business-rule map
    └── django_portal.md    #   URL map, role matrix, bridge sequence diagram
```

## How Django and Java share `smart_campus_db`

### 1. One set of credentials: the repo-root `.env`

Both stacks read `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` and `DB_PASSWORD`. Never hard-code credentials. When you add a variable, add it to `.env.example` too, and prefix Django-only variables with `DJANGO_`.

- **Django:** `settings.py` calls `load_dotenv(BASE_DIR.parent / ".env")` (`BASE_DIR` is `campus_portal/`) and builds `DATABASES["default"]` with `ENGINE = "django.db.backends.mysql"`. `campus_portal/campus_portal/__init__.py` calls `pymysql.install_as_MySQLdb()` so the MySQL backend runs on PyMySQL. That avoids building `mysqlclient`, which needs a C compiler on Windows.
- **Java:** the `config` package reads real environment variables first. If they're missing, it parses `.env`, searching upward from the working directory. It builds `jdbc:mysql://${DB_HOST}:${DB_PORT}/${DB_NAME}?useSSL=false&allowPublicKeyRetrieval=true&connectionTimeZone=UTC`.

### 2. Schema ownership: the SQL scripts are the source of truth

- Every domain table, view, trigger and routine is created by `database/*.sql`. Django migrations never create them.
- Django models for those tables and views declare `class Meta: managed = False` and `db_table = "<table>"`. To bootstrap them, run `python manage.py inspectdb` and clean up the output.
- `python manage.py migrate` creates only Django's own tables (`auth_*`, `django_*`) in the same database.
- To change the schema, do all of these in one commit:
  1. Edit and re-run the SQL.
  2. Update the unmanaged Django model.
  3. Update the Java model and DAO.
  4. Update the ER diagram in `docs/`.

### 3. Linking Django logins to people (decided in Phase 2)

`students` and `faculty` each carry `username VARCHAR(150) NOT NULL UNIQUE` and `email VARCHAR(254) NOT NULL UNIQUE`.
- **The link:** a Django login belongs to the person whose `username` equals `auth_user.username`.
- **No foreign key to `auth_user`,** so `schema.sql` and `seed_data.sql` stay self-contained for the DBMS Lab and the Java engine, and the SQL scripts never depend on `migrate` having run.
- **The role is derived, never stored** (`core/roles.py`): a superuser is **Admin**; a username found in `students` is **Student**; one found in `faculty` is **Faculty**. There are no Django Groups. A login matching none of these gets a 403 page.
- **Creating or syncing `auth_user` rows** must use the same username; `manage.py seed_demo_users` does this for the demo data.
- **To find the logged-in person,** use `core.roles.get_person(request.user)`, which returns the `Student` or `Faculty` row and is cached per request. Never take a person id from the URL.
- **Usernames are unique across both tables.** The `trg_students_before_*` / `trg_faculty_before_*` triggers reject a username that already exists in the other table, so a login can never map to two people.
- **Seed conventions:** student usernames are the lower-case roll number (`25cse001`), and faculty usernames are `first.last` (`ananya.rao`).

### 4. Invariants live in the database

Either application can write, so put the rules that must always hold in the database: FK, UNIQUE and CHECK constraints, plus triggers. Python or Java can repeat a check for friendlier error messages, but it must not be the only enforcement.

### 5. Django → Java bridge

A role-guarded utility view in the `core` app runs the compiled JAR:

```python
subprocess.run(
    [settings.JAVA_BIN, "-jar", str(settings.JAVA_ENGINE_JAR), command, *args],
    capture_output=True, text=True, timeout=60, cwd=settings.REPO_ROOT,
)
```

- **Implemented in `core/java_bridge.py`;** nothing else in Django may run a subprocess. The admin-only page `/engine/` uses it.
  - An allow-list covers `defaulters`, `gpa-report`, `dashboard`, `refresh-defaulters`, `student` and `enroll`, and every argument is matched against a strict regex.
  - `run_engine()` returns `EngineResult(command, data, elapsed_ms)` or raises `EngineError(error_type, message, hint, exit_code)`.
  - Bridge-side error types are `JarMissing`, `JavaMissing`, `Timeout`, `BadOutput`, `NotAllowed` and `BadArgument`. All other types come from the engine's stderr JSON.
- The actual argv is `java -Dfile.encoding=UTF-8 -jar <jar> <command> [args] [--year Y] --json`. The `-D` flag makes Java 17 write UTF-8 to a pipe; without it, Windows uses Cp1252.
- `JAVA_ENGINE_JAR` defaults to `REPO_ROOT / "java_engine" / "target" / "smart-campus-engine.jar"`, `JAVA_BIN` to `"java"` and `JAVA_ENGINE_TIMEOUT` to 30 s. Override them with `DJANGO_JAVA_ENGINE_JAR`, `DJANGO_JAVA_BIN` and `DJANGO_JAVA_ENGINE_TIMEOUT` in `.env`.
- The child process inherits Django's `os.environ`, which python-dotenv has already filled with the `DB_*` variables. The JAR therefore connects with the same credentials and needs no extra configuration.
- The same JAR runs standalone: `java -jar java_engine/target/smart-campus-engine.jar <command> [args]`.
- **CLI contract:** the result goes to stdout and error messages go to stderr. Exit codes are `0` for success, `1` for a runtime or database error and `2` for bad usage. Commands that Django calls must never prompt on stdin.
- **Django always passes `--json`.** Each call prints exactly one line of JSON:
  - Success, on stdout: `{"ok":true,"command":"<name>","data":...}`.
  - Failure, on stderr: `{"ok":false,"command":"<name>","error":{"type":"<Type>","message":"..."}}`.
  - Parse stdout when `returncode == 0`, otherwise parse stderr.
  - Keys are snake_case, matching the database columns.
  - Branch on `error.type`, never on the message: `Usage`, `StudentNotFound`, `CourseNotFound`, `EntityNotFound`, `DuplicateEnrollment`, `Validation`, `Database` or `Internal`.

#### Engine commands

`java -jar smart-campus-engine.jar <command> [args] [--json]`. Lookups are case-insensitive, because of the column collation.

| Command | Data source | `--json` `data` |
|---|---|---|
| `student <rollNo>` | `students` + `v_attendance_summary` + `marks` | student object with a `courses` list (attendance + `marks` or null) |
| `whois <username>` | `students`, then `faculty` | person object; `role` is `Student` or `Faculty` |
| `attendance <rollNo>` | `v_attendance_summary` | list of per-course rows |
| `attendance <rollNo> <courseCode>` | `attendance_records` | `{..., "sessions": [{"session_date","status"}]}` |
| `defaulters` | `v_defaulter_list` | `{"student_count","course_count","students":[{..., "courses":[...]}]}` |
| `gpa-report` | `v_student_cgpa_report` | list, sorted by `weighted_gpa` desc (nulls last), then roll number |
| `courses` | `courses` | list |
| `enroll <rollNo> <courseCode> [--year YYYY-YY]` | inserts into `enrollments` | `{"enrollment_id",...}`. Default year is the current academic year (it rolls over in July). |
| `refresh-defaulters` | `CALL sp_refresh_defaulter_flags()` | `{"flagged_students": n}` |
| `dashboard` | the three views, loaded concurrently | counts, averages, top 3, per-view `tasks` with thread names and timings |
| `help` | — | list of `{name, usage, summary}`. `<command> --help` shows one command. |

## Coding standards

### DBMS Lab (`database/`)

- **Target:** MySQL 8.0 (8.0.16+ is needed for CHECK constraints to be enforced). Use InnoDB and `utf8mb4` / `utf8mb4_unicode_ci`.
- **Three scripts, always run in this order:** `schema.sql` → `views_triggers.sql` → `seed_data.sql`. `database/init_db.py` runs them and is the normal way to (re)build the database.
  - `schema.sql` starts with `CREATE DATABASE IF NOT EXISTS smart_campus_db …`.
  - Every file starts with `USE smart_campus_db;` for manual `source` runs. `init_db.py` skips `USE` / `CREATE DATABASE` and uses `DB_NAME` instead.
  - Add new objects to the matching file rather than creating new numbered files.
- **Every script must be re-runnable:**
  - Tables: `DROP TABLE IF EXISTS` (children before parents), then `CREATE TABLE`.
  - Views: `CREATE OR REPLACE VIEW`.
  - Triggers, functions and procedures: `DROP … IF EXISTS`, then `CREATE`.
  - Seed data: `DELETE … WHERE <pk> > 0` (children first) before inserting. The `WHERE` keeps Workbench safe-update mode happy.

  Never drop or alter Django's tables (`auth_*`, `django_*`).
- **`init_db.py` must keep parsing every script.** Its splitter understands `DELIMITER`, quotes and `--` / `#` / `/* */` comments. Avoid client-only commands other than `DELIMITER`, such as `SOURCE` or `\G`.
- **Explicit 3NF:**
  - Atomic columns with no comma-separated lists or repeating groups (1NF).
  - No attribute depends on only part of a key (2NF).
  - No transitive dependencies (3NF). For example, a student row stores `department_id`, never the department name.
  - Reference data such as departments, programmes and semesters gets its own table.
  - Derived values such as GPA or attendance % are computed in views, not stored. If a trigger maintains a stored copy instead, document why. The current exceptions are `marks.total_marks/grade_points/letter_grade` (trigger-maintained), `students.cgpa` (official, includes earlier semesters) and `students.is_defaulter` (declared by `sp_refresh_defaulter_flags()`). See `docs/database_design.md`.
  - Write each table's functional dependencies down in `docs/database_design.md`.
- **Naming:**
  - Tables are plural snake_case (`students`, `attendance_records`). `faculty` is the exception, since it is already a collective noun.
  - The PK is `<entity>_id INT AUTO_INCREMENT`. Established short forms: `dept_id`, `slot_id`, `entry_id`, `mark_id`, `attendance_id`.
  - An FK column has the same name and type as the PK it references.
  - Constraints are named `pk_<table>`, `fk_<table>_<referenced>`, `uq_<table>_<cols>` and `chk_<table>_<rule>`.
  - Stored functions are `fn_<purpose>`, and procedures are `sp_<purpose>`.
- **Single-column surrogate PK on every table**, including junction tables. Enforce the natural key with a `UNIQUE` constraint instead. This keeps Django unmanaged models and Java DAOs simple.
- **Foreign keys:** declare every FK explicitly with `ON DELETE` / `ON UPDATE`. Default to `RESTRICT`. Use `CASCADE` only for rows that cannot exist without their parent.
- **Views:** `v_<purpose>` (`v_attendance_summary`, `v_defaulter_list`, `v_student_cgpa_report`). They are read-only reporting surfaces for both Django (unmanaged models, one unique column marked `primary_key=True`) and Java DAOs. Reuse a view rather than re-implementing its join in application code.
- **Triggers:**
  - Name them `trg_<table>_<before|after>_<insert|update|delete>`. A rule-named trigger such as `trg_prevent_timetable_faculty_clash` is fine, but its UPDATE twin then gets an `_update` suffix.
  - A MySQL trigger fires on exactly one event, so a "before save" rule needs an INSERT and an UPDATE trigger. Share their logic through an `fn_*` function, as the marks triggers do.
  - Wrap the body in `DELIMITER $$ … $$ DELIMITER ;`.
  - Reject bad data with `SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '…'`. That reaches Java as `SQLException` and Django as `django.db.utils.OperationalError` (error 1644, verified). CHECK violations are also `OperationalError` (3819); UNIQUE and FK violations are `IntegrityError` (1062 / 1451 / 1452).
  - Use triggers for cross-row rules and audit trails that CHECK constraints can't express.
- **Seed data** (`seed_data.sql`): insert parents before children with realistic demo data. Login accounts are created through Django, not SQL, because Django hashes passwords.

### Java Lab (`java_engine/`)

- **Toolchain:** Java 17 (`maven.compiler.release`) and Maven. Use no frameworks: no Spring, Hibernate/JPA or connection pools. The lab assesses raw JDBC and core OOP.
- **Package responsibilities:**
  - `config`: loads DB settings (environment variables, then `.env`) and hands out `Connection`s via `DriverManager`, one new connection per call.
  - `models`: plain domain classes, plus Java `record`s for read-only view rows. No SQL.
  - `dao`: one interface per entity plus a JDBC implementation (e.g. `StudentDao` / `JdbcStudentDao`). Only `dao` and `config` import `java.sql`. `JdbcDaoSupport` holds the shared `queryList` / `queryOne` plumbing.
  - `services`: business rules and orchestration. They depend on DAO *interfaces*, never on implementations.
  - `exceptions`: the project's exception hierarchy.
  - `cli`: argument parsing, the command registry, text tables and JSON output. `cli.Engine` is the only class that names the `Jdbc*Dao` implementations.
- **Don't re-implement database logic in Java.** Attendance %, the 75% threshold, grades and GPA come from the views and triggers. Java reads them, then filters, groups and sorts. The one Java-only rule is the semester match when enrolling; see the app-level rules in `docs/database_design.md`.
- **OOP requirements** (each must be visibly present):
  - *Abstraction:* abstract base classes hold shared state and declare abstract behaviour (e.g. `Person` → `Student`, `Faculty`).
  - *Inheritance and polymorphism:* subclasses override base behaviour, and services work with base types and interfaces.
  - *Interfaces:* a generic `CrudDao<T, ID>` is extended by entity DAOs, and services are coded against the interfaces.
  - *Encapsulation:* private fields, with validation in constructors and setters. Override `equals`/`hashCode`/`toString` on models.
  - *Custom exceptions:* every exception is checked and extends the root `SmartCampusException`:
    - `DatabaseException` wraps `SQLException` and exposes the MySQL error code.
    - `EntityNotFoundException` is the parent of `StudentNotFoundException` and `CourseNotFoundException`.
    - `DuplicateEnrollmentException` covers MySQL error 1062.
    - `ValidationException` covers CHECK error 3819 and app-level rules.
    - `getType()` (the class name minus "Exception") becomes `error.type` in JSON.

    DAOs catch `SQLException` and rethrow it wrapped, keeping the cause. Never swallow an exception or `printStackTrace()` and carry on.
  - *Collections:* use `List`/`Set`/`Map` (and streams) for in-memory processing. Declare variables by interface type (`List<Student> s = new ArrayList<>()`). Return empty collections, never `null`.
  - *Where each lab requirement is shown:*
    - Abstract class and polymorphism: `Person.describe()`, overridden by `Student` and `Faculty`; `whois` returns a `Person`.
    - Interface with default methods: `CrudDao.getById` / `existsById`, `StudentDao.getByRollNumber`.
    - Generics: `CrudDao<T, ID>`, `RowMapper<T>`, `TableFormatter<T>`, `TaskResult<T>`.
    - Multithreading: `ReportService.dashboard()` uses `CompletableFuture` on a 3-thread pool, with one connection per task.
    - Streams: `groupingBy`, `toMap`, and comparators.
    - Transactions: `JdbcReportDao.refreshDefaulterFlags`.
- **JDBC rules:**
  - Always use `PreparedStatement` with `?` placeholders. Never concatenate values into SQL.
  - Open `Connection`, `PreparedStatement` and `ResultSet` in try-with-resources.
  - For multi-statement writes, call `setAutoCommit(false)`, then `commit()`, and `rollback()` in the `catch`.
  - Map rows to objects in one private `mapRow(ResultSet)` helper per DAO.
  - Column names must match `database/schema.sql` exactly.
- **CLI:** `Main` delegates to `cli.Cli`, which parses `<command> [args]` and dispatches to services, following the stdout/stderr/exit-code contract above.
  - To add a command, register a `Command` in `cli/Commands.java` with its argument range and allowed options, and add a `TextRenderer` method and a `JsonMapper` method.
  - Never hand-build JSON strings; always go through `JsonWriter`, which handles the escaping.
  - An interactive menu is fine for standalone demos, but only behind an explicit command such as `menu`.
- **Tests:** `src/test/java` runs on every `mvnw package` and must not need a database. To check against real data, run the commands against MySQL. If you insert demo rows to do so, restore the seed afterwards with `python database/init_db.py --yes`.

### Django Lab (`campus_portal/`)

- **MVT, kept clean:**
  - *Models:* all live in `core/models.py`, as unmanaged mirrors of the SQL tables and views (see Schema ownership).
    - Foreign keys use `DO_NOTHING`, so MySQL's `ON DELETE` rules apply.
    - Trigger-computed columns (`marks.total_marks/grade_points/letter_grade`) and `students.is_defaulter` are `editable=False`.
    - **Never add a managed model with a ForeignKey to one of them.** `migrate` would create a real FK constraint, and `init_db.py`'s `DROP TABLE` would then fail.
  - *Views:* thin. They handle requests, call an app-level `services.py` for non-trivial logic, and render templates.
  - *Writes:* every write goes through `core/services.py`, which wraps it in `transaction.atomic()` and turns a database rejection (trigger SIGNAL, UNIQUE, CHECK, FK) into a `ServiceError` with a friendly message from `core/db_errors.py`. For a new named constraint, add its message to `CONSTRAINT_MESSAGES` there. ModelForms save through `services.save_form(form)`, which puts the message on the form.
  - *No duplicated business logic:* reports read the views (`AttendanceSummary`, `DefaulterRow`, `GpaReportRow`), and "declare defaulters" calls the procedure. Marks writes set only `internal_marks` / `external_marks`. Never compare against 75 or compute grades in Python or templates. To highlight defaulter rows, check membership in `DefaulterRow`.
  - *Templates:* presentation only.
  - All user input goes through Django Forms. Give each app's URLs a namespace (`app_name = "faculty"`) and always use `{% url %}` / `reverse()`, never hard-coded paths.
- **Templates and static files:**
  - Vanilla HTML5 + hand-written CSS3 only. **No Tailwind, Bootstrap or any other CSS framework or CDN stylesheet.** No JS frameworks; small vanilla JS only where unavoidable.
  - Use semantic elements (`header`, `nav`, `main`, `section`, `table`, `form`/`label`).
  - Keep one `templates/base.html` with `{% block %}`s, and have each role's layout extend it.
  - Put CSS in `static/css/`, with colours and spacing as custom properties in one place. Lay out with Flexbox/Grid and make it responsive with media queries.
  - Include `{% csrf_token %}` in every POST form.
- **Role-based portals:**
  - The role comes from `core.roles.get_role(user)`: superuser, else `students.username`, else `faculty.username`; see "Linking Django logins to people". After login, `/` redirects to the role's dashboard.
  - Prefixes: `/student/`, `/faculty/`, `/admin-portal/`, `/engine/` (admin-only Java bridge), `/accounts/login/` and `/accounts/logout/` (POST only). Django's built-in admin is a developer tool, not the Admin portal, and lives at `/django-admin/`.
  - Enforce access in **every** view with `@role_required(STUDENT|FACULTY|ADMIN)`, or `RoleRequiredMixin` with `allowed_roles` on class-based views, both from `core.roles`. Anonymous users are sent to login; a wrong role raises `PermissionDenied`, which renders the friendly `templates/403.html`. Hiding links in a template is not access control.
  - Students and faculty see only their own records. Filter querysets by `get_person(request.user)`; never trust an ID from the URL or form on its own. Faculty course pages check that `course.faculty` is the logged-in teacher and return 403 otherwise.
- **Java bridge** (`core/java_bridge.py`, `core/views.py`):
  - Pass arguments as a list and **never use `shell=True`**.
  - Accept only commands from the allow-list, and validate arguments with a Form (`core/forms.py`) and again in `build_command`.
  - Always set a `timeout`.
  - Handle a missing JAR (checked before starting Java), `FileNotFoundError`, `TimeoutExpired`, a non-zero `returncode` and non-JSON output by showing the error type and message. The page must never return a 500 because the JAR is absent.
  - **One engine call per request, never one per row.** Writes (`refresh-defaulters`, `enroll`) are POST + CSRF only.
- **Tests** live in `campus_portal/core/tests/`.
  - `core.test_runner.SmartCampusTestRunner` creates `test_<DB_NAME>`, runs Django's migrations, then loads the real `database/*.sql` (seed included) using `init_db.py`'s splitter, so tests never touch the development database.
  - Real-database tests subclass `core.tests.base.CampusTestCase`, which seeds the demo users. Mock `core.java_bridge.subprocess.run` (or `core.views.java_bridge.run_engine`) rather than calling Java.

### SE Lab (`docs/`)

- Write documents in Markdown and diagrams as Mermaid code blocks, so they render on GitHub/VS Code and diff cleanly.
- Expected artifacts:
  - SRS (IEEE 830-style)
  - Use-case diagram
  - ER diagram and functional dependencies (`database_design.md`, must match `schema.sql`)
  - Class diagram (must match `java_engine` models/dao)
  - DFD level 0/1
  - Sequence diagram for the Django → Java bridge (`django_portal.md`)
  - Test plan and test cases
- Update a diagram in the same commit as the code change that affects it.

## Setup, build and run

**Prerequisites:**
- MySQL Server 8.0.16+. The default Windows install is at `C:\Program Files\MySQL\MySQL Server 8.0\bin`; add it to PATH.
- JDK 17+ (`JAVA_HOME` set, or `java` on PATH).
- Python 3.10+.
- No global Maven install is needed. `java_engine/mvnw` (macOS/Linux) and `java_engine\mvnw.cmd` (Windows) download the pinned Maven version into `~/.m2/wrapper` on first run.

Run every command from the repo root unless a step says to `cd`. For a fresh machine, go in this order: `.env` → virtualenv → database → Maven build → Django migrate → runserver.

```powershell
# 1. Shared config
Copy-Item .env.example .env          # bash: cp .env.example .env — then set DB_PASSWORD

# 2. Python environment (needed by init_db.py and Django)
python -m venv .venv
.venv\Scripts\Activate.ps1           # bash: source .venv/bin/activate
pip install -r requirements.txt
#    If Activate.ps1 is blocked by the execution policy, skip activation and call the venv
#    directly, e.g. .venv\Scripts\python.exe database\init_db.py  (no system settings needed)

# 3. Database: creates smart_campus_db, runs the 3 scripts, prints row counts.
#    WARNING: drops and recreates all domain tables (asks first unless --yes).
python database/init_db.py           # --yes to skip the prompt, --no-seed for empty tables
#    Manual alternative with the mysql client (start it from the repo root):
#    mysql -u root -p   then   source database/schema.sql;  source database/views_triggers.sql;  source database/seed_data.sql;

# 4. Java engine
cd java_engine
.\mvnw.cmd clean package             # bash: ./mvnw clean package  -> runs tests, builds target/smart-campus-engine.jar
cd ..
java -jar java_engine/target/smart-campus-engine.jar help
java -jar java_engine/target/smart-campus-engine.jar defaulters --json

# 5. Django portal (virtualenv from step 2 active; without it use ..\.venv\Scripts\python.exe)
cd campus_portal
python manage.py migrate             # Django's own tables only (core's migration is all no-ops)
python manage.py seed_demo_users     # DEMO logins for every student/faculty row + "admin" (re-runnable)
python manage.py check
python manage.py test --noinput      # builds test_smart_campus_db from database/*.sql
python manage.py runserver           # http://127.0.0.1:8000/
```

Order between steps 3 and 5 doesn't matter, and both can be re-run. `init_db.py` never touches Django's tables, so logins survive a database rebuild, and `migrate` never touches the domain tables.

## Demo logins (DEMO ONLY)

`manage.py seed_demo_users` gives **every** demo account the same password: **`campus-demo-2026`**. It comes from `DJANGO_DEMO_PASSWORD` and defaults to that value.
- It exists only for local demos and lab evaluation.
- Never use it on a reachable server or for real people.
- The command refuses to run with `DJANGO_DEBUG` off unless you pass `--force`.

| Role | Usernames | Lands on |
|---|---|---|
| Admin (superuser) | `admin` | `/admin-portal/` |
| Faculty | `ananya.rao` (CS301), `kiran.kumar` (CS351, CS354), `meera.iyer` (CS352), `arjun.reddy` (CS353), `suresh.babu` (MA301) | `/faculty/` |
| Student | `25cse001` … `25cse010`. `25cse004` and `25cse009` are below 75% attendance and see the warning. | `/student/` |

## Gotchas

- **Stay on Django 5.2 LTS.** Django 6.1 requires MySQL 8.4+, and this project targets MySQL 8.0. 5.2 LTS is supported until April 2028.
- **Known DB bug, fix pending approval: the `REGEXP` CHECKs are case-insensitive.** Under `utf8mb4_unicode_ci`, `section REGEXP '^[A-Z]$'` also accepts `a`. The same applies to `chk_timetable_entries_section` and `chk_departments_dept_code`. The proposed fix is `REGEXP_LIKE(section, '^[A-Z]$', 'c')`. Until then, the Django test `test_check_constraint_message_for_bad_section` is marked as an expected failure.
- **Don't run `startproject` from the repo root.** There, the existing `campus_portal/` folder is importable as a package, and Django refuses the name. The project was created from inside the folder with `django-admin startproject campus_portal .`.
- **Django tests need a MySQL user that can `CREATE DATABASE`** and create functions/triggers (root locally). They build and drop `test_smart_campus_db`. Pass `--noinput`, or Django asks before deleting a leftover test database.
- **The test runner sets `DEBUG=False`,** so calling `seed_demo_users` from tests needs `force=True`. `CampusTestCase` already does this, and uses the MD5 password hasher so tests stay fast.
- **A bridge call takes about 0.7-1.1 s through the web server** (JVM start-up plus a fresh MySQL connection, measured on the dev server). That's fine for one call per page; never loop over rows calling the engine.
- **PowerShell 5.1 breaks multi-line `-c` arguments** (`manage.py shell -c "..."`) at embedded quotes. Put the code in a `.py` file instead.
- **Stopping `runserver` started from the venv needs two PIDs killed:** the venv launcher and its child Python process. Match them by command line, never by name alone.
- **PowerShell has no `<` redirection,** so `mysql -u root -p < database\schema.sql` fails there. Use `python database/init_db.py`, `source` inside the client, or wrap the command in `cmd /c "…"`.
- **Keep `cryptography` in requirements.txt.** PyMySQL needs it to authenticate against MySQL 8's default `caching_sha2_password`.
- **The JDBC URL needs `allowPublicKeyRetrieval=true`** when `useSSL=false`. Without it, Connector/J fails with "Public Key Retrieval is not allowed". This setting is for local development only.
- **Timestamps are UTC.** Django (`USE_TZ = True`) writes `DATETIME` values in UTC. Java therefore uses `connectionTimeZone=UTC`, and SQL scripts use `UTC_TIMESTAMP()`, not `NOW()`.
- **`.env` must be plain `KEY=value`.** python-dotenv strips quotes, but the Java parser doesn't, so a quoted password works in Django and fails in Java.
- **`migrate` never creates domain tables.** If Django reports a missing table, run `python database/init_db.py`.
- **Rebuilding the database erases domain data.** Both `init_db.py` and `schema.sql` drop and recreate every domain table. Dropping a table also drops its triggers, so always re-run `views_triggers.sql` after `schema.sql`; `init_db.py` does this for you.
- **Stored functions need privileges when binary logging is on** (the MySQL 8 default). `root` is fine. A non-root `DB_USER` gets error 1419 or 1418 on `CREATE FUNCTION/TRIGGER` unless the server sets `log_bin_trust_function_creators = 1`.
- **Re-declare defaulters after attendance changes.** `students.is_defaulter` only changes when `CALL sp_refresh_defaulter_flags();` runs. Use `v_defaulter_list` for live status.
- **Don't write the computed marks columns.** `total_marks`, `grade_points` and `letter_grade` are overwritten by triggers on every INSERT/UPDATE; write only `internal_marks` / `external_marks`.
- **Triggers change rows behind the ORM.** Call `obj.refresh_from_db()` after `save()` when a trigger modifies that row.
- **Django runs the last *built* JAR.** Re-run `.\mvnw.cmd clean package` (or `./mvnw clean package`) after any Java change.
- **Keep `mvnw` on LF line endings.** `.gitattributes` enforces this. A CRLF `mvnw` fails on macOS/Linux with `/bin/sh^M: bad interpreter`.
- **Trigger and procedure scripts need `DELIMITER $$`** when run through the `mysql` client.
- **The JAR finds `.env` by walking up from the working directory.** Running it from the repo root or from `java_engine/` both work. Real `DB_*` environment variables win over `.env`, so a stale variable in your shell silently points the JAR at the wrong database.
- **Each JAR call costs about half a second,** for JVM start-up plus a new MySQL connection. Django should make one call per page, never one per table row.
- **Don't hard-code `enrollment_id` (or any id) in tests or code.** InnoDB leaves gaps in AUTO_INCREMENT after `INSERT … SELECT` and after failed inserts; the first new enrollment after the seed is 64, not 61. Look rows up by natural key (roll number + course code).
- **Committing from Windows PowerShell 5.1:** piping a message into `git commit -F -` adds a UTF-8 BOM to the subject, and `-m` with embedded `"…"` gets split into extra arguments. Write the message to a file (UTF-8 without BOM) and use `git commit -F <file>`.
