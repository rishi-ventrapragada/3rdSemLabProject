"""Chapters 1-4: introduction, literature review, SRS, analysis and design."""

from content_common import (CASES, DOMAIN_TABLES, FACTS, LIVE, TESTS, columns, constraints, diagram,
                            diagram_title, foreign_keys, screen)


def chapter1(r):
    rc = FACTS["schema"]["row_counts"]
    r.chapter(1, "Introduction")
    r.h2("1.1 Introduction to the project")
    r.p("**Smart Campus & Academic Suite** is a college academic management system for one department. It keeps "
        "students, faculty, courses, enrollments, class timetables, attendance and marks in a single MySQL "
        "database, `smart_campus_db`, and gives each kind of user the part of that data they need. Students see "
        "their own attendance, marks, grades and CGPA. Faculty record attendance and marks for the courses they "
        "teach. The administrator manages master data, enrolls students, builds the timetable, publishes the "
        "defaulter list and reads academic reports.")
    r.p("The system has three parts that share the same database. A **MySQL 8.0** schema holds the data and the "
        "rules that must always hold (constraints, triggers, views and a stored procedure). A **Java 17** engine "
        "reads and writes the database through raw JDBC and runs reports from the command line. A **Django 5.2** "
        "web portal offers role-based pages for Admin, Faculty and Student, and can call the Java engine. The "
        "project was built as one codebase that serves four third-semester labs: DBMS, Java, Django and Software "
        "Engineering. This report is the Software Engineering deliverable and follows the SDLC from planning to "
        "maintenance.")
    r.h2("1.2 Background of the project")
    r.p("In most colleges, attendance is marked in registers or spreadsheets kept by each teacher, internal and "
        "external marks are typed into separate sheets, and the examination section computes grades and CGPA "
        "later. A student usually learns that their attendance has fallen below the 75% requirement only when "
        "the defaulter list is put up near the end of the semester. Timetables are prepared by hand, so a "
        "teacher can be booked into two classes at once without anyone noticing until the clash happens.")
    r.p("Relational databases were designed to remove exactly this kind of duplicated, inconsistent data by "
        "keeping each fact once and deriving everything else from it [1]. Role-based access control gives each "
        "user only the operations their role needs [2], [3]. The project applies both ideas to the daily "
        "academic work of a department.")
    r.h2("1.3 Problem statement")
    r.p("Academic records in the department are spread across registers, spreadsheets and separate examination "
        "files. The same student details are typed in several places, grades and attendance percentages are "
        "calculated by hand, and nothing stops two inconsistent copies from existing. Students cannot see their "
        "own standing in time to act on it, faculty cannot record attendance and marks in one place, and the "
        "administrator has no reliable, current view of defaulters, GPA or timetable clashes. **The problem is to "
        "build one consistent, secure system in which each user records or views academic data according to "
        "their role, and in which the academic rules (grading, the 75% attendance rule, timetable clashes, "
        "unique enrollments) are enforced automatically.**")
    r.h2("1.4 Motivation for the project")
    r.bullets([
        "Students should know their attendance and marks while there is still time to improve them.",
        "Teachers should spend less time on registers and grade calculations, and more on teaching.",
        "Rules such as \"75% attendance\" and the grading scale should be applied identically for everyone.",
        "One shared database lets the DBMS, Java, Django and Software Engineering labs be demonstrated on one "
        "realistic system instead of four unrelated toy programs.",
    ])
    r.h2("1.5 Objectives of the project")
    r.bullets([
        "**O1.** Design a normalised (3NF) relational database for departments, faculty, students, courses, "
        "enrollments, attendance, marks, rooms and timetables, with all integrity rules declared in MySQL.",
        "**O2.** Compute grades, attendance percentages, defaulters and GPA in the database (triggers, functions "
        "and views) so that every application gets the same answer.",
        "**O3.** Build a role-based web portal in which Admin, Faculty and Student each see and change only what "
        "their role allows.",
        "**O4.** Build an object-oriented Java engine that reads and writes the same database through JDBC and "
        "produces reports from the command line, including a concurrent dashboard and CSV export.",
        "**O5.** Connect the portal to the engine safely, so an administrator can run engine reports from the "
        "browser.",
        "**O6.** Verify the system with automated tests and documented test cases, and record the design with "
        "UML, ER and data flow diagrams.",
    ], numbered=False)
    r.h2("1.6 Scope of the project")
    r.p("**In scope:** one department's academic year (demo data: 3rd semester CSE, academic year 2026-27, "
        f"{rc['students']} students, {rc['faculty']} faculty members, {rc['courses']} courses, "
        f"{rc['enrollments']} enrollments, {rc['attendance_records']} attendance records and "
        f"{rc['marks']} marks rows). The system covers master data, enrollments, timetables, attendance, marks, "
        "grading, defaulters, GPA reports, a marks audit trail, a command-line engine and a web portal with "
        "three roles.")
    r.p("**Out of scope:** fee payment, admissions, library and hostel modules, e-mail or SMS notifications, "
        "a mobile app, and hosting on a public server. The demo logins share one password and are meant only "
        "for local evaluation.")
    r.h2("1.7 Existing system")
    r.p("The existing (manual) process followed in the department works as follows:")
    r.bullets([
        "The office keeps student and faculty details in spreadsheets; each new semester's list is typed again.",
        "Each teacher marks attendance in a paper register or a personal spreadsheet for every class.",
        "Near the cut-off date, teachers total the attendance by hand and send it to the office, which prepares "
        "the defaulter list (students below 75%).",
        "Internal marks are entered by teachers in one sheet; external marks arrive later from the examination "
        "branch in another.",
        "Totals, grade points, letter grades and CGPA are computed manually or with spreadsheet formulas that "
        "differ from sheet to sheet.",
        "The timetable is drawn by hand; clashes are noticed only when a teacher is due in two rooms at once.",
        "Students learn their standing only from notice boards or by asking the teacher.",
    ], numbered=True)
    r.h2("1.8 Limitations of the existing system")
    r.bullets([
        "**Redundancy and inconsistency:** the same student appears in many sheets, and the copies drift apart.",
        "**Manual calculation errors:** percentages, totals and grades are recomputed by hand.",
        "**Late information:** students find out they are defaulters too late to recover.",
        "**No enforcement of rules:** nothing prevents a duplicate enrollment, marks above the maximum, a "
        "Saturday attendance entry or a teacher double-booking.",
        "**No access control or audit trail:** anyone with the file can change any value, and nobody can tell "
        "who changed a mark or what it was before.",
        "**No consolidated reports:** department-wide GPA or attendance summaries take days to prepare.",
    ])
    r.h2("1.9 Proposed system")
    r.p("The proposed system replaces the registers and spreadsheets with one database and three role-based "
        "views of it. What each user type can do:")
    r.table(["User type", "What the proposed system provides"], [
        ["Student", "Own profile, per-course attendance percentage, internal/external marks, letter grade, "
                    "weighted GPA and official CGPA, class timetable, and a warning banner when any course is "
                    "below 75%. A student can never open another student's record."],
        ["Faculty", "Own courses and weekly timetable, course roster, attendance sheet for any weekday, marks "
                    "sheet with totals and grades computed by the database, and recent marks changes. A teacher "
                    "cannot open another teacher's course."],
        ["Admin", "Dashboard with counts and averages; add, edit, search and delete students, faculty and "
                  "courses; enroll students; add timetable entries with clash checks; live defaulter list and "
                  "\"declare defaulters\"; GPA report; marks audit history; the Java engine page; Django admin."],
        ["Java engine (CLI)", "Student lookup, attendance, defaulters, GPA report, enroll, declare defaulters, a "
                              "concurrent dashboard, CSV export and an interactive menu; `--json` output for "
                              "the portal."],
    ], [1.3, 4.5], "User types and their functions in the proposed system", size=10, bold_first_col=True)
    r.h2("1.10 Advantages of the proposed system")
    r.bullets([
        "Each fact is stored once (3NF), so there is no duplicate data to drift apart.",
        "Grades, attendance percentages, defaulters and GPA are computed by the database the same way for every "
        "user and every application.",
        "Invalid data is rejected at the source: CHECK, UNIQUE and foreign-key constraints and triggers stop "
        "bad marks, weekend attendance, duplicate enrollments and timetable clashes.",
        "Every page checks the user's role; students and faculty see only their own records.",
        "Every marks change is recorded automatically in an audit table.",
        "Reports that took days are available instantly (measured page times are about 50-70 ms, Chapter 9).",
        "The Java engine gives the same reports from a terminal or a CSV file, without the web server.",
    ])
    r.h2("1.11 Organization of the report")
    r.p("Chapter 2 reviews related research and existing systems. Chapter 3 is the Software Requirements "
        "Specification. Chapter 4 presents the architecture, UML diagrams, data flow diagrams, ER diagram and "
        "database, interface and security design. Chapter 5 describes the implementation. Chapter 6 covers "
        "testing, with unit, integration, white-box and black-box test cases and their real results. Chapter 7 "
        "explains deployment and installation, Chapter 8 maintenance, Chapter 9 the results and measured "
        "performance, and Chapter 10 concludes. Appendix A describes software configuration management, "
        "Appendix B risk management and Appendix C lists every automated test run.")


