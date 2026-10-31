package com.smartcampus.dao;

import com.smartcampus.config.ConnectionFactory;
import com.smartcampus.exceptions.DatabaseException;
import com.smartcampus.models.AttendanceSummary;
import com.smartcampus.models.GpaReportRow;

import java.sql.CallableStatement;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;

public class JdbcReportDao extends JdbcDaoSupport implements ReportDao {

    private static final String ALL_ATTENDANCE = """
            SELECT enrollment_id, student_id, roll_number, full_name, semester, section, course_id,
                   course_code, course_name, academic_year, total_classes, classes_attended, attendance_percentage
            FROM v_attendance_summary
            ORDER BY roll_number, course_code""";

    private static final String ATTENDANCE_BY_STUDENT = """
            SELECT enrollment_id, student_id, roll_number, full_name, semester, section, course_id,
                   course_code, course_name, academic_year, total_classes, classes_attended, attendance_percentage
            FROM v_attendance_summary
            WHERE student_id = ?
            ORDER BY course_code""";

    private static final String DEFAULTERS = """
            SELECT enrollment_id, student_id, roll_number, full_name, semester, section, course_id,
                   course_code, course_name, academic_year, total_classes, classes_attended, attendance_percentage
            FROM v_defaulter_list
            ORDER BY roll_number, course_code""";

    private static final String GPA_REPORT = """
            SELECT student_id, roll_number, full_name, dept_code, semester, section, courses_graded,
                   credits_graded, credits_earned, weighted_gpa, cgpa
            FROM v_student_cgpa_report
            ORDER BY roll_number""";

    private static final String REFRESH_DEFAULTERS = "{call sp_refresh_defaulter_flags()}";

    private static final String COUNT_DEFAULTERS = "SELECT COUNT(*) FROM students WHERE is_defaulter = TRUE";

    public JdbcReportDao(ConnectionFactory connections) {
        super(connections);
    }

    @Override
    public List<AttendanceSummary> findAllAttendance() throws DatabaseException {
        return queryList(ALL_ATTENDANCE, StatementBinder.NONE, this::mapAttendance);
    }

    @Override
    public List<AttendanceSummary> findAttendanceByStudentId(int studentId) throws DatabaseException {
        return queryList(ATTENDANCE_BY_STUDENT, ps -> ps.setInt(1, studentId), this::mapAttendance);
    }

    @Override
    public List<AttendanceSummary> findDefaulters() throws DatabaseException {
        return queryList(DEFAULTERS, StatementBinder.NONE, this::mapAttendance);
    }

    @Override
    public List<GpaReportRow> findGpaReport() throws DatabaseException {
        return queryList(GPA_REPORT, StatementBinder.NONE, this::mapGpaRow);
    }

    @Override
    public int refreshDefaulterFlags() throws DatabaseException {
        try (Connection conn = openConnection()) {
            conn.setAutoCommit(false);
            try (CallableStatement call = conn.prepareCall(REFRESH_DEFAULTERS);
                 PreparedStatement count = conn.prepareStatement(COUNT_DEFAULTERS)) {
                call.execute();
                int flagged;
                try (ResultSet rs = count.executeQuery()) {
                    rs.next();
                    flagged = rs.getInt(1);
                }
                conn.commit();
                return flagged;
            } catch (SQLException e) {
                conn.rollback();
                throw e;
            }
        } catch (SQLException e) {
            throw new DatabaseException("Could not refresh defaulter flags", e);
        }
    }

    private AttendanceSummary mapAttendance(ResultSet rs) throws SQLException {
        return new AttendanceSummary(
                rs.getInt("enrollment_id"),
                rs.getInt("student_id"),
                rs.getString("roll_number"),
                rs.getString("full_name"),
                rs.getInt("semester"),
                rs.getString("section"),
                rs.getInt("course_id"),
                rs.getString("course_code"),
                rs.getString("course_name"),
                rs.getString("academic_year"),
                rs.getInt("total_classes"),
                rs.getInt("classes_attended"),
                rs.getBigDecimal("attendance_percentage"));
    }

    private GpaReportRow mapGpaRow(ResultSet rs) throws SQLException {
        return new GpaReportRow(
                rs.getInt("student_id"),
                rs.getString("roll_number"),
                rs.getString("full_name"),
                rs.getString("dept_code"),
                rs.getInt("semester"),
                rs.getString("section"),
                rs.getInt("courses_graded"),
                rs.getInt("credits_graded"),
                rs.getInt("credits_earned"),
                rs.getBigDecimal("weighted_gpa"),
                rs.getBigDecimal("cgpa"));
    }
}
