package com.smartcampus.cli;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

/**
 * Parsed arguments: {@code <command> [positional...] [--json] [--name value...]}.
 * Flags may appear anywhere after the command name.
 */
public final class CommandLine {

    /** Options that take a value; {@code --json} and {@code --help} are the only boolean flags. */
    private static final Set<String> VALUE_OPTIONS = Set.of("--year");

    private final String command;
    private final List<String> positional;
    private final Map<String, String> options;
    private final boolean json;

    private CommandLine(String command, List<String> positional, Map<String, String> options, boolean json) {
        this.command = command;
        this.positional = List.copyOf(positional);
        this.options = Map.copyOf(options);
        this.json = json;
    }

    public static CommandLine parse(String[] args) throws UsageException {
        String command = null;
        List<String> positional = new ArrayList<>();
        Map<String, String> options = new LinkedHashMap<>();
        boolean json = false;

        for (int i = 0; i < args.length; i++) {
            String arg = args[i];
            if (arg.equals("--json")) {
                json = true;
            } else if (arg.equals("--help") || arg.equals("-h")) {
                options.put("--help", "true");
            } else if (VALUE_OPTIONS.contains(arg)) {
                if (i + 1 >= args.length || args[i + 1].startsWith("--")) {
                    throw new UsageException(arg + " needs a value");
                }
                options.put(arg, args[++i]);
            } else if (arg.startsWith("--")) {
                throw new UsageException("Unknown option " + arg);
            } else if (command == null) {
                command = arg;
            } else {
                positional.add(arg);
            }
        }
        return new CommandLine(command == null ? "help" : command, positional, options, json);
    }

    /** True if {@code --json} appears anywhere, even when the rest fails to parse. */
    public static boolean wantsJson(String[] args) {
        return List.of(args).contains("--json");
    }

    public String command() {
        return command;
    }

    public List<String> positional() {
        return positional;
    }

    public String arg(int index) {
        return positional.get(index);
    }

    public Optional<String> option(String name) {
        return Optional.ofNullable(options.get(name));
    }

    public Set<String> optionNames() {
        return options.keySet();
    }

    public boolean json() {
        return json;
    }

    public boolean helpRequested() {
        return options.containsKey("--help");
    }
}