def chapter2(r):
    r.chapter(2, "Literature Review")
    r.h2("2.1 Introduction")
    r.p("Before designing the system we studied published work on relational data modelling, role-based access "
        "control, and web-based academic and student information systems, and we examined three existing "
        "open-source systems used by schools and colleges. The sources below were located by web search and "
        "their bibliographic details were checked on the publisher or repository page; the full references are "
        "listed in the References section.")
    r.h2("2.2 Review of existing research papers")
    papers = [
        ("[1] E. F. Codd, \"A relational model of data for large shared data banks\" (1970).",
         "Codd introduced the relational model: data stored as relations (tables), a normal form for them, and "
         "data independence between applications and storage. **Relevance:** the project's schema follows this "
         "model and is normalised to 3NF so that each fact is stored once."),
        ("[2] R. S. Sandhu, E. J. Coyne, H. L. Feinstein and C. E. Youman, \"Role-based access control models\" "
         "(1996).",
         "The paper defines the RBAC family of models, in which permissions are attached to roles and users "
         "acquire permissions through their roles, which simplifies security administration. **Relevance:** the "
         "portal uses three roles (Admin, Faculty, Student) and checks the role on every page."),
        ("[3] D. F. Ferraiolo, J. F. Barkley and D. R. Kuhn, \"A role-based access control model and reference "
         "implementation within a corporate intranet\" (1999).",
         "The authors describe an RBAC model and a reference implementation for web servers on an intranet. "
         "**Relevance:** it shows RBAC enforced by the web application itself, which is the approach taken in "
         "`core/roles.py`."),
        ("[4] M. N. F. Hidayah and H. Sofyan, \"Design and implementation of an integrated web-based academic "
         "management and student admission monitoring system using Django framework\" (2026).",
         "A web system that brings academic data, payment administration and admissions into one platform, "
         "replacing manual and spreadsheet work; built with Python, Django and MySQL. **Relevance:** the closest "
         "match in technology; it confirms Django + MySQL as a practical stack for academic systems."),
        ("[5] J. Thilagavathi, G. P. Narasimha, S. Yasaswini and E. Aiswarya, \"College management system using "
         "Python & Django\" (2024).",
         "A Django platform that automates admissions, course and exam scheduling, attendance tracking, "
         "resource booking and reporting; it uses SQLite for storage. **Relevance:** similar functions, but the "
         "rules live in application code and the database is a single-user SQLite file."),
        ("[6] M. J. Davis and Z. Huang, \"ERP in higher education: A case study of SAP and Campus Management\" "
         "(2007).",
         "A case study of a university that replaced legacy student software with an ERP system, discussing "
         "critical success factors and staff acceptance. **Relevance:** large ERP suites are costly and need "
         "much adaptation; a department-level system can be small and fit its own rules exactly."),
    ]
    for title, body in papers:
        r.h3(title)
        r.p(body)
    r.h2("2.3 Review of existing applications or systems")
    systems = [
        ("[7] openSIS Classic (OS4ED).",
         "A web-based, GPL-licensed student information system for K-12, trade schools and higher education. "
         "Its repository lists PHP 8 with MySQL 5.7/8.0 or MariaDB, and features such as student and staff data, "
         "course manager and scheduling, attendance, a teacher gradebook, report cards and transcripts. The "
         "Community Edition is listed as version 9.3."),
        ("[8] Fedena.",
         "A school management system available in a free community (open-source) edition and paid editions. "
         "Attendance management and timetable management are among its core modules; the vendor's feature pages "
         "describe automated attendance reports and substitute-teacher allocation."),
        ("[9] Moodle Attendance activity (mod_attendance).",
         "A plugin for the Moodle learning management system, maintained by Dan Marsden, that lets teachers "
         "create attendance sessions and record statuses for students in a Moodle course. It handles attendance "
         "only; marks live in Moodle's own gradebook."),
    ]
    for title, body in systems:
        r.h3(title)
        r.p(body)
    r.h2("2.4 Comparison of related systems")
    r.table(["Feature", "openSIS [7]", "Fedena [8]", "Moodle Att. [9]", "Django CMS [5]", "Django AMS [4]",
             "Proposed"], [
        ["Stack", "PHP, MySQL", "Web app", "PHP plugin", "Django, SQLite", "Django, MySQL",
         "MySQL, Java 17, Django 5.2"],
        ["Attendance", "Yes", "Yes", "Yes", "Yes", "Not stated", "Yes"],
        ["Marks / grading", "Gradebook", "Not reviewed", "Moodle gradebook", "Exams", "Academic data",
         "Marks + DB-computed grades"],
        ["Rules enforced in the DB", "Not stated", "Not stated", "Not stated", "No (SQLite file)",
         "Not stated", "Yes: CHECK, UNIQUE, FK, 9 triggers"],
        ["Role-based portals", "Yes", "Yes", "Teacher/student", "Yes", "Yes", "Admin, Faculty, Student"],
        ["Marks audit trail", "Not stated", "Not stated", "Not stated", "Not stated", "Not stated",
         "Yes (AFTER trigger)"],
        ["Timetable clash check", "Scheduling", "Timetable module", "No", "Scheduling", "Not stated",
         "Yes (trigger + UNIQUE)"],
        ["Command-line / batch reports", "Not stated", "Not stated", "No", "No", "No",
         "Yes (Java engine, CSV)"],
        ["Cost", "Free (GPL)", "Free / paid", "Free", "Academic", "Academic", "Free (open tools)"],
    ], [1.25, 0.8, 0.8, 0.8, 0.8, 0.8, 1.0], "Comparison of related systems with the proposed system", size=8.5,
        bold_first_col=True)
    r.p("\"Not stated\" means the feature was not mentioned in the source we reviewed; it does not mean the "
        "system lacks it.", size=11)
    r.h2("2.5 Research gaps and limitations")
    r.bullets([
        "The Django-based academic systems [4], [5] place their rules in application code; nothing stops "
        "another program writing invalid data straight into the database.",
        "None of the reviewed sources describes an audit trail for marks changes.",
        "Large ERP suites [6] fit higher education only after heavy customisation and cost far more than a "
        "department can spend.",
        "The open-source suites [7], [8] are complete products; they are not designed to be studied lab by lab, "
        "with the database, OOP engine and web layer each visible on its own.",
        "Attendance-only tools [9] do not connect attendance to marks, GPA or the timetable.",
    ])
    r.h2("2.6 Proposed approach based on the literature review")
    r.p("From the relational model [1] the project takes a 3NF schema in which derived values (attendance %, "
        "grades, GPA) are computed by views and triggers instead of being typed in. From RBAC [2], [3] it takes "
        "three fixed roles, derived from the login and enforced on every request. Unlike [4] and [5], the "
        "academic rules are placed in the database itself, so the Django portal and the Java engine (and any "
        "future client) obey the same rules. A marks audit trail and a timetable clash trigger fill gaps not "
        "addressed in the reviewed sources. The system is kept small and department-sized, in contrast to "
        "the ERP approach studied in [6].")
    r.h2("2.7 Summary")
    r.p("Six research papers and three existing systems were reviewed. They confirm the value of web-based "
        "academic systems and of role-based access, and show two gaps that this project addresses: enforcing "
        "academic rules in the shared database rather than in one application, and keeping an automatic audit "
        "trail of marks.")


