from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from .base import CampusTestCase

STUDENT_PAGES = ["/student/"]
FACULTY_PAGES = ["/faculty/", "/faculty/courses/CS301/", "/faculty/courses/CS301/attendance/",
                 "/faculty/courses/CS301/marks/"]
ADMIN_PAGES = ["/admin-portal/", "/admin-portal/students/", "/admin-portal/students/add/",
               "/admin-portal/students/1/edit/", "/admin-portal/faculty/", "/admin-portal/faculty/add/",
               "/admin-portal/faculty/1/edit/", "/admin-portal/courses/", "/admin-portal/courses/add/",
               "/admin-portal/courses/1/edit/", "/admin-portal/enrollments/", "/admin-portal/timetable/",
               "/admin-portal/defaulters/", "/admin-portal/gpa-report/", "/engine/"]
ALL_PAGES = STUDENT_PAGES + FACULTY_PAGES + ADMIN_PAGES


class RoleAccessTests(CampusTestCase):
    """Every role against every portal page: 200 for its own, 403 (the friendly page) otherwise."""

    def assert_matrix(self, user, allowed):
        self.login(user)
        for page in ALL_PAGES:
            with self.subTest(user=user.username, page=page):
                response = self.client.get(page)
                if page in allowed:
                    self.assertEqual(response.status_code, 200)
                else:
                    self.assertEqual(response.status_code, 403)
                    self.assertContains(response, "Access denied", status_code=403)

    def test_student_reaches_only_the_student_portal(self):
        self.assert_matrix(self.student, STUDENT_PAGES)

    def test_faculty_reaches_only_the_faculty_portal(self):
        self.assert_matrix(self.teacher, FACULTY_PAGES)

    def test_admin_reaches_only_the_admin_portal_and_engine(self):
        self.assert_matrix(self.admin, ADMIN_PAGES)

    def test_anonymous_users_are_sent_to_login(self):
        for page in ALL_PAGES + ["/"]:
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response["Location"].startswith(reverse("accounts:login")))

    def test_teacher_cannot_open_another_teachers_course(self):
        self.login(self.other_teacher)
        self.assertEqual(self.client.get("/faculty/courses/CS301/").status_code, 403)
        self.assertEqual(self.client.get("/faculty/courses/CS351/").status_code, 200)

    def test_unknown_course_is_404(self):
        self.login(self.teacher)
        self.assertEqual(self.client.get("/faculty/courses/NOPE1/").status_code, 404)


class LoginRedirectTests(CampusTestCase):

    def login_with_password(self, username):
        return self.client.post(reverse("accounts:login"),
                                {"username": username, "password": settings.DEMO_USER_PASSWORD}, follow=True)

    def test_each_role_lands_on_its_dashboard(self):
        for username, path in [("admin", "/admin-portal/"), ("ananya.rao", "/faculty/"), ("25cse001", "/student/")]:
            with self.subTest(username=username):
                self.client.logout()
                response = self.login_with_password(username)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.request["PATH_INFO"], path)

    def test_wrong_password_stays_on_login(self):
        response = self.client.post(reverse("accounts:login"), {"username": "25cse001", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct username and password")

    def test_login_honours_next(self):
        self.client.post(reverse("accounts:login") + "?next=/faculty/courses/CS301/marks/",
                         {"username": "ananya.rao", "password": settings.DEMO_USER_PASSWORD,
                          "next": "/faculty/courses/CS301/marks/"})
        self.assertEqual(self.client.get("/faculty/courses/CS301/marks/").status_code, 200)

    def test_login_not_linked_to_a_person_gets_403_not_a_crash(self):
        stranger = get_user_model().objects.create_user("stranger", password="x-not-used-x")
        self.login(stranger)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "not linked to a student or faculty record", status_code=403)

    def test_logout_requires_post(self):
        self.login(self.student)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        self.client.post(reverse("accounts:logout"))
        self.assertEqual(self.client.get("/student/").status_code, 302)
