package com.smartcampus.exceptions;

/** Input that is well-formed but breaks a rule: a bad value, or an app-level business rule. */
public class ValidationException extends SmartCampusException {

    public ValidationException(String message) {
        super(message);
    }

    public ValidationException(String message, Throwable cause) {
        super(message, cause);
    }
}
