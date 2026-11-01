"""Search and pagination shared by the long admin lists."""

from functools import reduce
from operator import or_

from django import forms
from django.core.paginator import Paginator
from django.db.models import Q

PAGE_SIZE = 20


class SearchForm(forms.Form):
    q = forms.CharField(required=False, max_length=100, label="Search",
                        widget=forms.SearchInput(attrs={"placeholder": "Search..."}))


def search(request, queryset, fields):
    """
    Filters ``queryset`` by the ``q`` parameter across ``fields`` (case-insensitive contains, via
    the ORM, so always parameterized). Returns (filtered queryset, bound SearchForm).
    """
    form = SearchForm(request.GET or None)
    if form.is_valid() and form.cleaned_data["q"].strip():
        term = form.cleaned_data["q"].strip()
        queryset = queryset.filter(reduce(or_, (Q(**{f"{field}__icontains": term}) for field in fields)))
    return queryset, form


def paginate(request, queryset, per_page=PAGE_SIZE):
    """A Page for ``?page=N``; out-of-range or invalid numbers fall back to the nearest page."""
    return Paginator(queryset, per_page).get_page(request.GET.get("page"))
