package com.smartcampus.config;

import com.smartcampus.exceptions.ValidationException;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * MySQL connection settings shared with the Django portal.
 *
 * <p>Each {@code DB_*} value comes from a real environment variable if one is set (this is how
 * Django passes them to the JAR via {@code subprocess}), otherwise from the repo-root {@code .env},
 * found by walking up from the working directory. {@code .env} must be plain {@code KEY=value}
 * lines: no quotes, no {@code export}, no inline comments.
 */
public final class DatabaseConfig {

    public static final String ENV_FILE = ".env";
    private static final List<String> REQUIRED = List.of("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER");

    private final String host;
    private final int port;
    private final String databaseName;
    private final String user;
    private final String password;

    public DatabaseConfig(String host, int port, String databaseName, String user, String password) {
        this.host = host;
        this.port = port;
        this.databaseName = databaseName;
        this.user = user;
        this.password = password == null ? "" : password;
    }

    /** Loads settings from the environment, falling back to the nearest {@code .env}. */
    public static DatabaseConfig load() throws ValidationException {
        Optional<Path> envFile = findEnvFile(Paths.get("").toAbsolutePath());
        Map<String, String> values = new HashMap<>();
        if (envFile.isPresent()) {
            values.putAll(parseEnvFile(envFile.get()));
        }
        System.getenv().forEach((key, value) -> {
            if (key.startsWith("DB_")) {
                values.put(key, value);
            }
        });
        return fromMap(values, envFile.map(Path::toString).orElse("(no .env found)"));
    }

    static DatabaseConfig fromMap(Map<String, String> values, String source) throws ValidationException {
        List<String> missing = REQUIRED.stream()
                .filter(key -> values.getOrDefault(key, "").isBlank())
                .toList();
        if (!missing.isEmpty()) {
            throw new ValidationException("Missing " + String.join(", ", missing) + " in " + source
                    + ". Copy .env.example to .env at the repo root and fill it in.");
        }
        int port;
        try {
            port = Integer.parseInt(values.get("DB_PORT").trim());
        } catch (NumberFormatException e) {
            throw new ValidationException("DB_PORT must be a number, got '" + values.get("DB_PORT") + "'", e);
        }
        return new DatabaseConfig(values.get("DB_HOST").trim(), port, values.get("DB_NAME").trim(),
                values.get("DB_USER").trim(), values.getOrDefault("DB_PASSWORD", ""));
    }

    /** Parses {@code KEY=value} lines, skipping blanks and {@code #} comments. */
    static Map<String, String> parseEnvFile(Path file) throws ValidationException {
        Map<String, String> values = new HashMap<>();
        try {
            for (String line : Files.readAllLines(file, StandardCharsets.UTF_8)) {
                String trimmed = line.strip();
                int eq = trimmed.indexOf('=');
                if (trimmed.isEmpty() || trimmed.startsWith("#") || eq <= 0) {
                    continue;
                }
                values.put(trimmed.substring(0, eq).strip(), trimmed.substring(eq + 1));
            }
        } catch (IOException e) {
            throw new ValidationException("Cannot read " + file + ": " + e.getMessage(), e);
        }
        return values;
    }

    static Optional<Path> findEnvFile(Path start) {
        for (Path dir = start; dir != null; dir = dir.getParent()) {
            Path candidate = dir.resolve(ENV_FILE);
            if (Files.isRegularFile(candidate)) {
                return Optional.of(candidate);
            }
        }
        return Optional.empty();
    }

    /** JDBC URL with the options CLAUDE.md requires (local MySQL 8, UTC timestamps). */
    public String jdbcUrl() {
        return "jdbc:mysql://" + host + ":" + port + "/" + databaseName
                + "?useSSL=false&allowPublicKeyRetrieval=true&connectionTimeZone=UTC";
    }

    public String getUser() {
        return user;
    }

    /** Package-private: only {@link ConnectionFactory} needs the password. */
    String getPassword() {
        return password;
    }

    public String getDatabaseName() {
        return databaseName;
    }

    /** Never includes the password. */
    @Override
    public String toString() {
        return user + "@" + host + ":" + port + "/" + databaseName;
    }
}
