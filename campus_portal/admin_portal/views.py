from django.contrib import messages
from django.db.models import Avg, Count, F
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from core import services
from core.models import (AttendanceSummary, Course, DefaulterRow, Enrollment, Faculty, GpaReportRow, Student,
                         TimetableEntry)
from core.roles import ADMIN, RoleRequiredMixin, role_required

from .forms import (CourseForm, EnrollmentFilterForm, EnrollmentForm, FacultyForm, StudentForm,
                    TimetableEntryForm)

# Highest weighted GPA first; students with nothing graded yet go last.
GPA_ORDER = (F("weighted_gpa").desc(nulls_last=True), "roll_number")


@role_required(ADMIN)
def dashboard(request):
    summary = AttendanceSummary.objects.aggregate(avg=Avg("attendance_percentage"))
    return render(request, "admin_portal/dashboard.html", {
        "student_count": Student.objects.count(),
        "faculty_count": Faculty.objects.count(),
        "course_count": Course.objects.count(),
        "enrollment_count": Enrollment.objects.count(),
        "average_attendance": summary["avg"],
        "live_defaulters": DefaulterRow.objects.values("student").distinct().count(),
        "declared_defaulters": Student.objects.filter(is_defaulter=True).count(),
        "top_students": GpaReportRow.objects.order_by(*GPA_ORDER)[:5],
    })


@role_required(ADMIN)
def students(request):
    live_ids = set(DefaulterRow.objects.values_list("student_id", flat=True))
    rows = Student.objects.select_related("dept")
    return render(request, "admin_portal/students.html", {"students": rows, "live_ids": live_ids})


@role_required(ADMIN)
def faculty_list(request):
    rows = Faculty.objects.select_related("dept").annotate(course_count=Count("courses"))
    return render(request, "admin_portal/faculty.html", {"faculty": rows})


@role_required(ADMIN)
def courses(request):
    rows = Course.objects.select_related("dept", "faculty").annotate(student_count=Count("enrollments"))
    return render(request, "admin_portal/courses.html", {"courses": rows})


@role_required(ADMIN)
def enrollments(request):
    if request.method == "POST":
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                enrollment = services.enroll_student(data["student"], data["course"], data["academic_year"].strip())
            except services.ServiceError as error:
                form.add_error(None, str(error))
            else:
                messages.success(request, f"Enrolled {enrollment.student.roll_number} in "
                                          f"{enrollment.course.course_code} for {enrollment.academic_year}.")
                return redirect("admin_portal:enrollments")
    else:
        form = EnrollmentForm()

    filter_form = EnrollmentFilterForm(request.GET or None)
    rows = Enrollment.objects.select_related("student", "course")
    if filter_form.is_valid() and filter_form.cleaned_data["course"]:
        rows = rows.filter(course=filter_form.cleaned_data["course"])
    return render(request, "admin_portal/enrollments.html", {
        "form": form, "filter_form": filter_form, "enrollments": rows})


@role_required(ADMIN)
def timetable(request):
    if request.method == "POST":
        form = TimetableEntryForm(request.POST)
        if form.is_valid() and services.save_form(form) is not None:
            messages.success(request, "Timetable entry added.")
            return redirect("admin_portal:timetable")
    else:
        form = TimetableEntryForm()
    rows = TimetableEntry.objects.select_related("course", "course__faculty", "room", "slot")
    return render(request, "admin_portal/timetable.html", {"form": form, "entries": rows})


@role_required(ADMIN)
def defaulters(request):
    if request.method == "POST":
        try:
            flagged = services.refresh_defaulter_flags()
        except services.ServiceError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, f"Defaulter list declared: {flagged} student(s) flagged.")
        return redirect("admin_portal:defaulters")
    rows = DefaulterRow.objects.order_by("roll_number", "course_code")
    return render(request, "admin_portal/defaulters.html", {
        "rows": rows,
        "declared": Student.objects.filter(is_defaulter=True).order_by("roll_number"),
    })


@role_required(ADMIN)
def gpa_report(request):
    return render(request, "admin_portal/gpa_report.html", {"rows": GpaReportRow.objects.order_by(*GPA_ORDER)})


class AdminFormMixin(RoleRequiredMixin):
    """Admin-only create/update view whose save goes through services.save_form, so database
    rejections (UNIQUE, CHECK, trigger SIGNALs) are shown on the form instead of crashing."""

    allowed_roles = (ADMIN,)
    template_name = "admin_portal/form.html"
    title = ""

    def form_valid(self, form):
        obj = services.save_form(form)
        if obj is None:
            return self.form_invalid(form)
        self.object = obj
        messages.success(self.request, f"Saved {obj}.")
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.title
        context["back_url"] = self.success_url
        return context


class StudentCreateView(AdminFormMixin, CreateView):
    model, form_class, title = Student, StudentForm, "Add student"
    success_url = reverse_lazy("admin_portal:students")


class StudentUpdateView(AdminFormMixin, UpdateView):
    model, form_class, title = Student, StudentForm, "Edit student"
    success_url = reverse_lazy("admin_portal:students")


class FacultyCreateView(AdminFormMixin, CreateView):
    model, form_class, title = Faculty, FacultyForm, "Add faculty member"
    success_url = reverse_lazy("admin_portal:faculty_list")


class FacultyUpdateView(AdminFormMixin, UpdateView):
    model, form_class, title = Faculty, FacultyForm, "Edit faculty member"
    success_url = reverse_lazy("admin_portal:faculty_list")


class CourseCreateView(AdminFormMixin, CreateView):
    model, form_class, title = Course, CourseForm, "Add course"
    success_url = reverse_lazy("admin_portal:courses")


class CourseUpdateView(AdminFormMixin, UpdateView):
    model, form_class, title = Course, CourseForm, "Edit course"
    success_url = reverse_lazy("admin_portal:courses")
