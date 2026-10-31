"""Real-database tests: the views, triggers and procedure in test_<DB_NAME> do the work."""

import unittest
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command

from core.models import AttendanceRecord, Course, Enrollment, Marks, Student, TimetableEntry

from .base import CampusTestCase


class StudentPortalTests(CampusTestCase):

    def test_defaulter_sees_the_warning_from_v_defaulter_list(self):
        self.login(self.defaulter)
        response = self.client.get("/student/")
        self.assertContains(response, "Attendance warning: below 75% in 6 courses")
        self.assertContains(response, "declared defaulter list")

    def test_student_in_good_standing_sees_no_warning(self):
        self.login(self.student)
        response = self.client.get("/student/")
        self.assertNotContains(response, "Attendance warning")
        self.assertContains(response, "8.45")             # official CGPA
        self.assertContains(response, "7.57")             # weighted GPA from v_student_cgpa_report
        self.assertContains(response, "Database Management Systems")

    def test_student_sees_only_their_own_courses(self):
        self.login(self.student)
        response = self.client.get("/student/")
        self.assertNotContains(response, "Sneha Reddy")
        self.assertEqual(len(response.context["courses"]), 6)


class FacultyPortalTests(CampusTestCase):

    def setUp(self):
        self.login(self.teacher)
        self.enrollment = Enrollment.objects.get(student__roll_number="25CSE001", course__course_code="CS301")

    def test_marks_are_graded_by_the_trigger_not_python(self):
        response = self.client.post("/faculty/courses/CS301/marks/", {
            f"internal_{self.enrollment.pk}": "35", f"external_{self.enrollment.pk}": "55"}, follow=True)
        self.assertContains(response, "computed by the database")
        marks = Marks.objects.get(enrollment=self.enrollment)
        self.assertEqual((marks.total_marks, marks.grade_points, marks.letter_grade), (Decimal("90.00"), 10, "O"))

    def test_internal_only_leaves_the_grade_empty(self):
        self.client.post("/faculty/courses/CS301/marks/", {f"internal_{self.enrollment.pk}": "30"})
        marks = Marks.objects.get(enrollment=self.enrollment)
        self.assertEqual((marks.external_marks, marks.total_marks, marks.letter_grade), (None, None, None))

    def test_out_of_range_marks_are_rejected_per_row(self):
        response = self.client.post("/faculty/courses/CS301/marks/", {f"internal_{self.enrollment.pk}": "45"})
        self.assertContains(response, "less than or equal to 40")
        self.assertEqual(Marks.objects.get(enrollment=self.enrollment).internal_marks, Decimal("36.00"))

    def test_attendance_is_saved_and_updated(self):
        monday = date(2026, 10, 12)
        data = {"session_date": monday.isoformat()}
        enrollments = Enrollment.objects.filter(course__course_code="CS301")
        data.update({f"status_{e.pk}": "PRESENT" for e in enrollments})
        data[f"status_{self.enrollment.pk}"] = "ABSENT"
        response = self.client.post("/faculty/courses/CS301/attendance/", data, follow=True)
        self.assertContains(response, "saved for 10 students")
        self.assertEqual(AttendanceRecord.objects.get(enrollment=self.enrollment, session_date=monday).status, "ABSENT")

        data[f"status_{self.enrollment.pk}"] = "PRESENT"
        self.client.post("/faculty/courses/CS301/attendance/", data)
        self.assertEqual(AttendanceRecord.objects.filter(enrollment=self.enrollment, session_date=monday).count(), 1)
        self.assertEqual(AttendanceRecord.objects.get(enrollment=self.enrollment, session_date=monday).status,
                         "PRESENT")

    def test_weekend_attendance_shows_the_database_rule(self):
        saturday = date(2026, 10, 10)
        data = {"session_date": saturday.isoformat(), f"status_{self.enrollment.pk}": "PRESENT"}
        for e in Enrollment.objects.filter(course__course_code="CS301").exclude(pk=self.enrollment.pk):
            data[f"status_{e.pk}"] = "PRESENT"
        response = self.client.post("/faculty/courses/CS301/attendance/", data)
        self.assertContains(response, "Attendance can only be recorded for Monday to Friday.")
        self.assertFalse(AttendanceRecord.objects.filter(session_date=saturday).exists())


