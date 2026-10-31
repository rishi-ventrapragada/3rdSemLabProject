package com.smartcampus.models;

import java.time.LocalDate;
import java.util.Objects;

/** A row of {@code attendance_records}: one student's status in one session of one course. */
public class AttendanceRecord {

    private final int id;
    private final int enrollmentId;
    private final LocalDate sessionDate;
    private final AttendanceStatus status;

    public AttendanceRecord(int id, int enrollmentId, LocalDate sessionDate, AttendanceStatus status) {
        this.id = id;
        this.enrollmentId = enrollmentId;
        this.sessionDate = Objects.requireNonNull(sessionDate, "sessionDate");
        this.status = Objects.requireNonNull(status, "status");
    }

    public boolean isPresent() {
        return status == AttendanceStatus.PRESENT;
    }

    public int getId() {
        return id;
    }

    public int getEnrollmentId() {
        return enrollmentId;
    }

    public LocalDate getSessionDate() {
        return sessionDate;
    }

    public AttendanceStatus getStatus() {
        return status;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        return o instanceof AttendanceRecord other
                && enrollmentId == other.enrollmentId && sessionDate.equals(other.sessionDate);
    }

    @Override
    public int hashCode() {
        return Objects.hash(enrollmentId, sessionDate);
    }

    @Override
    public String toString() {
        return "AttendanceRecord{" + sessionDate + " " + status + ", enrollment=" + enrollmentId + "}";
    }
}
