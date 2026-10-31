from django.urls import path

from . import views

app_name = "admin_portal"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("students/", views.students, name="students"),
    path("students/add/", views.StudentCreateView.as_view(), name="student_add"),
    path("students/<int:pk>/edit/", views.StudentUpdateView.as_view(), name="student_edit"),
    path("faculty/", views.faculty_list, name="faculty_list"),
    path("faculty/add/", views.FacultyCreateView.as_view(), name="faculty_add"),
    path("faculty/<int:pk>/edit/", views.FacultyUpdateView.as_view(), name="faculty_edit"),
    path("courses/", views.courses, name="courses"),
    path("courses/add/", views.CourseCreateView.as_view(), name="course_add"),
    path("courses/<int:pk>/edit/", views.CourseUpdateView.as_view(), name="course_edit"),
    path("enrollments/", views.enrollments, name="enrollments"),
    path("timetable/", views.timetable, name="timetable"),
    path("defaulters/", views.defaulters, name="defaulters"),
    path("gpa-report/", views.gpa_report, name="gpa_report"),
]
