"""
Executes the report's unit, integration, white-box, black-box and security test cases against the
real system and records what actually happened. Each case states its expected result up front;
"actual" is the observed output and "status" is Pass only when the observation matches.

Writes go through the real views/triggers but run inside a transaction that is rolled back, so the
demo database is unchanged afterwards. Java cases run the real JAR through subprocess.

Run from the repo root:  .venv\\Scripts\\python.exe docs\\src\\evidence\\collect_cases.py
Writes docs/src/evidence/cases.json.
"""

import json
import os
import statistics
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "campus_portal"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "campus_portal.settings")
import django  # noqa: E402

django.setup()
from django.conf import settings  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402
from django.db import connection, transaction  # noqa: E402
from django.test import Client  # noqa: E402
from django.test.utils import setup_test_environment  # noqa: E402

from core import java_bridge, services  # noqa: E402
from core.db_errors import friendly_db_error  # noqa: E402
from core.models import (AttendanceRecord, AttendanceSummary, Course, Enrollment, Marks, MarksAuditRow,  # noqa: E402
                         Student, TimetableEntry)
from core.roles import get_role  # noqa: E402
from faculty_portal.forms import MarksSheetForm  # noqa: E402

setup_test_environment()
OUT = Path(__file__).resolve().parent / "cases.json"
JAR = REPO / "java_engine" / "target" / "smart-campus-engine.jar"
USERS = get_user_model().objects
RESULTS = {}


class Rollback(Exception):
    pass


@contextmanager
def rolled_back():
    """Everything inside runs in a transaction that is always rolled back."""
    with transaction.atomic():
        yield
        transaction.set_rollback(True)


def record(group, case_id, technique, module, objective, test_input, expected, run):
    started = time.monotonic()
    try:
        actual, passed = run()
    except Exception as exc:  # an unexpected crash is a real failure and is reported as such
        actual, passed = f"Unexpected {type(exc).__name__}: {exc}", False
    RESULTS.setdefault(group, []).append({
        "id": case_id, "technique": technique, "module": module, "objective": objective, "input": test_input,
        "expected": expected, "actual": actual, "status": "Pass" if passed else "Fail",
        "ms": round((time.monotonic() - started) * 1000)})
    print(f"{case_id:<6} {'PASS' if passed else 'FAIL'}  {actual[:110]}")


def client_for(username=None):
    client = Client()
    if username:
        client.force_login(USERS.get(username=username))
    return client


def java(*args, cwd=REPO):
    started = time.monotonic()
    proc = subprocess.run(["java", "-Dfile.encoding=UTF-8", "-jar", str(JAR), *args], cwd=cwd, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=60)
    return proc, round((time.monotonic() - started) * 1000)


def first_line(text):
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def grade_sql(total):
    with connection.cursor() as cursor:
        cursor.execute("SELECT fn_grade_points(%s), fn_letter_grade(fn_grade_points(%s))", [total, total])
        return cursor.fetchone()


def enrollment(roll, code):
    return Enrollment.objects.get(student__roll_number=roll, course__course_code=code)


def marks_post(client, enr, internal, external=""):
    return client.post("/faculty/courses/CS301/marks/", {f"internal_{enr.pk}": internal,
                                                         f"external_{enr.pk}": external})


