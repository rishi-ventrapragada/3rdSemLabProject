package com.smartcampus.dao;

import com.smartcampus.exceptions.DatabaseException;
import com.smartcampus.models.Faculty;

import java.util.Optional;

public interface FacultyDao extends CrudDao<Faculty, Integer> {

    Optional<Faculty> findByUsername(String username) throws DatabaseException;

    @Override
    default String entityName() {
        return "Faculty";
    }
}
