package com.smartcampus.dao;

import com.smartcampus.config.ConnectionFactory;
import com.smartcampus.exceptions.DatabaseException;
import com.smartcampus.models.Course;
import com.smartcampus.models.CourseType;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;
import java.util.Optional;

public class JdbcCourseDao extends JdbcDaoSupport implements CourseDao {

    private static final String FIND_BY_ID = """
            SELECT c.course_id, c.course_code, c.course_name, c.credits, c.course_type, c.hours_per_week,
                   c.semester, d.dept_code, f.full_name AS faculty_name
            FROM courses c
                JOIN departments d ON d.dept_id = c.dept_id
                LEFT JOIN faculty f ON f.faculty_id = c.faculty_id
            WHERE c.course_id = ?""";

    private static final String FIND_BY_CODE = """
            SELECT c.course_id, c.course_code, c.course_name, c.credits, c.course_type, c.hours_per_week,
                   c.semester, d.dept_code, f.full_name AS faculty_name
            FROM courses c
                JOIN departments d ON d.dept_id = c.dept_id
                LEFT JOIN faculty f ON f.faculty_id = c.faculty_id
            WHERE c.course_code = ?""";

    private static final String FIND_ALL = """
            SELECT c.course_id, c.course_code, c.course_name, c.credits, c.course_type, c.hours_per_week,
                   c.semester, d.dept_code, f.full_name AS faculty_name
            FROM courses c
                JOIN departments d ON d.dept_id = c.dept_id
                LEFT JOIN faculty f ON f.faculty_id = c.faculty_id
            ORDER BY c.course_code""";

    public JdbcCourseDao(ConnectionFactory connections) {
        super(connections);
    }

    @Override
    public Optional<Course> findById(Integer id) throws DatabaseException {
        return queryOne(FIND_BY_ID, ps -> ps.setInt(1, id), this::mapRow);
    }

    @Override
    public List<Course> findAll() throws DatabaseException {
        return queryList(FIND_ALL, StatementBinder.NONE, this::mapRow);
    }

    @Override
    public Optional<Course> findByCode(String courseCode) throws DatabaseException {
        return queryOne(FIND_BY_CODE, ps -> ps.setString(1, courseCode), this::mapRow);
    }

    private Course mapRow(ResultSet rs) throws SQLException {
        return new Course(
                rs.getInt("course_id"),
                rs.getString("course_code"),
                rs.getString("course_name"),
                rs.getInt("credits"),
                CourseType.valueOf(rs.getString("course_type")),
                rs.getInt("hours_per_week"),
                rs.getInt("semester"),
                rs.getString("dept_code"),
                rs.getString("faculty_name"));
    }
}
