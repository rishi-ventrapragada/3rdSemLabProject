package com.smartcampus.exceptions;

/**
 * Root of the engine's checked exception hierarchy.
 *
 * <p>Every failure the CLI reports to the user (or to Django) is one of these. {@link #getType()}
 * is a short, stable name that the {@code --json} error output carries, so callers can branch on
 * it without parsing the message.
 */
public class SmartCampusException extends Exception {

    public SmartCampusException(String message) {
        super(message);
    }

    public SmartCampusException(String message, Throwable cause) {
        super(message, cause);
    }

    /** Short error type for machine-readable output, e.g. {@code StudentNotFound}. */
    public String getType() {
        String name = getClass().getSimpleName();
        return name.endsWith("Exception") ? name.substring(0, name.length() - "Exception".length()) : name;
    }
}
