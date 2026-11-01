"""
Django's built-in admin (/django-admin/, superusers only): a developer tool next to the Admin
portal. Tables can be browsed and edited; deletes are switched off here so they go through the
portal, which turns MySQL's RESTRICT errors into friendly messages instead of a 500. The views
are read-only. Trigger-computed columns are shown read-only.
"""

from django.contrib import admin

from .models import (AttendanceRecord, AttendanceSummary, Course, DefaulterRow, Department, Enrollment, Faculty,
                     GpaReportRow, Marks, MarksAuditRow, Room, Student, TimeSlot, TimetableEntry)

admin.site.site_header = "Smart Campus - developer admin"
admin.site.site_title = "Smart Campus admin"
admin.site.index_title = "Tables and views of smart_campus_db"


class NoDeleteAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


class ReadOnlyAdmin(NoDeleteAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Department)
class DepartmentAdmin(NoDeleteAdmin):
    list_display = ("dept_code", "dept_name")
    search_fields = ("dept_code", "dept_name")


@admin.register(Room)
class RoomAdmin(NoDeleteAdmin):
    list_display = ("room_number", "room_type", "capacity")
    list_filter = ("room_type",)


@admin.register(TimeSlot)
class TimeSlotAdmin(NoDeleteAdmin):
    list_display = ("slot_id", "day_of_week", "slot_number", "start_time", "end_time")
    list_filter = ("day_of_week",)


@admin.register(Faculty)
class FacultyAdmin(NoDeleteAdmin):
    list_display = ("employee_code", "full_name", "username", "designation", "dept")
    list_filter = ("designation", "dept")
    search_fields = ("employee_code", "full_name", "username", "email")


@admin.register(Student)
class StudentAdmin(NoDeleteAdmin):
    list_display = ("roll_number", "full_name", "username", "semester", "section", "cgpa", "is_defaulter")
    list_filter = ("semester", "section", "is_defaulter", "dept")
    search_fields = ("roll_number", "full_name", "username", "email")
    readonly_fields = ("is_defaulter",)


@admin.register(Course)
class CourseAdmin(NoDeleteAdmin):
    list_display = ("course_code", "course_name", "course_type", "credits", "semester", "faculty")
    list_filter = ("course_type", "semester", "dept")
    search_fields = ("course_code", "course_name")


@admin.register(Enrollment)
class EnrollmentAdmin(NoDeleteAdmin):
    list_display = ("enrollment_id", "student", "course", "academic_year")
    list_filter = ("course", "academic_year")
    search_fields = ("student__roll_number", "student__full_name")
    list_select_related = ("student", "course")
    raw_id_fields = ("student",)


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(NoDeleteAdmin):
    list_display = ("attendance_id", "enrollment", "session_date", "status")
    list_filter = ("status", "session_date", "enrollment__course")
    date_hierarchy = "session_date"
    list_select_related = ("enrollment__student", "enrollment__course")
    raw_id_fields = ("enrollment",)


@admin.register(Marks)
class MarksAdmin(NoDeleteAdmin):
    list_display = ("mark_id", "enrollment", "internal_marks", "external_marks", "total_marks", "letter_grade")
    list_filter = ("letter_grade", "enrollment__course")
    readonly_fields = ("total_marks", "grade_points", "letter_grade")
    list_select_related = ("enrollment__student", "enrollment__course")
    raw_id_fields = ("enrollment",)


@admin.register(TimetableEntry)
class TimetableEntryAdmin(NoDeleteAdmin):
    list_display = ("entry_id", "slot", "section", "course", "room")
    list_filter = ("section", "slot__day_of_week", "room")


@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(ReadOnlyAdmin):
    list_display = ("roll_number", "full_name", "course_code", "total_classes", "classes_attended",
                    "attendance_percentage")
    list_filter = ("course_code", "section")
    search_fields = ("roll_number", "full_name")


@admin.register(DefaulterRow)
class DefaulterRowAdmin(ReadOnlyAdmin):
    list_display = ("roll_number", "full_name", "course_code", "attendance_percentage")


@admin.register(GpaReportRow)
class GpaReportRowAdmin(ReadOnlyAdmin):
    list_display = ("roll_number", "full_name", "section", "weighted_gpa", "cgpa")


@admin.register(MarksAuditRow)
class MarksAuditRowAdmin(ReadOnlyAdmin):
    list_display = ("changed_at", "roll_number", "course_code", "old_total", "old_letter_grade", "new_total",
                    "new_letter_grade")
    search_fields = ("roll_number", "course_code")