# ------------------------------------------------------------------------------------------------
# Unit tests (single functions/units of the Python and SQL code)
# ------------------------------------------------------------------------------------------------
def unit_tests():
    g = "unit"
    record(g, "UT01", "Unit", "core.services", "Academic year rolls over in July",
           "current_academic_year(2026-10-31) and (2026-06-30)", "2026-27 and 2025-26",
           lambda: ((a := services.current_academic_year(date(2026, 10, 31))) + " and "
                    + (b := services.current_academic_year(date(2026, 6, 30))), (a, b) == ("2026-27", "2025-26")))

    class FakeError(Exception):
        pass
    record(g, "UT02", "Unit", "core.db_errors", "Duplicate-enrollment error becomes a sentence",
           "MySQL error 1062 on uq_enrollments_student_course", "This student is already enrolled in that course.",
           lambda: ((m := friendly_db_error(FakeError(1062, "Duplicate entry '1-1' for key "
                                                            "'enrollments.uq_enrollments_student_course'"))),
                    m == "This student is already enrolled in that course."))
    record(g, "UT03", "Unit", "core.java_bridge", "Allowed command builds a safe argument list",
           "build_command('student', ['25CSE001'])", "List ending student, 25CSE001, --json with -Dfile.encoding",
           lambda: ((argv := java_bridge.build_command("student", ["25CSE001"]))[-3:].__repr__() + " (list)",
                    isinstance(argv, list) and argv[-3:] == ["student", "25CSE001", "--json"]
                    and "-Dfile.encoding=UTF-8" in argv))

    def not_allowed():
        try:
            java_bridge.build_command("rm", ["-rf"])
        except java_bridge.EngineError as error:
            return f"EngineError {error.error_type}: {error.message}", error.error_type == "NotAllowed"
        return "no error", False
    record(g, "UT04", "Unit", "core.java_bridge", "Command outside the allow-list is refused", "build_command('rm')",
           "EngineError NotAllowed", not_allowed)
    record(g, "UT05", "Unit", "core.roles", "Role is derived from the login",
           "admin, ananya.rao, 25cse001", "admin, faculty, student",
           lambda: ((r := ", ".join(get_role(USERS.get(username=u)) for u in ("admin", "ananya.rao", "25cse001"))),
                    r == "admin, faculty, student"))
    record(g, "UT06", "Unit", "fn_grade_points / fn_letter_grade", "Grading function maps 85 marks",
           "SELECT fn_grade_points(85), fn_letter_grade(...)", "9, A+",
           lambda: ((r := grade_sql(85)) and f"{r[0]}, {r[1]}", r == (9, "A+")))


