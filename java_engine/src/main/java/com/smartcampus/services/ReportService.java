package com.smartcampus.services;

import com.smartcampus.dao.ReportDao;
import com.smartcampus.dao.StudentDao;
import com.smartcampus.exceptions.DatabaseException;
import com.smartcampus.exceptions.SmartCampusException;
import com.smartcampus.models.AttendanceSummary;
import com.smartcampus.models.GpaReportRow;
import com.smartcampus.models.Student;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;
import java.util.concurrent.Callable;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

/**
 * Reports built on the database views. MySQL computes every percentage, the 75% threshold and
 * every GPA; this class only selects, groups, sorts and summarises the rows.
 */
public class ReportService {

    /** Weighted GPA descending (ungraded students last), then roll number. */
    static final Comparator<GpaReportRow> BY_GPA_DESC = Comparator
            .comparing(GpaReportRow::weightedGpa, Comparator.nullsLast(Comparator.<BigDecimal>reverseOrder()))
            .thenComparing(GpaReportRow::rollNumber);

    private final ReportDao reports;
    private final StudentDao students;

    public ReportService(ReportDao reports, StudentDao students) {
        this.reports = reports;
        this.students = students;
    }

    public List<AttendanceSummary> attendanceFor(String rollNumber) throws SmartCampusException {
        Student student = students.getByRollNumber(rollNumber.strip());
        return reports.findAttendanceByStudentId(student.getId());
    }

    /** {@code v_defaulter_list} grouped by roll number, keeping the view's order. */
    public Map<String, List<AttendanceSummary>> defaultersByStudent() throws DatabaseException {
        return reports.findDefaulters().stream()
                .collect(Collectors.groupingBy(AttendanceSummary::rollNumber, LinkedHashMap::new, Collectors.toList()));
    }

    public List<GpaReportRow> gpaReport() throws DatabaseException {
        return reports.findGpaReport().stream().sorted(BY_GPA_DESC).toList();
    }

    /** Re-declares {@code students.is_defaulter}; returns how many students are now flagged. */
    public int refreshDefaulters() throws DatabaseException {
        return reports.refreshDefaulterFlags();
    }

    /**
     * Loads the three reporting views at the same time on a small thread pool, then summarises
     * them. Each task opens its own JDBC connection ({@code ConnectionFactory} never shares one),
     * so the tasks are independent.
     */
    public Dashboard dashboard() throws DatabaseException {
        AtomicInteger threadNumber = new AtomicInteger(1);
        ExecutorService pool = Executors.newFixedThreadPool(3, runnable -> {
            Thread thread = new Thread(runnable, "report-worker-" + threadNumber.getAndIncrement());
            thread.setDaemon(true);
            return thread;
        });
        long start = System.nanoTime();
        try {
            CompletableFuture<TaskResult<List<AttendanceSummary>>> attendance =
                    CompletableFuture.supplyAsync(() -> timed(reports::findAllAttendance), pool);
            CompletableFuture<TaskResult<List<AttendanceSummary>>> defaulters =
                    CompletableFuture.supplyAsync(() -> timed(reports::findDefaulters), pool);
            CompletableFuture<TaskResult<List<GpaReportRow>>> gpa =
                    CompletableFuture.supplyAsync(() -> timed(reports::findGpaReport), pool);

            CompletableFuture.allOf(attendance, defaulters, gpa).join();
            long wallClock = (System.nanoTime() - start) / 1_000_000;
            return summarise(attendance.join(), defaulters.join(), gpa.join(), wallClock);
        } catch (CompletionException e) {
            if (e.getCause() instanceof DatabaseException db) {
                throw db;
            }
            throw e;
        } finally {
            pool.shutdown();
        }
    }

    private static Dashboard summarise(TaskResult<List<AttendanceSummary>> attendance,
                                       TaskResult<List<AttendanceSummary>> defaulters,
                                       TaskResult<List<GpaReportRow>> gpa,
                                       long wallClockMillis) {
        List<AttendanceSummary> withClasses = attendance.value().stream()
                .filter(row -> row.attendancePercentage() != null)
                .toList();

        BigDecimal overall = toPercent(withClasses.stream()
                .mapToDouble(row -> row.attendancePercentage().doubleValue())
                .average()
                .orElse(0));

        Map<String, BigDecimal> byCourse = withClasses.stream()
                .collect(Collectors.groupingBy(AttendanceSummary::courseCode, TreeMap::new,
                        Collectors.collectingAndThen(
                                Collectors.averagingDouble(row -> row.attendancePercentage().doubleValue()),
                                ReportService::toPercent)));

        long defaulterStudents = defaulters.value().stream().map(AttendanceSummary::studentId).distinct().count();

        List<GpaReportRow> top = gpa.value().stream()
                .filter(row -> row.weightedGpa() != null)
                .sorted(BY_GPA_DESC)
                .limit(3)
                .toList();

        Map<String, TaskResult<Integer>> tasks = new LinkedHashMap<>();
        tasks.put("v_attendance_summary", countOf(attendance));
        tasks.put("v_defaulter_list", countOf(defaulters));
        tasks.put("v_student_cgpa_report", countOf(gpa));

        return new Dashboard(gpa.value().size(), attendance.value().size(), overall, byCourse,
                defaulterStudents, defaulters.value().size(), top, tasks, wallClockMillis);
    }

    /** Runs a DAO call on the current thread, recording the thread name and duration. */
    private static <T> TaskResult<T> timed(Callable<T> task) {
        long start = System.nanoTime();
        try {
            T value = task.call();
            return new TaskResult<>(value, Thread.currentThread().getName(), (System.nanoTime() - start) / 1_000_000);
        } catch (Exception e) {
            throw new CompletionException(e);
        }
    }

    private static <T extends List<?>> TaskResult<Integer> countOf(TaskResult<T> result) {
        return new TaskResult<>(Objects.requireNonNull(result.value()).size(), result.threadName(), result.elapsedMillis());
    }

    private static BigDecimal toPercent(double value) {
        return BigDecimal.valueOf(value).setScale(2, RoundingMode.HALF_UP);
    }
}
