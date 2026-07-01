from app.tools.leave_submission_tool import submit_leave

print("=" * 60)
print("Leave Submission Test")
print("=" * 60)

response = submit_leave(
    employee_id="EMP001",
    manager_id="MGR001",
    leave_type="Annual",
    start_date="2026-07-10",
    end_date="2026-07-13",
    calendar_days=4,
    working_days=2,
    reason="Family Function"
)

print(response)