# ------------------------------------------------------------------------------------------------
# Integration tests (modules working together on the real database)
# ------------------------------------------------------------------------------------------------
def integration_tests():
    g = "integration"

    def login_redirects():
        outcomes = []
        for username in ("admin", "ananya.rao", "25cse001"):
            with rolled_back():
                client = Client()
                response = client.post("/accounts/login/", {"username": username,
                                                            "password": settings.DEMO_USER_PASSWORD}, follow=True)
                outcomes.append(f"{username} -> {response.request['PATH_INFO']}")
        text = "; ".join(outcomes)
        return text, text == "admin -> /admin-portal/; ananya.rao -> /faculty/; 25cse001 -> /student/"
    record(g, "IT01", "Integration", "accounts + core.roles", "Login lands each role on its own portal",
           "POST /accounts/login/ for admin, ananya.rao, 25cse001", "/admin-portal/, /faculty/, /student/",
           login_redirects)

    def marks_to_student_view():
        with rolled_back():
            enr = enrollment("25CSE001", "CS301")
            marks_post(client_for("ananya.rao"), enr, "38", "57")
            m = Marks.objects.get(enrollment=enr)
            page = client_for("25cse001").get("/student/").content.decode()
            shown = f"<strong>{m.letter_grade}</strong>" in page
            return (f"DB: {m.total_marks}, {m.grade_points}, {m.letter_grade}; student page shows grade: {shown}",
                    (m.total_marks, m.grade_points, m.letter_grade) == (Decimal("95.00"), 10, "O") and shown)
    record(g, "IT02", "Integration", "faculty_portal -> trg_marks_before_update -> student_portal",
           "Marks entered by faculty are graded by the trigger and shown to the student",
           "Faculty saves 38 + 57 for 25CSE001 in CS301", "95.00, 10, O stored and visible on /student/",
           marks_to_student_view)

    def attendance_to_view():
        with rolled_back():
            enr = enrollment("25CSE001", "CS301")
            before = AttendanceSummary.objects.get(enrollment_id=enr.pk).total_classes
            data = {"session_date": "2026-10-12"}
            data.update({f"status_{e.pk}": "PRESENT" for e in Enrollment.objects.filter(course__course_code="CS301")})
            client_for("ananya.rao").post("/faculty/courses/CS301/attendance/", data)
            after = AttendanceSummary.objects.get(enrollment_id=enr.pk)
            return (f"total_classes {before} -> {after.total_classes}; attendance {after.attendance_percentage}%",
                    after.total_classes == before + 1)
    record(g, "IT03", "Integration", "faculty_portal -> attendance_records -> v_attendance_summary",
           "A saved session updates the attendance view", "Mark all CS301 students PRESENT on Mon 2026-10-12",
           "total_classes increases by 1", attendance_to_view)

    def admin_enroll():
        with rolled_back():
            student = Student.objects.create(roll_number="25CSE061", username="25cse061", full_name="Report Probe",
                                             email="25cse061@smartcampus.example", semester=3, section="A", dept_id=1)
            response = client_for("admin").post("/admin-portal/enrollments/", {
                "student": student.pk, "course": Course.objects.get(course_code="CS301").pk,
                "academic_year": "2026-27"}, follow=True)
            text = "Enrolled 25CSE061 in CS301 for 2026-27." in response.content.decode()
            exists = Enrollment.objects.filter(student=student, course__course_code="CS301").exists()
            return f"message shown: {text}; row exists: {exists}", text and exists
    record(g, "IT04", "Integration", "admin_portal -> core.services -> enrollments",
           "Admin enroll form creates an enrollment", "New semester-3 student 25CSE061 + CS301, 2026-27",
           "Success message and new enrollments row", admin_enroll)

    def timetable_clash():
        with rolled_back():
            before = TimetableEntry.objects.count()
            response = client_for("admin").post("/admin-portal/timetable/", {
                "course": Course.objects.get(course_code="CS301").pk, "room": 3, "slot": 1, "section": "C"})
            page = response.content.decode()
            start = page.find("Timetable clash")
            message = page[start:page.find("<", start)] if start >= 0 else "(no clash message)"
            return (f"{message.strip()}; entries {before} -> {TimetableEntry.objects.count()}",
                    start >= 0 and TimetableEntry.objects.count() == before)
    record(g, "IT05", "Integration", "admin_portal -> trg_prevent_timetable_faculty_clash -> core.db_errors",
           "A teacher double-booking is refused with a readable message",
           "CS301 (Ananya Rao) in MON 09:00 slot for section C", "Clash message naming the teacher; no new row",
           timetable_clash)

    def audit_trail():
        with rolled_back():
            enr = enrollment("25CSE002", "CS301")
            marks_post(client_for("ananya.rao"), enr, "40", "60")
            rows = MarksAuditRow.objects.filter(roll_number="25CSE002")
            page = client_for("admin").get("/admin-portal/marks-audit/").content.decode()
            row = rows.first()
            return (f"{rows.count()} audit row: {row.old_total} ({row.old_letter_grade}) -> {row.new_total} "
                    f"({row.new_letter_grade}); on admin page: {'25CSE002' in page}",
                    rows.count() == 1 and row.new_letter_grade == "O" and "25CSE002" in page)
    record(g, "IT06", "Integration", "faculty_portal -> trg_marks_after_update -> v_marks_audit -> admin_portal",
           "A marks change is audited and visible to the admin", "Change 25CSE002 CS301 marks to 40 + 60",
           "One audit row with old and new grade, listed on /admin-portal/marks-audit/", audit_trail)

    def declare_defaulters():
        with rolled_back():
            Student.objects.filter(roll_number="25CSE001").update(is_defaulter=True)
            response = client_for("admin").post("/admin-portal/defaulters/", follow=True)
            flagged = sorted(Student.objects.filter(is_defaulter=True).values_list("roll_number", flat=True))
            shown = "2 student(s) flagged" in response.content.decode()
            return f"flagged after CALL: {', '.join(flagged)}; message: {shown}", flagged == ["25CSE004", "25CSE009"] and shown
    record(g, "IT07", "Integration", "admin_portal -> sp_refresh_defaulter_flags()",
           "Declaring defaulters re-computes every flag", "Stale flag on 25CSE001, then 'Declare defaulter list now'",
           "Only 25CSE004 and 25CSE009 flagged", declare_defaulters)

    def bridge_real():
        result = java_bridge.run_engine("defaulters")
        rolls = [s["roll_number"] for s in result.data["students"]]
        return (f"{result.data['student_count']} students ({', '.join(rolls)}), {result.data['course_count']} "
                f"course rows, {result.elapsed_ms} ms", rolls == ["25CSE004", "25CSE009"])
    record(g, "IT08", "Integration", "core.java_bridge -> Java JAR -> v_defaulter_list",
           "Django runs the real JAR and parses its JSON", "run_engine('defaulters')",
           "25CSE004 and 25CSE009 in the parsed data", bridge_real)

    def cli_gpa():
        proc, ms = java("gpa-report", "--json")
        data = json.loads(proc.stdout)["data"]
        return (f"exit {proc.returncode}, {len(data)} rows, first {data[0]['roll_number']} "
                f"({data[0]['weighted_gpa']}), {ms} ms", proc.returncode == 0 and data[0]["roll_number"] == "25CSE010")
    record(g, "IT09", "Integration", "Java CLI -> JDBC -> v_student_cgpa_report",
           "Engine reads the GPA view and sorts it", "java -jar smart-campus-engine.jar gpa-report --json",
           "Exit 0, 10 rows, 25CSE010 first", cli_gpa)

    def cli_duplicate():
        proc, ms = java("enroll", "25CSE001", "CS301", "--json")
        error = json.loads(proc.stderr)["error"]
        return f"exit {proc.returncode}, type {error['type']}: {error['message']}", \
            proc.returncode == 1 and error["type"] == "DuplicateEnrollment"
    record(g, "IT10", "Integration", "Java CLI -> enrollments UNIQUE constraint",
           "Duplicate enrollment is reported by the database through the engine",
           "enroll 25CSE001 CS301 --json", "Exit 1, error type DuplicateEnrollment", cli_duplicate)


