"""
Runs database/schema.sql, views_triggers.sql and seed_data.sql on a Django connection.

Reuses the DELIMITER-aware splitter from database/init_db.py, so there is exactly one SQL parser
in the project. Used by the test runner to build the test database from the real scripts.
"""

import importlib.util
from functools import lru_cache

from django.conf import settings


@lru_cache(maxsize=1)
def _init_db_module():
    path = settings.REPO_ROOT / "database" / "init_db.py"
    spec = importlib.util.spec_from_file_location("smart_campus_init_db", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_sql_scripts(connection, seed=True):
    """Executes the scripts in order on ``connection`` (already pointing at the target database)."""
    init_db = _init_db_module()
    files = init_db.SQL_FILES if seed else init_db.SQL_FILES[:-1]
    with connection.cursor() as cursor:
        for name in files:
            sql = (init_db.DATABASE_DIR / name).read_text(encoding="utf-8")
            for statement in init_db.split_statements(sql):
                if init_db.SKIPPED_STATEMENT.match(statement):
                    continue
                cursor.execute(statement)
                while cursor.nextset():  # drain CALL result sets
                    pass
