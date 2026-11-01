package com.smartcampus.services;

import com.smartcampus.dao.ReportDao;
import com.smartcampus.exceptions.ExportException;
import com.smartcampus.exceptions.SmartCampusException;
import com.smartcampus.exceptions.ValidationException;
import com.smartcampus.models.AttendanceSummary;
import com.smartcampus.models.GpaReportRow;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * Writes the reporting views to CSV files (file I/O for the Java Lab). Rows come straight from
 * {@link ReportDao}; nothing is recalculated here.
 */
public class ReportExporter {

    /** The reports that can be exported, by their CLI name. */
    public enum Report {
        GPA_REPORT("gpa-report"),
        DEFAULTERS("defaulters"),
        ATTENDANCE("attendance");

        private final String cliName;

        Report(String cliName) {
            this.cliName = cliName;
        }

        public String cliName() {
            return cliName;
        }

        public static Report fromName(String name) throws ValidationException {
            return Arrays.stream(values())
                    .filter(r -> r.cliName.equalsIgnoreCase(name.strip()))
                    .findFirst()
                    .orElseThrow(() -> new ValidationException("Unknown report '" + name + "'. Choose one of: "
                            + Arrays.stream(values()).map(Report::cliName).collect(Collectors.joining(", "))));
        }
    }

    /** What was written, for the command's output. */
    public record ExportResult(String report, Path file, int rows) {
    }

    private static final List<String> ATTENDANCE_HEADER = List.of("roll_number", "full_name", "section",
            "course_code", "course_name", "total_classes", "classes_attended", "attendance_percentage");

    private final ReportDao reports;

    public ReportExporter(ReportDao reports) {
        this.reports = reports;
    }

    public ExportResult export(String reportName, Path file) throws SmartCampusException {
        Report report = Report.fromName(reportName);
        int rows = switch (report) {
            case GPA_REPORT -> writeCsv(file,
                    List.of("roll_number", "full_name", "dept_code", "section", "courses_graded", "credits_graded",
                            "credits_earned", "weighted_gpa", "cgpa"),
                    reports.findGpaReport(),
                    (GpaReportRow r) -> Arrays.asList(r.rollNumber(), r.fullName(), r.deptCode(), r.section(),
                            r.coursesGraded(), r.creditsGraded(), r.creditsEarned(), r.weightedGpa(), r.cgpa()));
            case DEFAULTERS -> writeCsv(file, ATTENDANCE_HEADER, reports.findDefaulters(), ReportExporter::attendanceCells);
            case ATTENDANCE -> writeCsv(file, ATTENDANCE_HEADER, reports.findAllAttendance(), ReportExporter::attendanceCells);
        };
        return new ExportResult(report.cliName(), file.toAbsolutePath().normalize(), rows);
    }

    private static List<Object> attendanceCells(AttendanceSummary r) {
        return Arrays.asList(r.rollNumber(), r.fullName(), r.section(), r.courseCode(), r.courseName(),
                r.totalClasses(), r.classesAttended(), r.attendancePercentage());
    }

    /**
     * Writes a header line and one line per row. Generic over the row type: {@code cells} turns a
     * row into its column values. Parent folders are created; an existing file is replaced.
     *
     * @return the number of data rows written
     */
    public static <T> int writeCsv(Path file, List<String> header, List<T> rows, Function<T, List<?>> cells)
            throws ExportException {
        try {
            Path parent = file.toAbsolutePath().getParent();
            if (parent != null) {
                Files.createDirectories(parent);
            }
            try (BufferedWriter out = Files.newBufferedWriter(file, StandardCharsets.UTF_8)) {
                out.write(csvLine(header));
                out.newLine();
                for (T row : rows) {
                    out.write(csvLine(cells.apply(row)));
                    out.newLine();
                }
            }
        } catch (IOException e) {
            throw new ExportException("Could not write " + file, e);
        }
        return rows.size();
    }

    /** One CSV line (RFC 4180 quoting): fields with a comma, quote or line break are quoted. */
    static String csvLine(List<?> values) {
        return values.stream().map(ReportExporter::csvField).collect(Collectors.joining(","));
    }

    private static String csvField(Object value) {
        if (value == null) {
            return "";
        }
        String text = value.toString();
        if (text.contains(",") || text.contains("\"") || text.contains("\n") || text.contains("\r")) {
            return "\"" + text.replace("\"", "\"\"") + "\"";
        }
        return text;
    }
}
