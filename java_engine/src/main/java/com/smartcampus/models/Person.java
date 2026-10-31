package com.smartcampus.models;

import java.util.Objects;

/**
 * Shared state and behaviour of everyone with a login: students and faculty.
 *
 * <p>{@code username} is the link to Django's {@code auth_user.username} (see CLAUDE.md,
 * "Linking Django logins to people"). Subclasses must say what role they are and what
 * identifies them; {@link #describe()} is overridden to add role-specific details.
 */
public abstract class Person {

    private final int id;
    private final String username;
    private final String fullName;
    private final String email;
    private final String deptCode;

    protected Person(int id, String username, String fullName, String email, String deptCode) {
        if (id <= 0) {
            throw new IllegalArgumentException("id must be positive, got " + id);
        }
        this.id = id;
        this.username = requireText(username, "username");
        this.fullName = requireText(fullName, "fullName");
        this.email = requireText(email, "email");
        if (!email.contains("@")) {
            throw new IllegalArgumentException("email must contain '@': " + email);
        }
        this.deptCode = requireText(deptCode, "deptCode");
    }

    /** Role name as used for Django Groups: {@code Student} or {@code Faculty}. */
    public abstract String getRole();

    /** The institution's identifier: roll number for students, employee code for faculty. */
    public abstract String getIdentifier();

    /** One-line summary. Subclasses extend it with role-specific details. */
    public String describe() {
        return getRole() + " " + getIdentifier() + " - " + fullName + " <" + email + ">, " + deptCode;
    }

    protected static String requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(field + " must not be blank");
        }
        return value;
    }

    public int getId() {
        return id;
    }

    public String getUsername() {
        return username;
    }

    public String getFullName() {
        return fullName;
    }

    public String getEmail() {
        return email;
    }

    public String getDeptCode() {
        return deptCode;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        return o != null && getClass() == o.getClass() && id == ((Person) o).id;
    }

    @Override
    public int hashCode() {
        return Objects.hash(getClass(), id);
    }

    @Override
    public String toString() {
        return getClass().getSimpleName() + "{id=" + id + ", " + getIdentifier() + ", " + username + "}";
    }
}
