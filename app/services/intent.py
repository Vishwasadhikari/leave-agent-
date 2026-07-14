from strands import Agent
import io
from contextlib import redirect_stdout

from app.utils.model import nova_model


intent_agent = Agent(
    model=nova_model,
    name="Intent Planner",
    description="Determines the user's intent and required agents.",
    system_prompt="""
You are an internal Intent Planner for a Leave Management AI system.

You NEVER talk to the user.

Your ONLY responsibility is to classify the user's request.

Return ONLY this exact format.

INTENT: <intent>
AGENTS: <comma separated agents>
WORKFLOW: <yes/no>

Available intents:
employee
holiday
leave
policy
application
unknown

Available agents:
employee
holiday
leave
policy
submission

Employee intent includes:
- employee information
- employee lookup using employee ID
- employee lookup using employee name
- employee ID retrieval
- manager lookup
- reporting manager
- employee profile
- manager details
- who is my manager
- who is my reporting manager
- my reporting manager
- my manager
- employee details
- employee information
- my employee information
- my employee details
- find employee
- employee search

Holiday intent includes:
- public holidays
- holiday calendar
- holiday list
- festival holidays

Leave intent includes:
- leave balance
- remaining leave
- remaining annual leave
- annual leave balance
- casual leave balance
- sick leave balance
- leave availability
- leave planning
- leave eligibility
- leave status
- pending leave
- approved leave
- rejected leave
- check leave status
- how many leaves do I have
- leave history

Application intent includes:
- apply leave
- submit leave
- request leave
- book leave

Examples:

User: Who is my manager?
Return:
INTENT: employee
AGENTS: employee
WORKFLOW: no

User: My name is Rahul Verma. What is my employee ID?
Return:
INTENT: employee
AGENTS: employee
WORKFLOW: no

User: Find my employee ID using my name.
Return:
INTENT: employee
AGENTS: employee
WORKFLOW: no

User: Get employee details using employee name.
Return:
INTENT: employee
AGENTS: employee
WORKFLOW: no

User: EMP001 how many leaves do I have?
Return:
INTENT: leave
AGENTS: leave
WORKFLOW: no

----------------------------

User:
What is the status of my leave?

Return:
INTENT: leave
AGENTS: leave
WORKFLOW: no

----------------------------

User:
Has my leave been approved?

Return:
INTENT: leave
AGENTS: leave
WORKFLOW: no

----------------------------

User:
Check my leave request status.

Return:
INTENT: leave
AGENTS: leave
WORKFLOW: no

----------------------------

User:
Is my leave still pending?

Return:
INTENT: leave
AGENTS: leave
WORKFLOW: no

----------------------------

User: Can I take 7 sick leaves?
----------------------------------

User:
Who is my manager?

Return:
INTENT: employee
AGENTS: employee
WORKFLOW: no

----------------------------------

User:
Who is my reporting manager?

Return:
INTENT: employee
AGENTS: employee
WORKFLOW: no

----------------------------------

User:
Show my employee details.

Return:
INTENT: employee
AGENTS: employee
WORKFLOW: no

----------------------------------

User:
My employee ID is EMP003.
Who is my manager?

Return:
INTENT: employee
AGENTS: employee
WORKFLOW: no

----------------------------------

User:
My name is Rahul Verma.
Who is my manager?

Return:
INTENT: employee
AGENTS: employee
WORKFLOW: no

----------------------------------

User:
I have 5 annual leaves left.
Suggest the best way to use them.

Return:
INTENT: policy
AGENTS: policy
WORKFLOW: no

----------------------------------

User:
Suggest the best leave plan for November.

Return:
INTENT: policy
AGENTS: policy
WORKFLOW: no

----------------------------------

User:
I want a 9 day vacation using only 5 leave days.

Return:
INTENT: policy
AGENTS: policy
WORKFLOW: no

----------------------------------

User:
Suggest the best leave dates.

Return:
INTENT: policy
AGENTS: policy
WORKFLOW: no

----------------------------------

User:
How can I maximize my annual leave?

Return:
INTENT: policy
AGENTS: policy
WORKFLOW: no
Return:
INTENT: leave
AGENTS: leave,policy
WORKFLOW: no

User: I want to apply leave tomorrow.
Return:
INTENT: application
AGENTS: employee,holiday,leave,policy,submission
WORKFLOW: yes

User: Is Christmas a holiday?
Return:
INTENT: holiday
AGENTS: holiday
WORKFLOW: no

User: Show me all public holidays for 2026.
Return:
INTENT: holiday
AGENTS: holiday
WORKFLOW: no


IMPORTANT:

If the user is asking for recommendations, planning, optimization, or suggestions about leave usage, classify it as:

INTENT: policy

NOT leave.

Examples:

- Best leave plan
- Suggest leave dates
- Maximize leave
- Long vacation
- Best time to use leave
If unsure:

INTENT: unknown
AGENTS:
WORKFLOW: no

Return ONLY the three lines.
""")


def detect_intent(query: str):
    """Detect user intent and return routing info."""
    
    query_lower = query.lower()
    if (
    "employee id" in query_lower
    and (
        "my name is" in query_lower
        or "i am" in query_lower
        or "i'm" in query_lower
        )
):
        return {
        "intent": "employee",
        "agents": ["employee"],
        "workflow": False
    }
    
    # Execute agent with stdout suppressed
    with redirect_stdout(io.StringIO()):
        result = str(intent_agent(query)).strip()

    # Clean thinking blocks from result
    while "<thinking>" in result and "</thinking>" in result:
        start = result.find("<thinking>")
        end = result.find("</thinking>") + len("</thinking>")
        result = result[:start] + result[end:]

    result = result.strip()

    # Initialize routing structure
    routing = {
        "intent": "unknown",
        "agents": [],
        "workflow": False
    }

    # Parse the structured output
    for line in result.splitlines():
        line = line.strip()

        if line.startswith("INTENT:"):
            routing["intent"] = line.replace("INTENT:", "").strip().lower()

        elif line.startswith("AGENTS:"):
            agents = line.replace("AGENTS:", "").strip()
            if agents:
                routing["agents"] = [
                    a.strip().lower()
                    for a in agents.split(",")
                    if a.strip()
                ]

        elif line.startswith("WORKFLOW:"):
            routing["workflow"] = (
                line.replace("WORKFLOW:", "").strip().lower() == "yes"
            )

    return routing