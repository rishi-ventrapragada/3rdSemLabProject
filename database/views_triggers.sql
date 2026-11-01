-- =============================================================================
-- Smart Campus & Academic Suite :: DBMS Lab
-- views_triggers.sql -- stored functions, views, triggers and procedures
--
-- Run after schema.sql and before seed_data.sql. Re-runnable: every object is
-- dropped or replaced before it is created.
--
-- The trigger, function and procedure bodies contain ';', so they are wrapped in
-- DELIMITER $$ ... $$ for the mysql client. init_db.py understands DELIMITER too.
-- =============================================================================

USE smart_campus_db;


-- -----------------------------------------------------------------------------
-- Grading scale (total marks out of 100), shared by both marks triggers
--   >= 90 -> 10 O | >= 80 -> 9 A+ | >= 70 -> 8 A | >= 60 -> 7 B+
--   >= 50 ->  6 B | >= 40 -> 5 P  |  < 40 -> 0 F
-- -----------------------------------------------------------------------------

DROP FUNCTION IF EXISTS fn_grade_points;
DROP FUNCTION IF EXISTS fn_letter_grade;

DELIMITER $$

CREATE FUNCTION fn_grade_points(p_total DECIMAL(5, 2))
    RETURNS INT
    DETERMINISTIC
    NO SQL
BEGIN
    RETURN CASE
        WHEN p_total IS NULL THEN NULL
        WHEN p_total >= 90 THEN 10
        WHEN p_total >= 80 THEN 9
        WHEN p_total >= 70 THEN 8
        WHEN p_total >= 60 THEN 7
        WHEN p_total >= 50 THEN 6
        WHEN p_total >= 40 THEN 5
        ELSE 0
    END;
END$$

CREATE FUNCTION fn_letter_grade(p_grade_points INT)
    RETURNS VARCHAR(2)
    DETERMINISTIC
    NO SQL
BEGIN
    RETURN CASE p_grade_points
        WHEN 10 THEN 'O'
        WHEN 9 THEN 'A+'
        WHEN 8 THEN 'A'
        WHEN 7 THEN 'B+'
        WHEN 6 THEN 'B'
        WHEN 5 THEN 'P'
        WHEN 0 THEN 'F'
        ELSE NULL
    END;
END$$

DELIMITER ;


-- -----------------------------------------------------------------------------
-- Views
-- -----------------------------------------------------------------------------

-- One row per enrollment (student x course). enrollment_id is the unique key,
-- so Django's unmanaged model uses it as primary_key. Enrollments without any
-- attendance yet show 0 classes and a NULL percentage.
CREATE OR REPLACE VIEW v_attendance_summary AS
SELECT
    e.enrollment_id,
    s.student_id,
    s.roll_number,
    s.full_name,
    s.semester,
    s.section,
    c.course_id,
    c.course_code,
    c.course_name,
    e.academic_year,
    COUNT(a.attendance_id)                                 AS total_classes,
    CAST(COALESCE(SUM(a.status = 'PRESENT'), 0) AS UNSIGNED) AS classes_attended,
    CAST(
        CASE
            WHEN COUNT(a.attendance_id) = 0 THEN NULL
            ELSE ROUND(100 * SUM(a.status = 'PRESENT') / COUNT(a.attendance_id), 2)
        END AS DECIMAL(5, 2)
    )                                                      AS attendance_percentage
FROM enrollments e
    JOIN students s ON s.student_id = e.student_id
    JOIN courses c ON c.course_id = e.course_id
    LEFT JOIN attendance_records a ON a.enrollment_id = e.enrollment_id
GROUP BY
    e.enrollment_id, s.student_id, s.roll_number, s.full_name, s.semester, s.section,
    c.course_id, c.course_code, c.course_name, e.academic_year;

-- Student-course pairs below the 75% attendance requirement.
CREATE OR REPLACE VIEW v_defaulter_list AS
SELECT
    enrollment_id,
    student_id,
    roll_number,
    full_name,
    semester,
    section,
    course_id,
    course_code,
    course_name,
    academic_year,
    total_classes,
    classes_attended,
    attendance_percentage
FROM v_attendance_summary
WHERE attendance_percentage < 75.00;

