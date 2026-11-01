"""
Collects facts about the real project for the report: the live MySQL schema (tables, columns,
keys, CHECK constraints, views, triggers, routines), the git history and source line counts.

Run from the repo root:  .venv\\Scripts\\python.exe docs\\src\\evidence\\collect_facts.py
Writes docs/src/evidence/facts.json. Reads DB settings from .env (never writes them out).
"""

import json
import os
import subprocess
from collections import Counter
from pathlib import Path

import pymysql
from dotenv import load_dotenv

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "facts.json"
load_dotenv(REPO / ".env")


def query(cursor, sql, args=None):
    cursor.execute(sql, args)
    names = [d[0].lower() for d in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def schema_facts():
    conn = pymysql.connect(host=os.environ["DB_HOST"], port=int(os.environ["DB_PORT"]), user=os.environ["DB_USER"],
                           password=os.environ.get("DB_PASSWORD", ""), database=os.environ["DB_NAME"])
    db = os.environ["DB_NAME"]
    with conn.cursor() as c:
        tables = query(c, "SELECT table_name, table_type FROM information_schema.tables WHERE table_schema=%s "
                          "ORDER BY table_name", (db,))
        columns = query(c, "SELECT table_name, column_name, column_type, is_nullable, column_key, column_default, "
                           "extra, ordinal_position FROM information_schema.columns WHERE table_schema=%s "
                           "ORDER BY table_name, ordinal_position", (db,))
        constraints = query(c, "SELECT tc.table_name, tc.constraint_name, tc.constraint_type, cc.check_clause "
                               "FROM information_schema.table_constraints tc LEFT JOIN "
                               "information_schema.check_constraints cc ON cc.constraint_schema=tc.constraint_schema "
                               "AND cc.constraint_name=tc.constraint_name WHERE tc.table_schema=%s "
                               "ORDER BY tc.table_name, tc.constraint_type, tc.constraint_name", (db,))
        fks = query(c, "SELECT k.table_name, k.column_name, k.constraint_name, k.referenced_table_name, "
                       "k.referenced_column_name, r.update_rule, r.delete_rule FROM "
                       "information_schema.key_column_usage k JOIN information_schema.referential_constraints r "
                       "ON r.constraint_schema=k.constraint_schema AND r.constraint_name=k.constraint_name "
                       "WHERE k.table_schema=%s ORDER BY k.table_name", (db,))
        triggers = query(c, "SELECT trigger_name, event_manipulation, event_object_table, action_timing "
                            "FROM information_schema.triggers WHERE trigger_schema=%s ORDER BY trigger_name", (db,))
        routines = query(c, "SELECT routine_name, routine_type FROM information_schema.routines "
                            "WHERE routine_schema=%s ORDER BY routine_name", (db,))
        counts = {}
        for t in tables:
            name = t["table_name"]
            if name.startswith(("auth_", "django_")):
                continue
            c.execute(f"SELECT COUNT(*) FROM `{name}`")  # names come from information_schema, not input
            counts[name] = c.fetchone()[0]
        version = query(c, "SELECT VERSION() AS v")[0]["v"]
    conn.close()
    return {"mysql_version": version, "tables": tables, "columns": columns, "constraints": constraints,
            "foreign_keys": fks, "triggers": triggers, "routines": routines, "row_counts": counts}


def git_facts():
    fmt = "%h%x1f%ad%x1f%s"
    lines = subprocess.run(["git", "log", "--reverse", f"--format={fmt}", "--date=short"], cwd=REPO,
                           capture_output=True, text=True, check=True).stdout.splitlines()
    commits = [dict(zip(("hash", "date", "subject"), line.split("\x1f"))) for line in lines]
    files = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True).stdout.split()
    return {"commits": commits, "tracked_files": len(files)}


def loc_facts():
    """Non-blank source lines per component, counted from git-tracked files."""
    files = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True).stdout.split()
    groups = {
        "SQL (database/*.sql)": lambda f: f.startswith("database/") and f.endswith(".sql"),
        "Python tooling (database/init_db.py)": lambda f: f == "database/init_db.py",
        "Java main (java_engine/src/main)": lambda f: f.startswith("java_engine/src/main/") and f.endswith(".java"),
        "Java tests (java_engine/src/test)": lambda f: f.startswith("java_engine/src/test/") and f.endswith(".java"),
        "Django Python (excluding tests)": lambda f: f.startswith("campus_portal/") and f.endswith(".py")
        and "/tests/" not in f and "/migrations/" not in f,
        "Django tests": lambda f: f.startswith("campus_portal/") and "/tests/" in f and f.endswith(".py"),
        "Templates (HTML)": lambda f: f.startswith("campus_portal/templates/") and f.endswith(".html"),
        "CSS": lambda f: f.endswith(".css"),
    }
    result = {}
    for label, match in groups.items():
        chosen = [f for f in files if match(f)]
        lines = sum(sum(1 for line in (REPO / f).read_text(encoding="utf-8").splitlines() if line.strip())
                    for f in chosen)
        result[label] = {"files": len(chosen), "lines": lines}
    java_classes = Counter(f.split("/")[-2] for f in files
                           if f.startswith("java_engine/src/main/java/com/smartcampus/") and f.endswith(".java"))
    result["java_files_per_package"] = dict(java_classes)
    return result


if __name__ == "__main__":
    facts = {"schema": schema_facts(), "git": git_facts(), "loc": loc_facts()}
    OUT.write_text(json.dumps(facts, indent=1, default=str), encoding="utf-8")
    s = facts["schema"]
    print(f"MySQL {s['mysql_version']}: {len(s['tables'])} tables/views, {len(s['triggers'])} triggers, "
          f"{len(s['routines'])} routines; {len(facts['git']['commits'])} commits; written {OUT.name}")
    for k, v in facts["loc"].items():
        print(" ", k, v)
