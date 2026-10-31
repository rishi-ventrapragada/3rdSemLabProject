package com.smartcampus.cli;

import com.smartcampus.exceptions.SmartCampusException;

import java.io.PrintStream;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Parses arguments, runs one command and prints the result.
 *
 * <p>Output contract (CLAUDE.md): results to stdout, errors to stderr. With {@code --json},
 * stdout is {@code {"ok":true,"command":...,"data":...}} and stderr is
 * {@code {"ok":false,"command":...,"error":{"type":...,"message":...}}}, one line each.
 * Exit codes: 0 success, 1 runtime or database error, 2 bad usage.
 */
public final class Cli {

    public static final int OK = 0;
    public static final int RUNTIME_ERROR = 1;
    public static final int USAGE_ERROR = 2;

    private static final String JAR = "java -jar smart-campus-engine.jar";
    private static final String NL = System.lineSeparator();

    private Cli() {
    }

    public static int run(String[] args, PrintStream out, PrintStream err) {
        boolean json = CommandLine.wantsJson(args);
        String commandName = null;
        try {
            CommandLine cmd = CommandLine.parse(args);
            commandName = cmd.command();
            if (commandName.equals("help")) {
                out.print(json ? success("help", helpJson()) : helpText());
                return OK;
            }
            Command command = Commands.all().get(commandName);
            if (command == null) {
                throw new UsageException("Unknown command '" + commandName + "'. Run '" + JAR + " help'.");
            }
            if (cmd.helpRequested()) {
                out.print(json ? success(commandName, commandJson(command))
                        : "Usage: " + JAR + " " + command.usage() + " [--json]" + NL + command.summary() + NL);
                return OK;
            }
            command.validate(cmd);
            Command.Result result = command.handler().run(cmd, new Engine());
            out.print(json ? success(commandName, result.json()) : result.text());
            return OK;
        } catch (UsageException e) {
            fail(err, json, commandName, "Usage", e.getMessage());
            return USAGE_ERROR;
        } catch (SmartCampusException e) {
            fail(err, json, commandName, e.getType(), e.getMessage());
            return RUNTIME_ERROR;
        } catch (RuntimeException e) {
            fail(err, json, commandName, "Internal", e.toString());
            return RUNTIME_ERROR;
        }
    }

    private static String success(String command, Object data) {
        Map<String, Object> envelope = new LinkedHashMap<>();
        envelope.put("ok", true);
        envelope.put("command", command);
        envelope.put("data", data);
        return JsonWriter.write(envelope) + NL;
    }

    private static void fail(PrintStream err, boolean json, String command, String type, String message) {
        if (json) {
            Map<String, Object> error = new LinkedHashMap<>();
            error.put("type", type);
            error.put("message", message);
            Map<String, Object> envelope = new LinkedHashMap<>();
            envelope.put("ok", false);
            envelope.put("command", command);
            envelope.put("error", error);
            err.print(JsonWriter.write(envelope) + NL);
        } else {
            err.print("Error (" + type + "): " + message + NL);
        }
    }

    private static String helpText() {
        StringBuilder out = new StringBuilder()
                .append("Smart Campus Java engine").append(NL).append(NL)
                .append("Usage: ").append(JAR).append(" <command> [args] [--json]").append(NL).append(NL)
                .append("Commands:").append(NL);
        int width = Commands.all().values().stream().mapToInt(c -> c.usage().length()).max().orElse(0);
        Commands.all().values().forEach(c -> out.append("  ")
                .append(String.format("%-" + width + "s", c.usage())).append("  ").append(c.summary()).append(NL));
        return out.append(NL)
                .append("Options:").append(NL)
                .append("  --json   machine-readable output (for Django): {\"ok\":true,\"command\",\"data\"}").append(NL)
                .append("  --help   usage of one command, e.g. 'enroll --help'").append(NL).append(NL)
                .append("Exit codes: 0 success, 1 runtime/database error, 2 bad usage.").append(NL)
                .append("DB settings: DB_* environment variables, else the nearest .env up from the working directory.")
                .append(NL)
                .toString();
    }

    private static List<Map<String, Object>> helpJson() {
        return Commands.all().values().stream().map(Cli::commandJson).toList();
    }

    private static Map<String, Object> commandJson(Command command) {
        Map<String, Object> json = new LinkedHashMap<>();
        json.put("name", command.name());
        json.put("usage", command.usage());
        json.put("summary", command.summary());
        return json;
    }
}
