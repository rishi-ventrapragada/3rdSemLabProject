package com.smartcampus.dao;

import com.smartcampus.config.ConnectionFactory;
import com.smartcampus.exceptions.DatabaseException;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Shared JDBC plumbing for the {@code Jdbc*Dao} classes: open a connection, prepare the
 * statement, bind parameters, map rows, and close everything with try-with-resources.
 * Every {@link SQLException} leaves as a {@link DatabaseException} with the cause kept.
 */
public abstract class JdbcDaoSupport {

    private final ConnectionFactory connections;

    protected JdbcDaoSupport(ConnectionFactory connections) {
        this.connections = Objects.requireNonNull(connections, "connections");
    }

    protected Connection openConnection() throws DatabaseException {
        return connections.getConnection();
    }

    protected <T> List<T> queryList(String sql, StatementBinder binder, RowMapper<T> mapper)
            throws DatabaseException {
        try (Connection conn = openConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            binder.bind(ps);
            try (ResultSet rs = ps.executeQuery()) {
                List<T> rows = new ArrayList<>();
                while (rs.next()) {
                    rows.add(mapper.map(rs));
                }
                return rows;
            }
        } catch (SQLException e) {
            throw new DatabaseException("Database query failed", e);
        }
    }

    protected <T> Optional<T> queryOne(String sql, StatementBinder binder, RowMapper<T> mapper)
            throws DatabaseException {
        return queryList(sql, binder, mapper).stream().findFirst();
    }
}
