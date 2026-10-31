from django import forms

from core.models import AttendanceRecord


class AttendanceSheetForm(forms.Form):
    """One session: a date plus a PRESENT/ABSENT choice per enrolled student."""

    session_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, enrollments, **kwargs):
        super().__init__(*args, **kwargs)
        self.enrollments = list(enrollments)
        for enrollment in self.enrollments:
            self.fields[self.field_name(enrollment)] = forms.ChoiceField(
                choices=AttendanceRecord.Status.choices,
                initial=AttendanceRecord.Status.PRESENT,
                widget=forms.RadioSelect,
                label=f"{enrollment.student.roll_number} {enrollment.student.full_name}",
            )

    @staticmethod
    def field_name(enrollment):
        return f"status_{enrollment.pk}"

    def rows(self):
        """(enrollment, bound status field) pairs for the template."""
        return [(e, self[self.field_name(e)]) for e in self.enrollments]

    def statuses(self):
        return {e.pk: self.cleaned_data[self.field_name(e)] for e in self.enrollments}


class MarksSheetForm(forms.Form):
    """
    Internal (0-40) and external (0-60, blank until the exam is graded) marks per student. The
    ranges repeat the database CHECKs only to point at the exact row; MySQL still enforces them.
    Totals and grades are never entered here: the marks triggers compute them.
    """

    def __init__(self, *args, enrollments, **kwargs):
        super().__init__(*args, **kwargs)
        self.enrollments = list(enrollments)
        for enrollment in self.enrollments:
            self.fields[f"internal_{enrollment.pk}"] = forms.DecimalField(
                max_digits=5, decimal_places=2, min_value=0, max_value=40, required=False,
                label="Internal", widget=forms.NumberInput(attrs={"step": "0.5"}))
            self.fields[f"external_{enrollment.pk}"] = forms.DecimalField(
                max_digits=5, decimal_places=2, min_value=0, max_value=60, required=False,
                label="External", widget=forms.NumberInput(attrs={"step": "0.5"}))

    def rows(self):
        return [(e, self[f"internal_{e.pk}"], self[f"external_{e.pk}"]) for e in self.enrollments]

    def clean(self):
        cleaned = super().clean()
        for enrollment in self.enrollments:
            internal = cleaned.get(f"internal_{enrollment.pk}")
            external = cleaned.get(f"external_{enrollment.pk}")
            if internal is None and external is not None:
                self.add_error(f"internal_{enrollment.pk}", "Enter internal marks before external marks.")
        return cleaned

    def entries(self):
        """enrollment_id -> (internal, external) for every row with internal marks entered."""
        result = {}
        for enrollment in self.enrollments:
            internal = self.cleaned_data.get(f"internal_{enrollment.pk}")
            if internal is not None:
                result[enrollment.pk] = (internal, self.cleaned_data.get(f"external_{enrollment.pk}"))
        return result
