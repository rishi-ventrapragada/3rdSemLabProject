from django import forms

from core.models import Course, Faculty, Student, TimetableEntry
from core.services import current_academic_year


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["roll_number", "username", "full_name", "email", "semester", "section", "dept", "cgpa"]
        labels = {"dept": "Department", "cgpa": "Official CGPA"}
        help_texts = {
            "username": "Login name; must match the Django account (by convention the lower-case roll number).",
            "section": "One capital letter, e.g. A.",
        }
        widgets = {"section": forms.TextInput(attrs={"maxlength": 1, "size": 2})}


class FacultyForm(forms.ModelForm):
    class Meta:
        model = Faculty
        fields = ["employee_code", "username", "full_name", "email", "designation", "dept"]
        labels = {"dept": "Department"}
        help_texts = {"username": "Login name; by convention first.last."}


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["course_code", "course_name", "credits", "course_type", "hours_per_week", "semester", "dept",
                  "faculty"]
        labels = {"dept": "Department", "faculty": "Teacher"}


class TimetableEntryForm(forms.ModelForm):
    class Meta:
        model = TimetableEntry
        fields = ["course", "room", "slot", "section"]
        labels = {"slot": "Time slot"}
        widgets = {"section": forms.TextInput(attrs={"maxlength": 1, "size": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["course"].queryset = Course.objects.select_related("faculty")
        self.fields["course"].label_from_instance = (
            lambda c: f"{c.course_code} {c.course_name} ({c.faculty.full_name if c.faculty else 'no teacher'})")


class EnrollmentForm(forms.Form):
    student = forms.ModelChoiceField(queryset=Student.objects.order_by("roll_number"))
    course = forms.ModelChoiceField(queryset=Course.objects.order_by("course_code"))
    academic_year = forms.CharField(max_length=7, help_text="Format 2026-27.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["academic_year"].initial = current_academic_year()


class EnrollmentFilterForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.order_by("course_code"), required=False,
                                    empty_label="All courses")
