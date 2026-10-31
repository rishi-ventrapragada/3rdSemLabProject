package com.smartcampus.dao;

import com.smartcampus.exceptions.DatabaseException;
import com.smartcampus.models.Marks;

import java.util.List;

/** Read-only: total, grade points and letter grade are written by the database triggers. */
public interface MarksDao extends CrudDao<Marks, Integer> {

    List<Marks> findByStudentId(int studentId) throws DatabaseException;

    @Override
    default String entityName() {
        return "Marks";
    }
}
