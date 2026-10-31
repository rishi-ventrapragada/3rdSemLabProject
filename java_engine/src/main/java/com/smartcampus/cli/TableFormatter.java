package com.smartcampus.cli;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.function.Function;

/**
 * Renders a list of objects as an aligned plain-text table. Each column is a header plus a
 * function that extracts the cell value from a row; {@code null} and empty {@link Optional}
 * cells print as {@code -}.
 *
 * @param <T> row type
 */
public final class TableFormatter<T> {

    private enum Align { LEFT, RIGHT }

    private record Column<T>(String header, Function<? super T, ?> value, Align align) {
    }

    private static final String GAP = "  ";

    private final List<Column<T>> columns = new ArrayList<>();

    public TableFormatter<T> left(String header, Function<? super T, ?> value) {
        columns.add(new Column<>(header, value, Align.LEFT));
        return this;
    }

    public TableFormatter<T> right(String header, Function<? super T, ?> value) {
        columns.add(new Column<>(header, value, Align.RIGHT));
        return this;
    }

    public String render(List<? extends T> rows) {
        List<String[]> cells = new ArrayList<>();
        int[] widths = new int[columns.size()];
        for (int c = 0; c < columns.size(); c++) {
            widths[c] = columns.get(c).header().length();
        }
        for (T row : rows) {
            String[] line = new String[columns.size()];
            for (int c = 0; c < columns.size(); c++) {
                line[c] = cell(columns.get(c).value().apply(row));
                widths[c] = Math.max(widths[c], line[c].length());
            }
            cells.add(line);
        }

        StringBuilder out = new StringBuilder();
        String[] headers = columns.stream().map(Column::header).toArray(String[]::new);
        appendLine(out, headers, widths);
        String[] rules = new String[columns.size()];
        for (int c = 0; c < columns.size(); c++) {
            rules[c] = "-".repeat(widths[c]);
        }
        appendLine(out, rules, widths);
        for (String[] line : cells) {
            appendLine(out, line, widths);
        }
        return out.toString();
    }

    private void appendLine(StringBuilder out, String[] values, int[] widths) {
        StringBuilder line = new StringBuilder();
        for (int c = 0; c < values.length; c++) {
            if (c > 0) {
                line.append(GAP);
            }
            String padding = " ".repeat(widths[c] - values[c].length());
            line.append(columns.get(c).align() == Align.RIGHT ? padding + values[c] : values[c] + padding);
        }
        out.append(line.toString().stripTrailing()).append(System.lineSeparator());
    }

    private static String cell(Object value) {
        if (value instanceof Optional<?> optional) {
            value = optional.orElse(null);
        }
        return value == null ? "-" : value.toString();
    }
}
