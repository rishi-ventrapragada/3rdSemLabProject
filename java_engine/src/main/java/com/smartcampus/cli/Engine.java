package com.smartcampus.cli;

import com.smartcampus.config.ConnectionFactory;
import com.smartcampus.config.DatabaseConfig;
import com.smartcampus.dao.JdbcAttendanceRecordDao;
import com.smartcampus.dao.JdbcCourseDao;
import com.smartcampus.dao.JdbcEnrollmentDao;
import com.smartcampus.dao.JdbcFacultyDao;
import com.smartcampus.dao.JdbcMarksDao;
import com.smartcampus.dao.JdbcReportDao;
import com.smartcampus.dao.JdbcStudentDao;
import com.smartcampus.dao.StudentDao;
import com.smartcampus.exceptions.ValidationException;
import com.smartcampus.services.ReportExporter;
import com.smartcampus.services.ReportService;
import com.smartcampus.services.StudentService;

/**
 * Wires config -> DAOs -> services. Built lazily, so {@code help} and usage errors never need
 * a database or a {@code .env}. This is the only place that names the JDBC implementations.
 */
final class Engine {

    private StudentService studentService;
    private ReportService reportService;
    private ReportExporter reportExporter;

    StudentService students() throws ValidationException {
        wire();
        return studentService;
    }

    ReportService reports() throws ValidationException {
        wire();
        return reportService;
    }

    ReportExporter exporter() throws ValidationException {
        wire();
        return reportExporter;
    }

    private void wire() throws ValidationException {
        if (studentService != null) {
            return;
        }
        ConnectionFactory connections = new ConnectionFactory(DatabaseConfig.load());
        StudentDao studentDao = new JdbcStudentDao(connections);
        JdbcReportDao reportDao = new JdbcReportDao(connections);
        studentService = new StudentService(studentDao, new JdbcFacultyDao(connections),
                new JdbcCourseDao(connections), new JdbcEnrollmentDao(connections), new JdbcMarksDao(connections),
                new JdbcAttendanceRecordDao(connections), reportDao);
        reportService = new ReportService(reportDao, studentDao);
        reportExporter = new ReportExporter(reportDao);
    }
}