FRS = [
    ("FR1", "All", "The system shall authenticate users by username and password and redirect each user to the "
                   "dashboard of their role."),
    ("FR2", "All", "The system shall derive the role from the login: superuser = Admin, a username found in "
                   "`students` = Student, in `faculty` = Faculty; any other login gets an access-denied page."),
    ("FR3", "All", "A logged-in user shall be able to change their own password and log out (POST only)."),
    ("FR4", "Student", "A student shall view their own profile, enrolled courses and weekly timetable."),
    ("FR5", "Student", "A student shall view per-course attendance (classes held, attended, percentage)."),
    ("FR6", "Student", "A student shall view internal, external and total marks, grade points, letter grade, "
                       "weighted GPA and official CGPA."),
    ("FR7", "Student", "The student dashboard shall show a warning when any course is below 75% attendance."),
    ("FR8", "Faculty", "A faculty member shall view only the courses they teach and their weekly timetable."),
    ("FR9", "Faculty", "A faculty member shall record attendance (Present/Absent) for a course on a weekday; "
                       "re-saving a date shall update it."),
    ("FR10", "Faculty", "A faculty member shall enter internal (0-40) and external (0-60) marks; total, grade "
                        "points and letter grade shall be computed by the database."),
    ("FR11", "Admin", "The admin shall add, edit, search, paginate and delete students, faculty and courses."),
    ("FR12", "Admin", "The admin shall enroll a student in a course of the student's own semester; duplicate "
                      "enrollments shall be refused."),
    ("FR13", "Admin", "The admin shall add timetable entries; a teacher, room or section double-booking shall "
                      "be refused with a readable message."),
    ("FR14", "Admin", "The admin shall view the live defaulter list and declare defaulters (stored procedure)."),
    ("FR15", "Admin", "The admin shall view the GPA report and the marks audit history."),
    ("FR16", "Admin", "The admin shall run allowed Java engine commands from the portal and see the result or a "
                      "typed error."),
    ("FR17", "System", "Every change of marks shall be written to an audit table with old and new values and "
                       "the time of change."),
    ("FR18", "Engine", "The Java engine shall provide `student`, `whois`, `attendance`, `defaulters`, "
                       "`gpa-report`, `courses`, `enroll`, `refresh-defaulters`, `dashboard`, `export`, `menu` "
                       "and `help` commands, with text or `--json` output."),
    ("FR19", "Engine", "The engine shall export the GPA, defaulter and attendance reports to CSV files."),
    ("FR20", "Engine", "The `dashboard` command shall load the three reporting views concurrently and report "
                       "per-task thread names and timings."),
]


