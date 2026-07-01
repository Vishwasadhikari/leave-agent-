from strands import Agent

from app.tools.leave_submission_tool import submit_leave

submission_agent = Agent(

    name="Submission Agent",

    description="""
    Responsible for creating
    leave requests,
    approval requests,
    and sending approval emails.
    """,

    tools=[

        submit_leave

    ]

)