package com.smartcampus.cli;

import com.smartcampus.models.AttendanceSummary;
import com.smartcampus.models.Course;
import com.smartcampus.models.EnrollmentReceipt;
import com.smartcampus.models.GpaReportRow;
import com.smartcampus.models.Person;
import com.smartcampus.models.SessionHistory;
import com.smartcampus.models.StudentProfile;
import com.smartcampus.services.Dashboard;

import java.time.LocalDate;
import java.time.Month;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** The command registry, in the order {@code help} lists them. */
final class Commands {

    private static final Map<String, Command> ALL = build();

    private Commands() {
    }

    static Map<String, Command> all() {
        return ALL;
    }

    private static Map<String, Command> build() {
        Map<String, Command> commands = new LinkedHashMap<>();
        add(commands, new Command("student", "<rollNo>",
                "Profile with per-course attendance and marks", 1, 1, Set.of(),
                (cmd, engine) -> {
                    StudentProfile profile = engine.students().getProfile(cmd.arg(0));
                    return new Command.Result(JsonMapper.profile(profile), TextRenderer.profile(profile));
                }));
        add(commands, new Command("whois", "<username>",
                "Resolve a login username to its student or faculty member", 1, 1, Set.of(),
                (cmd, engine) -> {
                    Person person = engine.students().findPersonByUsername(cmd.arg(0));
                    return new Command.Result(JsonMapper.person(person), TextRenderer.person(person));
                }));
        add(commands, new Command("attendance", "<rollNo> [courseCode]",
                "Attendance per course, or every session of one course", 1, 2, Set.of(),
                (cmd, engine) -> {
                    if (cmd.positional().size() == 2) {
                        SessionHistory history = engine.students().getSessionHistory(cmd.arg(0), cmd.arg(1));
                        return new Command.Result(JsonMapper.sessions(history), TextRenderer.sessions(history));
                    }
                    List<AttendanceSummary> rows = engine.reports().attendanceFor(cmd.arg(0));
                    return new Command.Result(JsonMapper.list(rows, JsonMapper::attendance),
                            TextRenderer.attendance(rows));
                }));
        add(commands, new Command("defaulters", "",
                "Students below 75% attendance, grouped by student (v_defaulter_list)", 0, 0, Set.of(),
                (cmd, engine) -> {
                    Map<String, List<AttendanceSummary>> byStudent = engine.reports().defaultersByStudent();
                    return new Command.Result(JsonMapper.defaulters(byStudent), TextRenderer.defaulters(byStudent));
                }));
        add(commands, new Command("gpa-report", "",
                "Weighted GPA vs official CGPA, highest first (v_student_cgpa_report)", 0, 0, Set.of(),
                (cmd, engine) -> {
                    List<GpaReportRow> rows = engine.reports().gpaReport();
                    return new Command.Result(JsonMapper.list(rows, JsonMapper::gpa), TextRenderer.gpaReport(rows));
                }));
        add(commands, new Command("courses", "",
                "All courses with type, credits, semester and teacher", 0, 0, Set.of(),
                (cmd, engine) -> {
                    List<Course> courses = engine.students().listCourses();
                    return new Command.Result(JsonMapper.list(courses, JsonMapper::course),
                            TextRenderer.courses(courses));
                }));
        add(commands, new Command("enroll", "<rollNo> <courseCode> [--year YYYY-YY]",
                "Enroll a student in a course of their semester (default year: current)", 2, 2, Set.of("--year"),
                (cmd, engine) -> {
                    String year = cmd.option("--year").orElse(academicYear(LocalDate.now()));
                    EnrollmentReceipt receipt = engine.students().enroll(cmd.arg(0), cmd.arg(1), year);
                    return new Command.Result(JsonMapper.receipt(receipt), TextRenderer.receipt(receipt));
                }));
        add(commands, new Command("refresh-defaulters", "",
                "Re-declare students.is_defaulter via sp_refresh_defaulter_flags()", 0, 0, Set.of(),
                (cmd, engine) -> {
                    int flagged = engine.reports().refreshDefaulters();
                    return new Command.Result(Map.of("flagged_students", flagged), TextRenderer.refreshed(flagged));
                }));
        add(commands, new Command("dashboard", "",
                "Campus overview; loads the three report views concurrently", 0, 0, Set.of(),
                (cmd, engine) -> {
                    Dashboard dashboard = engine.reports().dashboard();
                    return new Command.Result(JsonMapper.dashboard(dashboard), TextRenderer.dashboard(dashboard));
                }));
        return commands;
    }

    private static void add(Map<String, Command> commands, Command command) {
        commands.put(command.name(), command);
    }

    /** Academic years start in July: October 2026 is in 2026-27, March 2027 still is too. */
    static String academicYear(LocalDate today) {
        int start = today.getMonthValue() >= Month.JULY.getValue() ? today.getYear() : today.getYear() - 1;
        return start + "-" + String.format("%02d", (start + 1) % 100);
    }
}
