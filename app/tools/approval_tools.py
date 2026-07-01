from datetime import datetime

from strands import tool

from app.services.dynamodb_service import db

@tool
def get_pending_requests():
    """
    Return all pending approvals.
    """

    pending = db.get_pending_approvals()

    return {
        "success": True,
        "requests": pending
    }
    
@tool
def approve_leave(
    request_id: str,
    manager_id: str,
    comments: str = "Approved"
):
    """
    Approve a leave request.
    """

    db.update_approval(
        request_id=request_id,
        status="Approved",
        approved_by=manager_id,
        comments=comments,
        approved_at=datetime.now().isoformat()
    )

    db.update_leave_request_status(
        request_id,
        "Approved"
    )

    return {
        "success": True,
        "message": "Leave Approved"
    }    
    
@tool
def reject_leave(
    request_id: str,
    manager_id: str,
    comments: str = "Rejected"
):
    """
    Reject a leave request.
    """

    db.update_approval(
        request_id=request_id,
        status="Rejected",
        approved_by=manager_id,
        comments=comments,
        approved_at=datetime.now().isoformat()
    )

    db.update_leave_request_status(
        request_id,
        "Rejected"
    )

    return {
        "success": True,
        "message": "Leave Rejected"
    }
    
        