package com.smartcampus.dao;

import com.smartcampus.config.ConnectionFactory;
import com.smartcampus.exceptions.DatabaseException;
import com.smartcampus.models.AttendanceRecord;
import com.smartcampus.models.AttendanceStatus;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public class JdbcAttendanceRecordDao extends JdbcDaoSupport implements AttendanceRecordDao {

    private static final String FIND_BY_ID = """
            SELECT attendance_id, enrollment_id, session_date, status
            FROM attendance_records
            WHERE attendance_id = ?""";

    private static final String FIND_BY_ENROLLMENT = """
            SELECT attendance_id, enrollment_id, session_date, status
            FROM attendance_records
            WHERE enrollment_id = ?
            ORDER BY session_date""";

    private static final String FIND_ALL = """
            SELECT attendance_id, enrollment_id, session_date, status
            FROM attendance_records
            ORDER BY enrollment_id, session_date""";

    public JdbcAttendanceRecordDao(ConnectionFactory connections) {
        super(connections);
    }

    @Override
    public Optional<AttendanceRecord> findById(Integer id) throws DatabaseException {
        return queryOne(FIND_BY_ID, ps -> ps.setInt(1, id), this::mapRow);
    }

    @Override
    public List<AttendanceRecord> findAll() throws DatabaseException {
        return queryList(FIND_ALL, StatementBinder.NONE, this::mapRow);
    }

    @Override
    public List<AttendanceRecord> findByEnrollmentId(int enrollmentId) throws DatabaseException {
        return queryList(FIND_BY_ENROLLMENT, ps -> ps.setInt(1, enrollmentId), this::mapRow);
    }

    private AttendanceRecord mapRow(ResultSet rs) throws SQLException {
        return new AttendanceRecord(
                rs.getInt("attendance_id"),
                rs.getInt("enrollment_id"),
                rs.getObject("session_date", LocalDate.class),
                AttendanceStatus.valueOf(rs.getString("status")));
    }
}
