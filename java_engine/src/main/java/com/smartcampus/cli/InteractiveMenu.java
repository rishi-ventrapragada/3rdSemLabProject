package com.smartcampus.cli;

import java.io.InputStream;
import java.io.PrintStream;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Scanner;

/**
 * Menu-driven console front end for standalone demos ({@code java -jar ... menu}). Each choice
 * prompts for its arguments with a {@link Scanner} and then runs the normal command through
 * {@link Cli#run}, so the menu adds no logic of its own. Django never calls this (CLAUDE.md:
 * commands Django calls must not read stdin).
 */
final class InteractiveMenu {

    /** One menu entry: the label shown, the command it runs and the prompts for its arguments. */
    private record Choice(String label, String command, List<String> prompts) {
    }

    private static final Map<String, Choice> CHOICES = new LinkedHashMap<>();

    static {
        CHOICES.put("1", new Choice("Student profile", "student", List.of("Roll number")));
        CHOICES.put("2", new Choice("Attendance of a student", "attendance", List.of("Roll number")));
        CHOICES.put("3", new Choice("Defaulters (below 75%)", "defaulters", List.of()));
        CHOICES.put("4", new Choice("GPA report", "gpa-report", List.of()));
        CHOICES.put("5", new Choice("Dashboard (concurrent)", "dashboard", List.of()));
        CHOICES.put("6", new Choice("Enroll a student", "enroll", List.of("Roll number", "Course code")));
        CHOICES.put("7", new Choice("Export a report to CSV", "export",
                List.of("Report (gpa-report, defaulters, attendance)", "File name")));
    }

    private final Scanner in;
    private final PrintStream out;
    private final PrintStream err;

    InteractiveMenu(InputStream in, PrintStream out, PrintStream err) {
        this.in = new Scanner(in);
        this.out = out;
        this.err = err;
    }

    /** Loops until the user chooses 0 or input ends. Returns exit code 0. */
    int run() {
        while (true) {
            out.println();
            out.println("Smart Campus engine - menu");
            CHOICES.forEach((key, choice) -> out.println("  " + key + ". " + choice.label()));
            out.println("  0. Exit");
            out.print("Choose: ");
            out.flush();
            if (!in.hasNextLine()) {
                break;
            }
            String key = readLine();
            if (key.equals("0")) {
                break;
            }
            Choice choice = CHOICES.get(key);
            if (choice == null) {
                out.println("Choose a number from 0 to " + CHOICES.size() + ".");
                continue;
            }
            List<String> args = new ArrayList<>(List.of(choice.command()));
            boolean cancelled = false;
            for (String prompt : choice.prompts()) {
                out.print(prompt + ": ");
                out.flush();
                String value = in.hasNextLine() ? readLine() : "";
                if (value.isEmpty()) {
                    cancelled = true;
                    break;
                }
                args.add(value);
            }
            if (cancelled) {
                out.println("Cancelled.");
                continue;
            }
            out.println();
            Cli.run(args.toArray(String[]::new), out, err);
        }
        out.println("Goodbye.");
        return Cli.OK;
    }

    /**
     * Next input line, trimmed. A leading UTF-8 byte-order mark is dropped: Windows PowerShell 5.1
     * adds one when piping into a program, and Java 17 decodes stdin as Cp1252, so it arrives as
     * "ï»¿" (or as U+FEFF under a UTF-8 default).
     */
    private String readLine() {
        String line = in.nextLine();
        for (String bom : new String[] {"﻿", "ï»¿"}) {
            if (line.startsWith(bom)) {
                line = line.substring(bom.length());
            }
        }
        return line.strip();
    }
}
