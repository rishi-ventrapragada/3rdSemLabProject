"""
The only place Django runs the Java engine (CLAUDE.md, "Django -> Java bridge").

Contract with java_engine (see the Engine commands table in CLAUDE.md):
  * always pass --json; exit 0 -> parse stdout {"ok":true,"command","data"}
  * exit != 0 -> parse stderr {"ok":false,"command","error":{"type","message"}}
  * exit codes: 0 success, 1 runtime/database error, 2 bad usage

Safety rules: an allow-list of commands, every argument validated against a strict pattern,
subprocess.run with an argument list and shell=False, and a timeout. Each call costs about half
a second (JVM start-up plus a new MySQL connection), so a page makes at most one call.
"""

import json
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

ROLL_NUMBER = re.compile(r"^[A-Za-z0-9]{1,20}$")
COURSE_CODE = re.compile(r"^[A-Za-z0-9]{1,10}$")
ACADEMIC_YEAR = re.compile(r"^\d{4}-\d{2}$")

# command -> patterns for its positional arguments, in order. Nothing else may be run.
ALLOWED_COMMANDS = {
    "defaulters": (),
    "gpa-report": (),
    "dashboard": (),
    "refresh-defaulters": (),
    "student": (ROLL_NUMBER,),
    "enroll": (ROLL_NUMBER, COURSE_CODE),
}
YEAR_OPTION_COMMANDS = {"enroll"}

BUILD_HINT = r"Build it from the repo root: cd java_engine; .\mvnw.cmd clean package   (bash: ./mvnw clean package)"


@dataclass(frozen=True)
class EngineResult:
    command: str
    data: object
    elapsed_ms: int


class EngineError(Exception):
    """A failed engine call. ``error_type`` is the engine's error.type, or a bridge-side type
    (JarMissing, JavaMissing, Timeout, BadOutput, NotAllowed, BadArgument)."""

    def __init__(self, error_type, message, hint="", exit_code=None):
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.hint = hint
        self.exit_code = exit_code


def build_command(command, args=(), year=None):
    """The exact argv for one call. Raises EngineError for anything off the allow-list."""
    if command not in ALLOWED_COMMANDS:
        raise EngineError("NotAllowed", f"'{command}' is not an allowed engine command.")
    patterns = ALLOWED_COMMANDS[command]
    args = [str(a).strip() for a in args]
    if len(args) != len(patterns):
        raise EngineError("BadArgument", f"'{command}' takes {len(patterns)} argument(s), got {len(args)}.")
    for value, pattern in zip(args, patterns):
        if not pattern.fullmatch(value):
            raise EngineError("BadArgument", f"Invalid argument for '{command}': {value!r}.")
    argv = [settings.JAVA_BIN, "-Dfile.encoding=UTF-8", "-jar", str(settings.JAVA_ENGINE_JAR), command, *args]
    if year is not None:
        if command not in YEAR_OPTION_COMMANDS or not ACADEMIC_YEAR.fullmatch(str(year)):
            raise EngineError("BadArgument", f"Invalid academic year {year!r} (expected e.g. 2026-27).")
        argv += ["--year", str(year)]
    return argv + ["--json"]


def run_engine(command, *args, year=None):
    """Runs one allowed command and returns its parsed ``data``; raises EngineError on failure."""
    argv = build_command(command, args, year)
    jar = Path(settings.JAVA_ENGINE_JAR)
    if not jar.is_file():
        raise EngineError("JarMissing", f"The engine JAR was not found at {jar}.", hint=BUILD_HINT)

    started = time.monotonic()
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=settings.JAVA_ENGINE_TIMEOUT,
            cwd=settings.REPO_ROOT,
            shell=False,
            check=False,
        )
    except FileNotFoundError:
        raise EngineError("JavaMissing", f"Java was not found (tried '{settings.JAVA_BIN}').",
                          hint="Install JDK 17+ or set DJANGO_JAVA_BIN in .env.") from None
    except subprocess.TimeoutExpired:
        raise EngineError("Timeout", f"The engine did not answer within {settings.JAVA_ENGINE_TIMEOUT} s.",
                          hint="Check that MySQL is running.") from None
    elapsed_ms = int((time.monotonic() - started) * 1000)

    if proc.returncode == 0:
        document = _parse(proc.stdout)
        if not document or document.get("ok") is not True or "data" not in document:
            raise EngineError("BadOutput", "The engine exited successfully but did not print a JSON result.",
                              exit_code=0)
        return EngineResult(command=document.get("command", command), data=document["data"], elapsed_ms=elapsed_ms)

    document = _parse(proc.stderr)
    error = document.get("error") if isinstance(document, dict) else None
    if isinstance(error, dict) and "type" in error:
        raise EngineError(error["type"], error.get("message", ""), exit_code=proc.returncode)
    raw = (proc.stderr or proc.stdout or "").strip()
    raise EngineError("Internal", raw[:500] or f"The engine failed with exit code {proc.returncode}.",
                      exit_code=proc.returncode)


def _parse(text):
    """The JSON document on the last non-empty line, or None (the JVM may print warnings first)."""
    lines = [line for line in (text or "").splitlines() if line.strip()]
    if not lines:
        return None
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return None
