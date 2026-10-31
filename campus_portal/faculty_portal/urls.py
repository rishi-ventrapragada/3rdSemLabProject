from django.urls import path

from . import views

app_name = "faculty_portal"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("courses/<str:course_code>/", views.course_detail, name="course"),
    path("courses/<str:course_code>/attendance/", views.attendance, name="attendance"),
    path("courses/<str:course_code>/marks/", views.marks, name="marks"),
]
