"""Chapters 5-10, references and appendices."""

from collections import OrderedDict, defaultdict

from content_common import (CASES, FACTS, LIVE, MACHINE, TESTS, VERSIONS, case_table, count_status, diagram,
                            screen, snippet)


def _shot(r, name, caption):
    r.figure(screen(name), caption, rotate_if_wide=False)


def chapter5(r):
    loc = FACTS["loc"]
    rc = FACTS["schema"]["row_counts"]
    r.chapter(5, "System Development and Implementation")
    r.h2("5.1 Introduction")
    r.p("This chapter describes how the design of Chapter 4 was implemented: the development environment, the "
        "technologies, the database implementation, each module, the main algorithms and real code from the "
        "repository, followed by screenshots of the running system. The source code is version-controlled with "
        "Git; configuration management is described in Appendix A.")
    r.h2("5.2 Development environment")
    r.table(["Item", "Details"], [
        ["Processor", MACHINE["cpu"]],
        ["Memory", MACHINE["ram"]],
        ["Operating system", MACHINE["os"]],
        ["Editor / IDE", VERSIONS["vscode"]],
        ["Version control", VERSIONS["git"] + " with a GitHub remote"],
        ["Database server", "MySQL Community Server " + VERSIONS["mysql"]],
        ["Java", VERSIONS["java"] + "; build with " + VERSIONS["maven"]],
        ["Python", VERSIONS["python"] + " in a virtual environment (.venv)"],
        ["Shell", "Windows PowerShell 5.1 and Git Bash"],
    ], [1.6, 4.2], "Development environment", bold_first_col=True)
    r.h2("5.3 Technologies used")
    r.table(["Layer", "Technology", "Why it was chosen"], [
        ["Database", "MySQL 8.0 (InnoDB, utf8mb4)", "CHECK constraints, triggers, views, stored routines and "
                                                    "transactions; required by the DBMS lab"],
        ["Engine", "Java 17 + JDBC", "Core OOP and raw JDBC are what the Java lab assesses; LTS release"],
        ["Web", "Django 5.2 LTS (MVT)", "Built-in authentication, forms, CSRF, ORM and admin; LTS until 2028"],
        ["Front end", "HTML5 + CSS3 (no framework)", "Semantic markup and hand-written responsive CSS"],
        ["Integration", "subprocess + JSON", "Language-neutral contract between Django and the JAR"],
        ["Documentation", "Markdown, Mermaid, PlantUML", "Text sources versioned with the code"],
    ], [1.1, 1.8, 2.9], "Technologies", size=9.5, bold_first_col=True)
    r.h2("5.4 Programming languages")
    r.table(["Language / file type", "Files", "Lines"], [
        ["SQL (database/*.sql)", loc["SQL (database/*.sql)"]["files"], loc["SQL (database/*.sql)"]["lines"]],
        ["Python: database/init_db.py", loc["Python tooling (database/init_db.py)"]["files"],
         loc["Python tooling (database/init_db.py)"]["lines"]],
        ["Java (main)", loc["Java main (java_engine/src/main)"]["files"],
         loc["Java main (java_engine/src/main)"]["lines"]],
        ["Java (tests)", loc["Java tests (java_engine/src/test)"]["files"],
         loc["Java tests (java_engine/src/test)"]["lines"]],
        ["Python: Django (excluding tests)", loc["Django Python (excluding tests)"]["files"],
         loc["Django Python (excluding tests)"]["lines"]],
        ["Python: Django tests", loc["Django tests"]["files"], loc["Django tests"]["lines"]],
        ["HTML templates", loc["Templates (HTML)"]["files"], loc["Templates (HTML)"]["lines"]],
        ["CSS", loc["CSS"]["files"], loc["CSS"]["lines"]],
    ], [3.4, 1.0, 1.0], "Source size by language (counted from the repository)", bold_first_col=False)
    r.h2("5.5 Frameworks and libraries")
    r.table(["Name", "Version", "Purpose"], [
        ["Django", "5.2.18", "Web framework (portal)"],
        ["PyMySQL", "1.2.3", "Pure-Python MySQL driver, installed as MySQLdb"],
        ["python-dotenv", "1.2.4", "Loads the shared .env file"],
        ["cryptography", "50.0.2", "MySQL 8 caching_sha2_password authentication"],
        ["MySQL Connector/J", "9.7.0", "JDBC driver for the Java engine"],
        ["JUnit Jupiter", "6.1.3", "Java unit tests"],
        ["maven-shade-plugin", "3.6.2", "Builds the runnable fat JAR"],
    ], [1.8, 0.9, 3.1], "Frameworks and libraries", size=9.5)
    r.h2("5.6 Database implementation")
    r.p("The database is created by three re-runnable scripts executed in order by `database/init_db.py`, which "
        "reads the credentials from `.env`, splits the scripts (it understands `DELIMITER`, quotes and comments) "
        "and prints the row counts:")
    r.bullets([
        "`schema.sql`: `CREATE DATABASE`, then `DROP TABLE IF EXISTS` and `CREATE TABLE` for the 11 tables with "
        "named PK, FK, UNIQUE and CHECK constraints.",
        "`views_triggers.sql`: 2 functions, 4 views, 9 triggers and 1 procedure (each dropped and re-created).",
        f"`seed_data.sql`: demo data: {rc['departments']} departments, {rc['faculty']} faculty, "
        f"{rc['students']} students, {rc['courses']} courses, {rc['rooms']} rooms, {rc['time_slots']} time slots, "
        f"{rc['timetable_entries']} timetable entries, {rc['enrollments']} enrollments, "
        f"{rc['attendance_records']} attendance records and {rc['marks']} marks rows.",
        "`queries.sql`: lab demonstration queries (joins, subqueries, window functions, transactions); not run "
        "by init_db.py.",
    ])
    r.p("Django's own tables (`auth_*`, `django_*`) are created by `manage.py migrate` in the same database; "
        "`init_db.py` never touches them, so logins survive a rebuild.")
    r.h2("5.7 Module-wise implementation")
    modules = [
        ("5.7.1 Authentication and roles", "`accounts` uses Django's login view. `core/roles.py` derives the role "
         "(superuser, else a `students.username` match, else a `faculty.username` match) and caches the person "
         "per request. `role_required` and `RoleRequiredMixin` guard every view."),
        ("5.7.2 Student portal", "`student_portal/views.py` loads the student from the login, then reads "
         "`v_attendance_summary`, the marks, `v_student_cgpa_report` and the timetable for that student only. The "
         "warning banner appears when the student has rows in `v_defaulter_list`."),
        ("5.7.3 Faculty portal", "Course pages check that `course.faculty` is the logged-in teacher. The "
         "attendance sheet and marks sheet are formsets; saving calls `services.save_attendance` or "
         "`services.save_marks`, which write only the raw columns inside one transaction."),
        ("5.7.4 Admin portal", "Class-based list, create, update and delete views for students, faculty and "
         "courses with search and pagination; enrollment and timetable forms; reports that read the views; the "
         "\"declare\" button calls the stored procedure; the marks audit page reads `v_marks_audit`."),
        ("5.7.5 Java engine", "`Main` delegates to `cli.Cli`, which parses the arguments, looks the command up in "
         "the registry and calls a service. Services depend on DAO interfaces; `cli.Engine` wires the JDBC "
         "implementations. Output goes through a text renderer or `JsonWriter`."),
        ("5.7.6 Django to Java bridge", "`core/java_bridge.py` validates the command against an allow-list, "
         "builds the argument list, checks that the JAR exists, runs it with a timeout and parses the single "
         "JSON line. The `/engine/` view renders the result or a typed error card."),
    ]
    for title, text in modules:
        r.h3(title)
        r.p(text)
    r.h2("5.8 Algorithm or pseudocode")
    r.h3("5.8.1 Grading (database trigger)")
    r.code("BEFORE INSERT/UPDATE ON marks:\n"
           "  IF internal IS NULL OR external IS NULL THEN total, points, letter := NULL\n"
           "  ELSE total  := internal + external\n"
           "       points := fn_grade_points(total)   -- >=90:10, >=80:9, >=70:8, >=60:7, >=50:6, >=40:5, else 0\n"
           "       letter := fn_letter_grade(points)  -- O, A+, A, B+, B, P, F\n"
           "AFTER UPDATE ON marks:\n"
           "  IF NOT (old.internal <=> new.internal AND old.external <=> new.external) THEN\n"
           "      INSERT INTO marks_audit(old/new internal, old/new external, changed_at = UTC_TIMESTAMP())")
    r.h3("5.8.2 Defaulter detection and declaration")
    r.code("v_attendance_summary: for each enrollment\n"
           "    held := COUNT(records); attended := COUNT(status = 'PRESENT')\n"
           "    percentage := ROUND(100 * attended / held, 2)   (NULL when no classes held)\n"
           "v_defaulter_list := rows of v_attendance_summary with percentage < 75\n"
           "sp_refresh_defaulter_flags():\n"
           "    UPDATE students SET is_defaulter = (student_id IN v_defaulter_list)")
    r.h3("5.8.3 Role check on every request")
    r.code("role_required(roles)(view):\n"
           "    if user not authenticated: redirect to login with ?next=\n"
           "    role := superuser ? ADMIN : (username in students ? STUDENT : (username in faculty ? FACULTY : NONE))\n"
           "    if role not in roles: raise PermissionDenied  -> 403 page\n"
           "    return view(request)")
    r.h3("5.8.4 Bridge call")
    r.code("run_engine(command, args):\n"
           "    if command not in ALLOWED or any arg fails its regex: raise EngineError(NotAllowed/BadArgument)\n"
           "    if JAR file missing: raise EngineError(JarMissing)\n"
           "    proc := subprocess.run([java, -Dfile.encoding=UTF-8, -jar, JAR, command, args..., --json],\n"
           "                           shell=False, timeout=30)\n"
           "    if exit code 0: return data from the JSON line on stdout\n"
           "    else: raise EngineError(error.type from the JSON line on stderr)")
    r.h2("5.9 Important code snippets")
    r.p("The snippets below are copied from the repository without changes.")
    r.h3("5.9.1 Grade points function (database/views_triggers.sql)")
    r.code(snippet("database/views_triggers.sql", "CREATE FUNCTION fn_grade_points", "END$$"))
    r.h3("5.9.2 Timetable clash trigger (database/views_triggers.sql)")
    r.code(snippet("database/views_triggers.sql", "CREATE TRIGGER trg_prevent_timetable_faculty_clash\n"[:-1],
                   "END$$"))
    r.h3("5.9.3 Declaring defaulters (database/views_triggers.sql)")
    r.code(snippet("database/views_triggers.sql", "CREATE PROCEDURE sp_refresh_defaulter_flags", "END$$"))
    r.h3("5.9.4 Role check decorator (campus_portal/core/roles.py)")
    r.code(snippet("campus_portal/core/roles.py", "def role_required", "return decorator"))
    r.h3("5.9.5 Saving marks (campus_portal/core/services.py)")
    r.code(snippet("campus_portal/core/services.py", "def save_marks", "return saved"))
    r.h3("5.9.6 Running the engine (campus_portal/core/java_bridge.py)")
    r.code(snippet("campus_portal/core/java_bridge.py", "def run_engine", "def _parse", include_end=False), size=8)
    r.h3("5.9.7 Concurrent dashboard (java_engine/.../services/ReportService.java)")
    r.code(snippet("java_engine/src/main/java/com/smartcampus/services/ReportService.java",
                   "public Dashboard dashboard()", "pool.shutdown();") + "\n        }\n    }", size=8)
    r.h3("5.9.8 Transaction in JDBC (java_engine/.../dao/JdbcReportDao.java)")
    r.code(snippet("java_engine/src/main/java/com/smartcampus/dao/JdbcReportDao.java",
                   "public int refreshDefaulterFlags()", "Could not refresh defaulter flags") + "\n        }\n    }",
           size=8)
    r.h2("5.10 Implementation screenshots")
    r.p("The screenshots were captured with Playwright (Chromium, 1280 px wide) from the running development "
        "server, logged in as each demo role. No password or `.env` content is visible.")
    _shot(r, "02_student_defaulter", "Student dashboard of a defaulter (25cse004) with the 75% warning")
    _shot(r, "04_student_ok", "Student dashboard of a student in good standing (25cse001)")
    _shot(r, "05_faculty_dashboard", "Faculty dashboard: own courses and weekly timetable (ananya.rao)")
    _shot(r, "06_faculty_roster", "Faculty course roster for CS301")
    _shot(r, "07_faculty_attendance", "Faculty attendance sheet for a date")
    _shot(r, "08_faculty_marks", "Faculty marks sheet; totals and grades come from the database")
    _shot(r, "09_admin_dashboard", "Admin dashboard")
    _shot(r, "10_admin_students_search", "Admin student list with search and pagination")
    _shot(r, "11_admin_student_form", "Admin student form")
    _shot(r, "12_admin_timetable_clash", "Timetable clash refused by the trigger, shown as a readable message")
    r.h2("5.11 Integration of modules")
    r.p("The modules are integrated through the shared database and one process boundary:")
    r.bullets([
        "**Portal and database:** unmanaged Django models map 10 tables and the 4 views; all writes go through "
        "`core/services.py`, which wraps them in `transaction.atomic()` and converts database rejections into "
        "friendly messages.",
        "**Engine and database:** DAOs use `PreparedStatement` on the same tables and views; the configuration is "
        "read from the same `.env`.",
        "**Portal and engine:** `core/java_bridge.py` starts the JAR with an argument list and parses one line of "
        "JSON; the child process inherits the `DB_*` variables, so no extra configuration is needed.",
        "**Rules in one place:** grades, the 75% rule, clash checks and audit live in MySQL, so the two "
        "applications cannot disagree. Integration cases IT01-IT10 (Section 6.5) verify each path.",
    ])
    r.h2("5.12 Challenges faced during development")
    r.table(["Challenge", "How it was solved"], [
        ["`REGEXP` CHECK constraints accepted lower-case sections because the column collation is "
         "case-insensitive", "Rewrote them as `REGEXP_LIKE(col, pattern, 'c')` and added a regression test "
                            "(commit c96e1f6)"],
        ["Java 17 on Windows wrote Cp1252 to a pipe, corrupting JSON text", "The bridge passes "
                                                                            "`-Dfile.encoding=UTF-8`"],
        ["Building mysqlclient needs a C compiler on Windows", "Used PyMySQL installed as MySQLdb"],
        ["Connector/J refused to connect: \"Public Key Retrieval is not allowed\"",
         "Added `allowPublicKeyRetrieval=true` to the local JDBC URL"],
        ["PowerShell 5.1 adds a UTF-8 BOM to piped stdin", "The interactive menu strips the BOM"],
        ["AUTO_INCREMENT leaves gaps, so ids differ from expectations", "Tests look rows up by natural key"],
        ["Django 6.1 needs MySQL 8.4", "Stayed on Django 5.2 LTS"],
        ["JVM start-up plus a new connection costs about 0.7 s per call", "At most one engine call per page"],
    ], [2.9, 2.9], "Development challenges and solutions", size=9.5)
    r.h2("5.13 Summary")
    r.p(f"The system was implemented in about {sum(v['lines'] for k, v in loc.items() if isinstance(v, dict) and 'lines' in v)} "
        "lines of SQL, Java, Python, HTML and CSS. The database holds the rules, the Java engine and the Django "
        "portal share it, and a guarded bridge connects them. The next chapter shows how this implementation "
        "was tested.")


