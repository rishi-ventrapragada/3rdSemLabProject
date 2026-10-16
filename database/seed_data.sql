-- =============================================================================
-- Smart Campus & Academic Suite :: DBMS Lab
-- seed_data.sql -- demo data: 3rd-semester CSE, academic year 2026-27
--
-- Run after schema.sql and views_triggers.sql. Re-runnable: existing domain rows
-- are deleted first (children before parents). The WHERE clauses keep MySQL
-- Workbench's safe-update mode happy.
--
-- Contents: 2 departments, 5 rooms, 20 time slots (4 per weekday), 5 faculty,
-- 10 students in sections A and B, 6 courses (2 theory + 4 labs), 60 enrollments,
-- 12 weeks of attendance per enrollment, marks for every enrollment, and a
-- clash-free 20-entry timetable.
--
-- Login accounts are NOT created here (Django hashes passwords). Create Django
-- users whose username matches students.username / faculty.username.
-- =============================================================================

USE smart_campus_db;

DELETE FROM timetable_entries  WHERE entry_id > 0;
DELETE FROM marks              WHERE mark_id > 0;
DELETE FROM attendance_records WHERE attendance_id > 0;
DELETE FROM enrollments        WHERE enrollment_id > 0;
DELETE FROM courses            WHERE course_id > 0;
DELETE FROM students           WHERE student_id > 0;
DELETE FROM faculty            WHERE faculty_id > 0;
DELETE FROM time_slots         WHERE slot_id > 0;
DELETE FROM rooms              WHERE room_id > 0;
DELETE FROM departments        WHERE dept_id > 0;


-- -----------------------------------------------------------------------------
-- Reference data
-- -----------------------------------------------------------------------------

INSERT INTO departments (dept_id, dept_code, dept_name) VALUES
    (1, 'CSE',  'Computer Science and Engineering'),
    (2, 'MATH', 'Mathematics');

INSERT INTO rooms (room_id, room_number, capacity, room_type) VALUES
    (1, 'CS-101', 66, 'LECTURE'),
    (2, 'CS-102', 66, 'LECTURE'),
    (3, 'CS-103', 40, 'LECTURE'),
    (4, 'LAB-1',  36, 'LAB'),
    (5, 'LAB-2',  36, 'LAB');

-- Slots 1-3 are one-hour lectures; slot 4 is the two-hour afternoon lab block.
-- slot_id = (day index * 4) + slot_number, so MON = 1-4, TUE = 5-8, ... FRI = 17-20.
INSERT INTO time_slots (slot_id, day_of_week, start_time, end_time, slot_number) VALUES
    ( 1, 'MON', '09:00', '10:00', 1), ( 2, 'MON', '10:00', '11:00', 2),
    ( 3, 'MON', '11:15', '12:15', 3), ( 4, 'MON', '14:00', '16:00', 4),
    ( 5, 'TUE', '09:00', '10:00', 1), ( 6, 'TUE', '10:00', '11:00', 2),
    ( 7, 'TUE', '11:15', '12:15', 3), ( 8, 'TUE', '14:00', '16:00', 4),
    ( 9, 'WED', '09:00', '10:00', 1), (10, 'WED', '10:00', '11:00', 2),
    (11, 'WED', '11:15', '12:15', 3), (12, 'WED', '14:00', '16:00', 4),
    (13, 'THU', '09:00', '10:00', 1), (14, 'THU', '10:00', '11:00', 2),
    (15, 'THU', '11:15', '12:15', 3), (16, 'THU', '14:00', '16:00', 4),
    (17, 'FRI', '09:00', '10:00', 1), (18, 'FRI', '10:00', '11:00', 2),
    (19, 'FRI', '11:15', '12:15', 3), (20, 'FRI', '14:00', '16:00', 4);


-- -----------------------------------------------------------------------------
-- People
-- -----------------------------------------------------------------------------

INSERT INTO faculty (faculty_id, employee_code, username, full_name, email, designation, dept_id) VALUES
    (1, 'FAC101', 'ananya.rao',  'Ananya Rao',  'ananya.rao@smartcampus.example',  'Professor',           1),
    (2, 'FAC102', 'kiran.kumar', 'Kiran Kumar', 'kiran.kumar@smartcampus.example', 'Associate Professor', 1),
    (3, 'FAC103', 'meera.iyer',  'Meera Iyer',  'meera.iyer@smartcampus.example',  'Assistant Professor', 1),
    (4, 'FAC104', 'arjun.reddy', 'Arjun Reddy', 'arjun.reddy@smartcampus.example', 'Assistant Professor', 1),
    (5, 'FAC201', 'suresh.babu', 'Suresh Babu', 'suresh.babu@smartcampus.example', 'Professor',           2);

