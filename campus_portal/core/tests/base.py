from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings


# Hashing 16 demo passwords with PBKDF2 in every test class is slow; tests don't need real hashing.
@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class CampusTestCase(TestCase):
    """
    Runs against test_<DB_NAME>, built by core.test_runner from the real database/*.sql (seed
    data included). Each test runs in a transaction that is rolled back, so the trigger-driven
    writes in one test never leak into another.
    """

    @classmethod
    def setUpTestData(cls):
        # --force: the test runner always sets DEBUG=False.
        call_command("seed_demo_users", force=True, verbosity=0)
        users = get_user_model().objects
        cls.admin = users.get(username="admin")
        cls.teacher = users.get(username="ananya.rao")       # teaches CS301
        cls.other_teacher = users.get(username="kiran.kumar")  # teaches CS351, CS354
        cls.student = users.get(username="25cse001")         # attendance fine
        cls.defaulter = users.get(username="25cse004")       # below 75% in all six courses

    def login(self, user):
        self.client.force_login(user)
