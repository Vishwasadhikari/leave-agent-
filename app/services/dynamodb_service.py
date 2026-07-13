import boto3


from app.config import (
    AWS_REGION,
    EMPLOYEE_TABLE,
    LEAVE_BALANCE_TABLE,
    HOLIDAY_TABLE,
    LEAVE_REQUEST_TABLE,
    APPROVAL_TABLE,
)


class DynamoDBService:

    def __init__(self):

        self.dynamodb = boto3.resource(
            "dynamodb",
            region_name=AWS_REGION
        )

        self.employee_table = self.dynamodb.Table(EMPLOYEE_TABLE)
        self.leave_balance_table = self.dynamodb.Table(LEAVE_BALANCE_TABLE)
        self.holiday_table = self.dynamodb.Table(HOLIDAY_TABLE)
        self.leave_request_table = self.dynamodb.Table(LEAVE_REQUEST_TABLE)
        self.approval_table = self.dynamodb.Table(APPROVAL_TABLE)
        
            # Employee Methods

        
    def get_employee(self, employee_id):

        response = self.employee_table.get_item(
            Key={
                "employee_id": employee_id
            }
        )

        return response.get("Item")
    def get_employee_by_name(self, employee_name):
        response = self.employee_table.scan()
        print(response["Items"])
        for employee in response["Items"]:
            if employee["name"].strip().lower() == employee_name.strip().lower():
                return employee
        return None
        
    def get_manager_by_name(self, manager_name):
        response = self.employee_table.scan()
        for employee in response["Items"]:
            if (
            employee["name"].lower() == manager_name.lower()
            and employee.get("role") == "Manager"
        ):
                return employee
        return None
        
    
    def employee_exists(self, employee_id):

        employee = self.get_employee(employee_id)

        return employee is not None
    
     # Leave Balance Methods
    
    def get_leave_balance(self, employee_id):

        response = self.leave_balance_table.get_item(
            Key={
                "employee_id": employee_id
            }
        )

        return response.get("Item")    
    
      # Holiday Methods 
    
    def get_all_holidays(self):

        response = self.holiday_table.scan()

        return response["Items"]  
    
    def get_holiday(self, date):

        response = self.holiday_table.get_item(
            Key={
                "holiday_date": date
            }
        )

        return response.get("Item")     
    
     #  # Leave Request Methods
    
    def create_leave_request(self, request):

        self.leave_request_table.put_item(
            Item=request
        )
        
        
    def get_leave_request(self, request_id):

        response = self.leave_request_table.get_item(
            Key={
                "request_id": request_id
            }
        )

        return response.get("Item")
    
    def create_approval_request(self, approval):

        self.approval_table.put_item(
            Item=approval
        )
        
         # Approval Methods
        
    def get_approval(self, request_id):

        response = self.approval_table.get_item(
            Key={
                "request_id": request_id
            }
        )

        return response.get("Item")
    
    def update_leave_balance(
        self,
        employee_id,
        annual_used,
        casual_used,
        sick_used
    ):

     self.leave_balance_table.update_item(

            Key={
                "employee_id": employee_id
            },

            UpdateExpression="""
            SET
            annual_used=:a,
            casual_used=:c,
            sick_used=:s
            """,

            ExpressionAttributeValues={
                ":a": annual_used,
                ":c": casual_used,
                ":s": sick_used
            }
        )
     
def get_pending_approvals(self):

    response = self.approval_table.scan()

    approvals = response["Items"]

    pending = []

    for item in approvals:

        if item["status"] == "Pending":

            pending.append(item)

    return pending 

def update_approval(
    self,
    request_id,
    status,
    approved_by,
    comments,
    approved_at
):

    self.approval_table.update_item(

        Key={
            "request_id": request_id
        },

        UpdateExpression="""
        SET
        #s=:status,
        approved_by=:approved_by,
        comments=:comments,
        approved_at=:approved_at
        """,

        ExpressionAttributeNames={
            "#s": "status"
        },

        ExpressionAttributeValues={
            ":status": status,
            ":approved_by": approved_by,
            ":comments": comments,
            ":approved_at": approved_at
        }
    )
    
def update_leave_request_status(
    self,
    request_id,
    status
):

    self.leave_request_table.update_item(

        Key={
            "request_id": request_id
        },

        UpdateExpression="SET #s=:status",

        ExpressionAttributeNames={
            "#s": "status"
        },

        ExpressionAttributeValues={
            ":status": status
        }
    )    
    
def update_leave_usage(
    self,
    employee_id,
    leave_type,
    days
):
    """
    Update used leave after approval.
    """

    field = f"{leave_type.lower()}_used"

    self.leave_balance_table.update_item(

        Key={
            "employee_id": employee_id
        },

        UpdateExpression=f"SET {field} = {field} + :days",

        ExpressionAttributeValues={
            ":days": days
        }

    )        
    
def get_latest_leave_status(self, employee_id):
        response = self.leave_request_table.scan(
        FilterExpression="employee_id = :employee_id",
        ExpressionAttributeValues={
            ":employee_id": employee_id
        }
    )
        leave_requests = response.get("Items", [])
        if not leave_requests:
            return None
        latest_request = max(
            leave_requests,
            key=lambda x: x["start_date"]
        )
        return {
        "request_id": latest_request.get("request_id"),
        "status": latest_request.get("status"),
        "leave_type": latest_request.get("leave_type"),
        "start_date": latest_request.get("start_date"),
        "end_date": latest_request.get("end_date"),
         "leave_status": latest_request.get("status")
    }
db = DynamoDBService() 