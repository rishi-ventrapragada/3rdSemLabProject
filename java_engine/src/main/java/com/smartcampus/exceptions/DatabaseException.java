package com.smartcampus.exceptions;

import java.sql.SQLException;

/**
 * A database call failed: connection refused, bad credentials, a rejected statement, and so on.
 * DAOs wrap every {@link SQLException} in this type and keep it as the cause.
 */
public class DatabaseException extends SmartCampusException {

    public DatabaseException(String message) {
        super(message);
    }

    public DatabaseException(String message, SQLException cause) {
        super(message + ": " + cause.getMessage(), cause);
    }

    /** MySQL vendor error code of the wrapped {@link SQLException}, or 0 if there is none. */
    public int getErrorCode() {
        return getCause() instanceof SQLException sql ? sql.getErrorCode() : 0;
    }
}
