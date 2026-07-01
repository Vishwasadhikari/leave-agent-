from strands import Agent

from app.tools.holiday_tools import (
    is_weekend,
    is_holiday
)

from app.tools.leave_tools import (
    calculate_working_days
)


holiday_agent = Agent(

    name="Holiday Agent",

    description="""
    Responsible for checking
    weekends,
    holidays,
    and calculating
    working leave days.
    """,

    tools=[

        is_weekend,

        is_holiday,

        calculate_working_days

    ]

)