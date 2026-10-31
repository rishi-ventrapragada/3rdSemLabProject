package com.smartcampus.dao;

import com.smartcampus.config.ConnectionFactory;
import com.smartcampus.exceptions.DatabaseException;
import com.smartcampus.models.Student;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;
import java.util.Optional;

public class JdbcStudentDao extends JdbcDaoSupport implements StudentDao {

    private static final String FIND_BY_ID = """
            SELECT s.student_id, s.roll_number, s.username, s.full_name, s.email, d.dept_code,
                   s.semester, s.section, s.cgpa, s.is_defaulter
            FROM students s
                JOIN departments d ON d.dept_id = s.dept_id
            WHERE s.student_id = ?""";

    private static final String FIND_BY_ROLL_NUMBER = """
            SELECT s.student_id, s.roll_number, s.username, s.full_name, s.email, d.dept_code,
                   s.semester, s.section, s.cgpa, s.is_defaulter
            FROM students s
                JOIN departments d ON d.dept_id = s.dept_id
            WHERE s.roll_number = ?""";

    private static final String FIND_BY_USERNAME = """
            SELECT s.student_id, s.roll_number, s.username, s.full_name, s.email, d.dept_code,
                   s.semester, s.section, s.cgpa, s.is_defaulter
            FROM students s
                JOIN departments d ON d.dept_id = s.dept_id
            WHERE s.username = ?""";

    private static final String FIND_ALL = """
            SELECT s.student_id, s.roll_number, s.username, s.full_name, s.email, d.dept_code,
                   s.semester, s.section, s.cgpa, s.is_defaulter
            FROM students s
                JOIN departments d ON d.dept_id = s.dept_id
            ORDER BY s.roll_number""";

    public JdbcStudentDao(ConnectionFactory connections) {
        super(connections);
    }

    @Override
    public Optional<Student> findById(Integer id) throws DatabaseException {
        return queryOne(FIND_BY_ID, ps -> ps.setInt(1, id), this::mapRow);
    }

    @Override
    public List<Student> findAll() throws DatabaseException {
        return queryList(FIND_ALL, StatementBinder.NONE, this::mapRow);
    }

    @Override
    public Optional<Student> findByRollNumber(String rollNumber) throws DatabaseException {
        return queryOne(FIND_BY_ROLL_NUMBER, ps -> ps.setString(1, rollNumber), this::mapRow);
    }

    @Override
    public Optional<Student> findByUsername(String username) throws DatabaseException {
        return queryOne(FIND_BY_USERNAME, ps -> ps.setString(1, username), this::mapRow);
    }

    private Student mapRow(ResultSet rs) throws SQLException {
        return new Student(
                rs.getInt("student_id"),
                rs.getString("roll_number"),
                rs.getString("username"),
                rs.getString("full_name"),
                rs.getString("email"),
                rs.getString("dept_code"),
                rs.getInt("semester"),
                rs.getString("section").charAt(0),
                rs.getBigDecimal("cgpa"),
                rs.getBoolean("is_defaulter"));
    }
}
