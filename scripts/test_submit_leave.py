from app.tools.leave_submission_tool import submit_leave

response = submit_leave(
    employee_id="EMP001",
    manager_id="MGR001",
    leave_type="annual",
    start_date="2026-07-10",
    end_date="2026-07-12",
    calendar_days=3,
    working_days=3,
    reason="Family Function"
)

print(response)