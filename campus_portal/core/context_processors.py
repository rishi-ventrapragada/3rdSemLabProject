from .roles import ROLE_LABELS, get_person, get_role


def campus_role(request):
    """Exposes ``campus_role``, ``campus_role_label`` and ``campus_person`` to every template."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"campus_role": None, "campus_role_label": "", "campus_person": None}
    role = get_role(user)
    return {
        "campus_role": role,
        "campus_role_label": ROLE_LABELS.get(role, ""),
        "campus_person": get_person(user),
    }
