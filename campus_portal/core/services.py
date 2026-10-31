"""
Write operations shared by the faculty and admin portals.

Rules that MySQL already enforces (uniqueness, CHECK ranges, timetable clashes, grade
calculation) are left to MySQL; this module runs the write in a transaction and turns any
rejection into a ServiceError with a friendly message. The one app-level rule is the semester
match on enroll (docs/database_design.md, "App-level rules").
"""

from contextlib import contextmanager
from datetime import date

from django.db import DatabaseError, connection, transaction

from .db_errors import friendly_db_error
from .models import AttendanceRecord, Enrollment, Marks, Student


class ServiceError(Exception):
    """A write was refused; ``str(error)`` is safe to show to the user."""


@contextmanager
def db_write():
    """Runs the block in a transaction; database rejections become ServiceError."""
    try:
        with transaction.atomic():
            yield
    except DatabaseError as exc:
        raise ServiceError(friendly_db_error(exc)) from exc


def current_academic_year(today=None):
    """Academic years start in July (same rule as the Java engine's default)."""
    today = today or date.today()
    start = today.year if today.month >= 7 else today.year - 1
    return f"{start}-{(start + 1) % 100:02d}"


def enroll_student(student, course, academic_year):
    """Creates an enrollment. App-level rule: the course must be in the student's semester."""
    if course.semester != student.semester:
        raise ServiceError(
            f"{course.course_code} is a semester {course.semester} course, "
            f"but {student.roll_number} is in semester {student.semester}."
        )
    with db_write():
        return Enrollment.objects.create(student=student, course=course, academic_year=academic_year)


def save_attendance(course, session_date, statuses):
    """
    Records one session. ``statuses`` maps enrollment_id -> "PRESENT"/"ABSENT". Only enrollments
    of ``course`` are written; anything else is ignored. Re-saving a date updates it.
    """
    valid_ids = set(course.enrollments.values_list("enrollment_id", flat=True))
    with db_write():
        for enrollment_id, status in statuses.items():
            if enrollment_id in valid_ids:
                AttendanceRecord.objects.update_or_create(
                    enrollment_id=enrollment_id, session_date=session_date, defaults={"status": status})
    return len(valid_ids & set(statuses))


def save_marks(course, entries):
    """
    Saves internal/external marks. ``entries`` maps enrollment_id -> (internal, external or None).
    Only the two raw columns are written: trg_marks_before_insert/update compute total_marks,
    grade_points and letter_grade, so Python never does.
    """
    valid_ids = set(course.enrollments.values_list("enrollment_id", flat=True))
    saved = 0
    with db_write():
        for enrollment_id, (internal, external) in entries.items():
            if enrollment_id in valid_ids:
                Marks.objects.update_or_create(
                    enrollment_id=enrollment_id,
                    defaults={"internal_marks": internal, "external_marks": external})
                saved += 1
    return saved


def refresh_defaulter_flags():
    """CALL sp_refresh_defaulter_flags(); returns how many students are now flagged."""
    with db_write():
        with connection.cursor() as cursor:
            cursor.execute("CALL sp_refresh_defaulter_flags()")
            while cursor.nextset():
                pass
    return Student.objects.filter(is_defaulter=True).count()


def save_form(form):
    """
    Saves a ModelForm. On a database rejection the friendly message is attached to the form as a
    non-field error and None is returned, so the view can re-render the form.
    """
    try:
        with db_write():
            return form.save()
    except ServiceError as error:
        form.add_error(None, str(error))
        return None