# ------------------------------------------------------------------------------------------------
# White-box tests (internal structure: statements, branches, paths, conditions, loops)
# ------------------------------------------------------------------------------------------------
def white_box():
    g = "white_box"
    for case_id, total, expected in [("WB01", 95, (10, "O")), ("WB02", 85, (9, "A+")), ("WB03", 75, (8, "A")),
                                     ("WB04", 65, (7, "B+")), ("WB05", 55, (6, "B")), ("WB06", 45, (5, "P")),
                                     ("WB07", 30, (0, "F")), ("WB08", None, (None, None))]:
        record(g, case_id, "Statement / branch coverage", "fn_grade_points (CASE)", "Execute every CASE branch once",
               f"total = {total}", f"{expected[0]}, {expected[1]}",
               lambda t=total, e=expected: ((r := grade_sql(t)) and f"{r[0]}, {r[1]}", r == e))

    for case_id, user, path, expected, branch in [
            ("WB09", None, "/student/", 302, "Anonymous branch"),
            ("WB10", "ananya.rao", "/student/", 403, "Wrong-role branch"),
            ("WB11", "25cse001", "/student/", 200, "Allowed branch")]:
        record(g, case_id, "Branch coverage", "core.roles.role_required", branch,
               f"{user or 'anonymous'} GET {path}", f"HTTP {expected}",
               lambda u=user, p=path, e=expected: ((s := client_for(u).get(p).status_code) and f"HTTP {s}", s == e))

    def enroll_path(kind):
        with rolled_back():
            student = Student.objects.get(roll_number="25CSE001")
            if kind == "mismatch":
                course = Course.objects.create(course_code="CS501", course_name="Compiler Design", credits=3,
                                               course_type="THEORY", hours_per_week=3, semester=5, dept_id=1)
            elif kind == "duplicate":
                course = Course.objects.get(course_code="CS301")
            else:
                student = Student.objects.create(roll_number="25CSE062", username="25cse062", full_name="Path Probe",
                                                 email="25cse062@smartcampus.example", semester=3, section="A",
                                                 dept_id=1)
                course = Course.objects.get(course_code="CS301")
            try:
                e = services.enroll_student(student, course, "2026-27")
                return f"created enrollment for {e.student.roll_number} in {e.course.course_code}", kind == "ok"
            except services.ServiceError as error:
                return f"ServiceError: {error}", kind != "ok"
    for case_id, kind, test_input, expected in [
            ("WB12", "mismatch", "Semester-3 student, semester-5 course", "ServiceError (semester rule)"),
            ("WB13", "duplicate", "25CSE001 + CS301 (already enrolled)", "ServiceError (duplicate, from MySQL 1062)"),
            ("WB14", "ok", "New semester-3 student + CS301", "Enrollment created")]:
        record(g, case_id, "Path coverage", "core.services.enroll_student", f"Execute path: {kind}", test_input,
               expected, lambda k=kind: enroll_path(k))

    def form_condition(internal, external):
        enr = enrollment("25CSE001", "CS301")
        form = MarksSheetForm({f"internal_{enr.pk}": internal, f"external_{enr.pk}": external}, enrollments=[enr])
        valid = form.is_valid()
        return valid, form.errors.get(f"internal_{enr.pk}", [""])[0]
    for case_id, internal, external, expected_valid in [("WB15", "", "", True), ("WB16", "", "50", False),
                                                        ("WB17", "30", "", True), ("WB18", "30", "50", True)]:
        record(g, case_id, "Condition coverage", "MarksSheetForm.clean",
               "internal is None AND external is not None", f"internal='{internal}', external='{external}'",
               "valid" if expected_valid else "error: Enter internal marks before external marks.",
               lambda i=internal, x=external, ev=expected_valid:
               ((r := form_condition(i, x)) and (f"valid" if r[0] else f"error: {r[1]}"), r[0] == ev))

    def audit_condition(new_internal, new_external):
        with rolled_back():
            enr = enrollment("25CSE003", "CS301")
            m = Marks.objects.get(enrollment=enr)
            internal = m.internal_marks if new_internal == "same" else Decimal(new_internal)
            external = m.external_marks if new_external == "same" else (None if new_external == "NULL"
                                                                         else Decimal(new_external))
            Marks.objects.filter(pk=m.pk).update(internal_marks=internal, external_marks=external)
            return MarksAuditRow.objects.filter(mark_id=m.pk).count()
    for case_id, ni, ne, expected in [("WB19", "same", "same", 0), ("WB20", "20", "same", 1),
                                      ("WB21", "same", "NULL", 1)]:
        record(g, case_id, "Condition coverage", "trg_marks_after_update",
               "NOT(old <=> new internal AND old <=> new external)", f"internal {ni}, external {ne}",
               f"{expected} audit row(s)",
               lambda a=ni, b=ne, e=expected: ((n := audit_condition(a, b)) is not None and f"{n} audit row(s)", n == e))

    for case_id, args, expected_exit, label in [("WB22", [], 0, "0 arguments (shows help)"),
                                                ("WB23", ["courses"], 0, "1 argument"),
                                                ("WB24", ["enroll", "25CSE001", "CS301", "--year", "2026-27", "--json"], 1,
                                                 "6 arguments incl. options")]:
        record(g, case_id, "Loop testing", "cli.CommandLine.parse (argument loop)", f"Loop over {label}",
               "java -jar ... " + " ".join(args), f"exit {expected_exit}",
               lambda a=args, e=expected_exit: ((r := java(*a)) and
                                                f"exit {r[0].returncode}: {first_line(r[0].stdout or r[0].stderr)[:70]}",
                                                r[0].returncode == e))

    for case_id, cwd, label in [("WB25", REPO, "0 parent steps (repo root)"),
                                ("WB26", REPO / "java_engine", "1 parent step"),
                                ("WB27", REPO / "java_engine" / "target", "2 parent steps")]:
        record(g, case_id, "Loop testing", "config.DatabaseConfig.findEnvFile (walk-up loop)", f"Find .env after {label}",
               f"java -jar ... courses (cwd={cwd.relative_to(REPO.parent)})", "exit 0 (connected)",
               lambda c=cwd: ((r := java("courses", cwd=c)) and f"exit {r[0].returncode}", r[0].returncode == 0))


