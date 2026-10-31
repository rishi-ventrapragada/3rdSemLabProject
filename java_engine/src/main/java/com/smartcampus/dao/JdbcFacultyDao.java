package com.smartcampus.dao;

import com.smartcampus.config.ConnectionFactory;
import com.smartcampus.exceptions.DatabaseException;
import com.smartcampus.models.Faculty;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;
import java.util.Optional;

public class JdbcFacultyDao extends JdbcDaoSupport implements FacultyDao {

    private static final String FIND_BY_ID = """
            SELECT f.faculty_id, f.employee_code, f.username, f.full_name, f.email, d.dept_code, f.designation
            FROM faculty f
                JOIN departments d ON d.dept_id = f.dept_id
            WHERE f.faculty_id = ?""";

    private static final String FIND_BY_USERNAME = """
            SELECT f.faculty_id, f.employee_code, f.username, f.full_name, f.email, d.dept_code, f.designation
            FROM faculty f
                JOIN departments d ON d.dept_id = f.dept_id
            WHERE f.username = ?""";

    private static final String FIND_ALL = """
            SELECT f.faculty_id, f.employee_code, f.username, f.full_name, f.email, d.dept_code, f.designation
            FROM faculty f
                JOIN departments d ON d.dept_id = f.dept_id
            ORDER BY f.employee_code""";

    public JdbcFacultyDao(ConnectionFactory connections) {
        super(connections);
    }

    @Override
    public Optional<Faculty> findById(Integer id) throws DatabaseException {
        return queryOne(FIND_BY_ID, ps -> ps.setInt(1, id), this::mapRow);
    }

    @Override
    public List<Faculty> findAll() throws DatabaseException {
        return queryList(FIND_ALL, StatementBinder.NONE, this::mapRow);
    }

    @Override
    public Optional<Faculty> findByUsername(String username) throws DatabaseException {
        return queryOne(FIND_BY_USERNAME, ps -> ps.setString(1, username), this::mapRow);
    }

    private Faculty mapRow(ResultSet rs) throws SQLException {
        return new Faculty(
                rs.getInt("faculty_id"),
                rs.getString("employee_code"),
                rs.getString("username"),
                rs.getString("full_name"),
                rs.getString("email"),
                rs.getString("dept_code"),
                rs.getString("designation"));
    }
}
