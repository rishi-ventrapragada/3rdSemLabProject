package com.smartcampus.models;

import java.util.List;

/** Everything the {@code student} command shows: the student and one standing per course. */
public record StudentProfile(Student student, List<CourseStanding> courses) {

    public StudentProfile {
        courses = List.copyOf(courses);
    }
}
