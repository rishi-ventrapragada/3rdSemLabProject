from django.db import connections
from django.test.runner import DiscoverRunner

from .sql_loader import load_sql_scripts


class SmartCampusTestRunner(DiscoverRunner):
    """
    Test runner for unmanaged models. Django creates test_<DB_NAME> and runs migrations, which
    only build Django's own tables. Then the real database/*.sql scripts load the domain tables,
    views, triggers and seed data, so tests run against the same schema as production, and never
    against the development database.
    """

    def setup_databases(self, **kwargs):
        old_config = super().setup_databases(**kwargs)
        load_sql_scripts(connections["default"])
        return old_config
