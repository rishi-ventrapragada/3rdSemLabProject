"""Phase 4.5: URL-wide access control, CRUD deletes, password change, search/pagination, audit trail,
Django admin, error pages and security headers."""

import re
from decimal import Decimal

from django.conf import settings
from django.contrib import admin
from django.test import RequestFactory
from django.urls import URLPattern, URLResolver, get_resolver, reverse
from django.views.defaults import server_error

from core.models import Course, Enrollment, Faculty, Marks, MarksAuditRow, Student

from .base import CampusTestCase

SAMPLE_ARGS = [(re.compile(r"<int:\w+>"), "1"), (re.compile(r"<str:\w+>"), "CS301"), (re.compile(r"<\w+>"), "x")]
PUBLIC = {"accounts/login/", "accounts/logout/"}  # logout is POST-only; it needs no role


def all_routes(patterns=None, prefix=""):
    """Every route in the project as a concrete path (converters filled with sample values)."""
    for entry in get_resolver().url_patterns if patterns is None else patterns:
        route = prefix + str(entry.pattern)
        if isinstance(entry, URLResolver):
            if not route.startswith("django-admin/"):
                yield from all_routes(entry.url_patterns, route)
        elif isinstance(entry, URLPattern):
            for converter, sample in SAMPLE_ARGS:
                route = converter.sub(sample, route)
            yield route


class EveryUrlIsProtectedTests(CampusTestCase):
    """Generated from the URL conf, so a newly added view without a role check fails here."""

    def setUp(self):
        self.routes = [r for r in all_routes() if r not in PUBLIC]
        self.assertGreater(len(self.routes), 25)

    def test_anonymous_requests_redirect_to_login(self):
        for route in self.routes:
            with self.subTest(route=route):
                response = self.client.get("/" + route)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response["Location"].startswith(reverse("accounts:login")))

    def test_each_role_is_refused_outside_its_own_portal(self):
        own_prefix = {"student": ("student/",), "faculty": ("faculty/",), "admin": ("admin-portal/", "engine/")}
        shared = ("", "accounts/password/")
        for role, user in [("student", self.student), ("faculty", self.teacher), ("admin", self.admin)]:
            self.login(user)
            for route in self.routes:
                if route in shared or route.startswith(own_prefix[role]):
                    continue
                with self.subTest(role=role, route=route):
                    self.assertEqual(self.client.get("/" + route).status_code, 403)


class DeleteTests(CampusTestCase):

    def setUp(self):
        self.login(self.admin)

    def test_confirm_page_then_cascading_delete_of_a_student(self):
        student = Student.objects.get(roll_number="25CSE010")
        self.assertContains(self.client.get(f"/admin-portal/students/{student.pk}/delete/"), "ON DELETE CASCADE")
        response = self.client.post(f"/admin-portal/students/{student.pk}/delete/", follow=True)
        self.assertContains(response, "Deleted 25CSE010 Meghana Krishnan.")
        self.assertFalse(Student.objects.filter(pk=student.pk).exists())
        self.assertFalse(Enrollment.objects.filter(student_id=student.pk).exists())

    def test_course_with_enrollments_is_protected_by_restrict(self):
        course = Course.objects.get(course_code="CS301")
        response = self.client.post(f"/admin-portal/courses/{course.pk}/delete/", follow=True)
        self.assertContains(response, "This course still has enrollments, so it cannot be removed.")
        self.assertTrue(Course.objects.filter(pk=course.pk).exists())

    def test_deleting_a_teacher_unassigns_their_courses(self):
        teacher = Faculty.objects.get(username="suresh.babu")
        self.client.post(f"/admin-portal/faculty/{teacher.pk}/delete/")
        self.assertIsNone(Course.objects.get(course_code="MA301").faculty_id)

    def test_delete_requires_post(self):
        student = Student.objects.get(roll_number="25CSE010")
        self.client.get(f"/admin-portal/students/{student.pk}/delete/")
        self.assertTrue(Student.objects.filter(pk=student.pk).exists())


