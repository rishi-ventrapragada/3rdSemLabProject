"""
Unmanaged mirrors of the tables and views created by database/*.sql.

Every model is ``managed = False``: Django never creates, alters or drops these tables, and
``migrate`` only touches Django's own auth/session tables. Column names, types and choices match
database/schema.sql exactly. Foreign keys use DO_NOTHING so the database's own ON DELETE rules
(RESTRICT / CASCADE / SET NULL) decide what happens, never Django's delete collector.

Never add a *managed* model with a ForeignKey to one of these: migrate would create a real
FK constraint, and schema.sql's DROP TABLE (run by init_db.py) would then fail.
"""

from django.db import models


class Department(models.Model):
    dept_id = models.AutoField(primary_key=True)
    dept_code = models.CharField(max_length=10, unique=True)
    dept_name = models.CharField(max_length=100, unique=True)

    class Meta:
        managed = False
        db_table = "departments"
        ordering = ["dept_code"]

    def __str__(self):
        return f"{self.dept_code} - {self.dept_name}"


class Room(models.Model):
    class RoomType(models.TextChoices):
        LECTURE = "LECTURE", "Lecture hall"
        LAB = "LAB", "Lab"

    room_id = models.AutoField(primary_key=True)
    room_number = models.CharField(max_length=20, unique=True)
    capacity = models.SmallIntegerField()
    room_type = models.CharField(max_length=7, choices=RoomType.choices)

    class Meta:
        managed = False
        db_table = "rooms"
        ordering = ["room_number"]

    def __str__(self):
        return f"{self.room_number} ({self.get_room_type_display()}, {self.capacity})"


class TimeSlot(models.Model):
    class Day(models.TextChoices):
        MON = "MON", "Monday"
        TUE = "TUE", "Tuesday"
        WED = "WED", "Wednesday"
        THU = "THU", "Thursday"
        FRI = "FRI", "Friday"

    slot_id = models.AutoField(primary_key=True)
    day_of_week = models.CharField(max_length=3, choices=Day.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_number = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = "time_slots"
        # slot_id follows day order in the seed data; ordering by it keeps MON..FRI.
        ordering = ["slot_id"]

    def __str__(self):
        return f"{self.day_of_week} {self.start_time:%H:%M}-{self.end_time:%H:%M} (slot {self.slot_number})"


class Faculty(models.Model):
    class Designation(models.TextChoices):
        PROFESSOR = "Professor"
        ASSOCIATE = "Associate Professor"
        ASSISTANT = "Assistant Professor"
        LECTURER = "Lecturer"

    faculty_id = models.AutoField(primary_key=True)
    employee_code = models.CharField(max_length=20, unique=True)
    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, unique=True)
    designation = models.CharField(max_length=50, choices=Designation.choices)
    dept = models.ForeignKey(Department, models.DO_NOTHING, db_column="dept_id", related_name="faculty")

    class Meta:
        managed = False
        db_table = "faculty"
        ordering = ["employee_code"]
        verbose_name_plural = "faculty"

    def __str__(self):
        return f"{self.full_name} ({self.employee_code})"


class Student(models.Model):
    student_id = models.AutoField(primary_key=True)
    roll_number = models.CharField(max_length=20, unique=True)
    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, unique=True)
    semester = models.SmallIntegerField()
    section = models.CharField(max_length=1)
    dept = models.ForeignKey(Department, models.DO_NOTHING, db_column="dept_id", related_name="students")
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    # Declared by sp_refresh_defaulter_flags(); v_defaulter_list is the live figure.
    is_defaulter = models.BooleanField(default=False, editable=False)

    class Meta:
        managed = False
        db_table = "students"
        ordering = ["roll_number"]

    def __str__(self):
        return f"{self.roll_number} {self.full_name}"


class Course(models.Model):
    class CourseType(models.TextChoices):
        THEORY = "THEORY", "Theory"
        LAB = "LAB", "Lab"

    course_id = models.AutoField(primary_key=True)
    course_code = models.CharField(max_length=10, unique=True)
    course_name = models.CharField(max_length=100)
    credits = models.SmallIntegerField()
    course_type = models.CharField(max_length=6, choices=CourseType.choices)
    hours_per_week = models.SmallIntegerField()
    semester = models.SmallIntegerField()
    dept = models.ForeignKey(Department, models.DO_NOTHING, db_column="dept_id", related_name="courses")
    faculty = models.ForeignKey(Faculty, models.DO_NOTHING, db_column="faculty_id", null=True, blank=True,
                                related_name="courses")

    class Meta:
        managed = False
        db_table = "courses"
        ordering = ["course_code"]

    def __str__(self):
        return f"{self.course_code} {self.course_name}"