def _junit_by_class():
    groups = OrderedDict()
    for case in TESTS["maven"]["cases"]:
        g = groups.setdefault(case["class"], [0, 0, 0.0])
        g[0] += 1
        g[1] += case["status"] == "Pass"
        g[2] += case["seconds"]
    return [[k, v[0], v[1], v[0] - v[1], f"{v[2]:.3f}"] for k, v in groups.items()]


def _django_by_module():
    groups = OrderedDict()
    for case in TESTS["django"]["cases"]:
        g = groups.setdefault(f"core.tests.{case['module']}", [0, 0])
        g[0] += 1
        g[1] += case["status"] == "Pass"
    return [[k, v[0], v[1], v[0] - v[1]] for k, v in groups.items()]


def _jacoco_by_package():
    agg = defaultdict(lambda: [0, 0, 0, 0])
    for row in TESTS["maven"]["coverage"]:
        a = agg[row["PACKAGE"].replace("com.smartcampus", "") or "(root)"]
        a[0] += int(row["LINE_COVERED"])
        a[1] += int(row["LINE_MISSED"])
        a[2] += int(row["BRANCH_COVERED"])
        a[3] += int(row["BRANCH_MISSED"])
    rows, total = [], [0, 0, 0, 0]
    for pkg in sorted(agg):
        lc, lm, bc, bm = agg[pkg]
        total = [t + x for t, x in zip(total, agg[pkg])]
        rows.append([pkg.lstrip(".") or "(root)", lc + lm, f"{100 * lc / (lc + lm):.1f}%",
                     f"{100 * bc / (bc + bm):.1f}%" if bc + bm else "n/a"])
    lc, lm, bc, bm = total
    rows.append(["Total", lc + lm, f"{100 * lc / (lc + lm):.1f}%", f"{100 * bc / (bc + bm):.1f}%"])
    return rows


