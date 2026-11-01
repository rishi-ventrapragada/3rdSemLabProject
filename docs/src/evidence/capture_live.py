"""
Against a running dev server (manage.py runserver 127.0.0.1:8765):
  1. measures page response times per role (median of 5 GETs) over real HTTP,
  2. captures screenshots of the key pages with Playwright (logged in as each demo role),
  3. renders real console output (CLI, Maven build, init_db) to terminal-style PNGs.
The one write (a marks change, to show the audit trail) is undone at the end by init_db.py --yes.
Passwords are typed into the login form but never appear in a screenshot.

Run from the repo root:  .venv\\Scripts\\python.exe docs\\src\\evidence\\capture_live.py
Writes docs/src/evidence/live.json and docs/src/figures/screens/*.png.
"""

import html
import http.cookiejar
import json
import os
import statistics
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[3]
BASE = "http://127.0.0.1:8765"
SHOTS = REPO / "docs" / "src" / "figures" / "screens"
OUT = Path(__file__).resolve().parent / "live.json"
PASSWORD = os.environ.get("DJANGO_DEMO_PASSWORD", "campus-demo-2026")  # demo-only, documented in CLAUDE.md
PY = REPO / ".venv" / "Scripts" / "python.exe"
JAR = REPO / "java_engine" / "target" / "smart-campus-engine.jar"

PAGES = {
    "25cse004": ["/student/"],
    "ananya.rao": ["/faculty/", "/faculty/courses/CS301/", "/faculty/courses/CS301/attendance/",
                   "/faculty/courses/CS301/marks/"],
    "admin": ["/admin-portal/", "/admin-portal/students/", "/admin-portal/faculty/", "/admin-portal/courses/",
              "/admin-portal/enrollments/", "/admin-portal/timetable/", "/admin-portal/defaulters/",
              "/admin-portal/gpa-report/", "/admin-portal/marks-audit/", "/engine/",
              "/engine/?command=dashboard", "/engine/?command=defaulters"],
}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def http_session(username):
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), NoRedirect)
    opener.open(BASE + "/accounts/login/").read()
    token = next(c.value for c in jar if c.name == "csrftoken")
    body = urllib.parse.urlencode({"username": username, "password": PASSWORD, "csrfmiddlewaretoken": token}).encode()
    request = urllib.request.Request(BASE + "/accounts/login/", data=body, headers={"Referer": BASE + "/accounts/login/"})
    try:
        opener.open(request)
    except urllib.error.HTTPError as redirect:  # 302 after login is expected
        if redirect.code != 302:
            raise
    return opener


def timed_get(opener, path):
    started = time.monotonic()
    with opener.open(BASE + path, timeout=60) as response:
        response.read()
        status = response.status
    return status, (time.monotonic() - started) * 1000


def measure_pages():
    results = []
    for username, pages in PAGES.items():
        opener = http_session(username)
        for path in pages:
            timed_get(opener, path)  # warm-up (template and query caches)
            runs = [timed_get(opener, path) for _ in range(5)]
            ms = [r[1] for r in runs]
            results.append({"role_user": username, "path": path, "status": runs[0][0],
                            "median_ms": round(statistics.median(ms), 1), "min_ms": round(min(ms), 1),
                            "max_ms": round(max(ms), 1)})
            print(f"{username:<11} {path:<38} {runs[0][0]} median {statistics.median(ms):7.1f} ms")
    return results


def login(page, username):
    page.goto(BASE + "/accounts/login/")
    page.fill("#id_username", username)
    page.fill("#id_password", PASSWORD)
    page.click("main button[type=submit]")
    page.wait_for_load_state("networkidle")


def shot(page, name, path=None, full=True, max_height=1700):
    if path:
        page.goto(BASE + path)
        page.wait_for_load_state("networkidle")
    height = page.evaluate("document.documentElement.scrollHeight")
    clip = {"x": 0, "y": 0, "width": page.viewport_size["width"], "height": min(height, max_height)}
    page.screenshot(path=str(SHOTS / f"{name}.png"), clip=clip if full else None, full_page=full)
    print("screenshot", name)


