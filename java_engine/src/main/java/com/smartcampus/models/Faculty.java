package com.smartcampus.models;

/** A row of {@code faculty}. */
public class Faculty extends Person {

    private final String employeeCode;
    private final String designation;

    public Faculty(int id, String employeeCode, String username, String fullName, String email, String deptCode,
                   String designation) {
        super(id, username, fullName, email, deptCode);
        this.employeeCode = requireText(employeeCode, "employeeCode");
        this.designation = requireText(designation, "designation");
    }

    @Override
    public String getRole() {
        return "Faculty";
    }

    @Override
    public String getIdentifier() {
        return employeeCode;
    }

    @Override
    public String describe() {
        return super.describe() + ", " + designation;
    }

    public String getEmployeeCode() {
        return employeeCode;
    }

    public String getDesignation() {
        return designation;
    }
}