def _django_coverage_by_app():
    agg = defaultdict(lambda: [0, 0, 0, 0])
    for path, c in TESTS["django"]["coverage_files"].items():
        a = agg[path.split("/")[0]]
        a[0] += c["covered_lines"]
        a[1] += c["num_statements"]
        a[2] += c["covered_branches"]
        a[3] += c["num_branches"]
    rows = [[app, v[1], f"{100 * v[0] / v[1]:.1f}%" if v[1] else "n/a",
             f"{100 * v[2] / v[3]:.1f}%" if v[3] else "n/a"] for app, v in sorted(agg.items())]
    t = TESTS["django"]["coverage_totals"]
    rows.append(["Total", t["num_statements"], f"{100 * t['covered_lines'] / t['num_statements']:.1f}%",
                 f"{100 * t['covered_branches'] / t['num_branches']:.1f}%"])
    return rows


def chapter6(r):
    mv, dj = TESTS["maven"], TESTS["django"]
    all_cases = CASES["unit"] + CASES["integration"] + CASES["white_box"] + CASES["black_box"]
    passed, failed = count_status(all_cases)
    r.chapter(6, "Software Testing")
    r.h2("6.1 Introduction")
    r.p("Testing was done at four levels (unit, integration, system and acceptance) and with both white-box "
        "and black-box techniques. Two automated suites run on every build: "
        f"{mv['summary']['run']} JUnit tests for the Java engine and {dj['ran']} Django tests for the portal. "
        f"In addition, {len(all_cases)} documented test cases were executed by a script "
        "(`docs/src/evidence/collect_cases.py`) against the real MySQL database, the real JAR and the Django "
        "test client. **Every \"Actual result\" and \"Status\" in this chapter was produced by actually running "
        f"the tests on {TESTS['run_at'][:10]}**; nothing was typed in by hand. Test writes were made inside "
        "transactions that were rolled back, and the database was rebuilt from the seed afterwards.")
    r.h2("6.2 Testing objectives")
    r.bullets([
        "Verify every functional requirement FR1-FR20 at least once.",
        "Show that the database rejects invalid data even when the application is bypassed.",
        "Show that every page enforces its role and that users see only their own records.",
        "Exercise every branch of the grading function and the main decision points in the code.",
        "Measure response times of pages and engine commands.",
        "Find and fix defects before the final submission.",
    ])
    r.h2("6.3 Testing methodology")
    r.table(["Level / technique", "Tool", "What was run"], [
        ["Unit (Java)", "JUnit 6 via Maven Wrapper; JaCoCo", f"{mv['summary']['run']} tests, no database"],
        ["Unit + integration (Django)", "Django test runner; coverage.py", f"{dj['ran']} tests on a throwaway "
                                                                          "test_smart_campus_db built from the "
                                                                          "real SQL scripts"],
        ["Documented cases (UT, IT, WB, BB)", "collect_cases.py", f"{len(all_cases)} cases on the real database, "
                                                                 "JAR and Django client"],
        ["System and performance", "Playwright + dev server; CLI timing", "17 live pages, 6 CLI commands"],
        ["Acceptance", "Manual walk-through per role", "Section 6.10"],
    ], [1.8, 1.9, 2.1], "Test levels and tools", size=9.5)
    r.h2("6.4 Unit testing")
    r.p("Unit tests check one function or class in isolation. The documented unit cases are listed first, "
        "followed by the automated suites grouped by test class.")
    case_table(r, CASES["unit"], "Unit test cases")
    r.table(["JUnit test class", "Tests", "Passed", "Failed", "Time (s)"], _junit_by_class(),
            [2.6, 0.7, 0.7, 0.7, 0.9], f"JUnit results (mvnw clean package, build {mv['build']})", size=9.5)
    r.table(["Django test module", "Tests", "Passed", "Failed"], _django_by_module(), [3.0, 0.8, 0.8, 0.8],
            f"Django test results ({dj['ran']} tests, result: {dj['result_line']})", size=9.5)
    r.h2("6.5 Integration testing")
    r.p("Integration tests follow data across module boundaries: portal to database to trigger to another "
        "portal, and portal to bridge to JAR to view.")
    case_table(r, CASES["integration"], "Integration test cases")
    r.h2("6.6 System testing")
    r.p("The complete system was started (MySQL, the Django development server and the built JAR) and every "
        "main page was requested as the role that owns it, using Playwright. All returned HTTP 200 with real "
        "data; the screenshots in Sections 5.10 and 9.3 were taken in the same run.")
    r.table(["Logged in as", "Page", "HTTP status"], [[p["role_user"], p["path"], p["status"]]
                                                     for p in LIVE["pages"]], [1.4, 3.2, 1.0],
            "System test: live pages", size=9.5)
    r.h2("6.7 Functional testing")
    r.p("Each functional requirement is traced to the tests that exercise it:")
    r.table(["Requirement", "Test cases", "Result"], [
        ["FR1, FR2 (login, role)", "IT01, UT05, WB09-WB11", "Pass"],
        ["FR3 (password, logout)", "Django tests in test_access / test_polish", "Pass"],
        ["FR4-FR7 (student views, warning)", "IT02, Django test_portals, live page /student/", "Pass"],
        ["FR8-FR9 (faculty courses, attendance)", "IT03, BB13-BB15, BB35", "Pass"],
        ["FR10 (marks, grading)", "IT02, BB01-BB12, BB23-BB27, WB01-WB08, WB15-WB18", "Pass"],
        ["FR11 (CRUD)", "BB16-BB18, BB31, Django test_polish", "Pass"],
        ["FR12 (enroll)", "IT04, WB12-WB14, BB19-BB22, IT10", "Pass"],
        ["FR13 (timetable clash)", "IT05", "Pass"],
        ["FR14 (defaulters)", "IT07, BB28", "Pass"],
        ["FR15, FR17 (GPA report, audit)", "IT06, IT09, WB19-WB21", "Pass"],
        ["FR16 (engine page)", "IT08, BB30, UT03, UT04", "Pass"],
        ["FR18-FR20 (engine commands, CSV, dashboard)", "JUnit CliTest, ReportExporterTest; WB22-WB27", "Pass"],
    ], [2.2, 2.8, 0.8], "Requirement traceability", size=9.5)
    r.h2("6.8 Performance testing")
    r.p("Each page was requested five times per role on the development server (Section 5.2 hardware) and the "
        "median, minimum and maximum response times were recorded. Each engine command was run five times "
        "from the command line.")
    r.table(["Page", "User", "Median (ms)", "Min (ms)", "Max (ms)"],
            [[p["path"], p["role_user"], p["median_ms"], p["min_ms"], p["max_ms"]] for p in LIVE["pages"]],
            [2.4, 1.0, 0.8, 0.8, 0.8], "Page response times (5 requests each)", size=9)
    r.table(["Command", "Median (ms)", "Min (ms)", "Max (ms)"],
            [[f"java -jar ... {k}", v["median_ms"], v["min_ms"], v["max_ms"]]
             for k, v in CASES["cli_timings"].items()], [2.8, 1.0, 1.0, 1.0],
            "Java engine command times (5 runs each, including JVM start-up)", size=9.5)
    r.p("All ordinary pages answered in under 70 ms (median). Pages that call the engine took about 0.67-0.75 s, "
        "almost all of it JVM start-up and a new MySQL connection, which is why the design allows at most one "
        "engine call per page (NFR2). NFR1 (under 1 s) is met.")
    r.h2("6.9 Security testing")
    r.p("Security tests tried the attacks a student or outsider is most likely to attempt (error guessing). "
        "In addition, `core/tests/test_polish.py` walks the whole URL configuration and checks that every route "
        "redirects anonymous users to the login page and returns 403 to every role outside its own prefix.")
    case_table(r, [c for c in CASES["black_box"] if c["technique"] == "Error guessing"],
               "Security test cases (error guessing)")
    r.h2("6.10 User Acceptance Testing (UAT)")
    r.p("UAT was carried out as a developer walk-through: each scenario below was performed on the running "
        "system with the demo accounts, following the use cases of Section 3.9. No external users took part, "
        "so this is not a formal UAT with real staff and students; that remains future work (Section 8.7).")
    r.table(["ID", "Role", "Scenario", "Acceptance criterion", "Evidence", "Result"], [
        ["UAT1", "Student", "Open the dashboard as 25cse004", "Warning for courses below 75%",
         "Figure 5.1", "Accepted"],
        ["UAT2", "Student", "Open the dashboard as 25cse001", "No warning; grades and CGPA shown",
         "Figure 5.2", "Accepted"],
        ["UAT3", "Faculty", "Record CS301 attendance on a weekday", "Saved; percentage changes", "IT03",
         "Accepted"],
        ["UAT4", "Faculty", "Enter CS301 marks", "Total and grade computed", "IT02, Figure 5.6", "Accepted"],
        ["UAT5", "Faculty", "Open another teacher's course", "403 page", "BB35", "Accepted"],
        ["UAT6", "Admin", "Double-book a teacher in the timetable", "Readable clash message",
         "IT05, Figure 5.10", "Accepted"],
        ["UAT7", "Admin", "Declare defaulters", "25CSE004 and 25CSE009 flagged", "IT07", "Accepted"],
        ["UAT8", "Admin", "Run the engine dashboard", "Counts, averages and thread timings",
         "Figure 9.6", "Accepted"],
    ], [0.5, 0.65, 1.55, 1.45, 1.0, 0.7], "User acceptance walk-through", size=8.5)
    r.h2("6.11 Test cases and test results")
    r.p("This section groups the documented cases by technique. White-box cases were designed from the code "
        "and SQL; black-box cases from the requirements only.")
    wb, bb = CASES["white_box"], CASES["black_box"]
    r.h3("6.11.1 White-box testing: statement and branch coverage")
    r.p("`fn_grade_points` has eight branches (NULL, seven grade bands). One input per branch executes every "
        "statement and every branch.")
    case_table(r, [c for c in wb if c["technique"] == "Statement / branch coverage"],
               "Statement and branch coverage of fn_grade_points")
    case_table(r, [c for c in wb if c["technique"] == "Branch coverage"],
               "Branch coverage of role_required")
    r.h3("6.11.2 White-box testing: path coverage")
    r.p("`core.services.enroll_student` has three independent paths: semester mismatch, database rejection "
        "(duplicate) and success.")
    case_table(r, [c for c in wb if c["technique"] == "Path coverage"], "Path coverage of enroll_student")
    r.h3("6.11.3 White-box testing: condition coverage")
    r.p("Each atomic condition of the compound decisions was made true and false at least once.")
    case_table(r, [c for c in wb if c["technique"] == "Condition coverage"],
               "Condition coverage of MarksSheetForm.clean and trg_marks_after_update")
    r.h3("6.11.4 White-box testing: loop testing")
    r.p("The argument-parsing loop was run with zero, one and many arguments, and the `.env` search loop with "
        "zero, one and two parent-directory steps.")
    case_table(r, [c for c in wb if c["technique"] == "Loop testing"], "Loop testing")
    r.h3("6.11.5 Code coverage")
    r.table(["Java package", "Lines", "Line coverage", "Branch coverage"], _jacoco_by_package(),
            [2.2, 0.9, 1.3, 1.3], "JaCoCo coverage of the Java engine by the JUnit suite", size=9.5)
    r.p("The JUnit suite deliberately needs no database, so the JDBC DAO classes are exercised by the "
        "integration cases (IT08-IT10, WB22-WB27) and live runs rather than by unit tests. This is why the "
        "`dao` and `models` packages show 0% unit-test coverage and the total is low; the CLI, configuration "
        "and export code that the unit tests target is covered much better.", size=11)
    r.table(["Django app", "Statements", "Line coverage", "Branch coverage"], _django_coverage_by_app(),
            [2.2, 0.9, 1.3, 1.3], "coverage.py results for the Django suite", size=9.5)
    r.h3("6.11.6 Black-box testing: equivalence partitioning and boundary value analysis")
    r.p("Internal marks have one valid class (0-40) and invalid classes below 0, above 40 and non-numeric. "
        "Boundaries were tested just outside, on and just inside each limit, and the grade scale at its "
        "boundaries.")
    case_table(r, [c for c in bb if c["technique"] in ("Equivalence partitioning", "Boundary value analysis",
                                                        "Equivalence partitioning / boundary")],
               "Equivalence partitioning and boundary value test cases")
    r.h3("6.11.7 Black-box testing: decision tables", new_page=True)
    r.table(["Rule", "Semester matches", "Already enrolled", "Expected action"], [
        ["R1", "Y", "N", "Enroll"], ["R2", "Y", "Y", "Refuse: already enrolled"],
        ["R3", "N", "N", "Refuse: wrong semester"], ["R4", "N", "Y", "Refuse: wrong semester"],
    ], [0.6, 1.5, 1.5, 2.2], "Decision table: enrollment", size=9.5)
    r.table(["Rule", "Internal given", "External given", "Expected action"], [
        ["R1", "N", "N", "Nothing written"], ["R2", "Y", "N", "Store; no total or grade yet"],
        ["R3", "Y", "Y", "Store; total and grade computed"], ["R4", "N", "Y", "Form error"],
    ], [0.6, 1.5, 1.5, 2.2], "Decision table: marks entry", size=9.5)
    case_table(r, [c for c in bb if c["technique"] == "Decision table"], "Decision table test cases")
    r.h3("6.11.8 Black-box testing: state transition")
    r.p("The marks record moves through the states of Figure 4.14 and a student's defaulter flag through "
        "those of Figure 4.15.")
    case_table(r, [c for c in bb if c["technique"] == "State transition"], "State transition test cases")
    r.h2("6.12 Defect identification and correction", new_page=True)
    r.table(["ID", "Defect", "Found by", "Correction", "Status"], [
        ["D1", "CHECK constraints for section and department code used `REGEXP`, which is case-insensitive "
               "under utf8mb4_unicode_ci, so 'a' was accepted", "Django test "
                                                               "test_check_constraint_message_for_bad_section",
         "`REGEXP_LIKE(col, pattern, 'c')` in schema.sql (commit c96e1f6); test BB17 now passes", "Fixed"],
        ["D2", "Paginated faculty and course lists had no stable order (Django UnorderedObjectListWarning)",
         "Warning seen while collecting test evidence for this report", "`.order_by()` added in "
                                                                        "admin_portal/views.py (commit 6de2bea)",
         "Fixed"],
        ["D3", "Engine JSON written as Cp1252 when Java ran under a pipe on Windows", "Integrating the bridge on "
                                                                                      "Windows",
         "`-Dfile.encoding=UTF-8` added to the argv", "Fixed"],
        ["D4", "Menu misread the first command when input was piped from PowerShell (BOM)", "Piping commands into "
                                                                                            "`menu`",
         "BOM stripped in `InteractiveMenu.readLine()`", "Fixed"],
        ["D5", "Test assumed the next enrollment id would be 61; InnoDB left a gap (64)", "Testing `enroll` against MySQL",
         "Tests look rows up by roll number and course code", "Fixed"],
    ], [0.4, 1.9, 1.3, 1.6, 0.55], "Defects found and corrected", size=8.5)
    r.p("No open defects remained when the final test run was made.")
    r.h2("6.13 Test summary")
    by_kind = [("Unit", CASES["unit"]), ("Integration", CASES["integration"]), ("White-box", CASES["white_box"]),
               ("Black-box (incl. security)", CASES["black_box"])]
    rows = [[k, len(v), *count_status(v)] for k, v in by_kind]
    rows += [["JUnit suite", mv["summary"]["run"], mv["summary"]["run"] - mv["summary"]["failures"] -
              mv["summary"]["errors"], mv["summary"]["failures"] + mv["summary"]["errors"]],
             ["Django suite", dj["ran"], sum(c["status"] == "Pass" for c in dj["cases"]),
              sum(c["status"] != "Pass" for c in dj["cases"])],
             ["System test pages", len(LIVE["pages"]), sum(p["status"] == 200 for p in LIVE["pages"]),
              sum(p["status"] != 200 for p in LIVE["pages"])]]
    total = [sum(r_[i] for r_ in rows) for i in (1, 2, 3)]
    rows.append(["Total", *total])
    r.table(["Category", "Executed", "Passed", "Failed"], rows, [2.6, 1.0, 1.0, 1.0], "Test summary", size=9.5)
    r.p(f"All {total[0]} executed tests and cases passed in the final run ({passed} of {len(all_cases)} "
        f"documented cases, {mv['summary']['run']} JUnit tests, {dj['ran']} Django tests and "
        f"{len(LIVE['pages'])} live pages). Five defects found earlier were corrected before this run.")


