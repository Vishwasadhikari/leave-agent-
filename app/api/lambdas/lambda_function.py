import boto3
from datetime import datetime

dynamodb = boto3.resource(
    "dynamodb",
    region_name="eu-north-1"
)

leave_requests = dynamodb.Table("LeaveRequests")
approval_queue = dynamodb.Table("ApprovalQueue")
leave_balances = dynamodb.Table("LeaveBalances")

MANAGER_ID = "MGR001"

def get_leave_request(request_id):

    response = leave_requests.get_item(
        Key={
            "request_id": request_id
        }
    )

    return response.get("Item")


def update_leave_request(request_id, status):

    leave_requests.update_item(

        Key={
            "request_id": request_id
        },

        UpdateExpression="SET #s = :status",

        ExpressionAttributeNames={
            "#s": "status"
        },

        ExpressionAttributeValues={
            ":status": status
        }
    )


def update_approval(
    request_id,
    status,
    approved_by=MANAGER_ID,
    comments=""
):

    approval_queue.update_item(

        Key={
            "request_id": request_id
        },

        UpdateExpression="""
        SET
        #s = :status,
        approved_by = :approved_by,
        approved_at = :approved_at,
        comments = :comments
        """,

        ExpressionAttributeNames={
            "#s": "status"
        },

        ExpressionAttributeValues={
            ":status": status,
            ":approved_by": approved_by,
            ":approved_at": datetime.now().isoformat(),
            ":comments": comments
        }
    )

    


def update_leave_balance(employee_id, leave_type, working_days):
    """
    Update the used leave count after approval.
    """

    field = f"{leave_type.lower()}_used"

    leave_balances.update_item(

        Key={
            "employee_id": employee_id
        },

        UpdateExpression=f"SET {field} = {field} + :days",

        ExpressionAttributeValues={
            ":days": working_days
        }
    )


def lambda_handler(event, context):

    params = event.get("queryStringParameters", {})

    action = params.get("action")
    request_id = params.get("request_id")

    if not action or not request_id:
        return {
            "statusCode": 400,
            "body": "Missing action or request_id"
        }

    if action not in ["approve", "reject"]:
        return {
            "statusCode": 400,
            "body": "Invalid action"
        }

    leave_request = get_leave_request(request_id)

    if leave_request is None:
        return {
            "statusCode": 404,
            "body": "Leave request not found."
        }

    if action == "approve":

        update_leave_request(request_id, "Approved")
        update_approval(
        request_id=request_id,
        status="Approved",
        approved_by="MGR001",
        comments="Approved via Email"
)

        update_leave_balance(
            employee_id=leave_request["employee_id"],
            leave_type=leave_request["leave_type"],
            working_days=leave_request["working_days"]
        )

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/html"
            },
            "body": """
            <html>
                <body style="font-family: Arial; text-align:center; margin-top:50px;">
                    <h1>✅ Leave Approved</h1>
                    <h2>The leave request has been approved successfully.</h2>
                </body>
            </html>
            """
        }

    elif action == "reject":

        update_leave_request(request_id, "Rejected")
        update_approval(
        request_id=request_id,
        status="Rejected",
        approved_by="MGR001",
        comments="Rejected via Email"
)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/html"
            },
            "body": """
            <html>
                <body style="font-family: Arial; text-align:center; margin-top:50px;">
                    <h1>❌ Leave Rejected</h1>
                    <h2>The leave request has been rejected.</h2>
                </body>
            </html>
            """
        }