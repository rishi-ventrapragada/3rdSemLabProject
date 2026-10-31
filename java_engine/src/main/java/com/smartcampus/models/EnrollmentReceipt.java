package com.smartcampus.models;

/** What the {@code enroll} command reports back: the saved enrollment and who/what it links. */
public record EnrollmentReceipt(Enrollment enrollment, Student student, Course course) {
}