def chapter7(r):
    bt = LIVE["build_timings"]
    r.chapter(7, "Deployment and Installation")
    r.h2("7.1 Introduction")
    r.p("This chapter explains how the system is installed and run. For the lab it is deployed on one Windows "
        "laptop; the same steps work on macOS and Linux with the shell commands adjusted.")
    r.h2("7.2 Deployment architecture")
    r.p("All components run on one machine (deployment diagram, Figure 4.17): the browser, the Django "
        "development server on port 8000, a JVM started for each engine call, and MySQL Server on port 3306. "
        "For a real deployment Django would run behind a production web server with TLS and "
        "`DJANGO_HTTPS=True`.")
    r.h2("7.3 Deployment environment")
    r.table(["Component", "Deployed as"], [
        ["Database", "MySQL Community Server 8.0.42, database smart_campus_db, localhost:3306"],
        ["Engine", "java_engine/target/smart-campus-engine.jar (fat JAR with the JDBC driver)"],
        ["Portal", "Django 5.2.18 development server, http://127.0.0.1:8000/"],
        ["Configuration", "Repository-root .env (git-ignored), copied from .env.example"],
        ["Client", "Any browser on the same machine"],
    ], [1.4, 4.4], "Deployment environment", bold_first_col=True)
    r.h2("7.4 System installation procedure")
    r.bullets([
        "Install MySQL Server 8.0.16+, JDK 17+ and Python 3.10+ (Maven is downloaded by the wrapper).",
        "Clone the repository and copy `.env.example` to `.env`; set `DB_PASSWORD`.",
        "Create the virtual environment: `python -m venv .venv`, then "
        "`.venv\\Scripts\\python.exe -m pip install -r requirements.txt`.",
        "Build the database: `.venv\\Scripts\\python.exe database\\init_db.py --yes`.",
        "Build the engine: `cd java_engine; .\\mvnw.cmd clean package` (runs the 29 JUnit tests).",
        "Prepare Django: `cd campus_portal`, then `manage.py migrate` and `manage.py seed_demo_users`.",
        "Start the portal: `manage.py runserver` and open http://127.0.0.1:8000/.",
    ], numbered=True)
    r.h2("7.5 Configuration details")
    r.p("All configuration is read from the repository-root `.env` file, which is git-ignored; only the "
        "template `.env.example` is committed. The values are not reproduced here.")
    r.table(["Variable", "Used by", "Meaning"], [
        ["DB_HOST, DB_PORT, DB_NAME", "Django, Java, init_db.py", "MySQL server and database name"],
        ["DB_USER, DB_PASSWORD", "Django, Java, init_db.py", "MySQL account (never committed)"],
        ["DJANGO_SECRET_KEY", "Django", "Signing key (required when DEBUG is off)"],
        ["DJANGO_DEBUG, DJANGO_ALLOWED_HOSTS", "Django", "Debug mode and host names"],
        ["DJANGO_HTTPS", "Django", "Turns on secure cookies, SSL redirect and HSTS"],
        ["DJANGO_DEMO_PASSWORD", "seed_demo_users", "Shared demo password (demo only)"],
        ["DJANGO_JAVA_BIN, DJANGO_JAVA_ENGINE_JAR, DJANGO_JAVA_ENGINE_TIMEOUT", "Bridge",
         "Java executable, JAR path and timeout (default 30 s)"],
    ], [2.4, 1.4, 2.0], "Configuration variables", size=9)
    r.h2("7.6 Database setup")
    r.p(f"`init_db.py` creates `smart_campus_db`, runs the three scripts and prints the row counts. On the "
        f"development machine it completed in {bt['init_db_s']} s. It asks for confirmation unless `--yes` is "
        "given, because it drops and recreates every domain table (Django's tables are not touched).")
    _shot(r, "26_init_db", "Database build with init_db.py")
    r.h2("7.7 Application deployment steps")
    r.p(f"`mvnw.cmd clean package` compiled the engine, ran the JUnit suite and built the fat JAR in "
        f"{bt['maven_clean_package_s']} s. `manage.py migrate` and `manage.py check` then completed with exit "
        f"code {bt['migrate_check_exit']}, and the development server was started.")
    _shot(r, "25_maven_build", "Maven build of the engine JAR")
    r.h2("7.8 User access and credentials management")
    r.bullets([
        "Logins are Django users; passwords are stored only as salted hashes.",
        "`manage.py seed_demo_users` creates one login per student and faculty row with the same username, plus "
        "an `admin` superuser. The shared demo password is documented in the README for evaluators and is not "
        "repeated here. The command refuses to run when DEBUG is off unless `--force` is given.",
        "The role is never stored: it is derived from the username on each request (Section 4.14).",
        "Every user can change their own password at /accounts/password/.",
        "Database credentials live only in the git-ignored `.env`; a secret scan is run before every push.",
    ])
    r.h2("7.9 User manual")
    r.h3("7.9.1 Student")
    r.bullets(["Log in with your roll number (for example 25cse001).",
               "The dashboard shows each course with attendance %, marks, grade and your GPA and CGPA.",
               "A red banner means at least one course is below 75% attendance.",
               "Use \"Change password\" in the header; log out with the header button."], numbered=True)
    r.h3("7.9.2 Faculty")
    r.bullets(["Log in with your username (first.last).",
               "Choose a course to see the roster.",
               "Attendance: pick a weekday date, mark each student, save.",
               "Marks: enter internal (0-40) and external (0-60) marks, save; totals and grades appear."],
              numbered=True)
    r.h3("7.9.3 Admin")
    r.bullets(["Log in as admin; the dashboard shows counts and averages.",
               "Students / Faculty / Courses: search, add, edit or delete (a confirmation page is shown).",
               "Enrollments and Timetable: add entries; clashes and duplicates are explained.",
               "Defaulters: review the live list, then \"Declare defaulter list now\".",
               "GPA report and Marks audit: read-only reports.",
               "Java engine: choose a command, run it, read the tables or the error card."], numbered=True)
    r.h3("7.9.4 Command line")
    r.code("java -jar java_engine/target/smart-campus-engine.jar help\n"
           "java -jar java_engine/target/smart-campus-engine.jar student 25CSE001\n"
           "java -jar java_engine/target/smart-campus-engine.jar dashboard\n"
           "java -jar java_engine/target/smart-campus-engine.jar export gpa-report gpa.csv\n"
           "java -jar java_engine/target/smart-campus-engine.jar menu")
    r.h2("7.10 Deployment screenshots")
    _shot(r, "21_cli_help", "Engine help output after deployment")
    _shot(r, "09_admin_dashboard", "Portal running after deployment (admin dashboard)")
    r.h2("7.11 Deployment challenges")
    r.bullets([
        "PowerShell's execution policy can block `Activate.ps1`; the steps call `.venv\\Scripts\\python.exe` "
        "directly so no system setting has to change.",
        "PowerShell has no `<` redirection, so the SQL scripts are run through `init_db.py`.",
        "A stale `DB_*` variable in the shell overrides `.env` for the JAR; the variables must be cleared.",
        "Django runs the last built JAR, so the engine must be rebuilt after any Java change.",
        "A fresh clone was tested end-to-end in Phase 4.5 to confirm that the six setup commands are enough.",
    ])


