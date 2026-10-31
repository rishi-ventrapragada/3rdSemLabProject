package com.smartcampus.cli;

import com.smartcampus.exceptions.SmartCampusException;

import java.util.Set;

/**
 * One CLI command: its name, argument syntax, help text, accepted options and handler.
 *
 * @param args    argument syntax shown in help, e.g. {@code <rollNo> [courseCode]}
 * @param minArgs fewest positional arguments accepted
 * @param maxArgs most positional arguments accepted
 * @param options value options accepted besides the global {@code --json}
 */
record Command(String name, String args, String summary, int minArgs, int maxArgs, Set<String> options,
               Handler handler) {

    /** Runs the command. Text and JSON renderings are both produced; Main prints one. */
    @FunctionalInterface
    interface Handler {
        Result run(CommandLine cmd, Engine engine) throws SmartCampusException, UsageException;
    }

    /** Output of a successful command: data for {@code --json} and the plain-text rendering. */
    record Result(Object json, String text) {
    }

    String usage() {
        return args.isEmpty() ? name : name + " " + args;
    }

    /** Checks argument count and options before anything touches the database. */
    void validate(CommandLine cmd) throws UsageException {
        int count = cmd.positional().size();
        if (count < minArgs || count > maxArgs) {
            throw new UsageException("Usage: " + usage());
        }
        for (String option : cmd.optionNames()) {
            if (!option.equals("--help") && !options.contains(option)) {
                throw new UsageException(option + " is not valid for '" + name + "'. Usage: " + usage());
            }
        }
    }
}
