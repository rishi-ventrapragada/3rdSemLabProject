package com.smartcampus.models;

import java.math.BigDecimal;

/**
 * A row of {@code v_student_cgpa_report}: the credit-weighted GPA from graded marks next to the
 * stored official CGPA. {@code weightedGpa} is null when nothing has been graded yet.
 */
public record GpaReportRow(
        int studentId,
        String rollNumber,
        String fullName,
        String deptCode,
        int semester,
        String section,
        int coursesGraded,
        int creditsGraded,
        int creditsEarned,
        BigDecimal weightedGpa,
        BigDecimal cgpa) {
}