def chapter8(r):
    r.chapter(8, "Maintenance and Future Enhancements")
    r.h2("8.1 Introduction")
    r.p("Maintenance keeps the system correct and useful after delivery. This chapter classifies the "
        "maintenance work already done, describes how future changes will be handled, and lists the current "
        "limitations and planned enhancements. Change control and release practice are given in Appendix A, "
        "and the project risks in Appendix B.")
    r.h2("8.2 Types of maintenance")
    r.h3("Corrective maintenance")
    r.p("Fixing defects after they are found. Examples from this project: case-sensitive CHECK constraints "
        "(commit c96e1f6) and stable ordering of paginated lists (commit 6de2bea). Each fix comes with a test.")
    r.h3("Adaptive maintenance")
    r.p("Adapting to a changed environment. The project stays on Django 5.2 LTS because Django 6.1 needs "
        "MySQL 8.4; moving to MySQL 8.4 will allow the upgrade. HTTPS settings are switched on by "
        "`DJANGO_HTTPS=True` when the portal moves behind TLS.")
    r.h3("Perfective maintenance")
    r.p("Adding features or improving usability. Phase 4.5 added the marks audit trail, CSV export, the "
        "interactive menu, delete pages, search and pagination, password change and the Django admin.")
    r.h3("Preventive maintenance")
    r.p("Preventing future faults: the URL-wide access test fails if a new page forgets its role check; "
        "rules live in the database so a new client cannot bypass them; scripts are re-runnable; dependency "
        "versions are pinned.")
    r.h2("8.3 Bug fixing and updates")
    r.p("A bug is first reproduced with a failing test, then fixed in the layer that owns the rule (SQL, Java "
        "or Django), and committed together with the test. Schema changes are made in one commit that updates "
        "the SQL, the unmanaged Django model, the Java model/DAO and the ER diagram (Appendix A.4).")
    r.h2("8.4 Performance improvement")
    r.bullets([
        "Reports read the database views instead of re-implementing joins in Python or Java.",
        "The engine dashboard loads its three views concurrently on a 3-thread pool.",
        "At most one engine call per page; most pages need none (about 50-70 ms).",
        "Future: a connection pool or a long-running engine service would remove the 0.6-0.8 s cost of each engine call.",
    ])
    r.h2("8.5 Security updates")
    r.bullets([
        "Follow Django 5.2 LTS security releases (supported until April 2028) and MySQL 8.0 updates.",
        "Keep `cryptography` and the JDBC driver current.",
        "Before production: set DEBUG off, a real secret key, allowed hosts and HTTPS; replace the demo logins.",
        "Run `manage.py check --deploy` after every settings change.",
    ])
    r.h2("8.6 User feedback and enhancements")
    r.p("Feedback from the guide and lab evaluators will be recorded as GitHub issues, prioritised, and handled "
        "through the change-control steps in Appendix A. Usability feedback during development already led to "
        "readable error messages with names instead of ids (for example in timetable clashes).")
    r.h2("8.7 Limitations of the current system")
    r.bullets([
        "Single department and a single active academic year in the demo data.",
        "No e-mail or SMS notifications to students or parents.",
        "Runs on the Django development server on localhost; not hardened for the internet.",
        "Demo accounts share one password.",
        "Each engine call starts a new JVM (about 0.7 s).",
        "No bulk import of students or marks from spreadsheets.",
        "Acceptance testing was done by the developer, not by real staff and students.",
    ])
    r.h2("8.8 Future enhancements")
    r.bullets([
        "Bulk CSV import of students, enrollments and marks.",
        "E-mail alerts to students who fall below 75% attendance.",
        "Multiple departments and academic years with history.",
        "Charts of attendance trends on the dashboards.",
        "Production deployment with Gunicorn/Nginx, TLS and a managed MySQL.",
        "A REST API for a mobile app.",
    ])
    r.h2("8.9 Maintenance plan")
    r.table(["Activity", "Frequency", "Responsibility"], [
        ["Back up smart_campus_db (mysqldump)", "Daily during the semester", "Admin"],
        ["Run both test suites", "Before every commit", "Developer"],
        ["Apply Django / MySQL security releases", "Monthly", "Developer"],
        ["Review marks_audit", "End of each assessment", "Admin"],
        ["Declare defaulters", "At each attendance cut-off", "Admin"],
        ["Review risks (Appendix B)", "Each semester", "Developer and guide"],
    ], [2.6, 1.7, 1.5], "Maintenance plan", size=9.5)