# ------------------------------------------------------------------------------------------------
# Black-box tests (requirements only: EP, BVA, decision table, state transition, error guessing)
# ------------------------------------------------------------------------------------------------
def black_box():
    g = "black_box"
    teacher = client_for("ananya.rao")

    def marks_input(internal, external=""):
        with rolled_back():
            enr = enrollment("25CSE001", "CS301")
            before = Marks.objects.get(enrollment=enr).internal_marks
            response = marks_post(teacher, enr, internal, external)
            saved = Marks.objects.get(enrollment=enr)
            accepted = response.status_code == 302
            return (f"accepted, stored {saved.internal_marks}" if accepted
                    else f"rejected (form error), stored value unchanged {before}"), accepted

    for case_id, technique, value, accept in [
            ("BB01", "Equivalence partitioning", "25", True), ("BB02", "Equivalence partitioning", "-5", False),
            ("BB03", "Equivalence partitioning", "45", False), ("BB04", "Equivalence partitioning", "abc", False),
            ("BB05", "Boundary value analysis", "-0.01", False), ("BB06", "Boundary value analysis", "0", True),
            ("BB07", "Boundary value analysis", "40", True), ("BB08", "Boundary value analysis", "40.01", False)]:
        record(g, case_id, technique, "Faculty marks entry (internal, 0-40)", "Validate internal marks",
               f"internal = {value}", "accepted" if accept else "rejected",
               lambda v=value, a=accept: ((r := marks_input(v)) and r[0], r[1] == a))

    def grade_boundary(internal, external):
        with rolled_back():
            enr = enrollment("25CSE001", "CS301")
            marks_post(teacher, enr, internal, external)
            m = Marks.objects.get(enrollment=enr)
            return f"{m.total_marks} -> {m.grade_points}, {m.letter_grade}", (m.grade_points, m.letter_grade)
    for case_id, internal, external, expected in [("BB09", "39.99", "0", (0, "F")), ("BB10", "40", "0", (5, "P")),
                                                  ("BB11", "30", "59.99", (9, "A+")), ("BB12", "30", "60", (10, "O"))]:
        record(g, case_id, "Boundary value analysis", "Grade scale via trg_marks_before_update",
               "Grade at a scale boundary", f"{internal} + {external}", f"{expected[0]}, {expected[1]}",
               lambda i=internal, x=external, e=expected: ((r := grade_boundary(i, x)) and r[0], r[1] == e))

    def attendance_on(day):
        with rolled_back():
            data = {"session_date": day}
            data.update({f"status_{e.pk}": "PRESENT" for e in Enrollment.objects.filter(course__course_code="CS301")})
            response = teacher.post("/faculty/courses/CS301/attendance/", data, follow=True)
            page = response.content.decode()
            if "saved for" in page:
                return "saved", True
            return ("rejected: Attendance can only be recorded for Monday to Friday."
                    if "Monday to Friday" in page else "rejected (other)"), False
    for case_id, day, label, accept in [("BB13", "2026-10-16", "Friday", True), ("BB14", "2026-10-17", "Saturday", False),
                                        ("BB15", "2026-10-19", "Monday", True)]:
        record(g, case_id, "Equivalence partitioning / boundary", "Attendance date (weekday rule, CHECK)",
               f"{label} session", day, "saved" if accept else "rejected (weekend)",
               lambda d=day, a=accept: ((r := attendance_on(d)) and r[0], r[1] == a))

    def section_value(value):
        with rolled_back():
            response = client_for("admin").post("/admin-portal/students/add/", {
                "roll_number": "25CSE063", "username": "25cse063", "full_name": "Section Probe",
                "email": "25cse063@smartcampus.example", "semester": 3, "section": value, "dept": 1, "cgpa": "7.00"})
            created = Student.objects.filter(roll_number="25CSE063").exists()
            page = response.content.decode()
            reason = ("Section must be a single capital letter" if "single capital letter" in page
                      else "at most 1 character" if "at most 1 character" in page else "")
            return ("created" if created else f"rejected: {reason}"), created
    for case_id, value, accept in [("BB16", "A", True), ("BB17", "a", False), ("BB18", "AB", False)]:
        record(g, case_id, "Equivalence partitioning", "Student section (REGEXP_LIKE CHECK)", "Validate section",
               f"section = '{value}'", "created" if accept else "rejected",
               lambda v=value, a=accept: ((r := section_value(v)) and r[0], r[1] == a))

    def enroll_rule(match, enrolled):
        with rolled_back():
            student = Student.objects.create(roll_number="25CSE064", username="25cse064", full_name="Rule Probe",
                                             email="25cse064@smartcampus.example", semester=3, section="A", dept_id=1)
            course = (Course.objects.get(course_code="CS301") if match else
                      Course.objects.create(course_code="CS502", course_name="Data Mining", credits=3,
                                            course_type="THEORY", hours_per_week=3, semester=5, dept_id=1))
            if enrolled:
                Enrollment.objects.create(student=student, course=course, academic_year="2026-27")
            try:
                services.enroll_student(student, course, "2026-27")
                return "enrolled"
            except services.ServiceError as error:
                return f"refused: {error}"
    for case_id, match, enrolled, expected in [
            ("BB19", True, False, "enrolled"), ("BB20", True, True, "refused: This student is already enrolled"),
            ("BB21", False, False, "refused: CS502 is a semester 5 course"),
            ("BB22", False, True, "refused: CS502 is a semester 5 course")]:
        record(g, case_id, "Decision table", "Enroll (semester match x already enrolled)",
               f"Rule: semester match={'Y' if match else 'N'}, enrolled={'Y' if enrolled else 'N'}",
               f"match={'Y' if match else 'N'}, enrolled={'Y' if enrolled else 'N'}", expected,
               lambda m=match, e=enrolled, x=expected: ((r := enroll_rule(m, e)) and r, r.startswith(x)))

    def marks_rule(internal, external):
        with rolled_back():
            enr = enrollment("25CSE001", "CS301")
            Marks.objects.filter(enrollment=enr).delete()
            response = marks_post(teacher, enr, internal, external)
            m = Marks.objects.filter(enrollment=enr).first()
            if response.status_code != 302:
                return "form error: Enter internal marks before external marks."
            if m is None:
                return "no marks row written"
            return f"stored; total={m.total_marks}, grade={m.letter_grade}"
    for case_id, internal, external, expected in [
            ("BB23", "", "", "no marks row written"), ("BB24", "30", "", "stored; total=None, grade=None"),
            ("BB25", "30", "50", "stored; total=80.00, grade=A+"), ("BB26", "", "50", "form error")]:
        record(g, case_id, "Decision table", "Marks entry (internal given x external given)",
               "Rule from the marks decision table", f"internal='{internal}', external='{external}'", expected,
               lambda i=internal, x=external, e=expected: ((r := marks_rule(i, x)) and r, r.startswith(e)))

    def marks_states():
        with rolled_back():
            enr = enrollment("25CSE001", "CS301")
            Marks.objects.filter(enrollment=enr).delete()
            states = ["No marks" if not Marks.objects.filter(enrollment=enr).exists() else "?"]
            marks_post(teacher, enr, "30")
            m = Marks.objects.get(enrollment=enr)
            states.append("Internal only" if m.letter_grade is None else "?")
            marks_post(teacher, enr, "30", "50")
            m.refresh_from_db()
            states.append(f"Graded ({m.letter_grade})")
            marks_post(teacher, enr, "35", "50")
            m.refresh_from_db()
            audits = MarksAuditRow.objects.filter(mark_id=m.pk).count()
            states.append(f"Re-graded ({m.letter_grade}, {audits} audit rows)")
            return " -> ".join(states)
    record(g, "BB27", "State transition", "Marks life cycle", "No marks -> internal -> graded -> re-graded",
           "Save internal 30; then 30+50; then 35+50",
           "No marks -> Internal only -> Graded (A+) -> Re-graded (A+, 2 audit rows)",
           lambda: ((r := marks_states()) and r,
                    r == "No marks -> Internal only -> Graded (A+) -> Re-graded (A+, 2 audit rows)"))

    def defaulter_states():
        with rolled_back():
            Student.objects.filter(roll_number="25CSE004").update(is_defaulter=False)
            before = Student.objects.get(roll_number="25CSE004").is_defaulter
            services.refresh_defaulter_flags()
            after = Student.objects.get(roll_number="25CSE004").is_defaulter
            return f"declared flag {before} -> {after}", (before, after) == (False, True)
    record(g, "BB28", "State transition", "Defaulter declaration (25CSE004, 66.67% / 58.33%)",
           "Not declared -> Declared on 'declare'", "Clear the flag, then CALL sp_refresh_defaulter_flags()",
           "False -> True", defaulter_states)

    def error_guess(kind):
        admin = client_for("admin")
        if kind == "sqli":
            response = admin.get("/admin-portal/students/", {"q": "25CSE001' OR '1'='1"})
            return f"HTTP {response.status_code}, {response.context['page_obj'].paginator.count} rows", \
                response.status_code == 200 and response.context["page_obj"].paginator.count == 0
        if kind == "bridge":
            response = admin.get("/engine/", {"command": "student", "lookup-roll_number": "25CSE001; dir"})
            ok = "Letters and digits only" in response.content.decode()
            return f"HTTP {response.status_code}, form error shown: {ok}", ok
        if kind == "username":
            with rolled_back():
                response = admin.post("/admin-portal/students/add/", {
                    "roll_number": "25CSE065", "username": "ananya.rao", "full_name": "Copy Cat",
                    "email": "copy@smartcampus.example", "semester": 3, "section": "A", "dept": 1, "cgpa": "7.00"})
                ok = "Username is already used by a faculty member" in response.content.decode()
                return f"message shown: {ok}", ok
        if kind == "xss":
            with rolled_back():
                Student.objects.create(roll_number="25CSE066", username="25cse066", full_name="<script>alert(1)</script>",
                                       email="xss@smartcampus.example", semester=3, section="A", dept_id=1)
                page = admin.get("/admin-portal/students/", {"q": "25CSE066"}).content.decode()
                escaped = "&lt;script&gt;alert(1)&lt;/script&gt;" in page and "<script>alert(1)</script>" not in page
                return f"rendered escaped: {escaped}", escaped
        if kind == "csrf":
            strict = Client(enforce_csrf_checks=True)
            strict.force_login(USERS.get(username="admin"))
            status = strict.post("/admin-portal/defaulters/").status_code
            return f"HTTP {status}", status == 403
        if kind == "role":
            status = client_for("25cse001").get("/admin-portal/students/").status_code
            return f"HTTP {status}", status == 403
        if kind == "other_teacher":
            status = client_for("kiran.kumar").get("/faculty/courses/CS301/marks/").status_code
            return f"HTTP {status}", status == 403
    for case_id, kind, test_input, expected in [
            ("BB29", "sqli", "Search q = 25CSE001' OR '1'='1", "HTTP 200, 0 rows (treated as text)"),
            ("BB30", "bridge", "Engine roll number '25CSE001; dir'", "Form error, engine not called"),
            ("BB31", "username", "New student with faculty username ananya.rao", "Trigger message shown"),
            ("BB32", "xss", "Student name <script>alert(1)</script>", "Name rendered escaped"),
            ("BB33", "csrf", "POST /admin-portal/defaulters/ without CSRF token", "HTTP 403"),
            ("BB34", "role", "Student opens /admin-portal/students/", "HTTP 403"),
            ("BB35", "other_teacher", "kiran.kumar opens CS301 marks (not his course)", "HTTP 403")]:
        record(g, case_id, "Error guessing", "Security / robustness", f"Guess: {kind}", test_input, expected,
               lambda k=kind: error_guess(k))


