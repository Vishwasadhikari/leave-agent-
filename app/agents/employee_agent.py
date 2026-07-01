from strands import Agent

from app.tools.employee_tools import (
    get_employee,
    validate_employee,
    get_manager
)

employee_agent = Agent(

    name="Employee Agent",

    description="""
    Responsible for validating employees,
    fetching employee details,
    and retrieving manager information.
    """,

    tools=[
        validate_employee,
        get_employee,
        get_manager
    ]
)