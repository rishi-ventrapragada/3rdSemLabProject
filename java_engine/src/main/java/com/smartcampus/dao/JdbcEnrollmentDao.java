package com.smartcampus.dao;

import com.smartcampus.config.ConnectionFactory;
import com.smartcampus.exceptions.DatabaseException;
import com.smartcampus.exceptions.DuplicateEnrollmentException;
import com.smartcampus.exceptions.ValidationException;
import com.smartcampus.models.Enrollment;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.List;
import java.util.Optional;

public class JdbcEnrollmentDao extends JdbcDaoSupport implements EnrollmentDao {

    /** MySQL ER_DUP_ENTRY. */
    static final int DUPLICATE_KEY = 1062;
    /** MySQL ER_CHECK_CONSTRAINT_VIOLATED. */
    static final int CHECK_VIOLATED = 3819;

    private static final String FIND_BY_ID = """
            SELECT enrollment_id, student_id, course_id, academic_year
            FROM enrollments
            WHERE enrollment_id = ?""";

    private static final String FIND_BY_STUDENT = """
            SELECT enrollment_id, student_id, course_id, academic_year
            FROM enrollments
            WHERE student_id = ?
            ORDER BY course_id""";

    private static final String FIND_ALL = """
            SELECT enrollment_id, student_id, course_id, academic_year
            FROM enrollments
            ORDER BY enrollment_id""";

    private static final String INSERT = """
            INSERT INTO enrollments (student_id, course_id, academic_year)
            VALUES (?, ?, ?)""";

    public JdbcEnrollmentDao(ConnectionFactory connections) {
        super(connections);
    }

    @Override
    public Optional<Enrollment> findById(Integer id) throws DatabaseException {
        return queryOne(FIND_BY_ID, ps -> ps.setInt(1, id), this::mapRow);
    }

    @Override
    public List<Enrollment> findAll() throws DatabaseException {
        return queryList(FIND_ALL, StatementBinder.NONE, this::mapRow);
    }

    @Override
    public List<Enrollment> findByStudentId(int studentId) throws DatabaseException {
        return queryList(FIND_BY_STUDENT, ps -> ps.setInt(1, studentId), this::mapRow);
    }

    @Override
    public Enrollment insert(Enrollment enrollment)
            throws DuplicateEnrollmentException, ValidationException, DatabaseException {
        if (enrollment.isSaved()) {
            throw new IllegalArgumentException("Enrollment is already saved: " + enrollment);
        }
        try (Connection conn = openConnection();
             PreparedStatement ps = conn.prepareStatement(INSERT, Statement.RETURN_GENERATED_KEYS)) {
            ps.setInt(1, enrollment.getStudentId());
            ps.setInt(2, enrollment.getCourseId());
            ps.setString(3, enrollment.getAcademicYear());
            ps.executeUpdate();
            try (ResultSet keys = ps.getGeneratedKeys()) {
                if (!keys.next()) {
                    throw new DatabaseException("INSERT INTO enrollments returned no generated key");
                }
                return enrollment.withId(keys.getInt(1));
            }
        } catch (SQLException e) {
            if (e.getErrorCode() == DUPLICATE_KEY) {
                throw new DuplicateEnrollmentException("student_id=" + enrollment.getStudentId(),
                        "course_id=" + enrollment.getCourseId(), e);
            }
            if (e.getErrorCode() == CHECK_VIOLATED) {
                throw new ValidationException("Rejected by the database: " + e.getMessage()
                        + " (academic year must look like 2026-27)", e);
            }
            throw new DatabaseException("Could not insert enrollment", e);
        }
    }

    private Enrollment mapRow(ResultSet rs) throws SQLException {
        return new Enrollment(
                rs.getInt("enrollment_id"),
                rs.getInt("student_id"),
                rs.getInt("course_id"),
                rs.getString("academic_year"));
    }
}
