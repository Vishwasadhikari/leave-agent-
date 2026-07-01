from dotenv import load_dotenv
import os

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID")

EMPLOYEE_TABLE = os.getenv("EMPLOYEE_TABLE")
LEAVE_BALANCE_TABLE = os.getenv("LEAVE_BALANCE_TABLE")
HOLIDAY_TABLE = os.getenv("HOLIDAY_TABLE")
LEAVE_REQUEST_TABLE = os.getenv("LEAVE_REQUEST_TABLE")
APPROVAL_TABLE = os.getenv("APPROVAL_TABLE")