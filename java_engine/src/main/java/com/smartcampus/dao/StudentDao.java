package com.smartcampus.dao;

import com.smartcampus.exceptions.DatabaseException;
import com.smartcampus.exceptions.StudentNotFoundException;
import com.smartcampus.models.Student;

import java.util.Optional;

public interface StudentDao extends CrudDao<Student, Integer> {

    Optional<Student> findByRollNumber(String rollNumber) throws DatabaseException;

    Optional<Student> findByUsername(String username) throws DatabaseException;

    /** Roll-number lookup that throws {@link StudentNotFoundException} instead of returning empty. */
    default Student getByRollNumber(String rollNumber) throws StudentNotFoundException, DatabaseException {
        return findByRollNumber(rollNumber).orElseThrow(() -> new StudentNotFoundException(rollNumber));
    }

    @Override
    default String entityName() {
        return "Student";
    }
}
