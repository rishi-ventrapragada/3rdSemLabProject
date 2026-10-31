package com.smartcampus.cli;

import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class JsonWriterTest {

    @Test
    void escapesQuoteInAName() {
        assertEquals("\"Dwayne \\\"The Rock\\\" Johnson\"", JsonWriter.quote("Dwayne \"The Rock\" Johnson"));
    }

    @Test
    void escapesBackslash() {
        assertEquals("\"C:\\\\dev\\\\3rdSemLabProject\"", JsonWriter.quote("C:\\dev\\3rdSemLabProject"));
    }

    @Test
    void escapesNewlinesTabsAndShortEscapes() {
        assertEquals("\"line1\\nline2\\r\\n\\tindented\\b\\f\"", JsonWriter.quote("line1\nline2\r\n\tindented\b\f"));
    }

    @Test
    void escapesOtherControlCharactersAsUnicode() {
        assertEquals("\"a\\u0000b\\u0001c\\u001fd\"", JsonWriter.quote("a\u0000b\u0001c\u001Fd"));
    }

    @Test
    void escapesLineAndParagraphSeparators() {
        assertEquals("\"x\\u2028y\\u2029z\"", JsonWriter.quote("x\u2028y\u2029z"));
    }

    @Test
    void leavesOrdinaryUnicodeAndApostrophesAlone() {
        assertEquals("\"O'Neil Ananyā 日本\"", JsonWriter.quote("O'Neil Ananyā 日本"));
    }

    @Test
    void writesAWholeStudentRecordWithAHostileName() {
        Map<String, Object> student = new LinkedHashMap<>();
        student.put("roll_number", "25CSE099");
        student.put("full_name", "Robert \"Bobby\" O'Brien\\Jr.\n");
        student.put("cgpa", new BigDecimal("8.50"));
        student.put("is_defaulter", false);
        student.put("external_marks", Optional.empty());
        student.put("enrolled_on", LocalDate.of(2026, 7, 20));
        student.put("courses", List.of("CS301", "MA301"));

        assertEquals("{\"roll_number\":\"25CSE099\","
                        + "\"full_name\":\"Robert \\\"Bobby\\\" O'Brien\\\\Jr.\\n\","
                        + "\"cgpa\":8.50,\"is_defaulter\":false,\"external_marks\":null,"
                        + "\"enrolled_on\":\"2026-07-20\",\"courses\":[\"CS301\",\"MA301\"]}",
                JsonWriter.write(student));
    }

    @Test
    void writesNullsNumbersAndNestedCollections() {
        List<Object> values = new ArrayList<>(Arrays.asList(null, 1, 2.5, new BigDecimal("1E+3"), Map.of()));
        assertEquals("[null,1,2.5,1000,{}]", JsonWriter.write(values));
    }

    @Test
    void rejectsValuesJsonCannotRepresent() {
        assertThrows(IllegalArgumentException.class, () -> JsonWriter.write(Double.NaN));
        assertThrows(IllegalArgumentException.class, () -> JsonWriter.write(new Object()));
        assertThrows(IllegalArgumentException.class, () -> JsonWriter.write(Map.of(1, "non-string key")));
    }
}