def chapter9(r):
    rc = FACTS["schema"]["row_counts"]
    mv, dj = TESTS["maven"], TESTS["django"]
    bt = LIVE["build_timings"]
    r.chapter(9, "Results and Discussion")
    r.h2("9.1 Introduction")
    r.p("This chapter presents what was built and how it performed. All numbers were measured on the "
        "development machine described in Section 5.2.")
    r.h2("9.2 Results obtained")
    r.table(["Result", "Value"], [
        ["Domain tables / views / triggers / functions / procedures", "11 / 4 / 9 / 2 / 1"],
        ["Seed data", f"{rc['students']} students, {rc['faculty']} faculty, {rc['courses']} courses, "
                      f"{rc['enrollments']} enrollments, {rc['attendance_records']} attendance records"],
        ["Live defaulter rows (v_defaulter_list)", f"{rc['v_defaulter_list']} course rows for 2 students "
                                                   "(25CSE004, 25CSE009)"],
        ["Java engine commands", "13 (incl. help, menu, export)"],
        ["Portal roles / main pages", "3 roles; 17 pages measured"],
        ["JUnit tests", f"{mv['summary']['run']} run, {mv['summary']['failures']} failures"],
        ["Django tests", f"{dj['ran']} run, result {dj['result_line']}"],
        ["Django line coverage", f"{dj['coverage_totals']['percent_covered']:.1f}%"],
        ["Documented test cases", f"{sum(len(CASES[k]) for k in ('unit', 'integration', 'white_box', 'black_box'))}"
                                  " executed, all passed"],
    ], [2.8, 3.0], "Results obtained", size=9.5, bold_first_col=True)
    r.h2("9.3 Output screenshots")
    _shot(r, "13_admin_defaulters", "Admin defaulter list with the declare button")
    _shot(r, "14_admin_gpa_report", "GPA report: weighted GPA next to the official CGPA")
    _shot(r, "15_admin_enrollments", "Enrollments list and enroll form")
    _shot(r, "16_admin_marks_audit", "Marks audit history written by the AFTER UPDATE trigger")
    _shot(r, "17_admin_delete_confirm", "Delete confirmation page")
    _shot(r, "18_engine_dashboard", "Java engine dashboard run from the portal, with thread names and timings")
    _shot(r, "19_engine_error", "Typed error card from the engine page")
    _shot(r, "03_access_denied", "Access denied (403) page for a wrong role")
    _shot(r, "20_django_admin", "Django admin over the domain tables and the four views")
    _shot(r, "22_cli_dashboard", "Engine dashboard in the terminal")
    _shot(r, "23_cli_defaulters", "Engine defaulter report in the terminal")
    _shot(r, "24_cli_student", "Engine student lookup in the terminal")
    r.h2("9.4 Performance evaluation")
    pages = [p for p in LIVE["pages"] if "command" not in p["path"]]
    med = sorted(p["median_ms"] for p in pages)
    r.table(["Measurement", "Result"], [
        ["Ordinary portal pages (median of medians, 15 pages)", f"{med[len(med) // 2]} ms "
                                                                f"(range {med[0]}-{med[-1]} ms)"],
        ["Engine page: dashboard (median)", f"{[p for p in LIVE['pages'] if 'dashboard' in p['path']][0]['median_ms']} ms"],
        ["Engine page: defaulters (median)", f"{[p for p in LIVE['pages'] if 'defaulters' in p['path'] and 'engine' in p['path']][0]['median_ms']} ms"],
        ["CLI help (JVM start-up only)", f"{CASES['cli_timings']['help']['median_ms']} ms"],
        ["CLI commands that query MySQL", f"{min(v['median_ms'] for k, v in CASES['cli_timings'].items() if k != 'help')}-"
                                          f"{max(v['median_ms'] for k, v in CASES['cli_timings'].items() if k != 'help')} ms"],
        ["Database rebuild (init_db.py)", f"{bt['init_db_s']} s"],
        ["Engine build with tests (mvnw clean package)", f"{bt['maven_clean_package_s']} s"],
        ["Django test suite (71 tests)", f"{dj['test_seconds']:.1f} s test time, {dj['wall_seconds']} s total"],
    ], [3.4, 2.4], "Performance evaluation", size=9.5)
    r.p("The difference between `help` (no database) and the other commands, about 0.5 s, is the cost of "
        "loading the JDBC driver and opening a MySQL connection; the JVM itself starts in about 0.17 s.")
    r.h2("9.5 Comparison with the existing system")
    r.table(["Aspect", "Existing (manual)", "Proposed system"], [
        ["Data storage", "Registers and spreadsheets, duplicated", "One 3NF database"],
        ["Grade calculation", "By hand or ad-hoc formulas", "Trigger, identical for everyone"],
        ["Attendance %", "Totalled near the cut-off", "Live from a view"],
        ["Defaulter list", "Prepared manually, late", "Live list; declared with one click"],
        ["Timetable clashes", "Found when they happen", "Refused when entered"],
        ["Access control", "Whoever holds the file", "Role checked on every page"],
        ["Change history", "None", "Automatic marks audit"],
        ["Report time", "Days", "Under 1 s (Table 9.2)"],
    ], [1.5, 2.1, 2.2], "Existing system vs proposed system", size=9.5, bold_first_col=True)
    r.h2("9.6 Discussion of results")
    r.p("Placing the rules in the database proved to be the key design decision. Tests IT02, IT05 and IT06 show "
        "that a change made through one application is graded, checked and audited without that application "
        "doing any of the work, and IT09-IT10 show the Java engine receiving the same answers and errors. "
        "Security tests showed no way for a student or teacher to reach another person's data, and the "
        "URL-wide test guarantees this for pages added later. The main cost is the engine's start-up time, "
        "which is acceptable for one call per page but would need a resident service for heavy use. Unit-test "
        "coverage of the Java DAO layer is low by design (no database in unit tests); that layer is covered by "
        "the integration and loop cases instead.")
    r.h2("9.7 Achievement of project objectives")
    r.table(["Objective", "Achieved", "Evidence"], [
        ["O1 Normalised database with rules", "Yes", "Section 4.8-4.9; CHECK/UNIQUE/FK tests"],
        ["O2 Derived values in the database", "Yes", "WB01-WB08, BB09-BB12, IT02, IT03"],
        ["O3 Role-based portal", "Yes", "IT01, WB09-WB11, BB34-BB35, test_polish"],
        ["O4 OOP Java engine with JDBC", "Yes", "Class diagrams; 29 JUnit tests; IT09-IT10"],
        ["O5 Safe portal-engine bridge", "Yes", "UT03-UT04, IT08, BB30"],
        ["O6 Tests and design documents", "Yes", "Chapters 4 and 6; Appendix C"],
    ], [2.3, 0.8, 2.7], "Achievement of objectives", size=9.5)
    r.h2("9.8 Summary")
    r.p("The system meets all six objectives and every non-functional requirement that was measured. Pages "
        "respond in tens of milliseconds, engine reports in under a second, and all automated tests and "
        "documented cases pass.")


