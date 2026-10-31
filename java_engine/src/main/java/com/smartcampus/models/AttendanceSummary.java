package com.smartcampus.models;

import java.math.BigDecimal;

/**
 * A row of {@code v_attendance_summary} (or {@code v_defaulter_list}, which has the same columns).
 * {@code attendancePercentage} is null when no classes have been held yet.
 */
public record AttendanceSummary(
        int enrollmentId,
        int studentId,
        String rollNumber,
        String fullName,
        int semester,
        String section,
        int courseId,
        String courseCode,
        String courseName,
        String academicYear,
        int totalClasses,
        int classesAttended,
        BigDecimal attendancePercentage) {
}
