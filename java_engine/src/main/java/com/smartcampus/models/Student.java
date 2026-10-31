package com.smartcampus.models;

import java.math.BigDecimal;

/** A row of {@code students}. */
public class Student extends Person {

    private static final BigDecimal MAX_CGPA = BigDecimal.TEN;

    private final String rollNumber;
    private final int semester;
    private final char section;
    private BigDecimal cgpa;
    private boolean defaulter;

    public Student(int id, String rollNumber, String username, String fullName, String email, String deptCode,
                   int semester, char section, BigDecimal cgpa, boolean defaulter) {
        super(id, username, fullName, email, deptCode);
        this.rollNumber = requireText(rollNumber, "rollNumber");
        if (semester < 1 || semester > 8) {
            throw new IllegalArgumentException("semester must be 1-8, got " + semester);
        }
        if (section < 'A' || section > 'Z') {
            throw new IllegalArgumentException("section must be a capital letter, got " + section);
        }
        this.semester = semester;
        this.section = section;
        setCgpa(cgpa);
        this.defaulter = defaulter;
    }

    @Override
    public String getRole() {
        return "Student";
    }

    @Override
    public String getIdentifier() {
        return rollNumber;
    }

    @Override
    public String describe() {
        return super.describe() + ", semester " + semester + " section " + section
                + ", CGPA " + cgpa + (defaulter ? ", DEFAULTER" : "");
    }

    public String getRollNumber() {
        return rollNumber;
    }

    public int getSemester() {
        return semester;
    }

    public char getSection() {
        return section;
    }

    public BigDecimal getCgpa() {
        return cgpa;
    }

    /** Official CGPA, 0.00 to 10.00 (mirrors {@code chk_students_cgpa}). */
    public final void setCgpa(BigDecimal cgpa) {
        if (cgpa == null || cgpa.signum() < 0 || cgpa.compareTo(MAX_CGPA) > 0) {
            throw new IllegalArgumentException("cgpa must be between 0.00 and 10.00, got " + cgpa);
        }
        this.cgpa = cgpa;
    }

    /** The declared detention status, set by {@code sp_refresh_defaulter_flags()}. */
    public boolean isDefaulter() {
        return defaulter;
    }

    public void setDefaulter(boolean defaulter) {
        this.defaulter = defaulter;
    }
}
