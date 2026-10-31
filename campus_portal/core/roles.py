"""
Role resolution and access control (CLAUDE.md, "Linking Django logins to people").

A login's role is derived, never stored:
  * admin   - the Django user is a superuser
  * student - auth_user.username matches students.username
  * faculty - auth_user.username matches faculty.username
There is no FK to auth_user; the database guarantees a username is never in both tables.
"""

from functools import wraps

from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .models import Faculty, Student

ADMIN = "admin"
FACULTY = "faculty"
STUDENT = "student"

ROLE_LABELS = {ADMIN: "Admin", FACULTY: "Faculty", STUDENT: "Student"}

_CACHE_ATTR = "_campus_role_cache"


def _resolve(user):
    """Returns (role, person) for a user, querying the database at most once per request."""
    cached = getattr(user, _CACHE_ATTR, None)
    if cached is not None:
        return cached
    role, person = None, None
    if user.is_authenticated:
        if user.is_superuser:
            role = ADMIN
        elif (student := Student.objects.filter(username=user.username).first()) is not None:
            role, person = STUDENT, student
        elif (teacher := Faculty.objects.filter(username=user.username).first()) is not None:
            role, person = FACULTY, teacher
    result = (role, person)
    setattr(user, _CACHE_ATTR, result)
    return result


def get_role(user):
    """``"admin"``, ``"faculty"``, ``"student"``, or None for anonymous / unlinked users."""
    return _resolve(user)[0]


def get_person(user):
    """The Student or Faculty row for this login, or None (admins have none)."""
    return _resolve(user)[1]


def role_required(*roles):
    """
    View decorator: anonymous users go to the login page, logged-in users with another role get
    a 403 page (templates/403.html), never a crash.

        @role_required(STUDENT)
        def dashboard(request): ...
    """
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if get_role(request.user) not in roles:
                raise PermissionDenied("This page is for: " + ", ".join(ROLE_LABELS[r] for r in roles))
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


class RoleRequiredMixin(AccessMixin):
    """Class-based-view equivalent of :func:`role_required`. Set ``allowed_roles``."""

    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if get_role(request.user) not in self.allowed_roles:
            raise PermissionDenied("This page is for: " + ", ".join(ROLE_LABELS[r] for r in self.allowed_roles))
        return super().dispatch(request, *args, **kwargs)
