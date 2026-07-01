from app.tools.employee_tools import (
    get_employee,
    validate_employee,
    get_manager
)

print("=" * 50)
print("Employee Tool Test")
print("=" * 50)

print(get_employee("EMP001"))
print()

print(validate_employee("EMP001"))
print()

print(get_manager("EMP001"))