from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def nav_class(context, url_name, exact=False):
    """
    ``active`` when the current page is ``url_name`` or below it, so "Students" stays highlighted
    on /admin-portal/students/3/edit/. Use ``exact=True`` for dashboard roots that prefix others.
    """
    request = context.get("request")
    if request is None:
        return ""
    target = reverse(url_name)
    matched = request.path == target if exact else request.path.startswith(target)
    return "active" if matched else ""


@register.simple_tag(takes_context=True)
def query_with(context, **changes):
    """The current query string with some parameters replaced, e.g. for pagination links."""
    params = context["request"].GET.copy()
    for key, value in changes.items():
        params[key] = value
    return params.urlencode()
