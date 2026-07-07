from datetime import datetime, timedelta

from strands import tool

from app.services.dynamodb_service import db
from app.tools.holiday_tools import is_holiday, is_weekend

@tool
def get_leave_balance(employee_id: str):
    """
    Get leave balance of an employee.
    """

    balance = db.get_leave_balance(employee_id)

    if balance is None:
        return {
            "success": False,
            "message": "Leave balance not found."
        }

    annual_remaining = (
        int(balance["annual_total"])
        - int(balance["annual_used"])
    )

    casual_remaining = (
        int(balance["casual_total"])
        - int(balance["casual_used"])
    )

    sick_remaining = (
        int(balance["sick_total"])
        - int(balance["sick_used"])
    )

    return {
        "success": True,
        "annual_remaining": annual_remaining,
        "casual_remaining": casual_remaining,
        "sick_remaining": sick_remaining
    }
    
@tool
def calculate_working_days(start_date: str, end_date: str):
    """
    Calculate actual leave days excluding
    weekends and holidays.
    """

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    calendar_days = (end - start).days + 1

    working_days = 0
    holidays = []

    current = start

    while current <= end:

        date = current.strftime("%Y-%m-%d")

        # Check holiday first
        holiday = is_holiday(date)

        if holiday["is_holiday"]:
            holidays.append(date)
            current += timedelta(days=1)
            continue

        # Then check weekend
        if is_weekend(date)["is_weekend"]:
            current += timedelta(days=1)
            continue

        # Count as working leave day
        working_days += 1

        current += timedelta(days=1)

    return {
        "calendar_days": calendar_days,
        "working_days": working_days,
        "holiday_count": len(holidays),
        "holidays": holidays
    }
@tool
def check_leave_availability(
    employee_id: str,
    leave_type: str,
    required_days: int
):
    """
    Check if enough leave balance exists.
    """

    balance = get_leave_balance(employee_id)

    if not balance["success"]:
        return balance

    remaining = {

        "annual": balance["annual_remaining"],

        "casual": balance["casual_remaining"],

        "sick": balance["sick_remaining"]

    }

    available = remaining.get(leave_type.lower(), 0)

    if available >= required_days:

        return {

            "approved": True,

            "remaining": available

        }

    return {

        "approved": False,

        "remaining": available

    }
@tool
def is_loss_of_pay(employee_id: str):
    """
    Returns whether employee falls under
    Loss Of Pay policy.
    """

    employee = db.get_employee(employee_id)

    if employee["employment_type"] == "Intern":

        return {

            "loss_of_pay": True

        }

    return {

        "loss_of_pay": False

    }
@tool
def get_leave_status(employee_id: str):
    """
    Retrieve the latest leave request status for an employee.
    """

    status = db.get_latest_leave_status(employee_id)

    if status is None:
        return {
            "status": "employee_not_found"
        }

    return status
            