-- 2025 batch, now in semester 3. cgpa is the official CGPA after semesters 1-2.
-- Student usernames are the lower-case roll number.
INSERT INTO students (student_id, roll_number, username, full_name, email, semester, section, dept_id, cgpa) VALUES
    ( 1, '25CSE001', '25cse001', 'Aarav Sharma',     '25cse001@smartcampus.example', 3, 'A', 1, 8.45),
    ( 2, '25CSE002', '25cse002', 'Diya Patel',       '25cse002@smartcampus.example', 3, 'A', 1, 9.12),
    ( 3, '25CSE003', '25cse003', 'Rohan Verma',      '25cse003@smartcampus.example', 3, 'A', 1, 7.38),
    ( 4, '25CSE004', '25cse004', 'Sneha Reddy',      '25cse004@smartcampus.example', 3, 'A', 1, 6.85),
    ( 5, '25CSE005', '25cse005', 'Vikram Singh',     '25cse005@smartcampus.example', 3, 'A', 1, 8.02),
    ( 6, '25CSE006', '25cse006', 'Ishita Gupta',     '25cse006@smartcampus.example', 3, 'B', 1, 9.31),
    ( 7, '25CSE007', '25cse007', 'Karthik Nair',     '25cse007@smartcampus.example', 3, 'B', 1, 7.76),
    ( 8, '25CSE008', '25cse008', 'Priya Menon',      '25cse008@smartcampus.example', 3, 'B', 1, 8.67),
    ( 9, '25CSE009', '25cse009', 'Rahul Joshi',      '25cse009@smartcampus.example', 3, 'B', 1, 6.42),
    (10, '25CSE010', '25cse010', 'Meghana Krishnan', '25cse010@smartcampus.example', 3, 'B', 1, 7.95);


-- -----------------------------------------------------------------------------
-- Courses (semester 3). Theory: 3 credits, 3 one-hour lectures a week.
-- Labs: 2 credits, one 2-hour block a week.
-- -----------------------------------------------------------------------------

INSERT INTO courses (course_id, course_code, course_name, credits, course_type, hours_per_week, semester, dept_id, faculty_id) VALUES
    (1, 'CS301', 'Database Management Systems', 3, 'THEORY', 3, 3, 1, 1),
    (2, 'MA301', 'Discrete Mathematics',        3, 'THEORY', 3, 3, 2, 5),
    (3, 'CS351', 'DBMS Lab',                    2, 'LAB',    2, 3, 1, 2),
    (4, 'CS352', 'Java Programming Lab',        2, 'LAB',    2, 3, 1, 3),
    (5, 'CS353', 'Django Web Development Lab',  2, 'LAB',    2, 3, 1, 4),
    (6, 'CS354', 'Software Engineering Lab',    2, 'LAB',    2, 3, 1, 2);


-- -----------------------------------------------------------------------------
-- Enrollments: every student takes every course offered in their semester.
-- -----------------------------------------------------------------------------

INSERT INTO enrollments (student_id, course_id, academic_year)
SELECT s.student_id, c.course_id, '2026-27'
FROM students s
    JOIN courses c ON c.semester = s.semester
ORDER BY s.student_id, c.course_id;


-- -----------------------------------------------------------------------------
-- Attendance: 12 weekly sessions per enrollment, starting Monday 2026-07-20.
-- Each course meets on a fixed weekday (course 1 Mon, 2 Tue, ... 5 Fri, 6 Mon).
--   * Baseline: about 1 absence in 10, i.e. at most 2 of 12 (>= 83.33%).
--   * Sneha Reddy (student 4) misses every 3rd week: below 75% in all 6 courses.
--   * Rahul Joshi (student 9) misses every 2nd week of Discrete Mathematics and
--     Java Programming Lab: below 75% in those 2 courses.
-- -----------------------------------------------------------------------------

INSERT INTO attendance_records (enrollment_id, session_date, status)
WITH RECURSIVE weeks (k) AS (
    SELECT 1
    UNION ALL
    SELECT k + 1 FROM weeks WHERE k < 12
)
SELECT
    e.enrollment_id,
    DATE_ADD('2026-07-20', INTERVAL (w.k - 1) * 7 + MOD(e.course_id - 1, 5) DAY),
    CASE
        WHEN e.student_id = 4 AND MOD(w.k, 3) = 0                     THEN 'ABSENT'
        WHEN e.student_id = 9 AND e.course_id IN (2, 4) AND MOD(w.k, 2) = 0 THEN 'ABSENT'
        WHEN MOD(e.student_id * 7 + e.course_id * 3 + w.k, 10) = 0    THEN 'ABSENT'
        ELSE 'PRESENT'
    END
