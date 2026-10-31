package com.smartcampus.exceptions;

/** No student has the given roll number, username or id. */
public class StudentNotFoundException extends EntityNotFoundException {

    public StudentNotFoundException(String key) {
        super("Student", key);
    }
}
