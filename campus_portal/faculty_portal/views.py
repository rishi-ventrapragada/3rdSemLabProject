from datetime import date

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from core import services
from core.models import AttendanceRecord, AttendanceSummary, Course, DefaulterRow, Enrollment, Marks, TimetableEntry
from core.roles import FACULTY, get_person, role_required

from .forms import AttendanceSheetForm, MarksSheetForm


def _my_course(request, course_code):
    """The course, if the logged-in teacher is assigned to it; 403 otherwise."""
    course = get_object_or_404(Course.objects.select_related("dept", "faculty"), course_code=course_code)
    if course.faculty_id != get_person(request.user).pk:
        raise PermissionDenied(f"You are not the assigned teacher for {course.course_code}.")
    return course


def _roster(course):
    return Enrollment.objects.filter(course=course).select_related("student").order_by("student__roll_number")


@role_required(FACULTY)
def dashboard(request):
    teacher = get_person(request.user)
    courses = Course.objects.filter(faculty=teacher).annotate(student_count=Count("enrollments"))
    timetable = (TimetableEntry.objects.filter(course__faculty=teacher)
                 .select_related("course", "room", "slot").order_by("slot__slot_id", "section"))
    return render(request, "faculty_portal/dashboard.html", {
        "teacher": teacher, "courses": courses, "timetable": timetable})


@role_required(FACULTY)
def course_detail(request, course_code):
    course = _my_course(request, course_code)
    attendance = {row.enrollment_id: row for row in AttendanceSummary.objects.filter(course=course)}
    marks = {m.enrollment_id: m for m in Marks.objects.filter(enrollment__course=course)}
    below_ids = set(DefaulterRow.objects.filter(course=course).values_list("enrollment_id", flat=True))
    rows = [(e, attendance.get(e.pk), marks.get(e.pk)) for e in _roster(course)]
    return render(request, "faculty_portal/course_detail.html", {
        "course": course, "rows": rows, "below_ids": below_ids})


@role_required(FACULTY)
def attendance(request, course_code):
    course = _my_course(request, course_code)
    roster = _roster(course)

    if request.method == "POST":
        form = AttendanceSheetForm(request.POST, enrollments=roster)
        if form.is_valid():
            session_date = form.cleaned_data["session_date"]
            try:
                count = services.save_attendance(course, session_date, form.statuses())
            except services.ServiceError as error:
                form.add_error(None, str(error))
            else:
                messages.success(request, f"Attendance for {course.course_code} on {session_date:%a %d %b %Y} "
                                          f"saved for {count} students.")
                return redirect(f"{request.path}?date={session_date.isoformat()}")
    else:
        session_date = _date_param(request.GET.get("date"))
        existing = dict(AttendanceRecord.objects.filter(enrollment__course=course, session_date=session_date)
                        .values_list("enrollment_id", "status"))
        initial = {"session_date": session_date}
        initial.update({AttendanceSheetForm.field_name(e): existing[e.pk] for e in roster if e.pk in existing})
        form = AttendanceSheetForm(initial=initial, enrollments=roster)

    return render(request, "faculty_portal/attendance.html", {"course": course, "form": form})


@role_required(FACULTY)
def marks(request, course_code):
    course = _my_course(request, course_code)
    roster = _roster(course)
    saved = {m.enrollment_id: m for m in Marks.objects.filter(enrollment__course=course)}

    if request.method == "POST":
        form = MarksSheetForm(request.POST, enrollments=roster)
        if form.is_valid():
            try:
                count = services.save_marks(course, form.entries())
            except services.ServiceError as error:
                form.add_error(None, str(error))
            else:
                messages.success(request, f"Marks saved for {count} students. Totals and grades were "
                                          "computed by the database.")
                return redirect(request.path)
    else:
        initial = {}
        for enrollment_id, m in saved.items():
            initial[f"internal_{enrollment_id}"] = m.internal_marks
            initial[f"external_{enrollment_id}"] = m.external_marks
        form = MarksSheetForm(initial=initial, enrollments=roster)

    rows = [(e, internal, external, saved.get(e.pk)) for e, internal, external in form.rows()]
    return render(request, "faculty_portal/marks.html", {"course": course, "form": form, "rows": rows})


def _date_param(value):
    try:
        return date.fromisoformat(value) if value else date.today()
    except ValueError:
        return date.today()
