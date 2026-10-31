from django import forms

from .java_bridge import ACADEMIC_YEAR, COURSE_CODE, ROLL_NUMBER
from .services import current_academic_year


class EngineStudentForm(forms.Form):
    roll_number = forms.RegexField(regex=ROLL_NUMBER, max_length=20, label="Roll number",
                                   error_messages={"invalid": "Letters and digits only, e.g. 25CSE001."})


class EngineEnrollForm(forms.Form):
    roll_number = forms.RegexField(regex=ROLL_NUMBER, max_length=20, label="Roll number",
                                   error_messages={"invalid": "Letters and digits only, e.g. 25CSE001."})
    course_code = forms.RegexField(regex=COURSE_CODE, max_length=10, label="Course code",
                                   error_messages={"invalid": "Letters and digits only, e.g. CS301."})
    academic_year = forms.RegexField(regex=ACADEMIC_YEAR, max_length=7, label="Academic year",
                                     error_messages={"invalid": "Format 2026-27."})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["academic_year"].initial = current_academic_year()
