from django.shortcuts import render

from core.models import AttendanceSummary, DefaulterRow, GpaReportRow, Marks, TimetableEntry
from core.roles import STUDENT, get_person, role_required


@role_required(STUDENT)
def dashboard(request):
    """The logged-in student's own record only; every query is filtered by that student."""
    student = get_person(request.user)
    attendance = AttendanceSummary.objects.filter(student=student).order_by("course_code")
    marks_by_enrollment = {m.enrollment_id: m for m in Marks.objects.filter(enrollment__student=student)}
    courses = [(row, marks_by_enrollment.get(row.enrollment_id)) for row in attendance]

    timetable = (TimetableEntry.objects
                 .filter(section=student.section, course__enrollments__student=student)
                 .select_related("course", "room", "slot", "course__faculty")
                 .order_by("slot__slot_id"))

    # Live list from v_defaulter_list; the 75% threshold lives in the view, not here.
    below_threshold = list(DefaulterRow.objects.filter(student=student).order_by("course_code"))

    return render(request, "student_portal/dashboard.html", {
        "student": student,
        "courses": courses,
        "gpa": GpaReportRow.objects.filter(student=student).first(),
        "below_threshold": below_threshold,
        "below_ids": {row.enrollment_id for row in below_threshold},
        "timetable": timetable,
    })
