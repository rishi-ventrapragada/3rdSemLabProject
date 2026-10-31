package com.smartcampus.config;

import com.smartcampus.exceptions.DatabaseException;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

/**
 * Hands out JDBC connections via {@link DriverManager}. No pool: every call opens a new
 * connection, which the caller closes with try-with-resources. Because connections are never
 * shared, DAOs can safely be called from several threads at once.
 */
public final class ConnectionFactory {

    private final DatabaseConfig config;

    public ConnectionFactory(DatabaseConfig config) {
        this.config = config;
    }

    public Connection getConnection() throws DatabaseException {
        try {
            return DriverManager.getConnection(config.jdbcUrl(), config.getUser(), config.getPassword());
        } catch (SQLException e) {
            throw new DatabaseException("Cannot connect to MySQL as " + config, e);
        }
    }

    public DatabaseConfig getConfig() {
        return config;
    }
}
