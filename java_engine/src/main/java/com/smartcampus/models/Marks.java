package com.smartcampus.models;

import java.math.BigDecimal;
import java.util.Objects;
import java.util.Optional;

/**
 * A row of {@code marks}. Read-only on purpose: {@code total_marks}, {@code grade_points} and
 * {@code letter_grade} are computed by the {@code trg_marks_before_*} triggers, so Java never
 * calculates or writes them.
 */
public class Marks {

    private final int id;
    private final int enrollmentId;
    private final BigDecimal internalMarks;
    private final BigDecimal externalMarks;
    private final BigDecimal totalMarks;
    private final Integer gradePoints;
    private final String letterGrade;

    public Marks(int id, int enrollmentId, BigDecimal internalMarks, BigDecimal externalMarks,
                 BigDecimal totalMarks, Integer gradePoints, String letterGrade) {
        this.id = id;
        this.enrollmentId = enrollmentId;
        this.internalMarks = Objects.requireNonNull(internalMarks, "internalMarks");
        this.externalMarks = externalMarks;
        this.totalMarks = totalMarks;
        this.gradePoints = gradePoints;
        this.letterGrade = letterGrade;
    }

    /** False until the end-semester exam is marked ({@code external_marks} is NULL). */
    public boolean isGraded() {
        return gradePoints != null;
    }

    public int getId() {
        return id;
    }

    public int getEnrollmentId() {
        return enrollmentId;
    }

    public BigDecimal getInternalMarks() {
        return internalMarks;
    }

    public Optional<BigDecimal> getExternalMarks() {
        return Optional.ofNullable(externalMarks);
    }

    public Optional<BigDecimal> getTotalMarks() {
        return Optional.ofNullable(totalMarks);
    }

    public Optional<Integer> getGradePoints() {
        return Optional.ofNullable(gradePoints);
    }

    public Optional<String> getLetterGrade() {
        return Optional.ofNullable(letterGrade);
    }

    @Override
    public boolean equals(Object o) {
        return this == o || (o instanceof Marks other && enrollmentId == other.enrollmentId);
    }

    @Override
    public int hashCode() {
        return Integer.hashCode(enrollmentId);
    }

    @Override
    public String toString() {
        return "Marks{enrollment=" + enrollmentId + ", " + internalMarks + "+" + externalMarks
                + "=" + totalMarks + " " + letterGrade + "}";
    }
}
