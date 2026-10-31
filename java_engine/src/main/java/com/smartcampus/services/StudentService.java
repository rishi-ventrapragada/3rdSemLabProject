package com.smartcampus.services;

import com.smartcampus.dao.AttendanceRecordDao;
import com.smartcampus.dao.CourseDao;
import com.smartcampus.dao.EnrollmentDao;
import com.smartcampus.dao.FacultyDao;
import com.smartcampus.dao.MarksDao;
import com.smartcampus.dao.ReportDao;
import com.smartcampus.dao.StudentDao;
import com.smartcampus.exceptions.DatabaseException;
import com.smartcampus.exceptions.DuplicateEnrollmentException;
import com.smartcampus.exceptions.EntityNotFoundException;
import com.smartcampus.exceptions.SmartCampusException;
import com.smartcampus.exceptions.ValidationException;
import com.smartcampus.models.AttendanceRecord;
import com.smartcampus.models.Course;
import com.smartcampus.models.CourseStanding;
import com.smartcampus.models.Enrollment;
import com.smartcampus.models.EnrollmentReceipt;
import com.smartcampus.models.Faculty;
import com.smartcampus.models.Marks;
import com.smartcampus.models.Person;
import com.smartcampus.models.SessionHistory;
import com.smartcampus.models.Student;
import com.smartcampus.models.StudentProfile;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * Student-facing operations: look-ups, the profile, session history and enrolling.
 * Depends only on DAO interfaces.
 */
public class StudentService {

    private final StudentDao students;
    private final FacultyDao faculty;
    private final CourseDao courses;
    private final EnrollmentDao enrollments;
    private final MarksDao marks;
    private final AttendanceRecordDao attendanceRecords;
    private final ReportDao reports;

    public StudentService(StudentDao students, FacultyDao faculty, CourseDao courses, EnrollmentDao enrollments,
                          MarksDao marks, AttendanceRecordDao attendanceRecords, ReportDao reports) {
        this.students = students;
        this.faculty = faculty;
        this.courses = courses;
        this.enrollments = enrollments;
        this.marks = marks;
        this.attendanceRecords = attendanceRecords;
        this.reports = reports;
    }

    public Student getStudent(String rollNumber) throws SmartCampusException {
        return students.getByRollNumber(rollNumber.strip());
    }

    /**
     * Resolves a login username to its person, the way Django will (CLAUDE.md, "Linking Django
     * logins to people"). The database guarantees a username is never both a student and a faculty
     * member, so the order of the two look-ups does not matter.
     */
    public Person findPersonByUsername(String username) throws SmartCampusException {
        String key = username.strip();
        Optional<Student> student = students.findByUsername(key);
        if (student.isPresent()) {
            return student.get();
        }
        Optional<Faculty> teacher = faculty.findByUsername(key);
        if (teacher.isPresent()) {
            return teacher.get();
        }
        throw new EntityNotFoundException("Person", key);
    }

    /** The student plus, for every enrolled course, attendance (from the view) and marks. */
    public StudentProfile getProfile(String rollNumber) throws SmartCampusException {
        Student student = getStudent(rollNumber);
        Map<Integer, Marks> marksByEnrollment = marks.findByStudentId(student.getId()).stream()
                .collect(Collectors.toMap(Marks::getEnrollmentId, Function.identity()));
        List<CourseStanding> standings = reports.findAttendanceByStudentId(student.getId()).stream()
                .map(summary -> new CourseStanding(summary, marksByEnrollment.get(summary.enrollmentId())))
                .toList();
        return new StudentProfile(student, standings);
    }

    /** Every recorded session of one course for one student, oldest first. */
    public SessionHistory getSessionHistory(String rollNumber, String courseCode) throws SmartCampusException {
        Student student = getStudent(rollNumber);
        Course course = courses.getByCode(courseCode.strip());
        Enrollment enrollment = enrollments.findByStudentId(student.getId()).stream()
                .filter(e -> e.getCourseId() == course.getId())
                .findFirst()
                .orElseThrow(() -> new EntityNotFoundException("Enrollment",
                        student.getRollNumber() + " in " + course.getCode()));
        List<AttendanceRecord> sessions = attendanceRecords.findByEnrollmentId(enrollment.getId());
        return new SessionHistory(student, course, sessions);
    }

    /**
     * Enrolls a student in a course.
     *
     * <p>App-level rule (not enforced by the database; see docs/database_design.md): a student may
     * only enroll in courses offered in their current semester. Duplicate enrollments are left to
     * the database's {@code uq_enrollments_student_course}; the academic-year format to
     * {@code chk_enrollments_academic_year}.
     */
    public EnrollmentReceipt enroll(String rollNumber, String courseCode, String academicYear)
            throws SmartCampusException {
        Student student = getStudent(rollNumber);
        Course course = courses.getByCode(courseCode.strip());
        if (course.getSemester() != student.getSemester()) {
            throw new ValidationException(course.getCode() + " is a semester " + course.getSemester()
                    + " course, but " + student.getRollNumber() + " is in semester " + student.getSemester());
        }
        try {
            Enrollment saved = enrollments.insert(
                    Enrollment.unsaved(student.getId(), course.getId(), academicYear.strip()));
            return new EnrollmentReceipt(saved, student, course);
        } catch (DuplicateEnrollmentException e) {
            throw new DuplicateEnrollmentException(student.getRollNumber(), course.getCode(), e.getCause());
        }
    }

    /** Every course, for listing what can be enrolled in. */
    public List<Course> listCourses() throws DatabaseException {
        return courses.findAll();
    }
}
