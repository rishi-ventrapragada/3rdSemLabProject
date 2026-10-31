import json
from pathlib import Path

from django.conf import settings
from django.shortcuts import render

from . import java_bridge
from .forms import EngineEnrollForm, EngineStudentForm
from .roles import ADMIN, role_required

READ_ONLY_COMMANDS = ("defaulters", "gpa-report", "dashboard")


@role_required(ADMIN)
def engine(request):
    """
    Admin page that runs the Java engine. Each request makes at most ONE engine call (about
    half a second each): read-only reports via GET buttons, writes (refresh-defaulters, enroll)
    via POST with CSRF.
    """
    student_form = EngineStudentForm(prefix="lookup")
    enroll_form = EngineEnrollForm(prefix="enroll")
    command, call = None, None

    if request.method == "POST":
        command = request.POST.get("command")
        if command == "refresh-defaulters":
            call = ("refresh-defaulters", (), None)
        elif command == "enroll":
            enroll_form = EngineEnrollForm(request.POST, prefix="enroll")
            if enroll_form.is_valid():
                d = enroll_form.cleaned_data
                call = ("enroll", (d["roll_number"], d["course_code"]), d["academic_year"])
    elif "command" in request.GET:
        command = request.GET["command"]
        if command in READ_ONLY_COMMANDS:
            call = (command, (), None)
        elif command == "student":
            student_form = EngineStudentForm(request.GET, prefix="lookup")
            if student_form.is_valid():
                call = ("student", (student_form.cleaned_data["roll_number"],), None)

    result, error = None, None
    if call is not None:
        name, args, year = call
        try:
            result = java_bridge.run_engine(name, *args, year=year)
        except java_bridge.EngineError as exc:
            error = exc
    elif command is not None and command not in ("student", "enroll"):
        error = java_bridge.EngineError("NotAllowed", f"'{command}' is not an allowed engine command.")

    return render(request, "core/engine.html", {
        "student_form": student_form,
        "enroll_form": enroll_form,
        "command": command,
        "result": result,
        "error": error,
        "raw_json": json.dumps(result.data, indent=2) if result else "",
        "jar_path": settings.JAVA_ENGINE_JAR,
        "jar_present": Path(settings.JAVA_ENGINE_JAR).is_file(),
        "build_hint": java_bridge.BUILD_HINT,
    })
