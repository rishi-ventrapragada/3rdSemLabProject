package com.smartcampus.models;

import java.util.List;

/** Session-by-session attendance of one student in one course. */
public record SessionHistory(Student student, Course course, List<AttendanceRecord> sessions) {

    public SessionHistory {
        sessions = List.copyOf(sessions);
    }

    public long presentCount() {
        return sessions.stream().filter(AttendanceRecord::isPresent).count();
    }
}
