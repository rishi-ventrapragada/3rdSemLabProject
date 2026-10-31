package com.smartcampus.cli;

import java.math.BigDecimal;
import java.time.temporal.TemporalAccessor;
import java.util.Iterator;
import java.util.Map;
import java.util.Optional;

/**
 * Minimal JSON serializer, so the engine JAR needs no JSON library.
 *
 * <p>Supports {@code null}, strings, characters, numbers, booleans, enums (by name), dates and
 * times (ISO-8601 strings), {@link Optional} (unwrapped), maps with string keys, and any
 * {@link Iterable}. Strings are escaped per RFC 8259: quote, backslash and every control
 * character below U+0020, plus U+2028/U+2029 so the output is also safe inside JavaScript.
 */
public final class JsonWriter {

    private static final char[] HEX = "0123456789abcdef".toCharArray();

    private JsonWriter() {
    }

    public static String write(Object value) {
        StringBuilder out = new StringBuilder();
        append(out, value);
        return out.toString();
    }

    /** The JSON string literal for {@code text}, including the surrounding quotes. */
    public static String quote(String text) {
        StringBuilder out = new StringBuilder(text.length() + 2);
        appendString(out, text);
        return out.toString();
    }

    private static void append(StringBuilder out, Object value) {
        if (value == null) {
            out.append("null");
        } else if (value instanceof String s) {
            appendString(out, s);
        } else if (value instanceof Character c) {
            appendString(out, c.toString());
        } else if (value instanceof BigDecimal d) {
            out.append(d.toPlainString());
        } else if (value instanceof Double || value instanceof Float) {
            double d = ((Number) value).doubleValue();
            if (!Double.isFinite(d)) {
                throw new IllegalArgumentException("JSON cannot represent " + d);
            }
            out.append(d);
        } else if (value instanceof Number n) {
            out.append(n);
        } else if (value instanceof Boolean b) {
            out.append(b.booleanValue());
        } else if (value instanceof Enum<?> e) {
            appendString(out, e.name());
        } else if (value instanceof TemporalAccessor t) {
            appendString(out, t.toString());
        } else if (value instanceof Optional<?> o) {
            append(out, o.orElse(null));
        } else if (value instanceof Map<?, ?> map) {
            appendObject(out, map);
        } else if (value instanceof Iterable<?> items) {
            appendArray(out, items.iterator());
        } else {
            throw new IllegalArgumentException("Cannot write " + value.getClass().getName() + " as JSON");
        }
    }

    private static void appendObject(StringBuilder out, Map<?, ?> map) {
        out.append('{');
        boolean first = true;
        for (Map.Entry<?, ?> entry : map.entrySet()) {
            if (!(entry.getKey() instanceof String key)) {
                throw new IllegalArgumentException("JSON object keys must be strings: " + entry.getKey());
            }
            if (!first) {
                out.append(',');
            }
            first = false;
            appendString(out, key);
            out.append(':');
            append(out, entry.getValue());
        }
        out.append('}');
    }

    private static void appendArray(StringBuilder out, Iterator<?> items) {
        out.append('[');
        boolean first = true;
        while (items.hasNext()) {
            if (!first) {
                out.append(',');
            }
            first = false;
            append(out, items.next());
        }
        out.append(']');
    }

    private static void appendString(StringBuilder out, String text) {
        out.append('"');
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            switch (c) {
                case '"' -> out.append("\\\"");
                case '\\' -> out.append("\\\\");
                case '\n' -> out.append("\\n");
                case '\r' -> out.append("\\r");
                case '\t' -> out.append("\\t");
                case '\b' -> out.append("\\b");
                case '\f' -> out.append("\\f");
                default -> {
                    if (c < 0x20 || c == ' ' || c == ' ') {
                        out.append("\\u")
                                .append(HEX[(c >> 12) & 0xF]).append(HEX[(c >> 8) & 0xF])
                                .append(HEX[(c >> 4) & 0xF]).append(HEX[c & 0xF]);
                    } else {
                        out.append(c);
                    }
                }
            }
        }
        out.append('"');
    }
}
