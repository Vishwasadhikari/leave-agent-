from app.services.dynamodb_service import db


print("=" * 50)
print("Testing DynamoDB Service")
print("=" * 50)


# ----------------------------
# Employee Test
# ----------------------------
employee = db.get_employee("EMP001")

print("\nEmployee Details")
print(employee)


# ----------------------------
# Leave Balance Test
# ----------------------------
balance = db.get_leave_balance("EMP001")

print("\nLeave Balance")
print(balance)


# ----------------------------
# Holiday Test
# ----------------------------
holidays = db.get_all_holidays()

print("\nTotal Holidays :", len(holidays))

print("\nFirst Holiday")

print(holidays[0])