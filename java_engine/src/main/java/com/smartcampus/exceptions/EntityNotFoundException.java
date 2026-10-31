package com.smartcampus.exceptions;

/** A lookup by key found no row. Subclasses name the specific entity. */
public class EntityNotFoundException extends SmartCampusException {

    private final String entity;
    private final String key;

    public EntityNotFoundException(String entity, String key) {
        super(entity + " not found: " + key);
        this.entity = entity;
        this.key = key;
    }

    public String getEntity() {
        return entity;
    }

    public String getKey() {
        return key;
    }
}