-- Credit-weighted GPA from graded marks: SUM(grade_points * credits) / SUM(credits),
-- shown next to the stored official cgpa. Marks still awaiting external marks
-- (grade_points IS NULL) are left out. Students without graded marks get NULL.
CREATE OR REPLACE VIEW v_student_cgpa_report AS
SELECT
    s.student_id,
    s.roll_number,
    s.full_name,
    d.dept_code,
    s.semester,
    s.section,
    COUNT(m.mark_id)                                                        AS courses_graded,
    CAST(COALESCE(SUM(CASE WHEN m.mark_id IS NOT NULL THEN c.credits END), 0) AS UNSIGNED)
                                                                            AS credits_graded,
    CAST(COALESCE(SUM(CASE WHEN m.grade_points > 0 THEN c.credits END), 0) AS UNSIGNED)
                                                                            AS credits_earned,
    CAST(
        ROUND(
            SUM(m.grade_points * c.credits)
                / NULLIF(SUM(CASE WHEN m.mark_id IS NOT NULL THEN c.credits END), 0),
            2
        ) AS DECIMAL(4, 2)
    )                                                                       AS weighted_gpa,
    s.cgpa
FROM students s
    JOIN departments d ON d.dept_id = s.dept_id
    LEFT JOIN enrollments e ON e.student_id = s.student_id
    LEFT JOIN courses c ON c.course_id = e.course_id
    LEFT JOIN marks m ON m.enrollment_id = e.enrollment_id AND m.grade_points IS NOT NULL
GROUP BY s.student_id, s.roll_number, s.full_name, d.dept_code, s.semester, s.section, s.cgpa;

-- Readable marks history. Grades are derived from the stored raw marks with the same
-- functions the marks triggers use, so the scale lives in one place. LEFT JOINs keep audit
-- rows whose marks/enrollment were deleted later; their student and course show as NULL.
CREATE OR REPLACE VIEW v_marks_audit AS
SELECT
    a.audit_id,
    a.mark_id,
    s.roll_number,
    s.full_name,
    c.course_code,
    c.course_name,
    a.old_internal,
    a.old_external,
    a.old_internal + a.old_external                                        AS old_total,
    fn_letter_grade(fn_grade_points(a.old_internal + a.old_external))      AS old_letter_grade,
    a.new_internal,
    a.new_external,
    a.new_internal + a.new_external                                        AS new_total,
    fn_letter_grade(fn_grade_points(a.new_internal + a.new_external))      AS new_letter_grade,
    a.changed_at
FROM marks_audit a
    LEFT JOIN marks m ON m.mark_id = a.mark_id
    LEFT JOIN enrollments e ON e.enrollment_id = m.enrollment_id
    LEFT JOIN students s ON s.student_id = e.student_id
    LEFT JOIN courses c ON c.course_id = e.course_id;


-- -----------------------------------------------------------------------------
-- Triggers
-- -----------------------------------------------------------------------------

DROP TRIGGER IF EXISTS trg_marks_before_insert;
DROP TRIGGER IF EXISTS trg_marks_before_update;
DROP TRIGGER IF EXISTS trg_marks_after_update;
DROP TRIGGER IF EXISTS trg_prevent_timetable_faculty_clash;
DROP TRIGGER IF EXISTS trg_prevent_timetable_faculty_clash_update;
DROP TRIGGER IF EXISTS trg_students_before_insert;
DROP TRIGGER IF EXISTS trg_students_before_update;
DROP TRIGGER IF EXISTS trg_faculty_before_insert;
DROP TRIGGER IF EXISTS trg_faculty_before_update;

DELIMITER $$

-- "trg_marks_before_save": MySQL triggers fire on exactly one event, so the
-- before-save logic is split into an INSERT and an UPDATE trigger. Both derive
-- total_marks, grade_points and letter_grade, overwriting any value the client
-- sent. While external_marks is NULL the three derived columns stay NULL.
CREATE TRIGGER trg_marks_before_insert
    BEFORE INSERT ON marks
    FOR EACH ROW
BEGIN
    SET NEW.total_marks = NEW.internal_marks + NEW.external_marks;
    SET NEW.grade_points = fn_grade_points(NEW.total_marks);
    SET NEW.letter_grade = fn_letter_grade(NEW.grade_points);
END$$

CREATE TRIGGER trg_marks_before_update
    BEFORE UPDATE ON marks
    FOR EACH ROW
BEGIN
    SET NEW.total_marks = NEW.internal_marks + NEW.external_marks;
    SET NEW.grade_points = fn_grade_points(NEW.total_marks);
    SET NEW.letter_grade = fn_letter_grade(NEW.grade_points);
END$$

-- Audit trail: an AFTER trigger, because it records a change that has already been
-- accepted (the BEFORE triggers and CHECKs ran first). Re-saving identical marks writes
-- nothing; <=> is MySQL's NULL-safe equality, needed because external_marks may be NULL.
CREATE TRIGGER trg_marks_after_update
    AFTER UPDATE ON marks
    FOR EACH ROW
