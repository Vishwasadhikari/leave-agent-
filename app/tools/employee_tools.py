from strands import tool

from app.services.dynamodb_service import db


@tool
def get_employee(employee_id: str):
    """
    Get employee details using employee ID.
    """

    employee = db.get_employee(employee_id)

    if employee is None:
        return {
            "success": False,
            "message": "Employee not found."
        }

    return {
        "success": True,
        "employee": employee
    }
    
@tool
def get_employee_by_name(employee_name: str):
    """
    Get employee details using employee name.
    """

    employee = db.get_employee_by_name(employee_name)

    if employee is None:

        return {
            "success": False,
            "message": "Employee not found."
        }

    return {
        "success": True,
        "employee": employee
    }
    
    
@tool
def get_manager_by_name(manager_name: str):
    """
    Get manager details using manager name.
    """

    manager = db.get_manager_by_name(manager_name)

    if manager is None:

        return {
            "success": False,
            "message": "Manager not found."
        }

    return {
        "success": True,
        "manager": manager
    }
    
@tool
def validate_employee(employee_id: str):
    """
    Check whether an employee exists.
    """

    exists = db.employee_exists(employee_id)

    return {
        "exists": exists
    }
    
@tool
def get_manager(employee_id: str):
    """
    Get the reporting manager of an employee.
    """

    employee = db.get_employee(employee_id)

    if employee is None:
        return {
            "success": False,
            "message": "Employee not found."
        }

    manager_id = employee["manager_id"]

    if manager_id == "NONE":
        return {
            "success": False,
            "message": "This employee has no manager."
        }

    manager = db.get_employee(manager_id)

    return {
        "success": True,
        "manager": manager
    }