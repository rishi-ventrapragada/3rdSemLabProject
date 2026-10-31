package com.smartcampus.dao;

import java.sql.PreparedStatement;
import java.sql.SQLException;

/** Sets the {@code ?} parameters of a {@link PreparedStatement}. Values are never concatenated into SQL. */
@FunctionalInterface
public interface StatementBinder {

    StatementBinder NONE = ps -> { };

    void bind(PreparedStatement ps) throws SQLException;
}