BEGIN
    IF NOT (OLD.internal_marks <=> NEW.internal_marks AND OLD.external_marks <=> NEW.external_marks) THEN
        INSERT INTO marks_audit (mark_id, old_internal, new_internal, old_external, new_external, changed_at)
        VALUES (NEW.mark_id, OLD.internal_marks, NEW.internal_marks, OLD.external_marks, NEW.external_marks,
                UTC_TIMESTAMP());
    END IF;
END$$

-- A faculty member cannot teach two classes in the same time slot. The course's
-- faculty_id is looked up and compared with every class already in NEW.slot_id.
-- Courses without an assigned faculty member never clash.
CREATE TRIGGER trg_prevent_timetable_faculty_clash
    BEFORE INSERT ON timetable_entries
    FOR EACH ROW
BEGIN
    DECLARE v_faculty_id INT;
    DECLARE v_clash_course VARCHAR(10);
    DECLARE v_msg VARCHAR(255);

    SET v_faculty_id = (SELECT faculty_id FROM courses WHERE course_id = NEW.course_id);

    IF v_faculty_id IS NOT NULL THEN
        SET v_clash_course = (
            SELECT c.course_code
            FROM timetable_entries te
                JOIN courses c ON c.course_id = te.course_id
            WHERE te.slot_id = NEW.slot_id
              AND c.faculty_id = v_faculty_id
            LIMIT 1);

        IF v_clash_course IS NOT NULL THEN
            SET v_msg = CONCAT('Timetable clash: faculty_id ', v_faculty_id,
                               ' already teaches ', v_clash_course,
                               ' in slot_id ', NEW.slot_id);
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_msg;
        END IF;
    END IF;
END$$

-- Same rule for edits, so moving an entry cannot create a clash. The row being
-- updated is excluded from the comparison.
CREATE TRIGGER trg_prevent_timetable_faculty_clash_update
    BEFORE UPDATE ON timetable_entries
    FOR EACH ROW
BEGIN
    DECLARE v_faculty_id INT;
    DECLARE v_clash_course VARCHAR(10);
    DECLARE v_msg VARCHAR(255);

    SET v_faculty_id = (SELECT faculty_id FROM courses WHERE course_id = NEW.course_id);

    IF v_faculty_id IS NOT NULL THEN
        SET v_clash_course = (
            SELECT c.course_code
            FROM timetable_entries te
                JOIN courses c ON c.course_id = te.course_id
            WHERE te.slot_id = NEW.slot_id
              AND c.faculty_id = v_faculty_id
              AND te.entry_id <> OLD.entry_id
            LIMIT 1);

        IF v_clash_course IS NOT NULL THEN
            SET v_msg = CONCAT('Timetable clash: faculty_id ', v_faculty_id,
                               ' already teaches ', v_clash_course,
                               ' in slot_id ', NEW.slot_id);
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_msg;
        END IF;
    END IF;
END$$

-- Django maps a login to a person by username, so a username must be unique
-- across students AND faculty. UNIQUE covers each table and these four triggers
-- cover the pair.
CREATE TRIGGER trg_students_before_insert
    BEFORE INSERT ON students
    FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1 FROM faculty WHERE username = NEW.username) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Username is already used by a faculty member';
    END IF;
END$$

CREATE TRIGGER trg_students_before_update
    BEFORE UPDATE ON students
    FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1 FROM faculty WHERE username = NEW.username) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Username is already used by a faculty member';
    END IF;
END$$

CREATE TRIGGER trg_faculty_before_insert
    BEFORE INSERT ON faculty
    FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1 FROM students WHERE username = NEW.username) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Username is already used by a student';
    END IF;
END$$

CREATE TRIGGER trg_faculty_before_update
    BEFORE UPDATE ON faculty
    FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1 FROM students WHERE username = NEW.username) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Username is already used by a student';
    END IF;
END$$

DELIMITER ;


-- -----------------------------------------------------------------------------
-- Procedures
-- -----------------------------------------------------------------------------

DROP PROCEDURE IF EXISTS sp_refresh_defaulter_flags;

DELIMITER $$

-- Declares the defaulter list: sets students.is_defaulter to TRUE for every
-- student below 75% in at least one course, and FALSE for everyone else.
-- Run it at the attendance cut-off (seed_data.sql calls it once). The DISTINCT
-- derived table is materialised, which lets the UPDATE read v_defaulter_list
-- even though that view also reads students.
CREATE PROCEDURE sp_refresh_defaulter_flags()
BEGIN
    UPDATE students s
        LEFT JOIN (SELECT DISTINCT student_id FROM v_defaulter_list) d
            ON d.student_id = s.student_id
    SET s.is_defaulter = (d.student_id IS NOT NULL)
    WHERE s.student_id > 0;
END$$

DELIMITER ;