def chapter3(r):
    r.chapter(3, "Software Requirements Specification (SRS)")
    r.h2("3.1 Introduction")
    r.p("This chapter specifies the requirements of Smart Campus & Academic Suite in the style of IEEE Std 830 "
        "[18]. It is written for the project team, the internal guide and the lab evaluators. Definitions of "
        "abbreviations are given in the List of Abbreviations; references are listed at the end of the report.")
    r.h3("3.1.1 Product perspective")
    r.p("The product is a new, self-contained system that replaces registers and spreadsheets. It consists of "
        "three cooperating components that share one MySQL database: the database layer (schema, views, "
        "triggers, functions and a procedure), the Java engine (command line, JDBC) and the Django portal "
        "(web, role-based). The portal calls the engine as a separate process. There is no dependency on any "
        "external college system.")
    r.h3("3.1.2 Product functions")
    r.bullets([
        "**Admin:** manage students, faculty and courses; enroll students; build the timetable; publish "
        "defaulters; view GPA and marks-audit reports; run engine commands; use Django admin.",
        "**Faculty:** view own courses, roster and timetable; record attendance; enter marks.",
        "**Student:** view own attendance, marks, grades, GPA/CGPA, timetable and defaulter warning.",
        "**Engine user (terminal):** run reports, enroll, declare defaulters, export CSV, interactive menu.",
    ])
    r.h3("3.1.3 User characteristics")
    r.table(["User", "Characteristics", "Technical skill assumed"], [
        ["Admin", "Office or department staff responsible for academic records", "Comfortable with web forms"],
        ["Faculty", "Teachers of one or more courses", "Basic web use"],
        ["Student", "Undergraduate students (II year)", "Basic web use, often on a phone"],
        ["Engine user", "Team member or lab evaluator", "Command line"],
    ], [1.1, 2.9, 1.8], "User characteristics", bold_first_col=True)
    r.h3("3.1.4 Operating environment")
    r.p("Server side: Windows 10/11, macOS or Linux with MySQL Server 8.0.16 or newer, JDK 17 or newer and "
        "Python 3.10 or newer. Client side: any current web browser (tested with Chromium); pages are "
        "responsive and work at phone width.")
    r.h3("3.1.5 Design and implementation constraints")
    r.bullets([
        "One MySQL 8.0 database shared by both applications; credentials only from the repository's `.env` file.",
        "SQL scripts are the source of truth for the schema; Django models are unmanaged (`managed = False`).",
        "Java: no frameworks (no Spring, Hibernate or connection pool); raw JDBC with `PreparedStatement` only.",
        "Django 5.2 LTS (Django 6.1 needs MySQL 8.4); vanilla HTML5 and hand-written CSS3, no CSS frameworks.",
        "The portal may start the engine only through `core/java_bridge.py`, with an allow-list and a timeout.",
    ])
    r.h3("3.1.6 Assumptions and dependencies")
    r.bullets([
        "One department and one academic year are active at a time; the academic year starts in July.",
        "Each login username is unique across students and faculty (enforced by triggers).",
        "MySQL, Java and Python are installed on the server machine; the engine JAR has been built.",
        "Attendance is recorded only for Monday to Friday sessions.",
    ])
    r.h2("3.2 Purpose of the software")
    r.p("The purpose of the software is to keep all academic records of a department in one consistent "
        "database, to compute grades, attendance percentages, defaulters and GPA automatically and identically "
        "for everyone, and to give students, faculty and the administrator secure, role-appropriate access to "
        "that data through a web portal and a command-line engine.")
    r.h2("3.3 Functional requirements")
    r.table(["ID", "Actor", "Requirement"], [list(fr) for fr in FRS], [0.55, 0.8, 4.45],
            "Functional requirements", size=9.5)
    r.h2("3.4 Non-functional requirements")
    r.table(["ID", "Category", "Requirement", "How it is met / measured"], [
        ["NFR1", "Performance", "Portal pages shall respond in under 1 s on the development machine.",
         "Median 47-69 ms for 15 pages; engine pages about 0.7 s (Section 6.8)."],
        ["NFR2", "Performance", "A page shall make at most one Java engine call.", "Enforced in `core/views.py`."],
        ["NFR3", "Security", "Every page shall check the user's role; students and faculty see only their own "
                             "records.", "`role_required` / `RoleRequiredMixin`; URL-wide test walks every route."],
        ["NFR4", "Security", "All POST forms shall be protected against CSRF; output shall be HTML-escaped; SQL "
                             "shall be parameterised.", "Django CSRF and auto-escaping; ORM and "
                             "`PreparedStatement` (tests BB29-BB33)."],
        ["NFR5", "Security", "Passwords shall be stored hashed; credentials never committed.",
         "Django PBKDF2 hashing; `.env` is git-ignored."],
        ["NFR6", "Integrity", "Academic rules shall be enforced by the database, not only by the application.",
         "CHECK, UNIQUE, FK constraints and 9 triggers."],
        ["NFR7", "Reliability", "A missing JAR, Java or database error shall show a message, never a crash.",
         "Typed `EngineError`; friendly DB errors; custom 403/404/500 pages."],
        ["NFR8", "Usability", "Pages shall be responsive down to phone width and use plain language messages.",
         "CSS Grid/Flexbox with media queries; `core/db_errors.py`."],
        ["NFR9", "Maintainability", "Code shall be layered (models, DAO, services, CLI; MVT) and covered by "
                                    "automated tests.", "29 JUnit + 71 Django tests; 96% Django line coverage."],
        ["NFR10", "Portability", "The system shall run on Windows, macOS and Linux.",
         "Maven Wrapper, Python venv, `.env`; LF line endings for `mvnw`."],
    ], [0.5, 0.9, 2.3, 2.1], "Non-functional requirements", size=9)
    r.h2("3.5 Hardware requirements")
    r.table(["Component", "Minimum", "Used for development and testing"], [
        ["Processor", "Dual-core 64-bit, 2 GHz", "AMD Ryzen 5 3550H, 4 cores / 8 threads"],
        ["Memory", "4 GB RAM", "13.9 GB usable RAM"],
        ["Storage", "2 GB free (MySQL, JDK, Python, Maven cache)", "SSD, 22 GB free"],
        ["Display / network", "Any; localhost only", "Laptop display, localhost"],
    ], [1.2, 2.2, 2.4], "Hardware requirements", bold_first_col=True)
    r.h2("3.6 Software requirements")
    r.table(["Software", "Version required", "Version used"], [
        ["Operating system", "Windows 10/11, macOS or Linux", "Windows 11 Home Single Language (build 26200)"],
        ["Database server", "MySQL 8.0.16+ (CHECK enforcement)", "MySQL 8.0.42"],
        ["Java", "JDK 17+", "OpenJDK 17.0.20.1"],
        ["Build tool", "Maven (via wrapper)", "Maven 3.9.16 via mvnw"],
        ["Python", "3.10+", "Python 3.13.3"],
        ["Web framework", "Django 5.2 LTS", "Django 5.2.18"],
        ["DB drivers", "PyMySQL; MySQL Connector/J", "PyMySQL 1.2.3; mysql-connector-j 9.7.0"],
        ["Browser", "Any current browser", "Chromium (Playwright), Microsoft Edge"],
    ], [1.4, 2.2, 2.2], "Software requirements", bold_first_col=True)
    r.h2("3.7 User requirements")
    r.bullets([
        "**Student:** \"I want to see my attendance and marks for every course, and to be warned early if I am "
        "below 75%.\"",
        "**Faculty:** \"I want to mark attendance and enter marks for my own courses quickly, and not have to "
        "calculate totals or grades.\"",
        "**Admin:** \"I want one place to manage students, faculty, courses and the timetable, to see who the "
        "defaulters are, and to know who changed a mark.\"",
        "**Evaluator:** \"I want to run the reports from the command line and see the same numbers as the web "
        "portal.\"",
    ])
    r.h2("3.8 System constraints")
    r.bullets([
        "Marks: internal 0-40, external 0-60, stored as DECIMAL(5,2); external marks require internal marks.",
        "Attendance status is PRESENT or ABSENT; one record per enrollment per date; weekdays only.",
        "Credits 1-6, hours per week 1-10, semester 1-8, section a single capital letter, department code 2-10 "
        "capital letters, academic year in the form 2026-27, designation from a fixed list (CHECK constraints).",
        "A student can enroll in a course only once, and only in a course of their own semester.",
        "A faculty member, a room and a section can each have only one class per time slot.",
        "The JAR is called with a 30-second timeout; only six commands are allowed from the portal.",
    ])
    r.h2("3.9 Use case specifications")
    r.p("The use case diagram is shown in Figure 4.3. The main use cases are specified below.")
    ucs = [
        ("UC1", "Log in", "Student, Faculty, Admin",
         "User signs in and is sent to the dashboard of their role.",
         "User has an account.",
         "1. User opens /accounts/login/. 2. Enters username and password. 3. System authenticates and derives "
         "the role. 4. System redirects to /student/, /faculty/ or /admin-portal/.",
         "3a. Wrong credentials: the form shows an error. 3b. Login matches no role: 403 page.",
         "User is logged in with a session."),
        ("UC2", "View own academic record", "Student",
         "Student views attendance, marks, grades, GPA/CGPA and timetable.",
         "Logged in as a student.",
         "1. Student opens /student/. 2. System finds the student by username. 3. System reads "
         "v_attendance_summary, marks and the timetable for that student only. 4. Page shows the data and a "
         "warning for courses below 75%.",
         "None: the URL takes no student id, so another record cannot be requested.",
         "No data changed."),
        ("UC3", "Record attendance", "Faculty",
         "Faculty marks Present/Absent for every student of a course on a date.",
         "Logged in as the course's teacher.",
         "1. Faculty opens the course's attendance page. 2. Chooses a weekday date. 3. Marks each student. "
         "4. Saves. 5. System writes the records in one transaction.",
         "2a. Weekend date: refused by the CHECK constraint with a message. 1a. Another teacher's course: 403.",
         "Attendance stored; v_attendance_summary updated."),
        ("UC4", "Enter marks", "Faculty",
         "Faculty enters internal and external marks; the database grades them.",
         "Logged in as the course's teacher.",
         "1. Faculty opens the marks sheet. 2. Enters internal (0-40) and external (0-60) marks. 3. Saves. "
         "4. Triggers compute total, grade points and letter grade. 5. Changes are written to marks_audit.",
         "2a. Out-of-range or external without internal: form error. 1a. Another teacher's course: 403.",
         "Marks graded and audited."),
        ("UC5", "Manage master data", "Admin",
         "Admin adds, edits, searches and deletes students, faculty and courses.",
         "Logged in as admin.",
         "1. Admin opens a list. 2. Searches or pages. 3. Adds or edits through a form, or deletes after a "
         "confirmation page. 4. System saves through core/services.py.",
         "3a. Rule broken (duplicate, bad section, username used by faculty): friendly message on the form. "
         "3b. Course with enrollments: delete refused (RESTRICT).",
         "Data changed consistently."),
        ("UC6", "Enroll student", "Admin",
         "Admin enrolls a student in a course for an academic year.",
         "Student and course exist.",
         "1. Admin opens Enrollments. 2. Chooses student, course and year. 3. System checks the semester "
         "match. 4. Inserts the enrollment.",
         "3a. Semester mismatch: refused. 4a. Already enrolled: UNIQUE violation shown as a sentence.",
         "Enrollment created."),
        ("UC7", "Add timetable entry", "Admin",
         "Admin schedules a course in a slot, room and section.",
         "Course, slot and room exist.",
         "1. Admin opens Timetable. 2. Fills the form. 3. Trigger and UNIQUE keys check clashes. 4. Entry saved.",
         "3a. Teacher, room or section already booked: refused with names in the message.",
         "Timetable updated."),
        ("UC8", "Declare defaulters", "Admin",
         "Admin publishes the defaulter list at the attendance cut-off.",
         "Attendance recorded.",
         "1. Admin opens Defaulters (live list from v_defaulter_list). 2. Clicks \"Declare defaulter list "
         "now\". 3. System runs CALL sp_refresh_defaulter_flags(). 4. Shows the number flagged.",
         "None.",
         "students.is_defaulter updated for every student."),
        ("UC9", "Run engine report", "Admin",
         "Admin runs an allowed Java engine command from the portal.",
         "JAR built; logged in as admin.",
         "1. Admin opens /engine/. 2. Chooses a command and arguments. 3. Portal validates them and runs the "
         "JAR with --json. 4. Result is shown as tables.",
         "3a. Invalid argument: form error. 3b. JAR or Java missing, timeout, engine error: typed error card.",
         "Report shown (enroll and refresh-defaulters also write)."),
    ]
    for uc in ucs:
        r.kv_table([["Use case ID", uc[0]], ["Name", uc[1]], ["Actors", uc[2]], ["Description", uc[3]],
                    ["Pre-condition", uc[4]], ["Main flow", uc[5]], ["Alternate flows", uc[6]],
                    ["Post-condition", uc[7]]], f"Use case specification {uc[0]}: {uc[1]}")
    r.h2("3.10 Feasibility study")
    r.h3("Technical feasibility")
    r.p("All technologies are mature, free and well documented: MySQL 8.0, Java 17 LTS, Django 5.2 LTS and "
        "Python 3. They run on the existing laptop (Section 3.5). The only integration risk, calling Java from "
        "Django, was solved with a subprocess bridge and a JSON contract, and was verified by integration test "
        "IT08 (Chapter 6). The project is technically feasible.")
    r.h3("Economic feasibility")
    r.table(["Item", "Cost"], [
        ["MySQL Community Server, OpenJDK, Python, Django, PyMySQL, Maven, JUnit", "Free (open-source licences)"],
        ["Development tools: VS Code, Git, PlantUML, LibreOffice, Playwright", "Free"],
        ["Hardware", "Existing personal laptop (no purchase)"],
        ["Hosting", "Not needed: runs on localhost for the lab"],
        ["Team effort", "Four students, during the lab hours of the semester"],
    ], [4.0, 1.8], "Cost estimate", bold_first_col=False)
    r.p("No licence or hardware cost is involved, so the project is economically feasible.")
    r.h3("Operational feasibility")
    r.p("Each role sees a small dashboard with plain-language messages, and the tasks mirror what users already "
        "do (marking attendance, entering marks). Errors are explained in sentences (for example \"Attendance "
        "can only be recorded for Monday to Friday\") rather than database codes. The portal works in any "
        "browser and at phone width, so users need no training beyond a short demo. The system is "
        "operationally feasible.")
    r.h3("Schedule feasibility")
    commits = FACTS["git"]["commits"]
    r.p(f"The work was planned in five phases and completed between {commits[0]['date']} (first commit) and "
        f"{commits[-1]['date']} ({len(commits)} commits, listed in Appendix A).")
    r.table(["Phase", "Work", "Completed (commit date)"], [
        ["1", "Scaffolding and build configuration", "2026-10-15"],
        ["2", "MySQL schema, views, triggers, seed data, init_db.py", "2026-10-16"],
        ["3", "Java engine: config, models, DAOs, services, CLI, tests", "2026-10-31"],
        ["4", "Django portal: three role portals, Java bridge, tests", "2026-10-31"],
        ["4.5", "Review and polish: audit trail, CSV export, menu, CRUD, security settings", "2026-11-01"],
        ["5", "Software Engineering documentation and this report", "2026-11-01"],
        ["5.1", "Report converted to a group report", commits[-1]["date"]],
    ], [0.6, 3.6, 1.6], "Project schedule (from the Git history)")
    r.p("All phases fitted within the semester's lab schedule, so the project is feasible in time.")


