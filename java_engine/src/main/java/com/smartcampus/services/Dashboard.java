package com.smartcampus.services;

import com.smartcampus.models.GpaReportRow;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

/**
 * Campus-wide overview built from the three reporting views, loaded concurrently.
 *
 * @param studentCount            students in {@code v_student_cgpa_report}
 * @param enrollmentCount         rows in {@code v_attendance_summary}
 * @param averageAttendance       mean attendance % across enrollments with classes held
 * @param averageAttendanceByCourse mean attendance % per course code, sorted by code
 * @param defaulterStudents       distinct students in {@code v_defaulter_list}
 * @param defaulterCourseCount    student-course pairs in {@code v_defaulter_list}
 * @param topStudents             up to 3 highest weighted GPAs
 * @param tasks                   which thread loaded each view and how long it took
 * @param wallClockMillis         total time for all three loads together
 */
public record Dashboard(
        int studentCount,
        int enrollmentCount,
        BigDecimal averageAttendance,
        Map<String, BigDecimal> averageAttendanceByCourse,
        long defaulterStudents,
        int defaulterCourseCount,
        List<GpaReportRow> topStudents,
        Map<String, TaskResult<Integer>> tasks,
        long wallClockMillis) {
}
