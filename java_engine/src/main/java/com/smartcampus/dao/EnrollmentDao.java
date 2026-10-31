package com.smartcampus.dao;

import com.smartcampus.exceptions.DatabaseException;
import com.smartcampus.exceptions.DuplicateEnrollmentException;
import com.smartcampus.exceptions.ValidationException;
import com.smartcampus.models.Enrollment;

import java.util.List;

public interface EnrollmentDao extends CrudDao<Enrollment, Integer> {

    List<Enrollment> findByStudentId(int studentId) throws DatabaseException;

    /**
     * Inserts an unsaved enrollment and returns it with its generated id.
     *
     * @throws DuplicateEnrollmentException the student is already enrolled in the course
     *                                      (MySQL 1062 on {@code uq_enrollments_student_course})
     * @throws ValidationException          a CHECK constraint rejected a value (MySQL 3819)
     */
    Enrollment insert(Enrollment enrollment)
            throws DuplicateEnrollmentException, ValidationException, DatabaseException;

    @Override
    default String entityName() {
        return "Enrollment";
    }
}