def chapter10(r):
    r.chapter(10, "Conclusion")
    r.h2("10.1 Conclusion")
    r.p("Smart Campus & Academic Suite replaces registers and spreadsheets with one consistent database and "
        "role-based access for students, faculty and the administrator. By enforcing grading, attendance, "
        "enrollment and timetable rules inside MySQL, it guarantees that the Django portal, the Java engine and "
        "any future client always agree. The system was designed, implemented, tested and documented following "
        "the SDLC, and all planned objectives were achieved.")
    r.h2("10.2 Summary of the project")
    r.bullets([
        "A 3NF MySQL schema with 11 tables, 4 views, 9 triggers, 2 functions and 1 procedure.",
        "A Java 17 engine with an OOP domain model, JDBC DAOs, services, a concurrent dashboard, CSV export and "
        "a CLI with JSON output.",
        "A Django 5.2 portal with Student, Faculty and Admin roles, CRUD, reports, an audit view and a bridge "
        "to the engine.",
        "Requirements, UML, DFD and ER design; 78 documented test cases and 100 automated tests, all passing.",
    ])
    r.h2("10.3 Contribution of the project")
    r.bullets([
        "Shows how one database can serve two applications in different languages with identical rules.",
        "Provides an automatic, tamper-evident history of marks changes.",
        "Gives students early warning of attendance shortfalls.",
        "Serves as a single worked example for the DBMS, Java, Django and Software Engineering labs.",
    ])
    r.h2("10.4 Learning outcomes")
    r.bullets([
        "Normalising a real schema and expressing business rules as constraints, triggers and views.",
        "Applying OOP (abstraction, inheritance, interfaces, generics, exceptions) and JDBC transactions in Java.",
        "Building a secure MVT web application with role-based access in Django.",
        "Integrating programs across languages through a process boundary and a JSON contract.",
        "Writing an SRS, drawing UML/DFD/ER diagrams as code, designing white- and black-box tests, and "
        "managing the work with Git.",
    ])
    r.h2("10.5 Scope for future work")
    r.p("Future work includes bulk import, notifications, multi-department support, charts, a REST API for a "
        "mobile app and a production deployment with TLS (Section 8.8), as well as a formal acceptance test "
        "with real faculty and students.")


REFERENCES = [
    "E. F. Codd, \"A relational model of data for large shared data banks,\" *Commun. ACM*, vol. 13, no. 6, "
    "pp. 377-387, Jun. 1970, doi: 10.1145/362384.362685.",
    "R. S. Sandhu, E. J. Coyne, H. L. Feinstein, and C. E. Youman, \"Role-based access control models,\" "
    "*Computer*, vol. 29, no. 2, pp. 38-47, Feb. 1996, doi: 10.1109/2.485845.",
    "D. F. Ferraiolo, J. F. Barkley, and D. R. Kuhn, \"A role-based access control model and reference "
    "implementation within a corporate intranet,\" *ACM Trans. Inf. Syst. Secur.*, vol. 2, no. 1, pp. 34-64, "
    "Feb. 1999, doi: 10.1145/300830.300834.",
    "M. N. F. Hidayah and H. Sofyan, \"Design and implementation of an integrated web-based academic management "
    "and student admission monitoring system using Django framework,\" *CODEX: J. Softw. Eng.*, vol. 1, no. 1, "
    "2026, doi: 10.33650/codex.v1i01.14454.",
    "J. Thilagavathi, G. P. Narasimha, S. Yasaswini, and E. Aiswarya, \"College management system using Python "
    "& Django,\" *Shanlax Int. J. Arts, Sci. Humanities*, vol. 11, no. S3, Jul. 2024, "
    "doi: 10.34293/sijash.v11iS3-July.7911.",
    "M. J. Davis and Z. Huang, \"ERP in higher education: A case study of SAP and Campus Management,\" "
    "*Issues Inf. Syst.*, vol. VIII, no. 1, pp. 120-126, 2007. [Online]. Available: "
    "https://iacis.org/iis/2007/Davis_Huang.pdf",
    "OS4ED, \"openSIS Classic: Open-source student information system,\" GitHub repository. [Online]. "
    "Available: https://github.com/OS4ED/openSIS-Classic (accessed Nov. 1, 2026).",
    "Foradian Technologies, \"Fedena: School management software,\" [Online]. Available: "
    "https://fedena.com/ (accessed Nov. 1, 2026).",
    "D. Marsden et al., \"Attendance (mod_attendance),\" Moodle Plugins Directory. [Online]. Available: "
    "https://moodle.org/plugins/mod_attendance (accessed Nov. 1, 2026).",
    "R. S. Pressman and B. R. Maxim, *Software Engineering: A Practitioner's Approach*, 9th ed. New York, NY, "
    "USA: McGraw-Hill, 2019.",
    "I. Sommerville, *Software Engineering*, 10th ed. Boston, MA, USA: Pearson, 2015.",
    "G. Booch, J. Rumbaugh, and I. Jacobson, *The Unified Modeling Language User Guide*, 2nd ed. Boston, MA, "
    "USA: Addison-Wesley, 2005.",
    "Django Software Foundation, \"Django 5.2 documentation,\" [Online]. Available: "
    "https://docs.djangoproject.com/en/5.2/ (accessed Nov. 1, 2026).",
    "Oracle Corporation, \"MySQL 8.0 reference manual,\" [Online]. Available: "
    "https://dev.mysql.com/doc/refman/8.0/en/ (accessed Nov. 1, 2026).",
    "PlantUML, \"PlantUML language reference guide,\" [Online]. Available: https://plantuml.com/ "
    "(accessed Nov. 1, 2026).",
    "The JUnit Team, \"JUnit user guide,\" [Online]. Available: https://docs.junit.org/ (accessed Nov. 1, 2026).",
    "Microsoft, \"Playwright for Python,\" [Online]. Available: https://playwright.dev/python/ "
    "(accessed Nov. 1, 2026).",
    "*IEEE Recommended Practice for Software Requirements Specifications*, IEEE Std 830-1998, 1998, "
    "doi: 10.1109/IEEESTD.1998.88286.",
]


