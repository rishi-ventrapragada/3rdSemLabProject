package com.smartcampus.exceptions;

/** No course has the given course code or id. */
public class CourseNotFoundException extends EntityNotFoundException {

    public CourseNotFoundException(String key) {
        super("Course", key);
    }
}
