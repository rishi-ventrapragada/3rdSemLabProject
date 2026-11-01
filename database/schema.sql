-- =============================================================================
-- Smart Campus & Academic Suite :: DBMS Lab
-- schema.sql -- 3NF tables, keys and constraints for smart_campus_db
--
-- Run order: schema.sql -> views_triggers.sql -> seed_data.sql
--   python database/init_db.py           (recommended; reads the repo-root .env)
--   mysql> source database/schema.sql    (manual, from the repo root)
--
-- Re-runnable: every table is dropped (children first) and recreated, so running
-- this file ERASES all domain data. Django's own tables (auth_*, django_*) are
-- never touched. Dropping a table also drops its triggers, so re-run
-- views_triggers.sql afterwards.
--
-- Requires MySQL 8.0.16+ (CHECK constraints are enforced from that version).
-- =============================================================================

CREATE DATABASE IF NOT EXISTS smart_campus_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE smart_campus_db;

-- Children before parents, so foreign keys never block a drop.
DROP TABLE IF EXISTS marks_audit;
DROP TABLE IF EXISTS timetable_entries;
DROP TABLE IF EXISTS marks;
DROP TABLE IF EXISTS attendance_records;
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS faculty;
DROP TABLE IF EXISTS time_slots;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS departments;


-- -----------------------------------------------------------------------------
-- Reference data
-- -----------------------------------------------------------------------------

