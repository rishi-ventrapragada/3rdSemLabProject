import json
import subprocess
import tempfile
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase, override_settings

from core import java_bridge
from core.java_bridge import EngineError, build_command, run_engine

from .base import CampusTestCase

_JAR_DIR = tempfile.TemporaryDirectory()
FAKE_JAR = Path(_JAR_DIR.name) / "smart-campus-engine.jar"
FAKE_JAR.write_bytes(b"not really a jar; subprocess is mocked")


def completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def ok(command, data):
    return completed(stdout=json.dumps({"ok": True, "command": command, "data": data}) + "\n")


def failed(command, error_type, message, code=1):
    return completed(returncode=code,
                     stderr=json.dumps({"ok": False, "command": command,
                                        "error": {"type": error_type, "message": message}}) + "\n")


@override_settings(JAVA_ENGINE_JAR=FAKE_JAR, JAVA_BIN="java", JAVA_ENGINE_TIMEOUT=7)
class BuildCommandTests(SimpleTestCase):

    def test_argv_is_a_list_with_json_flag_and_utf8(self):
        argv = build_command("student", ["25CSE001"])
        self.assertEqual(argv, ["java", "-Dfile.encoding=UTF-8", "-jar", str(FAKE_JAR), "student", "25CSE001",
                                "--json"])

    def test_enroll_with_year(self):
        self.assertEqual(build_command("enroll", ["25CSE001", "CS301"], year="2026-27")[-3:],
                         ["--year", "2026-27", "--json"])

    def test_commands_off_the_allow_list_are_refused(self):
        for command in ["help", "whois", "courses", "rm", "student;dir", ""]:
            with self.subTest(command=command):
                with self.assertRaises(EngineError) as ctx:
                    build_command(command)
                self.assertEqual(ctx.exception.error_type, "NotAllowed")

    def test_arguments_are_validated(self):
        bad = [("student", []), ("student", ["25CSE001", "extra"]), ("student", ["25CSE001 --json"]),
               ("student", ["$(whoami)"]), ("student", ["--help"]), ("enroll", ["25CSE001", "CS 301"]),
               ("defaulters", ["x"])]
        for command, args in bad:
            with self.subTest(command=command, args=args):
                with self.assertRaises(EngineError) as ctx:
                    build_command(command, args)
                self.assertEqual(ctx.exception.error_type, "BadArgument")

    def test_year_is_validated_and_only_for_enroll(self):
        for command, args, year in [("enroll", ["25CSE001", "CS301"], "2026/27"), ("defaulters", [], "2026-27")]:
            with self.subTest(command=command, year=year):
                with self.assertRaises(EngineError):
                    build_command(command, args, year=year)


