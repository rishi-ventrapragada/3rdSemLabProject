from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from core.roles import ADMIN, FACULTY, STUDENT, get_role

DASHBOARDS = {
    ADMIN: "admin_portal:dashboard",
    FACULTY: "faculty_portal:dashboard",
    STUDENT: "student_portal:dashboard",
}


class CampusLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


@login_required
def home(request):
    """After login (and at /), send each role to its own dashboard."""
    role = get_role(request.user)
    if role is None:
        raise PermissionDenied(
            f"The login '{request.user.username}' is not linked to a student or faculty record, "
            "and it is not an admin account."
        )
    return redirect(DASHBOARDS[role])
