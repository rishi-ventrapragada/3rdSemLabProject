package com.smartcampus.cli;

import com.smartcampus.models.AttendanceRecord;
import com.smartcampus.models.AttendanceSummary;
import com.smartcampus.models.Course;
import com.smartcampus.models.CourseStanding;
import com.smartcampus.models.EnrollmentReceipt;
import com.smartcampus.models.GpaReportRow;
import com.smartcampus.models.Marks;
import com.smartcampus.models.Person;
import com.smartcampus.models.SessionHistory;
import com.smartcampus.models.StudentProfile;
import com.smartcampus.services.Dashboard;
import com.smartcampus.services.TaskResult;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

/** Plain-text output for each command: aligned tables and short summary lines, ASCII only. */
final class TextRenderer {

    private static final String NL = System.lineSeparator();

    private TextRenderer() {
    }

    static String person(Person person) {
        return person.describe() + NL + "Username: " + person.getUsername() + NL;
    }

    static String profile(StudentProfile profile) {
        TableFormatter<CourseStanding> table = new TableFormatter<CourseStanding>()
                .left("Course", s -> s.attendance().courseCode())
                .left("Name", s -> s.attendance().courseName())
                .right("Classes", s -> s.attendance().totalClasses())
                .right("Present", s -> s.attendance().classesAttended())
                .right("Attendance", s -> percent(s.attendance().attendancePercentage()))
                .right("Internal", s -> s.marksIfPresent().map(Marks::getInternalMarks))
                .right("External", s -> s.marksIfPresent().flatMap(Marks::getExternalMarks))
                .right("Total", s -> s.marksIfPresent().flatMap(Marks::getTotalMarks))
                .left("Grade", s -> s.marksIfPresent().flatMap(Marks::getLetterGrade));
        return person(profile.student()) + NL + table.render(profile.courses());
    }

    static String attendance(List<AttendanceSummary> rows) {
        if (rows.isEmpty()) {
            return "No enrollments found." + NL;
        }
        AttendanceSummary first = rows.get(0);
        TableFormatter<AttendanceSummary> table = new TableFormatter<AttendanceSummary>()
                .left("Course", AttendanceSummary::courseCode)
                .left("Name", AttendanceSummary::courseName)
                .right("Classes", AttendanceSummary::totalClasses)
                .right("Present", AttendanceSummary::classesAttended)
                .right("Attendance", row -> percent(row.attendancePercentage()));
        return "Attendance for " + first.rollNumber() + " " + first.fullName()
                + " (section " + first.section() + ", " + first.academicYear() + ")" + NL + NL
                + table.render(rows);
    }

    static String sessions(SessionHistory history) {
        TableFormatter<AttendanceRecord> table = new TableFormatter<AttendanceRecord>()
                .left("Date", AttendanceRecord::getSessionDate)
                .left("Day", r -> r.getSessionDate().getDayOfWeek().toString().substring(0, 3))
                .left("Status", AttendanceRecord::getStatus);
        return history.student().getRollNumber() + " " + history.student().getFullName() + " in "
                + history.course().getCode() + " " + history.course().getName() + ": "
                + history.presentCount() + " of " + history.sessions().size() + " sessions attended" + NL + NL
                + table.render(history.sessions());
    }

    static String defaulters(Map<String, List<AttendanceSummary>> byStudent) {
        if (byStudent.isEmpty()) {
            return "No students are below 75% attendance." + NL;
        }
        int courseCount = byStudent.values().stream().mapToInt(List::size).sum();
        StringBuilder out = new StringBuilder()
                .append(byStudent.size()).append(" student(s) below 75% attendance in ")
                .append(courseCount).append(" course(s)").append(NL);
        TableFormatter<AttendanceSummary> table = new TableFormatter<AttendanceSummary>()
                .left("Course", AttendanceSummary::courseCode)
                .left("Name", AttendanceSummary::courseName)
                .right("Classes", AttendanceSummary::totalClasses)
                .right("Present", AttendanceSummary::classesAttended)
                .right("Attendance", row -> percent(row.attendancePercentage()));
        byStudent.values().forEach(rows -> {
            AttendanceSummary first = rows.get(0);
            out.append(NL).append(first.rollNumber()).append("  ").append(first.fullName())
                    .append(" (section ").append(first.section()).append(")").append(NL)
                    .append(indent(table.render(rows)));
        });
        return out.toString();
    }