@override_settings(JAVA_ENGINE_JAR=FAKE_JAR, JAVA_BIN="java", JAVA_ENGINE_TIMEOUT=7)
class RunEngineTests(SimpleTestCase):

    @mock.patch("core.java_bridge.subprocess.run")
    def test_success_parses_stdout_and_runs_without_a_shell(self, run):
        run.return_value = ok("gpa-report", [{"roll_number": "25CSE001"}])
        result = run_engine("gpa-report")
        self.assertEqual(result.data, [{"roll_number": "25CSE001"}])
        self.assertEqual(result.command, "gpa-report")
        args, kwargs = run.call_args
        self.assertIsInstance(args[0], list)
        self.assertIs(kwargs["shell"], False)
        self.assertEqual(kwargs["timeout"], 7)
        self.assertTrue(kwargs["capture_output"])

    @mock.patch("core.java_bridge.subprocess.run")
    def test_json_after_jvm_warnings_is_still_parsed(self, run):
        run.return_value = completed(stdout="Picked up JAVA_TOOL_OPTIONS: -Xmx1g\n"
                                            + json.dumps({"ok": True, "command": "dashboard", "data": {}}))
        self.assertEqual(run_engine("dashboard").data, {})

    @mock.patch("core.java_bridge.subprocess.run")
    def test_engine_error_type_comes_from_stderr_json(self, run):
        run.return_value = failed("student", "StudentNotFound", "Student not found: 25CSE999")
        with self.assertRaises(EngineError) as ctx:
            run_engine("student", "25CSE999")
        self.assertEqual(ctx.exception.error_type, "StudentNotFound")
        self.assertEqual(ctx.exception.message, "Student not found: 25CSE999")
        self.assertEqual(ctx.exception.exit_code, 1)

    @mock.patch("core.java_bridge.subprocess.run")
    def test_usage_error_keeps_exit_code_2(self, run):
        run.return_value = failed("enroll", "Usage", "Usage: enroll <rollNo> <courseCode>", code=2)
        with self.assertRaises(EngineError) as ctx:
            run_engine("enroll", "25CSE001", "CS301")
        self.assertEqual((ctx.exception.error_type, ctx.exception.exit_code), ("Usage", 2))

    @mock.patch("core.java_bridge.subprocess.run")
    def test_non_json_failure_is_internal(self, run):
        run.return_value = completed(returncode=1, stderr="Error: Unable to access jarfile")
        with self.assertRaises(EngineError) as ctx:
            run_engine("defaulters")
        self.assertEqual(ctx.exception.error_type, "Internal")
        self.assertIn("Unable to access jarfile", ctx.exception.message)

    @mock.patch("core.java_bridge.subprocess.run")
    def test_success_without_json_is_bad_output(self, run):
        run.return_value = completed(stdout="Usage: java -jar ...")
        with self.assertRaises(EngineError) as ctx:
            run_engine("defaulters")
        self.assertEqual(ctx.exception.error_type, "BadOutput")

    @mock.patch("core.java_bridge.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="java", timeout=7))
    def test_timeout(self, run):
        with self.assertRaises(EngineError) as ctx:
            run_engine("dashboard")
        self.assertEqual(ctx.exception.error_type, "Timeout")

    @mock.patch("core.java_bridge.subprocess.run", side_effect=FileNotFoundError("java"))
    def test_java_missing(self, run):
        with self.assertRaises(EngineError) as ctx:
            run_engine("dashboard")
        self.assertEqual(ctx.exception.error_type, "JavaMissing")

    @mock.patch("core.java_bridge.subprocess.run")
    def test_jar_missing_never_starts_java(self, run):
        with override_settings(JAVA_ENGINE_JAR=Path(_JAR_DIR.name) / "missing.jar"):
            with self.assertRaises(EngineError) as ctx:
                run_engine("defaulters")
        self.assertEqual(ctx.exception.error_type, "JarMissing")
        self.assertIn("mvnw", ctx.exception.hint)
        run.assert_not_called()


@override_settings(JAVA_ENGINE_JAR=FAKE_JAR)
class EngineViewTests(CampusTestCase):
    """The /engine/ page with the bridge mocked: one call per request, errors shown with their type."""

    def setUp(self):
        self.login(self.admin)

    @mock.patch("core.views.java_bridge.run_engine")
    def test_page_without_a_command_makes_no_call(self, run_engine):
        response = self.client.get("/engine/")
        self.assertEqual(response.status_code, 200)
        run_engine.assert_not_called()

    @mock.patch("core.views.java_bridge.run_engine")
    def test_gpa_report_renders_a_table_with_one_call(self, run_engine):
        run_engine.return_value = java_bridge.EngineResult("gpa-report", [
            {"roll_number": "25CSE010", "full_name": "Meghana Krishnan", "section": "B", "courses_graded": 6,
             "credits_graded": 14, "credits_earned": 14, "weighted_gpa": 8.0, "cgpa": 7.95}], 512)
        response = self.client.get("/engine/", {"command": "gpa-report"})
        self.assertContains(response, "Meghana Krishnan")
        self.assertContains(response, "512 ms")
        run_engine.assert_called_once_with("gpa-report", year=None)

    @mock.patch("core.views.java_bridge.run_engine")
    def test_student_lookup_passes_the_validated_roll_number(self, run_engine):
        run_engine.return_value = java_bridge.EngineResult("student", {"roll_number": "25CSE001", "courses": []}, 400)
        self.client.get("/engine/", {"command": "student", "lookup-roll_number": "25CSE001"})
        run_engine.assert_called_once_with("student", "25CSE001", year=None)

    @mock.patch("core.views.java_bridge.run_engine")
    def test_invalid_roll_number_never_reaches_the_engine(self, run_engine):
        response = self.client.get("/engine/", {"command": "student", "lookup-roll_number": "25CSE001; dir"})
        self.assertContains(response, "Letters and digits only")
        run_engine.assert_not_called()

    @mock.patch("core.views.java_bridge.run_engine")
    def test_engine_error_type_is_shown(self, run_engine):
        run_engine.side_effect = EngineError("StudentNotFound", "Student not found: 25CSE999", exit_code=1)
        response = self.client.get("/engine/", {"command": "student", "lookup-roll_number": "25CSE999"})
        self.assertContains(response, "StudentNotFound")
        self.assertContains(response, "Student not found: 25CSE999")

    @mock.patch("core.views.java_bridge.run_engine")
    def test_writes_require_post(self, run_engine):
        self.client.get("/engine/", {"command": "refresh-defaulters"})
        run_engine.assert_not_called()
        run_engine.return_value = java_bridge.EngineResult("refresh-defaulters", {"flagged_students": 2}, 300)
        response = self.client.post("/engine/", {"command": "refresh-defaulters"})
        self.assertContains(response, "2 student(s) flagged")
        run_engine.assert_called_once_with("refresh-defaulters", year=None)

    @mock.patch("core.views.java_bridge.run_engine")
    def test_enroll_form_passes_year(self, run_engine):
        run_engine.return_value = java_bridge.EngineResult("enroll", {
            "enrollment_id": 61, "roll_number": "25CSE001", "full_name": "Aarav Sharma", "course_code": "CS301",
            "course_name": "Database Management Systems", "academic_year": "2026-27"}, 450)
        response = self.client.post("/engine/", {"command": "enroll", "enroll-roll_number": "25CSE001",
                                                 "enroll-course_code": "CS301", "enroll-academic_year": "2026-27"})
        self.assertContains(response, "enrollment_id 61")
        run_engine.assert_called_once_with("enroll", "25CSE001", "CS301", year="2026-27")

    def test_missing_jar_shows_build_instructions(self):
        with override_settings(JAVA_ENGINE_JAR=Path(_JAR_DIR.name) / "missing.jar"):
            response = self.client.get("/engine/", {"command": "defaulters"})
        self.assertContains(response, "has not been built yet")
        self.assertContains(response, "JarMissing")
        self.assertContains(response, "mvnw.cmd clean package")

    def test_non_admins_get_403(self):
        for user in (self.student, self.teacher):
            self.login(user)
            self.assertEqual(self.client.get("/engine/", {"command": "defaulters"}).status_code, 403)
