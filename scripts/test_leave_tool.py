from app.tools.leave_tools import (
    get_leave_balance,
    calculate_working_days,
    check_leave_availability,
    is_loss_of_pay
)

print("=" * 50)
print("Leave Tool Test")
print("=" * 50)

print(get_leave_balance("EMP001"))
print()

print(calculate_working_days(
    "2026-08-13",
    "2026-08-18"
))
print()

print(check_leave_availability(
    "EMP001",
    "Annual",
    3
))
print()

print(is_loss_of_pay("INT001"))