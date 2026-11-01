#!/usr/bin/env python3
"""Initialise smart_campus_db from the SQL scripts in this folder.

Reads DB_HOST, DB_PORT, DB_NAME, DB_USER and DB_PASSWORD from the repo-root .env
(real environment variables take precedence), creates the database if it does
not exist, runs schema.sql -> views_triggers.sql -> seed_data.sql, and prints
row counts so you can see it worked. It needs neither the `mysql` client on PATH
nor shell `<` redirection.

Usage, from the repo root with the virtualenv active:

    python database/init_db.py             # asks before resetting existing tables
    python database/init_db.py --yes       # no prompt (scripts, CI)
    python database/init_db.py --no-seed   # schema, views and triggers only

WARNING: schema.sql drops and recreates every domain table, so existing data is
lost. Django's own tables (auth_*, django_*) are left alone.

Exit codes follow the project CLI contract: 0 success, 1 runtime or database
error, 2 bad usage.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

try:
    import pymysql
    from dotenv import load_dotenv
except ImportError as exc:  # pragma: no cover - depends on the environment
    sys.exit(f"Missing dependency ({exc.name}). Run: pip install -r requirements.txt")

DATABASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = DATABASE_DIR.parent

SQL_FILES = ("schema.sql", "views_triggers.sql", "seed_data.sql")

TABLES = (
    "departments", "rooms", "time_slots", "faculty", "students", "courses",
    "enrollments", "attendance_records", "marks", "timetable_entries", "marks_audit",
)
VIEWS = ("v_attendance_summary", "v_defaulter_list", "v_student_cgpa_report", "v_marks_audit")

# init_db.py creates and selects the database itself (honouring DB_NAME), so these
# statements, which exist for manual `source` runs, are skipped.
SKIPPED_STATEMENT = re.compile(r"^(USE|CREATE\s+DATABASE)\b", re.IGNORECASE)
DELIMITER_DIRECTIVE = re.compile(r"[ \t]*DELIMITER[ \t]+(\S+)[^\n]*", re.IGNORECASE)
SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9_]+$")


class InitError(Exception):
    """A failure to report to the user without a traceback."""


def split_statements(sql: str) -> list[str]:
    """Split a MySQL script into statements, the way the mysql client does.

    Honours DELIMITER directives, and ignores delimiters inside quotes,
    backticks, `--`/`#` line comments and /* */ block comments. Comments
    are dropped from the output.
    """
    statements: list[str] = []
    buf: list[str] = []
    delimiter = ";"
    quote: str | None = None
    at_line_start = True
    i, n = 0, len(sql)

    while i < n:
        if quote is None and at_line_start and not "".join(buf).strip():
            directive = DELIMITER_DIRECTIVE.match(sql, i)
            if directive:
                delimiter = directive.group(1)
                buf.clear()
                i = directive.end()
                continue

        ch = sql[i]
        at_line_start = ch == "\n"

        if quote is not None:
            buf.append(ch)
            if ch == "\\" and quote != "`" and i + 1 < n:
                buf.append(sql[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue

        if ch == "#" or (sql.startswith("--", i) and (i + 2 >= n or sql[i + 2] in " \t\r\n")):
            newline = sql.find("\n", i)
            i = n if newline == -1 else newline
            continue
        if sql.startswith("/*", i):
            end = sql.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        if ch in "'\"`":
            quote = ch
            buf.append(ch)
            i += 1
            continue
        if sql.startswith(delimiter, i):
            statement = "".join(buf).strip()
            if statement:
                statements.append(statement)
            buf.clear()
            i += len(delimiter)
            continue

        buf.append(ch)
        i += 1

    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def load_settings(env_file: Path) -> dict:
    """Load DB_* settings from env_file (if present) and the environment."""
    if env_file.is_file():
        load_dotenv(env_file)
    elif "DB_NAME" not in os.environ:
        raise InitError(
            f"No {env_file} found and DB_* variables are not set.\n"
            "Create it from the template: Copy-Item .env.example .env  (bash: cp .env.example .env)"
        )

    missing = [k for k in ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER") if not os.environ.get(k)]
    if missing:
        raise InitError(f"Missing setting(s) in {env_file}: {', '.join(missing)}")

    name = os.environ["DB_NAME"]
    if not SAFE_IDENTIFIER.match(name):
        raise InitError(f"DB_NAME may only contain letters, digits and underscores: {name!r}")
    try:
        port = int(os.environ["DB_PORT"])
    except ValueError:
        raise InitError(f"DB_PORT must be a number: {os.environ['DB_PORT']!r}") from None

    return {
        "host": os.environ["DB_HOST"],
        "port": port,
        "user": os.environ["DB_USER"],
        "password": os.environ.get("DB_PASSWORD", ""),
        "database": name,
    }


def connect(settings: dict) -> pymysql.connections.Connection:
    """Connect to the server (no database selected yet)."""
    try:
        return pymysql.connect(
            host=settings["host"],
            port=settings["port"],
            user=settings["user"],
            password=settings["password"],
            charset="utf8mb4",
            autocommit=True,
        )
    except pymysql.MySQLError as exc:
        hint = ""
        code = exc.args[0] if exc.args else None
        if code == 1045:
            hint = "\nCheck DB_USER / DB_PASSWORD in .env."
            if settings["password"] == "your_password":
                hint += " DB_PASSWORD is still the .env.example placeholder."
        elif code == 2003:
            hint = "\nIs the MySQL server running, and are DB_HOST / DB_PORT correct?"
        raise InitError(
            f"Could not connect to MySQL at {settings['host']}:{settings['port']} "
            f"as {settings['user']}: {exc}{hint}"
        ) from None


def confirm_reset(cursor, database: str, assume_yes: bool) -> bool:
    """Ask before schema.sql wipes existing domain tables."""
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = %s AND table_name IN %s",
        (database, TABLES),
    )
    if cursor.fetchone()[0] == 0 or assume_yes:
        return True
    if not sys.stdin.isatty():
        raise InitError(
            f"{database} already has Smart Campus tables. Re-run with --yes to drop and recreate them."
        )
    answer = input(f"{database} already has Smart Campus tables. Drop and recreate them? [y/N] ")
    return answer.strip().lower() in ("y", "yes")


def run_script(cursor, path: Path) -> int:
    """Execute every statement in path. Returns the number executed."""
    executed = 0
    for number, statement in enumerate(split_statements(path.read_text(encoding="utf-8")), 1):
        if SKIPPED_STATEMENT.match(statement):
            continue
        try:
            cursor.execute(statement)
            while cursor.nextset():  # drain CALL result sets
                pass
        except pymysql.MySQLError as exc:
            first_line = statement.splitlines()[0][:100]
            raise InitError(f"{path.name}, statement {number} ({first_line} ...):\n  {exc}") from None
        executed += 1
    return executed


def print_report(cursor) -> None:
    """Print row counts for every table and view, plus routine/trigger totals."""
    print("\nVerification")
    print(f"  {'object':<24}{'type':<7}{'rows':>6}")
    print(f"  {'-' * 24}{'-' * 7}{'-' * 6}")
    for name, kind in [(t, "table") for t in TABLES] + [(v, "view") for v in VIEWS]:
        # Identifiers cannot be bound as parameters; `name` comes from the constant TABLES/VIEWS above.
        cursor.execute(f"SELECT COUNT(*) FROM `{name}`")
        print(f"  {name:<24}{kind:<7}{cursor.fetchone()[0]:>6}")

    cursor.execute("SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = DATABASE()")
    triggers = cursor.fetchone()[0]
    cursor.execute(
        "SELECT routine_type, COUNT(*) FROM information_schema.routines "
        "WHERE routine_schema = DATABASE() GROUP BY routine_type ORDER BY routine_type"
    )
    routines = ", ".join(f"{count} {kind.lower()}(s)" for kind, count in cursor.fetchall())
    cursor.execute("SELECT COUNT(*) FROM students WHERE is_defaulter")
    defaulters = cursor.fetchone()[0]
    print(f"\n  {triggers} trigger(s), {routines or 'no routines'}; {defaulters} student(s) flagged as defaulters")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create smart_campus_db and load the schema, views, triggers and seed data.",
    )
    parser.add_argument("--env", type=Path, default=REPO_ROOT / ".env",
                        help="path to the .env file (default: repo-root .env)")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="drop and recreate existing tables without asking")
    parser.add_argument("--no-seed", action="store_true",
                        help="skip seed_data.sql (empty tables)")
    args = parser.parse_args(argv)

    try:
        settings = load_settings(args.env)
        database = settings["database"]
        conn = connect(settings)
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{database}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
                conn.select_db(database)
                print(f"Connected to {settings['host']}:{settings['port']} as {settings['user']}; "
                      f"database `{database}` is ready.")

                if not confirm_reset(cursor, database, args.yes):
                    print("Aborted; nothing was changed.")
                    return 1

                files = SQL_FILES[:-1] if args.no_seed else SQL_FILES
                for name in files:
                    count = run_script(cursor, DATABASE_DIR / name)
                    print(f"  ran {name:<20} {count:>3} statements")

                print_report(cursor)
        finally:
            conn.close()
    except InitError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 1

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
