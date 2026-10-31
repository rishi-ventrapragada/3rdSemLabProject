"""
Turns MySQL errors raised by constraints and triggers into messages a user can act on.

The database is the source of truth for these rules (CLAUDE.md, "Invariants live in the
database"); this module only translates its answers. Django preserves the MySQL error code in
``exc.args[0]`` and the server message in ``exc.args[1]``.
"""

import re

SIGNAL = 1644          # SIGNAL SQLSTATE '45000' from a trigger
DUPLICATE_KEY = 1062   # UNIQUE violation
ROW_REFERENCED = 1451  # FK RESTRICT on delete/update of a parent
NO_PARENT = 1452       # FK points at a missing row
CHECK_VIOLATED = 3819  # CHECK constraint

# Named constraints from database/schema.sql -> user-facing explanation.
CONSTRAINT_MESSAGES = {
    "uq_enrollments_student_course": "This student is already enrolled in that course.",
    "uq_timetable_entries_room_slot": "That room is already booked in this time slot.",
    "uq_timetable_entries_slot_section": "That section already has a class in this time slot.",
    "uq_attendance_records_enrollment_date": "Attendance for that student on that date already exists.",
    "uq_marks_enrollment": "Marks for this enrollment already exist.",
    "uq_students_roll_number": "Another student already has this roll number.",
    "uq_students_username": "Another student already has this username.",
    "uq_students_email": "Another student already has this email address.",
    "uq_faculty_employee_code": "Another faculty member already has this employee code.",
    "uq_faculty_username": "Another faculty member already has this username.",
    "uq_faculty_email": "Another faculty member already has this email address.",
    "uq_courses_course_code": "Another course already has this course code.",
    "chk_attendance_records_weekday": "Attendance can only be recorded for Monday to Friday.",
    "chk_marks_internal": "Internal marks must be between 0 and 40.",
    "chk_marks_external": "External marks must be between 0 and 60.",
    "chk_enrollments_academic_year": "Academic year must look like 2026-27.",
    "chk_students_username": "Usernames may contain only letters, digits and . @ + - _",
    "chk_faculty_username": "Usernames may contain only letters, digits and . @ + - _",
    "chk_students_email": "Enter a valid email address.",
    "chk_faculty_email": "Enter a valid email address.",
    "chk_students_semester": "Semester must be between 1 and 8.",
    "chk_students_section": "Section must be a single capital letter (A-Z).",
    "chk_students_cgpa": "CGPA must be between 0.00 and 10.00.",
    "chk_faculty_designation": "Choose one of the listed designations.",
    "chk_courses_credits": "Credits must be between 1 and 6.",
    "chk_courses_hours": "Hours per week must be between 1 and 10.",
    "chk_courses_semester": "Semester must be between 1 and 8.",
    "chk_timetable_entries_section": "Section must be a single capital letter (A-Z).",
    "fk_enrollments_courses": "This course still has enrollments, so it cannot be removed.",
    "fk_courses_faculty": "That faculty member does not exist.",
}

_CLASH = re.compile(r"faculty_id (\d+) already teaches (\S+) in slot_id (\d+)")

FALLBACKS = {
    DUPLICATE_KEY: "That value is already in use.",
    CHECK_VIOLATED: "A value is outside the allowed range.",
    ROW_REFERENCED: "This record is still used by other records, so it cannot be changed or removed.",
    NO_PARENT: "A selected related record does not exist.",
}


def error_code(exc):
    return exc.args[0] if exc.args and isinstance(exc.args[0], int) else None


def friendly_db_error(exc):
    """A short, actionable message for a database error raised by a write."""
    code = error_code(exc)
    server_message = str(exc.args[1]) if len(exc.args) > 1 else str(exc)

    if code == SIGNAL:
        return _explain_signal(server_message)
    for constraint, message in CONSTRAINT_MESSAGES.items():
        if constraint in server_message:
            return message
    return FALLBACKS.get(code, f"The database rejected the change: {server_message}")


def _explain_signal(message):
    """Trigger messages are already readable; the timetable clash gets names instead of ids."""
    match = _CLASH.search(message)
    if not match:
        return message
    from .models import Faculty, TimeSlot  # local import: models import nothing from here

    faculty_id, course_code, slot_id = match.groups()
    teacher = Faculty.objects.filter(pk=faculty_id).first()
    slot = TimeSlot.objects.filter(pk=slot_id).first()
    who = teacher.full_name if teacher else f"Faculty #{faculty_id}"
    when = str(slot) if slot else f"slot {slot_id}"
    return f"Timetable clash: {who} already teaches {course_code} at {when}. Choose another slot."
