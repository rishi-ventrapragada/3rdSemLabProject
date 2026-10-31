package com.smartcampus.dao;

import com.smartcampus.exceptions.CourseNotFoundException;
import com.smartcampus.exceptions.DatabaseException;
import com.smartcampus.models.Course;

import java.util.Optional;

public interface CourseDao extends CrudDao<Course, Integer> {

    Optional<Course> findByCode(String courseCode) throws DatabaseException;

    default Course getByCode(String courseCode) throws CourseNotFoundException, DatabaseException {
        return findByCode(courseCode).orElseThrow(() -> new CourseNotFoundException(courseCode));
    }

    @Override
    default String entityName() {
        return "Course";
    }
}
