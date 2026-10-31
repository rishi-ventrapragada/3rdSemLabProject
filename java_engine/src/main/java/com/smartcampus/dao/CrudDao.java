package com.smartcampus.dao;

import com.smartcampus.exceptions.DatabaseException;
import com.smartcampus.exceptions.EntityNotFoundException;

import java.util.List;
import java.util.Optional;

/**
 * Generic data-access contract shared by every entity DAO.
 *
 * <p>Implementations provide the lookups; the default methods build convenience behaviour on top
 * of them, so no implementation has to repeat it. Writes are declared on the specific DAO
 * interfaces where the application actually needs them (e.g. {@link EnrollmentDao#insert}).
 *
 * @param <T>  entity type
 * @param <ID> primary-key type
 */
public interface CrudDao<T, ID> {

    Optional<T> findById(ID id) throws DatabaseException;

    List<T> findAll() throws DatabaseException;

    /** Entity name used in "not found" messages, e.g. {@code Course}. */
    String entityName();

    /** Like {@link #findById} but fails loudly instead of returning an empty Optional. */
    default T getById(ID id) throws EntityNotFoundException, DatabaseException {
        return findById(id).orElseThrow(() -> new EntityNotFoundException(entityName(), String.valueOf(id)));
    }

    default boolean existsById(ID id) throws DatabaseException {
        return findById(id).isPresent();
    }
}