# ------------------------------------------------------------------------------------------------
# Java engine CLI timings (median of 5 runs each, read-only commands)
# ------------------------------------------------------------------------------------------------
def cli_timings():
    timings = {}
    for args in (["help"], ["courses"], ["student", "25CSE001"], ["defaulters"], ["gpa-report"], ["dashboard"]):
        runs = [java(*args, "--json")[1] for _ in range(5)]
        timings[" ".join(args)] = {"median_ms": statistics.median(runs), "min_ms": min(runs), "max_ms": max(runs)}
        print("timing", args, timings[" ".join(args)])
    return timings


if __name__ == "__main__":
    if not JAR.is_file():
        sys.exit("Build the JAR first: cd java_engine; .\\mvnw.cmd clean package")
    unit_tests()
    integration_tests()
    white_box()
    black_box()
    RESULTS["cli_timings"] = cli_timings()
    OUT.write_text(json.dumps(RESULTS, indent=1, default=str), encoding="utf-8")
    failed = [c["id"] for group in ("unit", "integration", "white_box", "black_box") for c in RESULTS[group]
              if c["status"] != "Pass"]
    total = sum(len(RESULTS[g]) for g in ("unit", "integration", "white_box", "black_box"))
    print(f"\n{total} cases, {total - len(failed)} passed, failed: {failed or 'none'}")