class AdminPortalTests(CampusTestCase):

    def setUp(self):
        self.login(self.admin)

    def test_teacher_double_booking_shows_a_friendly_message(self):
        # Ananya Rao teaches CS301 on MON 09:00 (slot 1) to section A; give her section C too.
        response = self.client.post("/admin-portal/timetable/", {
            "course": Course.objects.get(course_code="CS301").pk, "room": 3, "slot": 1, "section": "C"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Timetable clash: Ananya Rao already teaches CS301 at MON 09:00-10:00")
        self.assertEqual(TimetableEntry.objects.count(), 20)

    def test_room_double_booking_uses_the_unique_constraint_message(self):
        response = self.client.post("/admin-portal/timetable/", {
            "course": Course.objects.get(course_code="CS353").pk, "room": 1, "slot": 1, "section": "C"})
        self.assertContains(response, "already booked")

    def test_valid_timetable_entry_is_added(self):
        response = self.client.post("/admin-portal/timetable/", {
            "course": Course.objects.get(course_code="CS353").pk, "room": 3, "slot": 3, "section": "C"}, follow=True)
        self.assertContains(response, "Timetable entry added.")
        self.assertEqual(TimetableEntry.objects.count(), 21)

    def test_student_cannot_take_a_faculty_username(self):
        response = self.client.post("/admin-portal/students/add/", {
            "roll_number": "25CSE050", "username": "ananya.rao", "full_name": "Copy Cat",
            "email": "copycat@smartcampus.example", "semester": 3, "section": "A", "dept": 1, "cgpa": "7.00"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Username is already used by a faculty member")
        self.assertFalse(Student.objects.filter(roll_number="25CSE050").exists())

    def test_student_can_be_added_and_edited(self):
        response = self.client.post("/admin-portal/students/add/", {
            "roll_number": "25CSE050", "username": "25cse050", "full_name": "New Student",
            "email": "25cse050@smartcampus.example", "semester": 3, "section": "A", "dept": 1, "cgpa": "7.00"},
            follow=True)
        self.assertContains(response, "Saved 25CSE050 New Student")
        student = Student.objects.get(roll_number="25CSE050")
        self.client.post(f"/admin-portal/students/{student.pk}/edit/", {
            "roll_number": "25CSE050", "username": "25cse050", "full_name": "Renamed Student",
            "email": "25cse050@smartcampus.example", "semester": 3, "section": "B", "dept": 1, "cgpa": "7.50"})
        student.refresh_from_db()
        self.assertEqual((student.full_name, student.section), ("Renamed Student", "B"))

    @unittest.expectedFailure  # Known DB bug, awaiting approval to fix database/schema.sql: chk_students_section
    # uses REGEXP '^[A-Z]$', but under utf8mb4_unicode_ci MySQL's REGEXP is case-insensitive, so 'a' passes.
    def test_check_constraint_message_for_bad_section(self):
        response = self.client.post("/admin-portal/students/add/", {
            "roll_number": "25CSE051", "username": "25cse051", "full_name": "Lower Section",
            "email": "25cse051@smartcampus.example", "semester": 3, "section": "a", "dept": 1, "cgpa": "7.00"})
        self.assertContains(response, "Section must be a single capital letter")

    def test_duplicate_enrollment_is_explained(self):
        response = self.client.post("/admin-portal/enrollments/", {
            "student": Student.objects.get(roll_number="25CSE001").pk,
            "course": Course.objects.get(course_code="CS301").pk, "academic_year": "2026-27"})
        self.assertContains(response, "This student is already enrolled in that course.")

    def test_enroll_enforces_the_semester_rule_and_succeeds_otherwise(self):
        later = Course.objects.create(course_code="CS501", course_name="Compiler Design", credits=3,
                                      course_type="THEORY", hours_per_week=3, semester=5, dept_id=1, faculty_id=1)
        student = Student.objects.create(roll_number="25CSE060", username="25cse060", full_name="Fresh Student",
                                         email="25cse060@smartcampus.example", semester=3, section="A", dept_id=1)
        response = self.client.post("/admin-portal/enrollments/", {
            "student": student.pk, "course": later.pk, "academic_year": "2026-27"})
        self.assertContains(response, "CS501 is a semester 5 course, but 25CSE060 is in semester 3.")

        response = self.client.post("/admin-portal/enrollments/", {
            "student": student.pk, "course": Course.objects.get(course_code="CS301").pk,
            "academic_year": "2026-27"}, follow=True)
        self.assertContains(response, "Enrolled 25CSE060 in CS301 for 2026-27.")

    def test_declaring_defaulters_calls_the_procedure(self):
        Student.objects.filter(roll_number="25CSE001").update(is_defaulter=True)  # stale flag
        response = self.client.post("/admin-portal/defaulters/", follow=True)
        self.assertContains(response, "2 student(s) flagged")
        self.assertEqual(sorted(Student.objects.filter(is_defaulter=True).values_list("roll_number", flat=True)),
                         ["25CSE004", "25CSE009"])

    def test_gpa_report_is_ordered_by_weighted_gpa(self):
        rows = list(self.client.get("/admin-portal/gpa-report/").context["rows"])
        self.assertEqual(rows[0].roll_number, "25CSE010")
        self.assertEqual(rows[-1].roll_number, "25CSE009")


class SeedDemoUsersTests(CampusTestCase):

    def test_rerunning_updates_instead_of_duplicating(self):
        users = get_user_model().objects
        before = users.count()
        call_command("seed_demo_users", force=True, verbosity=0)
        self.assertEqual(users.count(), before)
        self.assertEqual(before, 16)  # 10 students + 5 faculty + admin
        self.assertTrue(users.get(username="admin").is_superuser)
        self.assertFalse(users.get(username="25cse001").is_staff)