def chapter4(r):
    r.chapter(4, "System Analysis and Design")
    r.h2("4.1 Introduction")
    r.p("This chapter turns the requirements of Chapter 3 into a design. It describes the architecture, the "
        "high- and low-level design, the UML diagrams, data flow diagrams, the ER diagram and database design, "
        "the input, output and user-interface design, the modules and the security design. Every diagram was "
        "drawn from the actual code and schema, and the database facts were read from the running MySQL "
        "server.")
    r.h2("4.2 System Architecture")
    r.p("The system follows a three-tier architecture with a shared database. The presentation tier is the "
        "browser (HTML5 and CSS3 pages) and the terminal (Java CLI). The application tier has two independent "
        "programs: the Django portal and the Java engine. The data tier is one MySQL database, which also holds "
        "the business rules (constraints, triggers, views, procedure). The portal talks to the engine only "
        "through a guarded subprocess call that exchanges JSON.")
    r.figure(diagram("d01_architecture"), diagram_title("d01_architecture"), native_dpi=170)
    r.h2("4.3 High-level design")
    r.p("At high level the system is divided into the modules shown in Figure 4.2. The database tier is "
        "built by three SQL scripts run in order (`schema.sql`, `views_triggers.sql`, `seed_data.sql`) by "
        "`init_db.py`. The Java engine is layered as config, models, DAO, services and CLI. The Django project "
        "has a `core` app (models, roles, services, bridge) and four feature apps (`accounts`, `student_portal`, "
        "`faculty_portal`, `admin_portal`).")
    r.figure(diagram("d02_high_level"), diagram_title("d02_high_level"), native_dpi=170)
    r.h2("4.4 Low-level design")
    r.p("The low-level design fixes the responsibility of each package or app, the interfaces between them and "
        "the data contract of the bridge.")
    loc = FACTS["loc"]["java_files_per_package"]
    r.table(["Java package", "Files", "Responsibility"], [
        ["config", loc["config"], "`DatabaseConfig` reads DB_* from environment variables, then `.env`; "
                                  "`ConnectionFactory` opens one JDBC connection per call."],
        ["models", loc["models"], "Abstract `Person` with `Student` and `Faculty`; `Course`, `Enrollment`, "
                                  "`AttendanceRecord`, `Marks`; records for view rows."],
        ["dao", loc["dao"], "Generic `CrudDao<T, ID>` and entity DAO interfaces; `Jdbc*Dao` implementations; "
                            "`JdbcDaoSupport` with `queryList` / `queryOne`; `ReportDao` for views and procedure."],
        ["services", loc["services"], "`StudentService` (profile, whois, enroll with semester rule), "
                                      "`ReportService` (defaulters, GPA, concurrent dashboard), `ReportExporter` "
                                      "(CSV)."],
        ["exceptions", loc["exceptions"], "Checked hierarchy rooted at `SmartCampusException`."],
        ["cli", loc["cli"], "Argument parsing, command registry, text tables, `JsonWriter`, interactive menu."],
    ], [1.0, 0.5, 4.3], "Java engine packages", size=9.5, bold_first_col=True)
    r.table(["Django app", "Responsibility"], [
        ["core", "Unmanaged models for 10 tables and 4 views (marks_audit is read through v_marks_audit); `roles.py` (role derivation and checks); "
                 "`services.py` (all writes, transactions); `db_errors.py` (friendly messages); "
                 "`java_bridge.py` and the `/engine/` view; `listing.py` (search and pagination); Django admin."],
        ["accounts", "Login, logout, password change, `/` role redirect, `seed_demo_users` command."],
        ["student_portal", "`/student/`: own profile, attendance, marks, CGPA, warning, timetable."],
        ["faculty_portal", "`/faculty/`: own courses, timetable, roster, attendance sheet, marks sheet."],
        ["admin_portal", "`/admin-portal/`: dashboard, CRUD, enrollments, timetable, reports, marks audit."],
    ], [1.2, 4.6], "Django apps", size=9.5, bold_first_col=True)
    r.p("**Bridge contract.** The portal runs `java -Dfile.encoding=UTF-8 -jar smart-campus-engine.jar <command> "
        "[args] --json`. On success the engine prints one line `{\"ok\":true,\"command\":...,\"data\":...}` "
        "on stdout with exit code 0; on failure it prints `{\"ok\":false,...,\"error\":{\"type\":...,"
        "\"message\":...}}` on stderr with exit code 1 (runtime/database error) or 2 (bad usage). The portal "
        "branches on `error.type`, never on the message.")
    r.h2("4.5 UML diagrams")
    r.p("All UML diagrams were written as PlantUML text in `docs/src/diagrams/` and rendered to PNG (see 4.5.10). "
        "Class names, methods and values match the source code and the database.")
    r.h3("4.5.1 Use Case Diagram")
    r.p("Three human actors use the portal. The MySQL database appears as a system actor, because its triggers "
        "and procedure compute grades, record the audit trail, check timetable clashes and declare defaulters.")
    r.figure(diagram("d03_use_case"), diagram_title("d03_use_case"), native_dpi=170)
    r.h3("4.5.2 Class Diagram")
    r.p("The domain model shows abstraction and inheritance (`Person` to `Student`/`Faculty`, with "
        "`describe()` overridden), encapsulation (private fields validated in constructors) and Java records "
        "for read-only view rows.")
    r.figure(diagram("d05_class_domain"), diagram_title("d05_class_domain"), native_dpi=170)
    r.figure(diagram("d05b_class_exceptions"), diagram_title("d05b_class_exceptions"), native_dpi=170)
    r.figure(diagram("d06_class_layers"), diagram_title("d06_class_layers"), native_dpi=170)
    r.figure(diagram("d06b_class_services"), diagram_title("d06b_class_services"), native_dpi=170)
    r.h3("4.5.3 Object Diagram")
    r.p("The object diagram is a snapshot of real rows: defaulter 25CSE004's CS301 enrollment, its attendance "
        "summary and marks, as read from `smart_campus_db`.")
    r.figure(diagram("d04_object"), diagram_title("d04_object"), native_dpi=170)
    r.h3("4.5.4 Sequence Diagram")
    r.figure(diagram("d11_sequence_bridge"), diagram_title("d11_sequence_bridge"), native_dpi=170)
    r.figure(diagram("d12_sequence_marks"), diagram_title("d12_sequence_marks"), native_dpi=170)
    r.h3("4.5.5 Collaboration Diagram")
    r.figure(diagram("d13_collaboration"), diagram_title("d13_collaboration"), native_dpi=170)
    r.h3("4.5.6 Activity Diagram")
    r.figure(diagram("d07_activity_marks"), diagram_title("d07_activity_marks"), native_dpi=170)
    r.figure(diagram("d08_activity_defaulters"), diagram_title("d08_activity_defaulters"), native_dpi=170)
    r.h3("4.5.7 State Diagram")
    r.figure(diagram("d09_state_marks"), diagram_title("d09_state_marks"), native_dpi=170)
    r.figure(diagram("d10_state_defaulter"), diagram_title("d10_state_defaulter"), native_dpi=170)
    r.h3("4.5.8 Component Diagram")
    r.figure(diagram("d14_component"), diagram_title("d14_component"), native_dpi=170)
    r.h3("4.5.9 Deployment Diagram")
    r.p("For the lab the whole system runs on one machine: the browser, the Django development server, the "
        "JVM started per request and the MySQL server all communicate over localhost.")
    r.figure(diagram("d15_deployment"), diagram_title("d15_deployment"), native_dpi=170)
    r.h3("4.5.10 CASE tools used")
    r.p("The diagrams were **not** drawn with StarUML or Rational Rose. They were written as plain-text "
        "**PlantUML 1.2026.9** sources (`docs/src/diagrams/*.puml`, with a shared style file `_style.iuml`) and "
        "rendered to PNG at 170 dpi by `docs/src/render_diagrams.py`, using PlantUML's built-in Smetana layout "
        "engine so that Graphviz is not needed. The project's own design notes in `docs/database_design.md` and "
        "`docs/django_portal.md` use **Mermaid**, which GitHub and VS Code render directly. Text-based diagrams "
        "were chosen because they are kept in Git next to the code, show clear differences when changed, and "
        "can be regenerated with one command.")
    r.table(["Tool", "Used for"], [
        ["PlantUML 1.2026.9 (Smetana layout)", "All 21 report diagrams: UML, ERD, DFD"],
        ["Mermaid (GitHub / VS Code preview)", "ER, flow and sequence diagrams in docs/*.md"],
        ["Visual Studio Code 1.143.1", "Editing code, SQL and diagram sources"],
        ["Git 2.53.0 and GitHub", "Version control (Appendix A)"],
        ["Maven Wrapper, JUnit 6, JaCoCo 0.8.16", "Java build, unit tests and coverage"],
        ["Django test runner, coverage.py 7.17.0", "Django tests and coverage"],
        ["Playwright 1.64.1 (Chromium)", "Screenshots and page timings"],
        ["python-docx 1.2.0, LibreOffice 26.8.2", "Building and checking this report"],
    ], [2.6, 3.2], "CASE and support tools", bold_first_col=True)
    r.h2("4.6 Data Flow Diagrams")
    r.p("The data flow diagrams use the Gane-Sarson notation: external entities as rectangles, processes as "
        "numbered rounded boxes and data stores as open-ended boxes named after the real tables.")
    r.figure(diagram("d17_dfd0"), diagram_title("d17_dfd0"), native_dpi=170)
    r.figure(diagram("d18_dfd1"), diagram_title("d18_dfd1"), native_dpi=170)
    r.figure(diagram("d19_dfd2"), diagram_title("d19_dfd2"), native_dpi=170)
    r.h2("4.7 Entity Relationship Diagram (ERD)")
    r.p("The ERD shows the 11 domain tables with their primary keys, foreign keys and cardinalities. "
        "`marks_audit` deliberately has no foreign key, so the history survives when a marks row is deleted.")
    r.figure(diagram("d16_erd"), diagram_title("d16_erd"), native_dpi=170)
    r.h2("4.8 Database design")
    s = FACTS["schema"]
    n_check, n_unique = len(constraints("CHECK")), len(constraints("UNIQUE"))
    n_fk = len([f for f in s["foreign_keys"] if f["table_name"] in DOMAIN_TABLES])
    r.p(f"The database `smart_campus_db` runs on MySQL {s['mysql_version']} with InnoDB and `utf8mb4`. It has "
        f"11 domain tables, 4 views, {len(s['triggers'])} triggers, 2 stored functions and 1 stored procedure, "
        f"with {n_fk} foreign keys, {n_unique} UNIQUE constraints and {n_check} CHECK constraints. Every table "
        "has a single-column surrogate primary key; natural keys (roll number, course code, student + course, "
        "room + slot, slot + section) are UNIQUE constraints.")
    r.p("**Normalisation.** Every column is atomic (1NF). Every table has a single-column key, so no attribute "
        "can depend on part of a key (2NF). Non-key attributes depend only on the key: for example a student "
        "row stores `dept_id`, not the department name, and a course stores `faculty_id`, not the teacher's "
        "name (3NF). The full functional dependencies are recorded in `docs/database_design.md`.")
    r.table(["Table", "Key functional dependencies"], [
        ["students", "student_id -> roll_number, username, email, full_name, semester, section, dept_id, cgpa, "
                     "is_defaulter; roll_number -> student_id"],
        ["courses", "course_id -> course_code, course_name, credits, course_type, hours_per_week, semester, "
                    "dept_id, faculty_id"],
        ["enrollments", "enrollment_id -> student_id, course_id, academic_year; (student_id, course_id) -> "
                        "enrollment_id"],
        ["attendance_records", "attendance_id -> enrollment_id, session_date, status; (enrollment_id, "
                               "session_date) -> attendance_id"],
        ["marks", "mark_id -> enrollment_id, internal_marks, external_marks; total_marks, grade_points and "
                  "letter_grade are maintained by triggers (documented exception)"],
        ["timetable_entries", "entry_id -> course_id, room_id, slot_id, section; (room_id, slot_id) -> entry_id; "
                              "(slot_id, section) -> entry_id"],
    ], [1.4, 4.4], "Main functional dependencies", size=9.5, bold_first_col=True)
    r.p("**Derived values.** Attendance percentage, defaulter status and GPA are computed in views. Three "
        "stored copies are documented exceptions: `marks.total_marks / grade_points / letter_grade` (kept by "
        "triggers so they can never disagree with the raw marks), `students.cgpa` (the official CGPA, which "
        "includes earlier semesters) and `students.is_defaulter` (set only when the defaulter list is declared).")
    trig_rows = [[t["trigger_name"], t["action_timing"], t["event_manipulation"], t["event_object_table"]]
                 for t in s["triggers"]]
    purpose = {
        "trg_faculty_before_insert": "Username must not exist in students",
        "trg_faculty_before_update": "Same rule on update",
        "trg_students_before_insert": "Username must not exist in faculty",
        "trg_students_before_update": "Same rule on update",
        "trg_marks_before_insert": "Compute total, grade points, letter grade",
        "trg_marks_before_update": "Recompute total and grade",
        "trg_marks_after_update": "Write old/new marks to marks_audit",
        "trg_prevent_timetable_faculty_clash": "Refuse a teacher double-booking",
        "trg_prevent_timetable_faculty_clash_update": "Same rule on update",
    }
    r.table(["Trigger", "Timing", "Event", "Table", "Purpose"],
            [row + [purpose.get(row[0], "")] for row in trig_rows], [2.3, 0.65, 0.65, 1.1, 1.8],
            "Triggers in smart_campus_db", size=8.5)
    r.table(["View / routine", "Purpose"], [
        ["v_attendance_summary", "Classes held, attended and percentage per enrollment"],
        ["v_defaulter_list", "Enrollments below 75% attendance"],
        ["v_student_cgpa_report", "Credit-weighted GPA of graded courses, next to the official CGPA"],
        ["v_marks_audit", "Audit rows joined with roll number, course and old/new grades"],
        ["fn_grade_points(total)", "Grade points 10/9/8/7/6/5/0 from the total"],
        ["fn_letter_grade(points)", "Letter grade O, A+, A, B+, B, P, F"],
        ["sp_refresh_defaulter_flags()", "Sets students.is_defaulter from v_defaulter_list"],
    ], [2.2, 3.6], "Views, functions and procedure", size=9.5, bold_first_col=True)
    r.h2("4.9 Database tables and attributes")
    r.p("The following tables were generated from MySQL's `information_schema` for the running database, so "
        "they match `database/schema.sql` exactly.")
    for table in DOMAIN_TABLES:
        fks = {f["column_name"]: f for f in foreign_keys(table)}
        rows = []
        for c in sorted(columns(table), key=lambda c: c["ordinal_position"]):
            notes = []
            if c["column_key"] == "PRI":
                notes.append("PK")
            if c["column_name"] in fks:
                f = fks[c["column_name"]]
                notes.append(f"FK -> {f['referenced_table_name']} (on delete {f['delete_rule'].lower()})")
            if c["column_key"] == "UNI":
                notes.append("UNIQUE")
            if "auto_increment" in (c["extra"] or ""):
                notes.append("auto increment")
            if c["column_default"] not in (None, "NULL"):
                notes.append(f"default {c['column_default']}")
            rows.append([c["column_name"], c["column_type"], "Yes" if c["is_nullable"] == "YES" else "No",
                         ", ".join(notes)])
        r.table(["Attribute", "Data type", "Null", "Key / notes"], rows, [1.6, 1.5, 0.5, 2.2],
                f"Table {table}", size=9)
    checks = [[c["table_name"], c["constraint_name"], c["check_clause"]] for c in constraints("CHECK")]
    r.table(["Table", "CHECK constraint", "Rule (as stored by MySQL)"], checks, [1.2, 2.0, 2.6],
            "CHECK constraints", size=8)
    r.h2("4.10 Input design")
    r.p("All input goes through Django forms, which validate types and ranges before the database checks them "
        "again. Inputs are kept short and use choices where possible.")
    r.table(["Form", "Fields", "Validation"], [
        ["Login", "Username, password", "Django authentication; error on wrong credentials"],
        ["Attendance sheet", "Date; Present/Absent per student", "Date picker; weekday CHECK in MySQL"],
        ["Marks sheet", "Internal (0-40), external (0-60) per student", "Decimal ranges; external needs "
                                                                          "internal; CHECK in MySQL"],
        ["Student / faculty / course", "All master-data fields", "ModelForm; UNIQUE, CHECK and username "
                                                                 "triggers"],
        ["Enrollment", "Student, course, academic year", "Semester match (app rule); UNIQUE key"],
        ["Timetable entry", "Course, slot, room, section", "Clash trigger; UNIQUE (slot, room) and "
                                                                 "(slot, section)"],
        ["Engine command", "Command, roll number, course code", "Allow-list and regex in form and bridge"],
        ["Search", "Free text q", "ORM icontains (parameterised)"],
    ], [1.5, 2.1, 2.2], "Input forms", size=9.5, bold_first_col=True)
    r.h2("4.11 Output design")
    r.table(["Output", "Shown to", "Source"], [
        ["Attendance and marks cards, warning banner", "Student", "v_attendance_summary, marks, v_defaulter_list"],
        ["Course roster, marks sheet with grades", "Faculty", "enrollments, marks (trigger-computed)"],
        ["Dashboard counts and averages", "Admin", "tables and views"],
        ["Defaulter list, GPA report, marks audit", "Admin", "v_defaulter_list, v_student_cgpa_report, "
                                                             "v_marks_audit"],
        ["Engine result tables and error cards", "Admin", "JSON from the Java engine"],
        ["Text tables, JSON, CSV files", "Terminal user", "Java engine CLI"],
    ], [2.4, 1.0, 2.4], "Outputs of the system", size=9.5)
    r.h2("4.12 User interface design")
    r.p("The interface is written in semantic HTML5 (`header`, `nav`, `main`, `section`, `table`, `form`, "
        "`label`) with one hand-written stylesheet, `static/css/campus.css`. Colours and spacing are CSS custom "
        "properties defined once; layouts use Flexbox and Grid, and media queries stack the cards and make "
        "tables scroll at phone width. No CSS framework or JavaScript framework is used. Every role has the "
        "same header with the user's name and role, a navigation bar and a log-out button. Messages appear as "
        "coloured banners; tables show a clear \"no records\" row when empty. The login page is shown below; "
        "the other screens appear in Sections 5.10 and 9.3.")
    r.figure(screen("01_login"), "Login page", rotate_if_wide=False)
    r.h2("4.13 Module design")
    r.table(["Module", "Inputs", "Processing", "Outputs"], [
        ["Authentication & roles", "Username, password", "Django auth; role derived from tables", "Session, "
                                                                                              "redirect"],
        ["Student portal", "Session", "Read own rows only", "Record page"],
        ["Attendance", "Date, statuses", "update_or_create in one transaction", "attendance_records"],
        ["Marks & grading", "Internal, external", "Triggers compute grade; AFTER trigger audits", "marks, "
                                                                                                "marks_audit"],
        ["Master data (CRUD)", "Form fields", "services.save_form / delete_object", "Rows or friendly error"],
        ["Enrollment", "Student, course, year", "Semester check, insert", "enrollments"],
        ["Timetable", "Course, slot, room, section", "Clash trigger + UNIQUE", "timetable_entries"],
        ["Reports & defaulters", "None / declare button", "Views; CALL procedure", "Report pages, flags"],
        ["Java engine", "Command, args", "DAO -> views/tables; concurrent dashboard", "Text, JSON, CSV"],
        ["Bridge", "Command form", "Validate, run JAR, parse JSON", "Result or typed error"],
    ], [1.4, 1.2, 2.0, 1.2], "Module design", size=9, bold_first_col=True)
    r.h2("4.14 Security and access control design")
    r.p("Access control follows role-based access control [2]: permissions belong to the three roles, and a "
        "user's role is derived on every request, never stored or taken from the URL.")
    r.table(["URL prefix", "Student", "Faculty", "Admin", "Anonymous"], [
        ["/student/", "200", "403", "403", "302 to login"],
        ["/faculty/ (own courses only)", "403", "200", "403", "302 to login"],
        ["/admin-portal/", "403", "403", "200", "302 to login"],
        ["/engine/", "403", "403", "200", "302 to login"],
        ["/accounts/password/", "200", "200", "200", "302 to login"],
        ["/django-admin/", "-", "-", "200 (superuser)", "login"],
    ], [2.2, 0.8, 0.8, 1.1, 1.0], "Role and access matrix (HTTP status returned)", size=9.5)
    r.table(["Threat", "Design measure"], [
        ["Unauthorised page access", "`@role_required` / `RoleRequiredMixin` on every view; a test walks the "
                                     "whole URL configuration"],
        ["Reading another person's data", "Person found from the login (`get_person`); no ids from the URL; "
                                          "faculty course pages check the teacher"],
        ["SQL injection", "Django ORM and Java `PreparedStatement` only"],
        ["Cross-site scripting", "Django template auto-escaping"],
        ["Cross-site request forgery", "CSRF token on every POST form; logout is POST only"],
        ["Command injection via the bridge", "Argument list, `shell=False`, allow-list of 6 commands, regex per "
                                             "argument, 30 s timeout"],
        ["Credential leaks", "Credentials only in git-ignored `.env`; hashed passwords; demo password refused "
                             "when DEBUG is off"],
        ["Session theft", "HttpOnly cookies, SameSite=Lax; secure cookies and HSTS when DJANGO_HTTPS=True"],
        ["Silent marks tampering", "AFTER UPDATE trigger records every change in marks_audit"],
    ], [1.9, 3.9], "Security threats and measures", size=9.5, bold_first_col=True)
