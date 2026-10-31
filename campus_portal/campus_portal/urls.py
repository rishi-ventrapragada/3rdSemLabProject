"""
URL prefixes (CLAUDE.md, Django Lab): /student/, /faculty/, /admin-portal/ for the three portals,
/engine/ for the admin-only Java bridge, and /django-admin/ for Django's developer admin.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("accounts.urls")),
    path("student/", include("student_portal.urls")),
    path("faculty/", include("faculty_portal.urls")),
    path("admin-portal/", include("admin_portal.urls")),
    path("engine/", include("core.urls")),
    path("django-admin/", admin.site.urls),
]
