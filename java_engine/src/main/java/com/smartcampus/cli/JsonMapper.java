package com.smartcampus.cli;

import com.smartcampus.models.AttendanceRecord;
import com.smartcampus.models.AttendanceSummary;
import com.smartcampus.models.Course;
import com.smartcampus.models.CourseStanding;
import com.smartcampus.models.EnrollmentReceipt;
import com.smartcampus.models.Faculty;
import com.smartcampus.models.GpaReportRow;
import com.smartcampus.models.Marks;
import com.smartcampus.models.Person;
import com.smartcampus.models.SessionHistory;
import com.smartcampus.models.Student;
import com.smartcampus.models.StudentProfile;
import com.smartcampus.services.Dashboard;
import com.smartcampus.services.TaskResult;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

/**
 * Converts domain objects into ordered maps for {@link JsonWriter}. Keys are snake_case to match
 * the database columns, so Django can use the same names on both sides.
 */
final class JsonMapper {

    private JsonMapper() {
    }

    /** Any person; the role-specific fields depend on the runtime type. */
    static Map<String, Object> person(Person person) {
        Map<String, Object> json = new LinkedHashMap<>();
        json.put("role", person.getRole());
        json.put("identifier", person.getIdentifier());
        json.put("username", person.getUsername());
        json.put("full_name", person.getFullName());
        json.put("email", person.getEmail());
        json.put("dept_code", person.getDeptCode());
        if (person instanceof Student student) {
            json.put("student_id", student.getId());
            json.put("roll_number", student.getRollNumber());
            json.put("semester", student.getSemester());
            json.put("section", student.getSection());
            json.put("cgpa", student.getCgpa());
            json.put("is_defaulter", student.isDefaulter());
        } else if (person instanceof Faculty faculty) {
            json.put("faculty_id", faculty.getId());
            json.put("employee_code", faculty.getEmployeeCode());
            json.put("designation", faculty.getDesignation());
        }
        json.put("description", person.describe());
        return json;
    }

    static Map<String, Object> attendance(AttendanceSummary row) {
        Map<String, Object> json = new LinkedHashMap<>();
        json.put("enrollment_id", row.enrollmentId());
        json.put("student_id", row.studentId());
        json.put("roll_number", row.rollNumber());
        json.put("full_name", row.fullName());
        json.put("section", row.section());
        json.put("course_code", row.courseCode());
        json.put("course_name", row.courseName());
        json.put("academic_year", row.academicYear());
        json.put("total_classes", row.totalClasses());
        json.put("classes_attended", row.classesAttended());
        json.put("attendance_percentage", row.attendancePercentage());
        return json;
    }

    static Map<String, Object> marks(Marks marks) {
        Map<String, Object> json = new LinkedHashMap<>();
        json.put("internal_marks", marks.getInternalMarks());
        json.put("external_marks", marks.getExternalMarks());
        json.put("total_marks", marks.getTotalMarks());
        json.put("grade_points", marks.getGradePoints());
        json.put("letter_grade", marks.getLetterGrade());
        return json;
    }

    static Map<String, Object> profile(StudentProfile profile) {
        Map<String, Object> json = person(profile.student());
        json.put("courses", list(profile.courses(), JsonMapper::standing));
        return json;
    }

    static Map<String, Object> standing(CourseStanding standing) {
        Map<String, Object> json = attendance(standing.attendance());
        json.put("marks", standing.marksIfPresent().map(JsonMapper::marks).orElse(null));
        return json;
    }

    static Map<String, Object> gpa(GpaReportRow row) {
        Map<String, Object> json = new LinkedHashMap<>();
        json.put("student_id", row.studentId());
        json.put("roll_number", row.rollNumber());
        json.put("full_name", row.fullName());
        json.put("dept_code", row.deptCode());
        json.put("semester", row.semester());
        json.put("section", row.section());
        json.put("courses_graded", row.coursesGraded());
        json.put("credits_graded", row.creditsGraded());
        json.put("credits_earned", row.creditsEarned());
        json.put("weighted_gpa", row.weightedGpa());
        json.put("cgpa", row.cgpa());
        return json;
    }