def references(r):
    r.unnumbered_main("References")
    for index, ref in enumerate(REFERENCES, 1):
        paragraph = r.p(f"[{index}]\t" + ref.replace("*", ""), align="left", size=11, space_after=4)
        fmt = paragraph.paragraph_format
        from docx.shared import Inches
        fmt.left_indent = Inches(0.45)
        fmt.first_line_indent = Inches(-0.45)
        fmt.tab_stops.add_tab_stop(Inches(0.45))
        fmt.line_spacing = 1.15


def appendix_a(r):
    commits = FACTS["git"]["commits"]
    r.unnumbered_main("Appendix A: Software Configuration Management")
    r.p("Software Configuration Management (SCM) identifies the items that make up the system, controls "
        "changes to them, and records how each version was built and released. This appendix describes the "
        "SCM actually used in the project and is referred to from Chapters 5 and 8.")
    r.h2("A.1 Configuration identification")
    r.table(["Configuration item", "Location", "Identified by"], [
        ["Database scripts", "database/*.sql, init_db.py", "Git path + commit"],
        ["Java engine source and build", "java_engine/ (pom.xml, src/)", "Maven version 1.0.0-SNAPSHOT + commit"],
        ["Django portal", "campus_portal/", "Git path + commit"],
        ["Dependencies", "requirements.txt, pom.xml", "Pinned versions"],
        ["Configuration template", ".env.example (real .env is git-ignored)", "Git path"],
        ["Design documents", "docs/*.md, docs/src/diagrams/*.puml", "Git path + commit"],
        ["Test evidence", "docs/src/evidence/*.json", "Generated by scripts; committed"],
        ["Project guide", "CLAUDE.md, README.md", "Updated when each phase lands"],
    ], [1.9, 2.3, 1.6], "Configuration items", size=9.5)
    r.h2("A.2 Version control")
    r.p(f"The repository is managed with Git and hosted on GitHub; all work is on the `main` branch. Commit "
        "messages follow the Conventional Commits style (`feat`, `fix`, `docs`, `test`, `chore` with a scope "
        f"such as `database`, `java` or `django`). The history up to this report contains {len(commits)} "
        f"commits and {FACTS['git']['tracked_files']} tracked files; the commits that generate this report "
        "follow them.")
    r.table(["Commit", "Date", "Message"], [[c["hash"], c["date"], c["subject"]] for c in commits],
            [0.75, 0.95, 4.1], "Git history of the project", size=8.5)
    r.h2("A.3 Baselines")
    r.table(["Baseline", "Commit", "Contents"], [
        ["Phase 1: scaffolding", "4ae9dc0", "Folder structure, Maven fat-JAR setup, project guide"],
        ["Phase 2: database", "c62e999", "Schema, views, triggers, seed data, init_db.py"],
        ["Phase 3: Java engine", "5937f1f", "Config, models, DAOs, services, CLI, tests, docs"],
        ["Phase 4: Django portal", "6f74e2b", "Three portals, bridge, tests, docs"],
        ["Phase 4.5: polish", "6de2bea", "Audit trail, CSV export, menu, CRUD, security, fixes"],
    ], [1.6, 0.8, 3.4], "Baselines", size=9.5)
    r.h2("A.4 Change control")
    r.bullets([
        "A change starts from a requirement, a defect (Chapter 6.12) or review feedback.",
        "Its impact is checked against the rule \"the SQL scripts are the source of truth\": a schema change "
        "must update, in one commit, the SQL, the unmanaged Django model, the Java model and DAO, and the ER "
        "diagram.",
        "The change is made with a test that fails before and passes after.",
        "Both suites are run; then a secret scan checks that no `.env` content or password is staged.",
        "The commit is pushed only after the scan is clean; database fixes were approved by the developer "
        "before `database/` was touched.",
    ], numbered=True)
    r.h2("A.5 Build and release management")
    r.table(["Artifact", "Built by", "Release check"], [
        ["smart_campus_db", "python database/init_db.py --yes", "Row counts printed; Django tests load the "
                                                                "same scripts"],
        ["smart-campus-engine.jar", "mvnw clean package (Maven 3.9.16 pinned by the wrapper)", "29 JUnit tests "
                                                                                              "must pass"],
        ["Django portal", "pip install -r requirements.txt; migrate", "manage.py check; 71 tests must pass"],
        ["Project report", "docs/src/report/build_report.py", "Rendered with LibreOffice and checked page by "
                                                              "page"],
    ], [1.6, 2.3, 1.9], "Build and release", size=9.5)
    r.h2("A.6 SCM tools")
    r.table(["Tool", "Use"], [
        ["Git 2.53.0", "Version control, history, baselines"],
        ["GitHub", "Remote repository and backup"],
        [".gitignore", "Keeps .env, build output, virtual environments and downloaded tools out of Git"],
        [".gitattributes", "Forces LF line endings for mvnw"],
        ["Maven Wrapper", "Reproducible Maven version for every build"],
        ["requirements.txt / pom.xml", "Pinned dependency versions"],
    ], [1.8, 4.0], "SCM tools", size=9.5)


def appendix_b(r):
    r.unnumbered_main("Appendix B: Risk Management")
    r.p("Risks were identified at the start of each phase, rated for probability and impact (Low, Medium, "
        "High), and tracked until closed. This appendix is referred to from Chapter 8.")
    r.table(["ID", "Risk", "Prob.", "Impact", "Mitigation", "Status"], [
        ["R1", "Database password or .env committed to GitHub", "Medium", "High",
         ".env git-ignored; secret scan in a separate step before every push", "Controlled"],
        ["R2", "Rules implemented differently in Django and Java", "High", "High",
         "Rules placed in MySQL triggers, views and constraints", "Closed"],
        ["R3", "init_db.py run against real data and erases it", "Low", "High",
         "Confirmation prompt unless --yes; Django tables never touched", "Controlled"],
        ["R4", "Engine JAR missing or Java not installed on the server", "Medium", "Medium",
         "Bridge checks the JAR first; typed errors with a build hint; never a 500 page", "Closed"],
        ["R5", "Command injection through the bridge", "Low", "High",
         "Argument list, shell=False, allow-list, regex, timeout", "Closed"],
        ["R6", "Framework incompatibility (Django 6.1 needs MySQL 8.4)", "Medium", "Medium",
         "Stay on Django 5.2 LTS", "Closed"],
        ["R7", "Platform differences (Windows encodings, BOM, line endings)", "High", "Medium",
         "-Dfile.encoding=UTF-8, BOM stripping, .gitattributes for mvnw", "Closed"],
        ["R8", "A new page added without a role check", "Medium", "High",
         "URL-wide access test fails the suite", "Controlled"],
        ["R9", "Schedule slip near the semester end", "Medium", "Medium",
         "Phased plan; each phase committed and usable on its own", "Closed"],
        ["R10", "Slow engine calls if used per table row", "Medium", "Medium",
         "Design rule: one engine call per page", "Controlled"],
        ["R11", "Loss of the laptop or disk", "Low", "High", "Code pushed to GitHub after each phase; database "
                                                            "rebuilt from scripts", "Controlled"],
    ], [0.4, 1.6, 0.6, 0.6, 2.0, 0.75], "Risk register", size=8.5)
    r.p("Risk exposure was highest in Phase 3 and 4 (R2, R5, R7), when the two applications were connected; "
        "all three were closed by design decisions that are verified by tests in Chapter 6.")


def appendix_c(r):
    r.unnumbered_main("Appendix C: Automated Test Log")
    r.p(f"Every automated test from the final run on {TESTS['run_at'][:10]}, as reported by Maven Surefire and "
        "the Django test runner.")
    r.table(["#", "JUnit class", "Test", "Time (s)", "Status"],
            [[i, c["class"], c["name"], f"{c['seconds']:.3f}", c["status"]]
             for i, c in enumerate(TESTS["maven"]["cases"], 1)], [0.35, 1.5, 3.0, 0.6, 0.5],
            "JUnit tests", size=8)
    r.table(["#", "Module.Class", "Test", "Status"],
            [[i, f"{c['module']}.{c['class']}", c["name"], c["status"]]
             for i, c in enumerate(TESTS["django"]["cases"], 1)], [0.35, 2.2, 2.8, 0.5],
            "Django tests", size=8)
