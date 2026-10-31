package com.smartcampus.dao;

import com.smartcampus.config.ConnectionFactory;
import com.smartcampus.exceptions.DatabaseException;
import com.smartcampus.models.Marks;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;
import java.util.Optional;

public class JdbcMarksDao extends JdbcDaoSupport implements MarksDao {

    private static final String FIND_BY_ID = """
            SELECT mark_id, enrollment_id, internal_marks, external_marks, total_marks, grade_points, letter_grade
            FROM marks
            WHERE mark_id = ?""";

    private static final String FIND_BY_STUDENT = """
            SELECT m.mark_id, m.enrollment_id, m.internal_marks, m.external_marks, m.total_marks,
                   m.grade_points, m.letter_grade
            FROM marks m
                JOIN enrollments e ON e.enrollment_id = m.enrollment_id
            WHERE e.student_id = ?
            ORDER BY e.course_id""";

    private static final String FIND_ALL = """
            SELECT mark_id, enrollment_id, internal_marks, external_marks, total_marks, grade_points, letter_grade
            FROM marks
            ORDER BY mark_id""";

    public JdbcMarksDao(ConnectionFactory connections) {
        super(connections);
    }

    @Override
    public Optional<Marks> findById(Integer id) throws DatabaseException {
        return queryOne(FIND_BY_ID, ps -> ps.setInt(1, id), this::mapRow);
    }

    @Override
    public List<Marks> findAll() throws DatabaseException {
        return queryList(FIND_ALL, StatementBinder.NONE, this::mapRow);
    }

    @Override
    public List<Marks> findByStudentId(int studentId) throws DatabaseException {
        return queryList(FIND_BY_STUDENT, ps -> ps.setInt(1, studentId), this::mapRow);
    }

    private Marks mapRow(ResultSet rs) throws SQLException {
        return new Marks(
                rs.getInt("mark_id"),
                rs.getInt("enrollment_id"),
                rs.getBigDecimal("internal_marks"),
                rs.getBigDecimal("external_marks"),
                rs.getBigDecimal("total_marks"),
                rs.getObject("grade_points", Integer.class),
                rs.getString("letter_grade"));
    }
}
