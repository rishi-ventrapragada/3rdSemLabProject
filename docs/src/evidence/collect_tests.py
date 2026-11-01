"""
Runs both automated test suites for real and records every result for the report:
  * Maven/JUnit via mvnw with JaCoCo coverage (plugin invoked by coordinates; pom.xml unchanged)
  * Django via coverage.py (statement + branch coverage) and `manage.py test -v 2`

Run from the repo root:  .venv\\Scripts\\python.exe docs\\src\\evidence\\collect_tests.py
Writes docs/src/evidence/tests.json.
"""

import csv
import json
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "tests.json"
PY = REPO / ".venv" / "Scripts" / "python.exe"
JACOCO = "org.jacoco:jacoco-maven-plugin:0.8.16"


def run(cmd, cwd):
    started = time.monotonic()
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          shell=False)
    return proc, round(time.monotonic() - started, 1)


def maven():
    engine = REPO / "java_engine"
    proc, seconds = run([str(engine / "mvnw.cmd"), "-B", "clean", f"{JACOCO}:prepare-agent", "package",
                         f"{JACOCO}:report"], engine)
    cases = []
    for report in sorted((engine / "target" / "surefire-reports").glob("TEST-*.xml")):
        for case in ET.parse(report).getroot().iter("testcase"):
            failed = case.find("failure") is not None or case.find("error") is not None
            cases.append({"class": case.get("classname").replace("com.smartcampus.", ""), "name": case.get("name"),
                          "seconds": float(case.get("time", 0)), "status": "Fail" if failed else "Pass"})
    coverage = []
    with open(engine / "target" / "site" / "jacoco" / "jacoco.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            coverage.append({k: row[k] for k in ("PACKAGE", "CLASS", "INSTRUCTION_MISSED", "INSTRUCTION_COVERED",
                                                  "BRANCH_MISSED", "BRANCH_COVERED", "LINE_MISSED", "LINE_COVERED")})
    summary = re.search(r"Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)\s*$", proc.stdout, re.M)
    return {"exit_code": proc.returncode, "wall_seconds": seconds,
            "build": "SUCCESS" if "BUILD SUCCESS" in proc.stdout else "FAILURE",
            "summary": dict(zip(("run", "failures", "errors", "skipped"), map(int, summary.groups()))) if summary else None,
            "cases": cases, "coverage": coverage}


def django():
    portal = REPO / "campus_portal"
    cov = [str(PY), "-m", "coverage"]
    source = "core,accounts,admin_portal,faculty_portal,student_portal,campus_portal"
    proc, seconds = run(cov + ["run", "--branch", f"--source={source}", "--omit=*/migrations/*,*/tests/*",
                               "manage.py", "test", "--noinput", "-v", "2"], portal)
    output = proc.stdout + proc.stderr
    # Each test prints "name (core.tests.module.Class.name)", possibly followed by log lines (e.g. the
    # "Forbidden" warnings of 403 tests), then " ... ok|FAIL|ERROR". Take the first verdict before the next test.
    headers = list(re.finditer(r"^(test_\w+) \(core\.tests\.(\w+)\.(\w+)\.\1\)", output, re.M))
    cases = []
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(output)
        # The verdict may follow on a later line when warnings are printed in between: it is the last
        # "... ok" or bare "ok"/"FAIL"/"ERROR"/"skipped ..." line of the segment (log lines never end that way).
        segment = output[header.end():end]
        verdicts = re.findall(r"(?:^|\.\.\. )(ok|FAIL|ERROR|skipped)\b[^\n]*$", segment, re.M)
        result = verdicts[-1] if verdicts else "unknown"
        if result != "ok":
            print(f"--- {header.group(0)} -> {result}\n{segment[:1500]}\n---")
        name, module, klass = header.groups()
        cases.append({"module": module, "class": klass, "name": name,
                      "status": {"ok": "Pass", "skipped": "Skip"}.get(result, "Fail")})
    ran = re.search(r"^Ran (\d+) tests? in ([\d.]+)s", output, re.M)
    passed_all = proc.returncode == 0 and re.search(r"^OK\b", output, re.M)
    if passed_all and any(c["status"] != "Pass" for c in cases):
        sys.exit("Parser disagrees with Django's own OK result; refusing to write tests.json")
    run(cov + ["json", "-o", str(portal / ".coverage.json")], portal)
    data = json.loads((portal / ".coverage.json").read_text(encoding="utf-8"))
    (portal / ".coverage.json").unlink()
    (portal / ".coverage").unlink(missing_ok=True)
    files = {path.replace("\\", "/"): {k: info["summary"][k] for k in ("num_statements", "covered_lines",
                                                                       "num_branches", "covered_branches",
                                                                       "percent_covered")}
             for path, info in data["files"].items()}
    totals = {k: data["totals"][k] for k in ("num_statements", "covered_lines", "num_branches", "covered_branches",
                                             "percent_covered")}
    return {"exit_code": proc.returncode, "wall_seconds": seconds, "ran": int(ran.group(1)) if ran else None,
            "test_seconds": float(ran.group(2)) if ran else None,
            "result_line": next((l for l in output.splitlines() if l.startswith(("OK", "FAILED"))), ""),
            "cases": cases, "coverage_files": files, "coverage_totals": totals}


if __name__ == "__main__":
    result = {"run_at": datetime.now().isoformat(timespec="seconds"), "maven": maven(), "django": django()}
    OUT.write_text(json.dumps(result, indent=1), encoding="utf-8")
    m, d = result["maven"], result["django"]
    print(f"Maven: {m['build']} {m['summary']} in {m['wall_seconds']} s; {len(m['cases'])} cases parsed")
    print(f"Django: {d['result_line']} ran={d['ran']} parsed={len(d['cases'])} in {d['wall_seconds']} s; "
          f"coverage {d['coverage_totals']['percent_covered']:.1f}%")
    sys.exit(0 if m["build"] == "SUCCESS" and d["result_line"].startswith("OK") else 1)
