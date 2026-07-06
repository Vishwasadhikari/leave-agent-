from datetime import datetime
import uuid

from strands import tool

from app.services.dynamodb_service import db
from app.services.ses_service import send_approval_email


@tool
def submit_leave(
    employee_id: str,
    manager_id: str,
    leave_type: str,
    start_date: str,
    end_date: str,
    calendar_days: int,
    working_days: int,
    reason: str
):
    print("\n========== SUBMIT DEBUG ==========")
    print("employee_id :", employee_id)
    print("manager_id  :", manager_id)
    print("leave_type  :", leave_type)
    print("start_date  :", start_date)
    print("end_date    :", end_date)
    print("calendar_days :", calendar_days)
    print("working_days  :", working_days)
    print("reason :", reason)
    print("==================================\n")

    request_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now().isoformat()

    employee = db.get_employee(employee_id)

    if employee is None:
        print("❌ Employee not found")
        return {
            "success": False,
            "status": "error",
            "message": "Employee not found."
        }

    manager = db.get_employee(manager_id)

    if manager is None:
        print("❌ Manager not found")
        return {
            "success": False,
            "status": "error",
            "message": "Manager not found."
        }

    print("✅ Employee validated")
    print("✅ Manager validated")

    leave_request = {
        "request_id": request_id,
        "employee_id": employee_id,
        "manager_id": manager_id,
        "leave_type": leave_type,
        "start_date": start_date,
        "end_date": end_date,
        "calendar_days": calendar_days,
        "working_days": working_days,
        "reason": reason,
        "status": "Pending",
        "created_at": timestamp,
        "updated_at": timestamp
    }

    try:
        db.create_leave_request(leave_request)
        print("✅ Leave request created")
    except Exception as e:
        print("❌ Error creating leave request:", e)
        return {
            "success": False,
            "status": "error",
            "message": f"Failed to create leave request: {str(e)}"
        }

    approval = {
        "request_id": request_id,
        "employee_id": employee_id,
        "manager_id": manager_id,
        "status": "Pending",
        "approved_by": "",
        "approved_at": "",
        "comments": "",
        "email_sent": False
    }

    try:
        db.create_approval_request(approval)
        print("✅ Approval record created")
    except Exception as e:
        print("❌ Error creating approval:", e)
        return {
            "success": False,
            "status": "error",
            "message": f"Failed to create approval record: {str(e)}"
        }

    approval_sent = False

    try:
        send_approval_email(
            manager_email=manager["email"],
            employee_name=employee["name"],
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            request_id=request_id
        )

        approval_sent = True
        print("✅ Email sent")

    except Exception as e:
        print("⚠️ Email failed:", e)

    print("✅ submit_leave() completed")

    return {
        "request_id": request_id,
        "status": "submitted",
        "approval_sent": approval_sent,
        "manager_id": manager_id,
        "message": "Leave request submitted successfully."
    }