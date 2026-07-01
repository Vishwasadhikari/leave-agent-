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
    """
    Submit a leave request.
    """

    request_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"

    timestamp = datetime.now().isoformat()

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

    # Save Leave Request
    db.create_leave_request(leave_request)

    # Save Approval Request
    db.create_approval_request(approval)

    # Get Employee Details
    employee = db.get_employee(employee_id)

    # Get Manager Details
    manager = db.get_employee(manager_id)

    # Send Approval Email
    send_approval_email(

        manager_email=manager["email"],

        employee_name=employee["name"],

        leave_type=leave_type,

        start_date=start_date,

        end_date=end_date,

        reason=reason,

        request_id=request_id

    )

    return {

        "success": True,

        "request_id": request_id,

        "message": "Leave request submitted successfully and approval email sent."

    }