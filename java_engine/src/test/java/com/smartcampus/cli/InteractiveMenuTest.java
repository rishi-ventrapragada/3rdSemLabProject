package com.smartcampus.cli;

import org.junit.jupiter.api.Test;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** The menu loop with scripted keyboard input. No choice here reaches the database. */
class InteractiveMenuTest {

    private String run(String keyboard) {
        return runBytes(keyboard.getBytes(StandardCharsets.UTF_8));
    }

    private String runBytes(byte[] keyboard) {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        PrintStream print = new PrintStream(out, true, StandardCharsets.UTF_8);
        int code = new InteractiveMenu(new ByteArrayInputStream(keyboard), print, print).run();
        assertEquals(Cli.OK, code);
        return out.toString(StandardCharsets.UTF_8);
    }

    @Test
    void listsChoicesAndExitsOnZero() {
        String output = run("0\n");
        assertTrue(output.contains("1. Student profile"));
        assertTrue(output.contains("7. Export a report to CSV"));
        assertTrue(output.contains("Goodbye."));
    }

    @Test
    void rejectsUnknownChoices() {
        assertTrue(run("42\n0\n").contains("Choose a number from 0 to 7."));
    }

    @Test
    void blankAnswerCancelsWithoutRunningTheCommand() {
        String output = run("6\n25CSE001\n\n0\n");
        assertTrue(output.contains("Course code: "));
        assertTrue(output.contains("Cancelled."));
    }

    @Test
    void leadingByteOrderMarkFromPowerShellPipesIsIgnored() {
        // The raw bytes PowerShell 5.1 sends when piping "0": a UTF-8 BOM (EF BB BF), then "0\n".
        // Without the fix the first choice is misread and the menu prints "Choose a number".
        byte[] piped = {(byte) 0xEF, (byte) 0xBB, (byte) 0xBF, '0', '\n'};
        String output = runBytes(piped);
        assertTrue(output.contains("Goodbye."));
        assertTrue(!output.contains("Choose a number"), "a BOM-prefixed 0 must exit at once");
    }

    @Test
    void endOfInputExitsCleanly() {
        assertTrue(run("").contains("Goodbye."));
    }

    @Test
    void menuRefusesJson() {
        ByteArrayOutputStream err = new ByteArrayOutputStream();
        int code = Cli.run(new String[] {"menu", "--json"}, new PrintStream(new ByteArrayOutputStream()),
                new PrintStream(err, true, StandardCharsets.UTF_8));
        assertEquals(Cli.USAGE_ERROR, code);
        assertTrue(err.toString(StandardCharsets.UTF_8).contains("menu is interactive"));
    }
}
