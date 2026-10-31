package com.smartcampus.dao;

import com.smartcampus.exceptions.DatabaseException;
import com.smartcampus.models.AttendanceSummary;
import com.smartcampus.models.GpaReportRow;

import java.util.List;

/**
 * Read access to the reporting views and the defaulter procedure in {@code views_triggers.sql}.
 * The percentages, the 75% threshold and the weighted GPA are all computed by MySQL; this DAO
 * only reads them.
 */
public interface ReportDao {

    /** {@code v_attendance_summary} for every enrollment. */
    List<AttendanceSummary> findAllAttendance() throws DatabaseException;

    /** {@code v_attendance_summary} rows for one student, ordered by course code. */
    List<AttendanceSummary> findAttendanceByStudentId(int studentId) throws DatabaseException;

    /** {@code v_defaulter_list}: student-course pairs below 75%. */
    List<AttendanceSummary> findDefaulters() throws DatabaseException;

    /** {@code v_student_cgpa_report} for every student. */
    List<GpaReportRow> findGpaReport() throws DatabaseException;

    /**
     * Calls {@code sp_refresh_defaulter_flags()} and returns how many students are now flagged.
     * Both steps run in one transaction.
     */
    int refreshDefaulterFlags() throws DatabaseException;
}
