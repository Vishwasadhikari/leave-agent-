from strands import Agent

from app.tools.leave_tools import (
    get_leave_balance,
    calculate_working_days,
    check_leave_availability,
    is_loss_of_pay
)

leave_agent = Agent(

    name="Leave Agent",

    description="""
    Responsible for leave balance validation,
    leave availability,
    loss of pay policy,
    and leave day calculations.
    """,

    tools=[

        get_leave_balance,

        calculate_working_days,

        check_leave_availability,

        is_loss_of_pay

    ]

)