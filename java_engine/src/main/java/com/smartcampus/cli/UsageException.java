package com.smartcampus.cli;

/** The command line itself is wrong (unknown command, missing argument, bad flag). Exit code 2. */
public class UsageException extends Exception {

    public UsageException(String message) {
        super(message);
    }
}
