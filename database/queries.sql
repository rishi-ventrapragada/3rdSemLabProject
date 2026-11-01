-- =============================================================================
-- Smart Campus & Academic Suite :: DBMS Lab
-- queries.sql -- worked example queries for lab demonstrations
--
-- Read-only except section 12, which runs inside a transaction and rolls back, and
-- section 13, which re-declares the same defaulters the seed already declared. Run after
-- init_db.py, from the repo root:
--   mysql -u root -p smart_campus_db   then   source database/queries.sql
-- Not part of init_db.py; it only demonstrates SQL features against the seed data.
-- =============================================================================

USE smart_campus_db;

-- 1. INNER JOIN (3 tables): every enrollment with student and course names.
SELECT s.roll_number, s.full_name, c.course_code, c.course_name, e.academic_year
FROM enrollments e
    JOIN students s ON s.student_id = e.student_id
    JOIN courses c ON c.course_id = e.course_id
ORDER BY s.roll_number, c.course_code
LIMIT 12;

-- 2. LEFT JOIN + COUNT: every course with its enrollment count, including courses nobody takes.
SELECT c.course_code, c.course_name, COUNT(e.enrollment_id) AS students
FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.course_id
GROUP BY c.course_id, c.course_code, c.course_name
ORDER BY c.course_code;

-- 3. GROUP BY ... HAVING: courses whose average attendance is below 88%.
SELECT course_code, course_name, ROUND(AVG(attendance_percentage), 2) AS avg_attendance
FROM v_attendance_summary
GROUP BY course_code, course_name
HAVING AVG(attendance_percentage) < 88
ORDER BY avg_attendance;

-- 4. Nested subquery: students whose official CGPA is above the average CGPA.
SELECT roll_number, full_name, cgpa
FROM students
WHERE cgpa > (SELECT AVG(cgpa) FROM students)
ORDER BY cgpa DESC;

-- 5. Correlated subquery: each student's best course by total marks.
SELECT s.roll_number, s.full_name, c.course_code, m.total_marks, m.letter_grade
FROM marks m
    JOIN enrollments e ON e.enrollment_id = m.enrollment_id
    JOIN students s ON s.student_id = e.student_id
    JOIN courses c ON c.course_id = e.course_id
WHERE m.total_marks = (
    SELECT MAX(m2.total_marks)
    FROM marks m2
        JOIN enrollments e2 ON e2.enrollment_id = m2.enrollment_id
    WHERE e2.student_id = e.student_id
)
ORDER BY s.roll_number;

-- 6. EXISTS / NOT EXISTS: faculty with and without a class on Friday.
SELECT f.full_name,
       CASE WHEN EXISTS (
           SELECT 1
           FROM timetable_entries te
               JOIN courses c ON c.course_id = te.course_id
               JOIN time_slots ts ON ts.slot_id = te.slot_id
           WHERE c.faculty_id = f.faculty_id AND ts.day_of_week = 'FRI'
       ) THEN 'teaches on Friday' ELSE 'free on Friday' END AS friday
FROM faculty f
ORDER BY f.full_name;

-- 7. UNION ALL: one list of every login name with its role (the Django login design).
SELECT username, full_name, 'Student' AS role FROM students
UNION ALL
SELECT username, full_name, 'Faculty' AS role FROM faculty
ORDER BY role, username;

-- 8. Self join: pairs of courses taught by the same teacher.
SELECT f.full_name, a.course_code AS course_1, b.course_code AS course_2
FROM courses a
    JOIN courses b ON b.faculty_id = a.faculty_id AND a.course_id < b.course_id
    JOIN faculty f ON f.faculty_id = a.faculty_id;

-- 9. Window functions (MySQL 8): rank students by weighted GPA, overall and within each section.
SELECT roll_number, full_name, section, weighted_gpa,
       RANK() OVER (ORDER BY weighted_gpa DESC)                       AS overall_rank,
       RANK() OVER (PARTITION BY section ORDER BY weighted_gpa DESC)  AS section_rank
FROM v_student_cgpa_report
ORDER BY overall_rank, roll_number;

-- 10. CASE bucketing on a view: how many enrollments fall in each attendance band.
SELECT CASE
           WHEN attendance_percentage >= 90 THEN '90-100%'
           WHEN attendance_percentage >= 75 THEN '75-89%'
           ELSE 'below 75% (defaulter)'
       END AS band,
       COUNT(*) AS enrollments
FROM v_attendance_summary
GROUP BY band
ORDER BY band;

-- 11. Stored functions directly: the grading scale at its boundaries.
SELECT t.total, fn_grade_points(t.total) AS grade_points, fn_letter_grade(fn_grade_points(t.total)) AS letter
FROM (SELECT 95 AS total UNION ALL SELECT 89.99 UNION ALL SELECT 60 UNION ALL SELECT 40 UNION ALL SELECT 39.99) t;

-- 12. Transaction: change a mark, watch both triggers act (BEFORE recomputes the grade,
--     AFTER writes the audit row), then ROLLBACK so nothing persists.
START TRANSACTION;
UPDATE marks m
    JOIN enrollments e ON e.enrollment_id = m.enrollment_id
    JOIN students s ON s.student_id = e.student_id
    JOIN courses c ON c.course_id = e.course_id
SET m.external_marks = 60
WHERE s.roll_number = '25CSE001' AND c.course_code = 'CS351';
SELECT roll_number, course_code, old_total, old_letter_grade, new_total, new_letter_grade
FROM v_marks_audit
ORDER BY audit_id DESC
LIMIT 1;
ROLLBACK;

-- 13. Stored procedure: declare the defaulter list, then read the flags it set.
CALL sp_refresh_defaulter_flags();
SELECT roll_number, full_name, is_defaulter FROM students WHERE is_defaulter = TRUE;