def screenshots(browser):
    context = browser.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=1)
    page = context.new_page()
    page.goto(BASE + "/accounts/login/")
    page.fill("#id_username", "25cse004")  # username only: the password field stays empty in the image
    shot(page, "01_login", full=False)

    login(page, "25cse004")
    shot(page, "02_student_defaulter")
    shot(page, "03_access_denied", "/admin-portal/students/", full=False)
    context.clear_cookies()

    login(page, "25cse001")
    shot(page, "04_student_ok", "/student/")
    context.clear_cookies()

    login(page, "ananya.rao")
    shot(page, "05_faculty_dashboard", "/faculty/")
    shot(page, "06_faculty_roster", "/faculty/courses/CS301/")
    shot(page, "07_faculty_attendance", "/faculty/courses/CS301/attendance/?date=2026-10-05")
    page.goto(BASE + "/faculty/courses/CS301/marks/")
    first_internal = page.locator("input[name^=internal_]").first
    first_internal.fill("38")  # one real change, so the audit trail has something to show
    page.click("main form[method=post] button[type=submit]")
    page.wait_for_load_state("networkidle")
    shot(page, "08_faculty_marks")
    context.clear_cookies()

    login(page, "admin")
    shot(page, "09_admin_dashboard", "/admin-portal/")
    shot(page, "10_admin_students_search", "/admin-portal/students/?q=25CSE00")
    shot(page, "11_admin_student_form", "/admin-portal/students/1/edit/", full=False)
    page.goto(BASE + "/admin-portal/timetable/")
    page.select_option("#id_course", label=page.locator("#id_course option", has_text="CS301").first.inner_text())
    page.select_option("#id_room", index=3)
    page.select_option("#id_slot", index=1)
    page.fill("#id_section", "C")
    page.click("main form[method=post] button[type=submit]")
    page.wait_for_load_state("networkidle")
    shot(page, "12_admin_timetable_clash", full=False)
    shot(page, "13_admin_defaulters", "/admin-portal/defaulters/")
    shot(page, "14_admin_gpa_report", "/admin-portal/gpa-report/")
    shot(page, "15_admin_enrollments", "/admin-portal/enrollments/")
    shot(page, "16_admin_marks_audit", "/admin-portal/marks-audit/", full=False)
    shot(page, "17_admin_delete_confirm", "/admin-portal/courses/1/delete/", full=False)
    shot(page, "18_engine_dashboard", "/engine/?command=dashboard")
    shot(page, "19_engine_error", "/engine/?command=student&lookup-roll_number=25CSE999", full=False)
    shot(page, "20_django_admin", "/django-admin/", full=False)
    context.close()


def terminal_image(browser, name, title, text):
    page = browser.new_page(viewport={"width": 1100, "height": 400})
    page.set_content(
        "<html><body style='margin:0;background:#fff'><div id='t' style='display:inline-block;margin:0;"
        "background:#0f172a;color:#e2e8f0;font:14px Consolas,monospace;padding:14px 18px;border-radius:6px;"
        f"min-width:900px'><div style='color:#94a3b8;margin-bottom:8px'>{html.escape(title)}</div>"
        f"<pre style='margin:0;white-space:pre-wrap'>{html.escape(text)}</pre></div></body></html>")
    page.locator("#t").screenshot(path=str(SHOTS / f"{name}.png"))
    page.close()
    print("terminal", name)


def run(cmd, cwd=REPO):
    started = time.monotonic()
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc, round(time.monotonic() - started, 1)


def terminals(browser):
    timings = {}
    for name, args in (("21_cli_help", ["help"]), ("22_cli_dashboard", ["dashboard"]),
                       ("23_cli_defaulters", ["defaulters"]), ("24_cli_student", ["student", "25CSE004"])):
        proc, seconds = run(["java", "-jar", str(JAR), *args])
        terminal_image(browser, name, "PS C:\\dev\\3rdSemLabProject> java -jar java_engine\\target\\"
                                      f"smart-campus-engine.jar {' '.join(args)}", proc.stdout.rstrip())
    proc, seconds = run([str(REPO / "java_engine" / "mvnw.cmd"), "-B", "clean", "package"], REPO / "java_engine")
    keep = [l for l in proc.stdout.splitlines() if any(k in l for k in ("Building Smart", "Tests run:", "Building jar",
                                                                        "BUILD", "Total time"))]
    terminal_image(browser, "25_maven_build", "PS C:\\dev\\3rdSemLabProject\\java_engine> .\\mvnw.cmd clean package",
                   "\n".join(l.replace(str(REPO), "C:\\dev\\3rdSemLabProject") for l in keep))
    timings["maven_clean_package_s"] = seconds
    proc, seconds = run([str(PY), "database/init_db.py", "--yes"])  # also undoes the audit-trail marks change
    terminal_image(browser, "26_init_db", "PS C:\\dev\\3rdSemLabProject> .venv\\Scripts\\python.exe "
                                          "database\\init_db.py --yes", proc.stdout.rstrip())
    timings["init_db_s"] = seconds
    proc, seconds = run([str(PY), "manage.py", "migrate", "--check"], REPO / "campus_portal")
    timings["migrate_check_exit"] = proc.returncode
    return timings


if __name__ == "__main__":
    SHOTS.mkdir(parents=True, exist_ok=True)
    result = {"pages": measure_pages()}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        screenshots(browser)
        result["build_timings"] = terminals(browser)
        browser.close()
    OUT.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print("done:", len(result["pages"]), "page timings,", len(list(SHOTS.glob("*.png"))), "images")
