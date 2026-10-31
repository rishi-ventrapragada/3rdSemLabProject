"""
Creates (or refreshes) DEMO logins: one Django user per row of students and faculty, plus one
admin superuser. DEMO ONLY: every account gets the same shared password (CLAUDE.md, "Demo
logins"). Safe to re-run: existing users are updated, never duplicated.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import Faculty, Student


class Command(BaseCommand):
    help = "Create/refresh DEMO-ONLY logins for every seeded student and faculty member, plus an admin."

    def add_arguments(self, parser):
        parser.add_argument("--admin-username", default="admin", help="username of the demo superuser")
        parser.add_argument("--force", action="store_true",
                            help="allow running with DJANGO_DEBUG off (never do this on a real deployment)")

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError("Refusing to create shared-password demo users while DEBUG is off. Use --force.")

        admin_username = options["admin_username"]
        if (Student.objects.filter(username=admin_username).exists()
                or Faculty.objects.filter(username=admin_username).exists()):
            raise CommandError(f"'{admin_username}' is a student/faculty username; pick another --admin-username.")

        password = settings.DEMO_USER_PASSWORD
        counts = {"created": 0, "updated": 0}
        with transaction.atomic():
            for student in Student.objects.all():
                self._upsert(student.username, student.email, student.full_name, password, counts)
            for teacher in Faculty.objects.all():
                self._upsert(teacher.username, teacher.email, teacher.full_name, password, counts)
            self._upsert(admin_username, "admin@smartcampus.example", "Campus Admin", password, counts,
                         superuser=True)

        self.stdout.write(self.style.SUCCESS(
            f"Demo users ready: {counts['created']} created, {counts['updated']} updated "
            f"({Student.objects.count()} students, {Faculty.objects.count()} faculty, admin '{admin_username}'). "
            "All share the DEMO password documented in CLAUDE.md."))

    @staticmethod
    def _upsert(username, email, full_name, password, counts, superuser=False):
        user, created = get_user_model().objects.get_or_create(username=username)
        first, _, last = full_name.partition(" ")
        user.first_name, user.last_name, user.email = first, last, email
        user.is_active = True
        user.is_staff = user.is_superuser = superuser
        user.set_password(password)
        user.save()
        counts["created" if created else "updated"] += 1
