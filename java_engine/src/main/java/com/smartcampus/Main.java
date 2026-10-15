package com.smartcampus;

/**
 * Command-line entry point for the Smart Campus Java engine.
 *
 * <p>Runs standalone ({@code java -jar target/smart-campus-engine.jar <command> [args]}) or is
 * invoked by the Django portal via {@code subprocess}. Contract: results go to stdout, errors to
 * stderr, exit code 0 = success, 1 = runtime/database error, 2 = bad usage.
 *
 * <p>Commands are registered here as services are implemented.
 */
public final class Main {

    private Main() {
    }

    public static void main(String[] args) {
        if (args.length == 0) {
            System.out.println("Usage: java -jar smart-campus-engine.jar <command> [args]");
            System.out.println("No commands are implemented yet.");
            return;
        }
        System.err.println("Unknown command: " + args[0]);
        System.exit(2);
    }
}
