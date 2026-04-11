*** Core Tables & Data Flow *** 

Organization
    → PayrollSchedule
        → PayrollPeriod
            → PayrollEntry
    → Employee


- Organization → stores company/firm information
Basic company details (type, name)

- Employee → stores individual employee data
Personal info: first_name, last_name, SIN (Social Insurance Number), email, address

- PayrollPeriod → represents a payroll cycle
Start/end dates and status (draft/finalized)

- PayrollEntry → stores individual payroll records for an employee per period

    Hours: regular_hours, overtime_hours
    Rates: hourly_rate, overtime_rate
    Earnings: bonus, vacation
    Deductions: CPP, EI, tax
    Calculated totals: gross, total_deduction, net

- T4Record → tax year summary per employee
    Aggregates annual employment income, CPP contributions, EI premiums, income tax deducted
    Links to a CRA submission

- CRASubmission → bulk submission to Canada Revenue Agency
    Groups T4 records by tax year/business
    Stores XML content and submission status (draft/submitted/accepted/rejected)

Relationships

PayrollEntry uses (employee_id, payroll_period_id) to track hours/deductions per employee per pay period
T4Record aggregates PayrollEntry data annually per employee
CRASubmission bundles multiple T4Records for CRA filing
All tables include ten_id for multi-tenant data isolation


