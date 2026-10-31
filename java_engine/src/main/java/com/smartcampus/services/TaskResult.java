package com.smartcampus.services;

/**
 * The value a background task produced, plus which thread ran it and for how long.
 *
 * @param <T> the task's result type
 */
public record TaskResult<T>(T value, String threadName, long elapsedMillis) {
}
