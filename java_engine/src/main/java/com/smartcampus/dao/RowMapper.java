package com.smartcampus.dao;

import java.sql.ResultSet;
import java.sql.SQLException;

/** Turns the current row of a {@link ResultSet} into an object. Each DAO passes its {@code mapRow}. */
@FunctionalInterface
public interface RowMapper<T> {

    T map(ResultSet rs) throws SQLException;
}