class Enrollment(models.Model):
    enrollment_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, models.DO_NOTHING, db_column="student_id", related_name="enrollments")
    course = models.ForeignKey(Course, models.DO_NOTHING, db_column="course_id", related_name="enrollments")
    academic_year = models.CharField(max_length=7)

    class Meta:
        managed = False
        db_table = "enrollments"
        ordering = ["student__roll_number", "course__course_code"]

    def __str__(self):
        return f"{self.student.roll_number} in {self.course.course_code} ({self.academic_year})"


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"

    attendance_id = models.AutoField(primary_key=True)
    enrollment = models.ForeignKey(Enrollment, models.DO_NOTHING, db_column="enrollment_id",
                                   related_name="attendance_records")
    session_date = models.DateField()
    status = models.CharField(max_length=7, choices=Status.choices)

    class Meta:
        managed = False
        db_table = "attendance_records"
        ordering = ["session_date"]


class Marks(models.Model):
    """total_marks, grade_points and letter_grade are written by trg_marks_before_* only."""

    mark_id = models.AutoField(primary_key=True)
    enrollment = models.OneToOneField(Enrollment, models.DO_NOTHING, db_column="enrollment_id", related_name="marks")
    internal_marks = models.DecimalField(max_digits=5, decimal_places=2)
    external_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, editable=False)
    grade_points = models.IntegerField(null=True, editable=False)
    letter_grade = models.CharField(max_length=2, null=True, editable=False)

    class Meta:
        managed = False
        db_table = "marks"
        verbose_name_plural = "marks"


class TimetableEntry(models.Model):
    entry_id = models.AutoField(primary_key=True)
    course = models.ForeignKey(Course, models.DO_NOTHING, db_column="course_id", related_name="timetable_entries")
    room = models.ForeignKey(Room, models.DO_NOTHING, db_column="room_id", related_name="timetable_entries")
    slot = models.ForeignKey(TimeSlot, models.DO_NOTHING, db_column="slot_id", related_name="timetable_entries")
    section = models.CharField(max_length=1)

    class Meta:
        managed = False
        db_table = "timetable_entries"
        ordering = ["slot__slot_id", "section"]
        verbose_name_plural = "timetable entries"


# ---------------------------------------------------------------------------------------------
# Read-only reporting views (database/views_triggers.sql). Never save these.
# ---------------------------------------------------------------------------------------------

class AttendanceSummaryBase(models.Model):
    enrollment_id = models.IntegerField(primary_key=True)
    student = models.ForeignKey(Student, models.DO_NOTHING, db_column="student_id", related_name="+")
    roll_number = models.CharField(max_length=20)
    full_name = models.CharField(max_length=100)
    semester = models.SmallIntegerField()
    section = models.CharField(max_length=1)
    course = models.ForeignKey(Course, models.DO_NOTHING, db_column="course_id", related_name="+")
    course_code = models.CharField(max_length=10)
    course_name = models.CharField(max_length=100)
    academic_year = models.CharField(max_length=7)
    total_classes = models.IntegerField()
    classes_attended = models.IntegerField()
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True)

    class Meta:
        abstract = True
        ordering = ["roll_number", "course_code"]


class AttendanceSummary(AttendanceSummaryBase):
    """v_attendance_summary: one row per enrollment."""

    class Meta(AttendanceSummaryBase.Meta):
        managed = False
        db_table = "v_attendance_summary"
        verbose_name_plural = "attendance summaries"


class DefaulterRow(AttendanceSummaryBase):
    """v_defaulter_list: enrollments below 75% attendance (threshold lives in the view)."""

    class Meta(AttendanceSummaryBase.Meta):
        managed = False
        db_table = "v_defaulter_list"


class GpaReportRow(models.Model):
    """v_student_cgpa_report: credit-weighted GPA from graded marks next to the official CGPA."""

    student = models.OneToOneField(Student, models.DO_NOTHING, db_column="student_id", primary_key=True,
                                   related_name="+")
    roll_number = models.CharField(max_length=20)
    full_name = models.CharField(max_length=100)
    dept_code = models.CharField(max_length=10)
    semester = models.SmallIntegerField()
    section = models.CharField(max_length=1)
    courses_graded = models.IntegerField()
    credits_graded = models.IntegerField()
    credits_earned = models.IntegerField()
    weighted_gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2)

    class Meta:
        managed = False
        db_table = "v_student_cgpa_report"
        ordering = ["roll_number"]