CREATE TABLE departments (
    dept_id     INT          NOT NULL AUTO_INCREMENT,
    dept_code   VARCHAR(10)  NOT NULL,
    dept_name   VARCHAR(100) NOT NULL,
    CONSTRAINT pk_departments PRIMARY KEY (dept_id),
    CONSTRAINT uq_departments_dept_code UNIQUE (dept_code),
    CONSTRAINT uq_departments_dept_name UNIQUE (dept_name),
    -- REGEXP_LIKE(..., 'c'): plain REGEXP follows the column's case-insensitive collation,
    -- so '^[A-Z]' would also accept lower-case letters.
    CONSTRAINT chk_departments_dept_code CHECK (REGEXP_LIKE(dept_code, '^[A-Z]{2,10}$', 'c'))
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE rooms (
    room_id      INT                      NOT NULL AUTO_INCREMENT,
    room_number  VARCHAR(20)              NOT NULL,
    capacity     SMALLINT                 NOT NULL,
    room_type    ENUM ('LECTURE', 'LAB')  NOT NULL,
    CONSTRAINT pk_rooms PRIMARY KEY (room_id),
    CONSTRAINT uq_rooms_room_number UNIQUE (room_number),
    CONSTRAINT chk_rooms_capacity CHECK (capacity BETWEEN 1 AND 500)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE time_slots (
    slot_id      INT                                        NOT NULL AUTO_INCREMENT,
    day_of_week  ENUM ('MON', 'TUE', 'WED', 'THU', 'FRI')   NOT NULL,
    start_time   TIME                                       NOT NULL,
    end_time     TIME                                       NOT NULL,
    slot_number  TINYINT                                    NOT NULL,
    CONSTRAINT pk_time_slots PRIMARY KEY (slot_id),
    CONSTRAINT uq_time_slots_day_slot UNIQUE (day_of_week, slot_number),
    CONSTRAINT uq_time_slots_day_start UNIQUE (day_of_week, start_time),
    CONSTRAINT chk_time_slots_order CHECK (end_time > start_time),
    CONSTRAINT chk_time_slots_slot_number CHECK (slot_number BETWEEN 1 AND 10)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- People
--
-- username links a row to its Django login: auth_user.username = username.
-- There is deliberately no FK to auth_user, so this schema and the seed data
-- stay self-contained for the DBMS Lab and the Java engine. The pattern below
-- matches Django's username rules (ASCII subset). views_triggers.sql adds
-- triggers that keep a username from existing in both students and faculty.
-- -----------------------------------------------------------------------------

CREATE TABLE faculty (
    faculty_id     INT           NOT NULL AUTO_INCREMENT,
    employee_code  VARCHAR(20)   NOT NULL,
    username       VARCHAR(150)  NOT NULL,
    full_name      VARCHAR(100)  NOT NULL,
    email          VARCHAR(254)  NOT NULL,
    designation    VARCHAR(50)   NOT NULL,
    dept_id        INT           NOT NULL,
    CONSTRAINT pk_faculty PRIMARY KEY (faculty_id),
    CONSTRAINT uq_faculty_employee_code UNIQUE (employee_code),
    CONSTRAINT uq_faculty_username UNIQUE (username),
    CONSTRAINT uq_faculty_email UNIQUE (email),
    CONSTRAINT fk_faculty_departments FOREIGN KEY (dept_id)
        REFERENCES departments (dept_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_faculty_username CHECK (username REGEXP '^[A-Za-z0-9.@+_-]+$'),
    CONSTRAINT chk_faculty_email CHECK (email LIKE '_%@_%._%'),
    CONSTRAINT chk_faculty_designation CHECK (designation IN (
        'Professor', 'Associate Professor', 'Assistant Professor', 'Lecturer'))
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- cgpa and is_defaulter are stored on purpose (see docs/database_design.md):
--   cgpa         official cumulative GPA, which includes earlier semesters that are
--                not in this database, so it cannot be derived here.
--                v_student_cgpa_report shows it next to the GPA computed from marks.
--   is_defaulter the declared detention status, set by sp_refresh_defaulter_flags()
--                at the attendance cut-off. v_defaulter_list is the live figure.
CREATE TABLE students (
    student_id    INT           NOT NULL AUTO_INCREMENT,
    roll_number   VARCHAR(20)   NOT NULL,
    username      VARCHAR(150)  NOT NULL,
    full_name     VARCHAR(100)  NOT NULL,
    email         VARCHAR(254)  NOT NULL,
    semester      TINYINT       NOT NULL,
    section       CHAR(1)       NOT NULL,
    dept_id       INT           NOT NULL,
    cgpa          DECIMAL(4, 2) NOT NULL DEFAULT 0.00,
    is_defaulter  BOOLEAN       NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_students PRIMARY KEY (student_id),
    CONSTRAINT uq_students_roll_number UNIQUE (roll_number),
    CONSTRAINT uq_students_username UNIQUE (username),
    CONSTRAINT uq_students_email UNIQUE (email),
    CONSTRAINT fk_students_departments FOREIGN KEY (dept_id)
        REFERENCES departments (dept_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_students_username CHECK (username REGEXP '^[A-Za-z0-9.@+_-]+$'),
    CONSTRAINT chk_students_email CHECK (email LIKE '_%@_%._%'),
    CONSTRAINT chk_students_semester CHECK (semester BETWEEN 1 AND 8),
    CONSTRAINT chk_students_section CHECK (REGEXP_LIKE(section, '^[A-Z]$', 'c')),  -- 'c' = case-sensitive
    CONSTRAINT chk_students_cgpa CHECK (cgpa BETWEEN 0.00 AND 10.00)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- Academics
-- -----------------------------------------------------------------------------

-- faculty_id is nullable: a course can exist before a teacher is assigned,
-- and becomes unassigned (not deleted) if its faculty member is removed.
CREATE TABLE courses (
    course_id       INT                      NOT NULL AUTO_INCREMENT,
    course_code     VARCHAR(10)              NOT NULL,
    course_name     VARCHAR(100)             NOT NULL,
    credits         TINYINT                  NOT NULL,
    course_type     ENUM ('THEORY', 'LAB')   NOT NULL,
    hours_per_week  TINYINT                  NOT NULL,
    semester        TINYINT                  NOT NULL,
    dept_id         INT                      NOT NULL,
    faculty_id      INT                      NULL,
    CONSTRAINT pk_courses PRIMARY KEY (course_id),
    CONSTRAINT uq_courses_course_code UNIQUE (course_code),
    CONSTRAINT fk_courses_departments FOREIGN KEY (dept_id)
        REFERENCES departments (dept_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_courses_faculty FOREIGN KEY (faculty_id)
        REFERENCES faculty (faculty_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_courses_credits CHECK (credits BETWEEN 1 AND 6),
    CONSTRAINT chk_courses_hours CHECK (hours_per_week BETWEEN 1 AND 10),
    CONSTRAINT chk_courses_semester CHECK (semester BETWEEN 1 AND 8)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- An enrollment cannot exist without its student (CASCADE); a course with
-- enrollments cannot be deleted (RESTRICT).
CREATE TABLE enrollments (
    enrollment_id  INT      NOT NULL AUTO_INCREMENT,
    student_id     INT      NOT NULL,
    course_id      INT      NOT NULL,
    academic_year  CHAR(7)  NOT NULL,
    CONSTRAINT pk_enrollments PRIMARY KEY (enrollment_id),
    CONSTRAINT uq_enrollments_student_course UNIQUE (student_id, course_id),
    CONSTRAINT fk_enrollments_students FOREIGN KEY (student_id)
        REFERENCES students (student_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_enrollments_courses FOREIGN KEY (course_id)
        REFERENCES courses (course_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_enrollments_academic_year CHECK (academic_year REGEXP '^[0-9]{4}-[0-9]{2}$')
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- One record per enrollment per day. Classes run Monday to Friday only
-- (DAYOFWEEK: 1 = Sunday ... 7 = Saturday).
CREATE TABLE attendance_records (
    attendance_id  INT                         NOT NULL AUTO_INCREMENT,
    enrollment_id  INT                         NOT NULL,
    session_date   DATE                        NOT NULL,
    status         ENUM ('PRESENT', 'ABSENT')  NOT NULL,
    CONSTRAINT pk_attendance_records PRIMARY KEY (attendance_id),
    CONSTRAINT uq_attendance_records_enrollment_date UNIQUE (enrollment_id, session_date),
    CONSTRAINT fk_attendance_records_enrollments FOREIGN KEY (enrollment_id)
        REFERENCES enrollments (enrollment_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_attendance_records_weekday CHECK (DAYOFWEEK(session_date) BETWEEN 2 AND 6)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Internal (continuous assessment) is out of 40 and external (end-semester exam)
-- out of 60, so the total is out of 100. external_marks stays NULL until the exam
-- is graded. total_marks, grade_points and letter_grade are written only by the
-- trg_marks_before_* triggers (views_triggers.sql); never set them directly.
CREATE TABLE marks (
    mark_id         INT            NOT NULL AUTO_INCREMENT,
    enrollment_id   INT            NOT NULL,
    internal_marks  DECIMAL(5, 2)  NOT NULL,
    external_marks  DECIMAL(5, 2)  NULL,
    total_marks     DECIMAL(5, 2)  NULL,
    grade_points    INT            NULL,
    letter_grade    VARCHAR(2)     NULL,
    CONSTRAINT pk_marks PRIMARY KEY (mark_id),
    CONSTRAINT uq_marks_enrollment UNIQUE (enrollment_id),
    CONSTRAINT fk_marks_enrollments FOREIGN KEY (enrollment_id)
        REFERENCES enrollments (enrollment_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_marks_internal CHECK (internal_marks BETWEEN 0 AND 40),
    CONSTRAINT chk_marks_external CHECK (external_marks BETWEEN 0 AND 60),
    CONSTRAINT chk_marks_total CHECK (total_marks BETWEEN 0 AND 100),
    CONSTRAINT chk_marks_grade_points CHECK (grade_points IN (0, 5, 6, 7, 8, 9, 10)),
    CONSTRAINT chk_marks_letter_grade CHECK (letter_grade IN ('O', 'A+', 'A', 'B+', 'B', 'P', 'F'))
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- A room hosts one class per slot, and a section attends one class per slot.
-- A faculty member teaching one class per slot is enforced by the
-- trg_prevent_timetable_faculty_clash* triggers, because that rule spans two tables.
CREATE TABLE timetable_entries (
    entry_id   INT      NOT NULL AUTO_INCREMENT,
    course_id  INT      NOT NULL,
    room_id    INT      NOT NULL,
    slot_id    INT      NOT NULL,
    section    CHAR(1)  NOT NULL,
    CONSTRAINT pk_timetable_entries PRIMARY KEY (entry_id),
    CONSTRAINT uq_timetable_entries_room_slot UNIQUE (room_id, slot_id),
    CONSTRAINT uq_timetable_entries_slot_section UNIQUE (slot_id, section),
    CONSTRAINT fk_timetable_entries_courses FOREIGN KEY (course_id)
        REFERENCES courses (course_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_timetable_entries_rooms FOREIGN KEY (room_id)
        REFERENCES rooms (room_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_timetable_entries_time_slots FOREIGN KEY (slot_id)
        REFERENCES time_slots (slot_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_timetable_entries_section CHECK (REGEXP_LIKE(section, '^[A-Z]$', 'c'))  -- 'c' = case-sensitive
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- Audit trail
-- -----------------------------------------------------------------------------

-- One row per change to a student's marks, written only by trg_marks_after_update
-- (views_triggers.sql). It deliberately has NO foreign key to marks, because the history
-- must outlive a deleted marks row. Only the raw marks are kept: the grades are derived
-- from them in v_marks_audit through fn_grade_points / fn_letter_grade, which keeps this
-- table in 3NF. changed_at is UTC (UTC_TIMESTAMP()), like every timestamp in this project.
CREATE TABLE marks_audit (
    audit_id      INT            NOT NULL AUTO_INCREMENT,
    mark_id       INT            NOT NULL,
    old_internal  DECIMAL(5, 2)  NULL,
    new_internal  DECIMAL(5, 2)  NULL,
    old_external  DECIMAL(5, 2)  NULL,
    new_external  DECIMAL(5, 2)  NULL,
    changed_at    DATETIME       NOT NULL,
    CONSTRAINT pk_marks_audit PRIMARY KEY (audit_id),
    INDEX idx_marks_audit_mark (mark_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
