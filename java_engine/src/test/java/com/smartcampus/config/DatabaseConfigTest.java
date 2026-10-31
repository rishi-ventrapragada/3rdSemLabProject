package com.smartcampus.config;

import com.smartcampus.exceptions.ValidationException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class DatabaseConfigTest {

    @Test
    void parsesEnvFileSkippingCommentsAndBlankLines(@TempDir Path dir) throws Exception {
        Path env = Files.writeString(dir.resolve(".env"), String.join("\n",
                "# Shared settings",
                "",
                "DB_HOST=localhost",
                "DB_PORT=3306",
                "DB_NAME=smart_campus_db",
                "DB_USER=root",
                "DB_PASSWORD=p@ss=word#1",
                "not a setting"));

        Map<String, String> values = DatabaseConfig.parseEnvFile(env);

        assertEquals("localhost", values.get("DB_HOST"));
        assertEquals("p@ss=word#1", values.get("DB_PASSWORD"), "only the first '=' splits; '#' mid-value is kept");
        assertEquals(5, values.size());
    }

    @Test
    void buildsJdbcUrlWithRequiredOptionsAndHidesPassword() throws ValidationException {
        DatabaseConfig config = DatabaseConfig.fromMap(Map.of(
                "DB_HOST", "localhost", "DB_PORT", "3306", "DB_NAME", "smart_campus_db",
                "DB_USER", "root", "DB_PASSWORD", "secret"), "test");

        assertEquals("jdbc:mysql://localhost:3306/smart_campus_db"
                + "?useSSL=false&allowPublicKeyRetrieval=true&connectionTimeZone=UTC", config.jdbcUrl());
        assertFalse(config.toString().contains("secret"));
    }

    @Test
    void reportsMissingAndInvalidSettings() {
        ValidationException missing = assertThrows(ValidationException.class,
                () -> DatabaseConfig.fromMap(Map.of("DB_HOST", "localhost"), "test"));
        assertTrue(missing.getMessage().contains("DB_PORT, DB_NAME, DB_USER"));

        assertThrows(ValidationException.class, () -> DatabaseConfig.fromMap(Map.of(
                "DB_HOST", "h", "DB_PORT", "abc", "DB_NAME", "n", "DB_USER", "u"), "test"));
    }

    @Test
    void findsEnvFileInAParentDirectory(@TempDir Path root) throws IOException {
        Files.writeString(root.resolve(".env"), "DB_HOST=x\n");
        Path nested = Files.createDirectories(root.resolve("java_engine/target"));

        assertEquals(root.resolve(".env"), DatabaseConfig.findEnvFile(nested).orElseThrow());
    }
}
