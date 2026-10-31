package com.smartcampus.models;

import java.util.Objects;

/**
 * A row of {@code enrollments}. An id of 0 means "not saved yet"; the DAO returns a copy with
 * the generated id via {@link #withId(int)}.
 */
public class Enrollment {

    private final int id;
    private final int studentId;
    private final int courseId;
    private final String academicYear;

    public Enrollment(int id, int studentId, int courseId, String academicYear) {
        if (id < 0 || studentId <= 0 || courseId <= 0) {
            throw new IllegalArgumentException("invalid ids: id=" + id + ", student=" + studentId + ", course=" + courseId);
        }
        if (academicYear == null || academicYear.isBlank()) {
            throw new IllegalArgumentException("academicYear must not be blank");
        }
        this.id = id;
        this.studentId = studentId;
        this.courseId = courseId;
        this.academicYear = academicYear;
    }

    /** A new, unsaved enrollment. */
    public static Enrollment unsaved(int studentId, int courseId, String academicYear) {
        return new Enrollment(0, studentId, courseId, academicYear);
    }

    public Enrollment withId(int generatedId) {
        return new Enrollment(generatedId, studentId, courseId, academicYear);
    }

    public boolean isSaved() {
        return id > 0;
    }

    public int getId() {
        return id;
    }

    public int getStudentId() {
        return studentId;
    }

    public int getCourseId() {
        return courseId;
    }

    public String getAcademicYear() {
        return academicYear;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof Enrollment other)) {
            return false;
        }
        return studentId == other.studentId && courseId == other.courseId && academicYear.equals(other.academicYear);
    }

    @Override
    public int hashCode() {
        return Objects.hash(studentId, courseId, academicYear);
    }

    @Override
    public String toString() {
        return "Enrollment{id=" + id + ", student=" + studentId + ", course=" + courseId + ", " + academicYear + "}";
    }
}
