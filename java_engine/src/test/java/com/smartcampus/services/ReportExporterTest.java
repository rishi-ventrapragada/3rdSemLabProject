package com.smartcampus.services;

import com.smartcampus.exceptions.ValidationException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ReportExporterTest {

    private record Row(String name, BigDecimal gpa) {
    }

    @Test
    void quotesFieldsWithCommasQuotesAndLineBreaks() {
        assertEquals("plain,\"a,b\",\"say \"\"hi\"\"\",\"two\nlines\",,8.50",
                ReportExporter.csvLine(Arrays.asList("plain", "a,b", "say \"hi\"", "two\nlines", null,
                        new BigDecimal("8.50"))));
    }

    @Test
    void writesHeaderAndRowsAndCreatesParentFolders(@TempDir Path dir) throws Exception {
        Path file = dir.resolve("reports/2026/gpa.csv");
        List<Row> rows = List.of(new Row("Aarav Sharma", new BigDecimal("7.57")),
                new Row("Robert \"Bobby\" O'Brien", null));

        int written = ReportExporter.writeCsv(file, List.of("name", "gpa"), rows, r -> Arrays.asList(r.name(), r.gpa()));

        assertEquals(2, written);
        List<String> lines = Files.readAllLines(file, StandardCharsets.UTF_8);
        assertEquals(List.of("name,gpa", "Aarav Sharma,7.57", "\"Robert \"\"Bobby\"\" O'Brien\","), lines);
    }

    @Test
    void reportNamesAreCaseInsensitiveAndUnknownOnesAreRejected() throws ValidationException {
        assertEquals(ReportExporter.Report.GPA_REPORT, ReportExporter.Report.fromName("GPA-Report"));
        ValidationException error = assertThrows(ValidationException.class,
                () -> ReportExporter.Report.fromName("salaries"));
        assertTrue(error.getMessage().contains("gpa-report, defaulters, attendance"));
    }
}
