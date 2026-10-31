package com.smartcampus.exceptions;

/**
 * The student is already enrolled in the course. Raised when MySQL rejects the insert with
 * error 1062 on {@code uq_enrollments_student_course}; the database is the source of truth.
 */
public class DuplicateEnrollmentException extends SmartCampusException {

    public DuplicateEnrollmentException(String rollNumber, String courseCode, Throwable cause) {
        super(rollNumber + " is already enrolled in " + courseCode, cause);
    }
}