    static String gpaReport(List<GpaReportRow> rows) {
        TableFormatter<GpaReportRow> table = new TableFormatter<GpaReportRow>()
                .left("Roll No", GpaReportRow::rollNumber)
                .left("Name", GpaReportRow::fullName)
                .left("Sec", GpaReportRow::section)
                .right("Graded", GpaReportRow::coursesGraded)
                .right("Credits", GpaReportRow::creditsGraded)
                .right("Earned", GpaReportRow::creditsEarned)
                .right("Weighted GPA", GpaReportRow::weightedGpa)
                .right("CGPA (official)", GpaReportRow::cgpa);
        return "GPA report, highest weighted GPA first (v_student_cgpa_report)" + NL + NL + table.render(rows);
    }

    static String courses(List<Course> courses) {
        TableFormatter<Course> table = new TableFormatter<Course>()
                .left("Code", Course::getCode)
                .left("Name", Course::getName)
                .left("Type", Course::getType)
                .right("Credits", Course::getCredits)
                .right("Sem", Course::getSemester)
                .left("Faculty", Course::getFacultyName);
        return table.render(courses);
    }

    static String receipt(EnrollmentReceipt receipt) {
        return "Enrolled " + receipt.student().getRollNumber() + " (" + receipt.student().getFullName() + ") in "
                + receipt.course().getCode() + " " + receipt.course().getName() + " for "
                + receipt.enrollment().getAcademicYear() + " (enrollment_id " + receipt.enrollment().getId() + ")" + NL;
    }

    static String refreshed(int flagged) {
        return "Defaulter flags refreshed from v_defaulter_list: " + flagged + " student(s) flagged." + NL;
    }

    static String dashboard(Dashboard d) {
        StringBuilder out = new StringBuilder()
                .append("Smart Campus dashboard").append(NL).append(NL)
                .append("Students:            ").append(d.studentCount()).append(NL)
                .append("Enrollments:         ").append(d.enrollmentCount()).append(NL)
                .append("Average attendance:  ").append(percent(d.averageAttendance())).append(NL)
                .append("Defaulters:          ").append(d.defaulterStudents()).append(" student(s), ")
                .append(d.defaulterCourseCount()).append(" course entries below 75%").append(NL).append(NL);

        out.append("Average attendance by course").append(NL);
        TableFormatter<Map.Entry<String, BigDecimal>> byCourse = new TableFormatter<Map.Entry<String, BigDecimal>>()
                .left("Course", Map.Entry::getKey)
                .right("Attendance", e -> percent(e.getValue()));
        out.append(byCourse.render(List.copyOf(d.averageAttendanceByCourse().entrySet()))).append(NL);

        out.append("Top weighted GPA").append(NL);
        TableFormatter<GpaReportRow> top = new TableFormatter<GpaReportRow>()
                .left("Roll No", GpaReportRow::rollNumber)
                .left("Name", GpaReportRow::fullName)
                .right("Weighted GPA", GpaReportRow::weightedGpa);
        out.append(top.render(d.topStudents())).append(NL);

        out.append("Loaded concurrently in ").append(d.wallClockMillis()).append(" ms").append(NL);
        TableFormatter<Map.Entry<String, TaskResult<Integer>>> tasks =
                new TableFormatter<Map.Entry<String, TaskResult<Integer>>>()
                        .left("View", Map.Entry::getKey)
                        .right("Rows", e -> e.getValue().value())
                        .left("Thread", e -> e.getValue().threadName())
                        .right("ms", e -> e.getValue().elapsedMillis());
        out.append(tasks.render(List.copyOf(d.tasks().entrySet())));
        return out.toString();
    }

    /** {@code 66.67%}, or {@code -} when no classes have been held. Safe in string concatenation. */
    private static String percent(BigDecimal value) {
        return value == null ? "-" : value.toPlainString() + "%";
    }

    private static String indent(String block) {
        StringBuilder out = new StringBuilder();
        block.lines().forEach(line -> out.append("  ").append(line).append(NL));
        return out.toString();
    }
}
