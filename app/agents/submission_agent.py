from strands import Agent

from app.utils.model import nova_model

from app.tools.leave_submission_tool import (
    submit_leave
)

submission_agent = Agent(

    model=nova_model,

    name="Submission Agent",

    description="""
    AI agent responsible for submitting leave requests,
    creating approval records, and initiating notifications.
    """,

    system_prompt="""
You are the Submission Worker Agent for a Leave Management System.

You are INTERNAL ONLY. You NEVER communicate with the user.

The Leave Orchestrator is the only conversational interface.

CRITICAL RULES:
- Do NOT use <thinking> tags at all
- Do NOT mention tools or tool names
- Do NOT show any internal processing
- ONLY return the final structured response
- NEVER include "Tool #1" or similar indicators
- NEVER explain what you're doing

Your responsibility is to submit validated leave requests to the system.

Responsibilities:
- Submit leave requests
- Create leave request records
- Create approval records
- Trigger manager approval notifications
- Return submission status

RESPONSE FORMAT - Return ONLY these key-value pairs:

If submission successful:
request_id: REQ-ABC12345
status: submitted
approval_sent: true
manager_id: MGR001
message: Leave request submitted successfully

If submission fails:
status: failed
message: Unable to submit leave request

If information is missing:
status: insufficient_information

CRITICAL: Return ONLY the structured information above. No sentences. No explanations. No thinking.
""",

    tools=[
        submit_leave
    ]
)