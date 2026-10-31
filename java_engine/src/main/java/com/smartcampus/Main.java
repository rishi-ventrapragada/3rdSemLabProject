package com.smartcampus;

import com.smartcampus.cli.Cli;

/**
 * Command-line entry point for the Smart Campus Java engine.
 *
 * <p>Runs standalone ({@code java -jar target/smart-campus-engine.jar <command> [args] [--json]})
 * or is invoked by the Django portal via {@code subprocess}. Contract: results go to stdout,
 * errors to stderr, exit code 0 = success, 1 = runtime/database error, 2 = bad usage.
 * Run {@code help} for the command list.
 */
public final class Main {

    private Main() {
    }

    public static void main(String[] args) {
        System.exit(Cli.run(args, System.out, System.err));
    }
}