class PasswordChangeTests(CampusTestCase):

    def test_user_can_change_password_and_log_in_with_it(self):
        self.client.post(reverse("accounts:login"), {"username": "25cse001", "password": settings.DEMO_USER_PASSWORD})
        response = self.client.post(reverse("accounts:password_change"), {
            "old_password": settings.DEMO_USER_PASSWORD,
            "new_password1": "a-much-better-passphrase-42", "new_password2": "a-much-better-passphrase-42"},
            follow=True)
        self.assertContains(response, "Your password was changed.")
        self.assertEqual(response.request["PATH_INFO"], "/student/")  # session survived the change
        self.client.logout()
        self.assertTrue(self.client.login(username="25cse001", password="a-much-better-passphrase-42"))

    def test_weak_or_mismatched_passwords_are_rejected(self):
        self.login(self.student)
        response = self.client.post(reverse("accounts:password_change"), {
            "old_password": settings.DEMO_USER_PASSWORD, "new_password1": "12345678", "new_password2": "12345679"})
        self.assertContains(response, "didn")  # "The two password fields didn't match."


class SearchAndPaginationTests(CampusTestCase):

    def setUp(self):
        self.login(self.admin)

    def test_enrollments_are_paginated(self):
        first = self.client.get("/admin-portal/enrollments/")
        self.assertEqual(len(first.context["page_obj"]), 20)
        self.assertContains(first, "Page 1 of 3")
        self.assertEqual(self.client.get("/admin-portal/enrollments/?page=99").context["page_obj"].number, 3)

    def test_search_filters_and_keeps_other_filters(self):
        response = self.client.get("/admin-portal/enrollments/", {"q": "Sneha"})
        self.assertEqual(response.context["page_obj"].paginator.count, 6)
        cs301 = Course.objects.get(course_code="CS301").pk
        response = self.client.get("/admin-portal/enrollments/", {"q": "Sneha", "course": cs301})
        self.assertEqual(response.context["page_obj"].paginator.count, 1)

    def test_empty_search_result_shows_an_empty_state(self):
        response = self.client.get("/admin-portal/students/", {"q": "nobody-by-this-name"})
        self.assertContains(response, "No students match")

    def test_active_navigation_link(self):
        response = self.client.get("/admin-portal/students/1/edit/")
        self.assertContains(response, 'class="active" href="/admin-portal/students/"')


class MarksAuditTests(CampusTestCase):

    def test_changed_marks_are_audited_by_the_after_trigger(self):
        self.login(self.teacher)
        enrollment = Enrollment.objects.get(student__roll_number="25CSE001", course__course_code="CS301")
        before = Marks.objects.get(enrollment=enrollment)
        self.client.post("/faculty/courses/CS301/marks/", {f"internal_{enrollment.pk}": "40",
                                                           f"external_{enrollment.pk}": "60"})
        rows = list(MarksAuditRow.objects.all())
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0].old_total, rows[0].old_letter_grade), (before.total_marks, before.letter_grade))
        self.assertEqual((rows[0].new_total, rows[0].new_letter_grade), (Decimal("100.00"), "O"))
        self.assertContains(self.client.get("/faculty/courses/CS301/marks/"), "Recent changes")

        # Saving identical marks again is not a change.
        self.client.post("/faculty/courses/CS301/marks/", {f"internal_{enrollment.pk}": "40",
                                                           f"external_{enrollment.pk}": "60"})
        self.assertEqual(MarksAuditRow.objects.count(), 1)

        self.login(self.admin)
        self.assertContains(self.client.get("/admin-portal/marks-audit/"), "25CSE001")


class DjangoAdminTests(CampusTestCase):

    def test_every_registered_model_has_a_working_changelist(self):
        self.login(self.admin)
        self.assertEqual(self.client.get("/django-admin/").status_code, 200)
        for model in admin.site._registry:
            url = reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist")
            with self.subTest(model=model.__name__):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_deletes_are_routed_to_the_portal(self):
        self.login(self.admin)
        url = reverse("admin:core_course_delete", args=[1])
        self.assertEqual(self.client.get(url).status_code, 403)


class ErrorPageAndHeaderTests(CampusTestCase):

    def test_custom_404_page(self):
        self.login(self.student)
        response = self.client.get("/no-such-page/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page not found", status_code=404)

    def test_custom_500_page_needs_no_context(self):
        response = server_error(RequestFactory().get("/"))
        self.assertEqual(response.status_code, 500)
        self.assertIn(b"Something went wrong", response.content)

    def test_security_headers_and_session_cookie(self):
        self.client.post(reverse("accounts:login"), {"username": "25cse001", "password": settings.DEMO_USER_PASSWORD})
        response = self.client.get("/student/")
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response["Referrer-Policy"], "same-origin")
        session_cookie = self.client.cookies[settings.SESSION_COOKIE_NAME]
        self.assertTrue(session_cookie["httponly"])
        self.assertEqual(session_cookie["samesite"], "Lax")
        self.assertEqual(session_cookie["max-age"], "")  # expires when the browser closes
