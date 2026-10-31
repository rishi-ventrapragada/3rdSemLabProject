package com.smartcampus.cli;

import org.junit.jupiter.api.Test;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** CLI behaviour that needs no database: help, usage errors and their exit codes. */
class CliTest {

    private final ByteArrayOutputStream out = new ByteArrayOutputStream();
    private final ByteArrayOutputStream err = new ByteArrayOutputStream();

    private int run(String... args) {
        return Cli.run(args, new PrintStream(out, true, StandardCharsets.UTF_8),
                new PrintStream(err, true, StandardCharsets.UTF_8));
    }

    private String stdout() {
        return out.toString(StandardCharsets.UTF_8);
    }

    private String stderr() {
        return err.toString(StandardCharsets.UTF_8);
    }

    @Test
    void helpListsEveryCommandAndExitsZero() {
        assertEquals(Cli.OK, run("help"));
        for (String name : Commands.all().keySet()) {
            assertTrue(stdout().contains(name), "help should list " + name);
        }
    }

    @Test
    void noArgumentsShowsHelp() {
        assertEquals(Cli.OK, run());
        assertTrue(stdout().contains("Commands:"));
    }

    @Test
    void unknownCommandIsAUsageError() {
        assertEquals(Cli.USAGE_ERROR, run("expel", "25CSE001"));
        assertTrue(stderr().contains("Unknown command 'expel'"));
    }

    @Test
    void wrongArgumentCountIsAUsageErrorBeforeAnyDatabaseCall() {
        assertEquals(Cli.USAGE_ERROR, run("enroll", "25CSE001"));
        assertTrue(stderr().contains("Usage: enroll <rollNo> <courseCode>"));
    }

    @Test
    void optionsAreCheckedPerCommand() {
        assertEquals(Cli.USAGE_ERROR, run("defaulters", "--year", "2026-27"));
        assertEquals(Cli.USAGE_ERROR, run("student", "25CSE001", "--colour"));
        assertEquals(Cli.USAGE_ERROR, run("enroll", "25CSE001", "CS301", "--year"));
    }

    @Test
    void usageErrorsAreJsonOnStderrWhenRequested() {
        assertEquals(Cli.USAGE_ERROR, run("gpa-report", "extra", "--json"));
        assertEquals("", stdout());
        assertTrue(stderr().startsWith("{\"ok\":false,\"command\":\"gpa-report\",\"error\":{\"type\":\"Usage\""),
                stderr());
    }

    @Test
    void academicYearRollsOverInJuly() {
        assertEquals("2026-27", Commands.academicYear(LocalDate.of(2026, 10, 31)));
        assertEquals("2026-27", Commands.academicYear(LocalDate.of(2026, 7, 1)));
        assertEquals("2025-26", Commands.academicYear(LocalDate.of(2026, 6, 30)));
        assertEquals("2099-00", Commands.academicYear(LocalDate.of(2099, 8, 1)));
    }
}
