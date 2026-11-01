package com.smartcampus.exceptions;

import java.io.IOException;

/** A report could not be written to a file. Wraps the underlying {@link IOException}. */
public class ExportException extends SmartCampusException {

    public ExportException(String message, IOException cause) {
        super(message + ": " + cause.getMessage(), cause);
    }
}