FROM enrollments e
    CROSS JOIN weeks w
ORDER BY e.enrollment_id, w.k;


-- -----------------------------------------------------------------------------
-- Marks: internal out of 40, external out of 60. Only these two columns are
-- inserted; trg_marks_before_insert fills total_marks, grade_points and letter_grade.
-- Values come from a fixed formula (internal 24-39, external 18-58) plus two
-- hand-set results: a fail for Rahul Joshi in Discrete Mathematics and a bare
-- pass for Sneha Reddy in DBMS.
-- -----------------------------------------------------------------------------

INSERT INTO marks (enrollment_id, internal_marks, external_marks)
SELECT
    e.enrollment_id,
    CASE
        WHEN e.student_id = 9 AND e.course_id = 2 THEN 14.00
        WHEN e.student_id = 4 AND e.course_id = 1 THEN 18.00
        ELSE 24 + MOD(e.student_id * 7 + e.course_id * 5, 16)
    END,
    CASE
        WHEN e.student_id = 9 AND e.course_id = 2 THEN 18.00
        WHEN e.student_id = 4 AND e.course_id = 1 THEN 24.50
        ELSE 18 + MOD(e.student_id * 13 + e.course_id * 11, 41)
    END
FROM enrollments e
ORDER BY e.enrollment_id;


-- -----------------------------------------------------------------------------
-- Timetable: section A uses CS-101 and LAB-1, section B uses CS-102 and LAB-2.
-- Each section has 3 lectures per theory course and 1 lab block per lab course.
-- Shared teachers are never double-booked (trg_prevent_timetable_faculty_clash
-- rejects any insert that would be).
-- -----------------------------------------------------------------------------

INSERT INTO timetable_entries (entry_id, course_id, room_id, slot_id, section) VALUES
    -- Section A
    ( 1, 1, 1,  1, 'A'),  -- MON 09:00  CS301 DBMS               CS-101
    ( 2, 2, 1,  2, 'A'),  -- MON 10:00  MA301 Discrete Maths     CS-101
    ( 3, 3, 4,  4, 'A'),  -- MON 14:00  CS351 DBMS Lab           LAB-1
    ( 4, 2, 1,  5, 'A'),  -- TUE 09:00  MA301 Discrete Maths     CS-101
    ( 5, 1, 1,  6, 'A'),  -- TUE 10:00  CS301 DBMS               CS-101
    ( 6, 4, 4,  8, 'A'),  -- TUE 14:00  CS352 Java Lab           LAB-1
    ( 7, 1, 1,  9, 'A'),  -- WED 09:00  CS301 DBMS               CS-101
    ( 8, 2, 1, 11, 'A'),  -- WED 11:15  MA301 Discrete Maths     CS-101
    ( 9, 5, 4, 12, 'A'),  -- WED 14:00  CS353 Django Lab         LAB-1
    (10, 6, 4, 16, 'A'),  -- THU 14:00  CS354 SE Lab             LAB-1
    -- Section B
    (11, 2, 2,  1, 'B'),  -- MON 09:00  MA301 Discrete Maths     CS-102
    (12, 1, 2,  2, 'B'),  -- MON 10:00  CS301 DBMS               CS-102
    (13, 4, 5,  4, 'B'),  -- MON 14:00  CS352 Java Lab           LAB-2
    (14, 1, 2,  5, 'B'),  -- TUE 09:00  CS301 DBMS               CS-102
    (15, 2, 2,  6, 'B'),  -- TUE 10:00  MA301 Discrete Maths     CS-102
    (16, 5, 5,  8, 'B'),  -- TUE 14:00  CS353 Django Lab         LAB-2
    (17, 2, 2,  9, 'B'),  -- WED 09:00  MA301 Discrete Maths     CS-102
    (18, 1, 2, 11, 'B'),  -- WED 11:15  CS301 DBMS               CS-102
    (19, 3, 5, 12, 'B'),  -- WED 14:00  CS351 DBMS Lab           LAB-2
    (20, 6, 5, 20, 'B');  -- FRI 14:00  CS354 SE Lab             LAB-2


-- -----------------------------------------------------------------------------
-- Attendance cut-off: declare the defaulters (sets students.is_defaulter).
-- -----------------------------------------------------------------------------

CALL sp_refresh_defaulter_flags();
