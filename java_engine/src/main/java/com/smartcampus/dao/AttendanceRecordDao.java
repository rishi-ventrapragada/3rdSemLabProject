package com.smartcampus.dao;

import com.smartcampus.exceptions.DatabaseException;
import com.smartcampus.models.AttendanceRecord;

import java.util.List;

public interface AttendanceRecordDao extends CrudDao<AttendanceRecord, Integer> {

    /** Session-by-session attendance for one enrollment, oldest first. */
    List<AttendanceRecord> findByEnrollmentId(int enrollmentId) throws DatabaseException;

    @Override
    default String entityName() {
        return "AttendanceRecord";
    }
}
