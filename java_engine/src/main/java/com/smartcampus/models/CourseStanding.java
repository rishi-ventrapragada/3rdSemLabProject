package com.smartcampus.models;

import java.util.Optional;

/** One course on a student's profile: attendance from the view plus marks, if any exist. */
public record CourseStanding(AttendanceSummary attendance, Marks marks) {

    public Optional<Marks> marksIfPresent() {
        return Optional.ofNullable(marks);
    }
}
