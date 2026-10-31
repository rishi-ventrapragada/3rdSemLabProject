package com.smartcampus.models;

import java.util.Objects;
import java.util.Optional;

/** A row of {@code courses}, with the department code and teacher's name joined in. */
public class Course {

    private final int id;
    private final String code;
    private final String name;
    private final int credits;
    private final CourseType type;
    private final int hoursPerWeek;
    private final int semester;
    private final String deptCode;
    private final String facultyName;

    public Course(int id, String code, String name, int credits, CourseType type, int hoursPerWeek,
                  int semester, String deptCode, String facultyName) {
        if (id <= 0) {
            throw new IllegalArgumentException("id must be positive, got " + id);
        }
        if (credits < 1 || credits > 6) {
            throw new IllegalArgumentException("credits must be 1-6, got " + credits);
        }
        this.id = id;
        this.code = Objects.requireNonNull(code, "code");
        this.name = Objects.requireNonNull(name, "name");
        this.credits = credits;
        this.type = Objects.requireNonNull(type, "type");
        this.hoursPerWeek = hoursPerWeek;
        this.semester = semester;
        this.deptCode = Objects.requireNonNull(deptCode, "deptCode");
        this.facultyName = facultyName;
    }

    public int getId() {
        return id;
    }

    public String getCode() {
        return code;
    }

    public String getName() {
        return name;
    }

    public int getCredits() {
        return credits;
    }

    public CourseType getType() {
        return type;
    }

    public int getHoursPerWeek() {
        return hoursPerWeek;
    }

    public int getSemester() {
        return semester;
    }

    public String getDeptCode() {
        return deptCode;
    }

    /** Empty when no teacher is assigned ({@code courses.faculty_id} is NULL). */
    public Optional<String> getFacultyName() {
        return Optional.ofNullable(facultyName);
    }

    @Override
    public boolean equals(Object o) {
        return this == o || (o instanceof Course other && id == other.id);
    }

    @Override
    public int hashCode() {
        return Integer.hashCode(id);
    }

    @Override
    public String toString() {
        return "Course{" + code + " " + name + ", " + type + ", " + credits + " cr, sem " + semester + "}";
    }
}