    static Map<String, Object> course(Course course) {
        Map<String, Object> json = new LinkedHashMap<>();
        json.put("course_id", course.getId());
        json.put("course_code", course.getCode());
        json.put("course_name", course.getName());
        json.put("course_type", course.getType());
        json.put("credits", course.getCredits());
        json.put("hours_per_week", course.getHoursPerWeek());
        json.put("semester", course.getSemester());
        json.put("dept_code", course.getDeptCode());
        json.put("faculty_name", course.getFacultyName());
        return json;
    }

    static Map<String, Object> sessions(SessionHistory history) {
        Map<String, Object> json = new LinkedHashMap<>();
        json.put("roll_number", history.student().getRollNumber());
        json.put("full_name", history.student().getFullName());
        json.put("course_code", history.course().getCode());
        json.put("course_name", history.course().getName());
        json.put("total_classes", history.sessions().size());
        json.put("classes_attended", history.presentCount());
        json.put("sessions", list(history.sessions(), JsonMapper::session));
        return json;
    }

    static Map<String, Object> session(AttendanceRecord record) {
        Map<String, Object> json = new LinkedHashMap<>();
        json.put("session_date", record.getSessionDate());
        json.put("status", record.getStatus());
        return json;
    }

    static Map<String, Object> receipt(EnrollmentReceipt receipt) {
        Map<String, Object> json = new LinkedHashMap<>();
        json.put("enrollment_id", receipt.enrollment().getId());
        json.put("roll_number", receipt.student().getRollNumber());
        json.put("full_name", receipt.student().getFullName());
        json.put("course_code", receipt.course().getCode());
        json.put("course_name", receipt.course().getName());
        json.put("academic_year", receipt.enrollment().getAcademicYear());
        return json;
    }

    static Map<String, Object> defaulters(Map<String, List<AttendanceSummary>> byStudent) {
        List<Map<String, Object>> students = byStudent.values().stream()
                .map(rows -> {
                    AttendanceSummary first = rows.get(0);
                    Map<String, Object> json = new LinkedHashMap<>();
                    json.put("student_id", first.studentId());
                    json.put("roll_number", first.rollNumber());
                    json.put("full_name", first.fullName());
                    json.put("section", first.section());
                    json.put("courses", list(rows, JsonMapper::attendance));
                    return json;
                })
                .toList();
        Map<String, Object> json = new LinkedHashMap<>();
        json.put("student_count", students.size());
        json.put("course_count", byStudent.values().stream().mapToInt(List::size).sum());
        json.put("students", students);
        return json;
    }

    static Map<String, Object> dashboard(Dashboard dashboard) {
        Map<String, Object> json = new LinkedHashMap<>();
        json.put("student_count", dashboard.studentCount());
        json.put("enrollment_count", dashboard.enrollmentCount());
        json.put("average_attendance", dashboard.averageAttendance());
        json.put("average_attendance_by_course", dashboard.averageAttendanceByCourse());
        json.put("defaulter_students", dashboard.defaulterStudents());
        json.put("defaulter_course_count", dashboard.defaulterCourseCount());
        json.put("top_students", list(dashboard.topStudents(), JsonMapper::gpa));
        Map<String, Object> tasks = new LinkedHashMap<>();
        dashboard.tasks().forEach((view, task) -> tasks.put(view, task(task)));
        json.put("tasks", tasks);
        json.put("wall_clock_ms", dashboard.wallClockMillis());
        return json;
    }

    static Map<String, Object> task(TaskResult<Integer> task) {
        Map<String, Object> json = new LinkedHashMap<>();
        json.put("rows", task.value());
        json.put("thread", task.threadName());
        json.put("elapsed_ms", task.elapsedMillis());
        return json;
    }

    static <T> List<Map<String, Object>> list(List<T> items, Function<T, Map<String, Object>> mapper) {
        return items.stream().map(mapper).toList();
    }
}
