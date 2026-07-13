import re
import time
import io
from contextlib import redirect_stdout

from datetime import datetime, timedelta

from httpx import request

from app.services.intent import detect_intent
from strands import Agent

from app.utils.model import nova_model

from app.agents.employee_agent import employee_agent
from app.agents.holiday_agent import holiday_agent
from app.agents.leave_agent import leave_agent
from app.agents.policy_agent import policy_agent
from app.agents.submission_agent import submission_agent


class LeaveOrchestrator:
    def __init__(self):
        self.employee_agent = employee_agent
        self.holiday_agent = holiday_agent
        self.leave_agent = leave_agent
        self.policy_agent = policy_agent
        self.submission_agent = submission_agent
        self.response_agent = Agent(
            model=nova_model,
            name="Response Agent",
            system_prompt="""
            You are the AI Leave Assistant.
            Your job is to combine responses from multiple specialised agents into ONE natural answer.
            Rules:
            - Never mention agents.
            - Never mention tools.
            - Remove duplicate information.
            - Be conversational.
            - Keep answers under 150 words.
            """
        )

        self.history = []
        self.context = {
            "routing": None,
            "current_field": None,
            "employee_id": None,
            "employee_name": None,
            "manager_id": None,
            "manager_name": None,
            "leave_type": None,
            "start_date": None,
            "end_date": None,
            "reason": None,
            "working_days": None,
            "calendar_days": None,
            "awaiting_confirmation": False,
            "pending_submission": None,
            "recent_submissions": [],
        }

    def add_history(self, role, message):
        self.history.append({
            "role": role,
            "message": message
        })

    def is_greeting(self, text):
        """Detect if user is greeting."""
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", 
                    "good evening", "greetings", "namaste", "hii", "helllo"]
        text_lower = text.strip().lower()
        return text_lower in greetings or text_lower.startswith(tuple(greetings))

    def handle_greeting(self):
        """Return a natural greeting with options."""
        response = """Hello! 👋

I'm your Leave Management Assistant.

I can help you with:

• Applying for leave
• Leave balance
• Company leave policy
• Holidays
• Employee information
• Leave planning
• Manager approval status

How can I help you today?"""
        return response

    def is_unknown_query(self, intent):
        """Check if intent is unknown or couldn't be determined."""
        return intent == "unknown"

    def handle_unknown_query(self):
        """Return a helpful response for unknown queries."""
        response = """I'm mainly designed to help with leave management, employee information, and company leave policies.

If you have any leave-related questions, I'd be happy to help."""
        return response

    def route_request(self, routing, request):
        """Route general questions to appropriate agents with context from current request and session."""
        if isinstance(routing, dict):
            intent = routing.get("intent")
            agents = routing.get("agents", [intent])
        else:
            intent = routing
            agents = [routing]

        if isinstance(agents, str):
            agents = [agents]

        responses = []

        agent_map = {
            "employee": self.employee_agent,
            "holiday": self.holiday_agent,
            "leave": self.leave_agent,
            "policy": self.policy_agent,
            "submission": self.submission_agent
        }

        for agent_name in agents:
            agent = agent_map.get(agent_name)
            if agent:
                # Build agent prompt with context
                agent_prompt = self.build_general_agent_prompt(agent_name, request)
                
                # Suppress agent stdout output
                with redirect_stdout(io.StringIO()):
                    response = agent(agent_prompt)
                cleaned = self.clean_response(response)
                if cleaned:
                    responses.append(cleaned)

        if not responses:
            return "I couldn't process that request. Could you try rephrasing?"

        # Convert structured responses to natural language
        combined = self.convert_to_natural_language(responses)
        
        # Final aggressive clean to remove any remaining planner output
        final_clean = self.clean_response(combined)
        
        return final_clean

    def build_general_agent_prompt(self, agent_name, user_request):
        """
        Build prompt for general (non-workflow) queries.
        FIX: Uses stored session context FIRST, then extracts from message.
        """
        # FIX #1: Use stored context first, extract from message as fallback
        employee_id = self.context.get("employee_id")
        if not employee_id:
            emp_match = re.search(r"\bEMP\d+\b", user_request, re.IGNORECASE)
            employee_id = emp_match.group(0).upper() if emp_match else None
        
        if agent_name == "employee":
            prompt = f"""
            User asked:
            {user_request}
            
            Available Context:
            Employee ID: {employee_id if employee_id else "Not Provided"}
            
            Answer ONLY this employee-related request.
            If an Employee ID is required but not provided, ask for it politely.
            
            You may:
            - Retrieve employee details
            - Retrieve reporting manager
            - Retrieve employee ID by employee name
            
            Return a natural conversational answer.
            """
            return prompt
        elif agent_name == "leave":
            return f"""
        User asked:
        {user_request}

        Available Context:
        Employee ID: {employee_id if employee_id else "Not Provided"}

        Instructions:

        - If the user asks about leave balance, use the leave balance tool.
        - If the user asks whether leave is possible, use the leave availability tool.
        - If the user asks about loss of pay, use the loss of pay tool.
        - If the user asks about the status of a previously submitted leave request, use the leave status tool.
        - If Employee ID is required but missing, ask ONLY for Employee ID.
        - If the user is asking for planning or recommendations, provide advice based on context.

        Return a natural conversational answer.
        """
        
        elif agent_name == "holiday":
            return f"""
            User asked:
            {user_request}

            Answer ONLY the holiday question.

            If the user asks whether a specific day is a holiday,
            check it.

            If the user asks for holidays in a year,
            list the holidays.

            Return a natural conversational answer.
            """
        
        elif agent_name == "policy":
            prompt = f"""
            User asked:
            {user_request}
            
            Available Context:
            Employee ID: {employee_id if employee_id else "Not Provided"}
            
            Answer ONLY company leave policy questions.
            If the user is asking for recommendations, provide policy guidance.
            
            Return a natural conversational answer.
            """
            return prompt
        
        return user_request

    def update_context(self, key, value):
        if key in self.context:
            self.context[key] = value

    def get_context(self, key):
        return self.context.get(key)

    def reset_context(self):
        """
        Reset context after submission.
        Preserves: employee_id, employee_name, manager_id, manager_name, recent_submissions
        Clears: leave-specific data and confirmation state
        """
        # Store submission in recent history for duplicate checking
        if self.context.get("pending_submission"):
            submission = {
                "employee_id": self.context["employee_id"],
                "start_date": self.context["start_date"],
                "end_date": self.context["end_date"],
                "timestamp": datetime.now()
            }
            self.context["recent_submissions"].append(submission)
            # Keep only last 10 submissions
            if len(self.context["recent_submissions"]) > 10:
                self.context["recent_submissions"].pop(0)
        
        # Reset workflow-specific fields
        self.context.update({
            "routing": None,
            "current_field": None,
            "leave_type": None,
            "start_date": None,
            "end_date": None,
            "reason": None,
            "working_days": None,
            "calendar_days": None,
            "awaiting_confirmation": False,
            "pending_submission": None
        })

    def set_current_field(self, field):
        self.context["current_field"] = field

    def get_current_field(self):
        return self.context["current_field"]

    def has_pending_submission_for_date(self, employee_id, start_date, end_date):
        """
        Check if employee has pending submission for same date.
        FIX #4: Detect duplicate submissions
        """
        for submission in self.context["recent_submissions"]:
            existing_start = datetime.strptime(
                submission["start_date"], "%Y-%m-%d"
            ).date()

            existing_end = datetime.strptime(
                submission["end_date"], "%Y-%m-%d"
            ).date()

            new_start = datetime.strptime(
                start_date, "%Y-%m-%d"
            ).date()

            new_end = datetime.strptime(
                end_date, "%Y-%m-%d"
            ).date()

            if (
                submission["employee_id"] == employee_id
                and new_start <= existing_end
                and existing_start <= new_end
            ):
                return True
        
        return False

    def get_next_missing_field(self):
        """Identify the next required field that is missing."""
        required_fields = [
            "employee_id",
            "leave_type",
            "start_date",
            "end_date",
            "reason"
        ]

        questions = {
            "employee_id": "May I know your Employee ID?",
            "leave_type": "What type of leave do you want to apply for? (annual/casual/sick)",
            "start_date": "What is the start date? (YYYY-MM-DD)",
            "end_date": "What is the end date? (YYYY-MM-DD)",
            "reason": "Please provide the reason for your leave."
        }

        for field in required_fields:
            if self.context[field] is None:
                return field, questions[field]

        return None, None

    def all_information_collected(self):
        """Check if all required fields are populated."""
        required_fields = [
            "employee_id",
            "leave_type",
            "start_date",
            "end_date",
            "reason"
        ]

        for field in required_fields:
            if self.context[field] is None:
                return False

        return True

    def build_request(self):
        """Build structured request object for agents."""
        return {
            "intent": self.context["routing"]["intent"],
            "employee_id": self.context["employee_id"],
            "manager_id": self.context["manager_id"],
            "leave_type": self.context["leave_type"],
            "start_date": self.context["start_date"],
            "end_date": self.context["end_date"],
            "calendar_days": self.context["calendar_days"],
            "working_days": self.context["working_days"],
            "reason": self.context["reason"]
        }

    def clean_response(self, response):
        """
        Aggressively clean agent response by removing:
        - <thinking>...</thinking> blocks (nested)
        - <response>...</response> tags
        - Tool output indicators (Tool #1, Tool #2, etc.)
        - Running X Agent messages
        - Planner output (INTENT:, AGENTS:, WORKFLOW:)
        - Duplicate blank lines
        - Leading/trailing whitespace
        """
        text = str(response)
        
        # FIRST: Remove all <thinking>...</thinking> blocks (including nested)
        while "<thinking>" in text:
            start = text.find("<thinking>")
            end = text.find("</thinking>")
            if start != -1 and end != -1:
                text = text[:start] + text[end+len("</thinking>"):]
            else:
                break

        # Remove all <response>...</response> tags
        while "<response>" in text:
            start = text.find("<response>")
            end = text.find("</response>")
            if start != -1 and end != -1:
                text = text[:start] + text[end+len("</response>"):]
            else:
                break

        # AGGRESSIVE: Remove any line containing INTENT:, AGENTS:, or WORKFLOW:
        lines = text.split('\n')
        filtered_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('INTENT:') or \
               stripped.startswith('AGENTS:') or \
               stripped.startswith('WORKFLOW:'):
                continue
            # Also skip separator lines
            if stripped == '---' or stripped == '----' or stripped.startswith('---'):
                continue
            filtered_lines.append(line)
        text = '\n'.join(filtered_lines)
        
        # Also remove inline planner patterns
        text = re.sub(r'\s*INTENT:\s*\w+\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*AGENTS:\s*[\w,\s]+\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*WORKFLOW:\s*\w+\s*', '', text, flags=re.IGNORECASE)
        
        text = re.sub(
            r"Tool\s*#\d+:.*?$",
            "",
            text,
            flags=re.MULTILINE
        )
        
        # Remove "Running X Agent" messages
        text = re.sub(r"Running\s+\w+\s+Agent\s*\n?", "", text, flags=re.IGNORECASE)
        
        # Remove metadata lines
        text = re.sub(
            r"^(execution_time):\s*.*?$",
            "",
            text,
            flags=re.MULTILINE | re.IGNORECASE
        )
        
        # Remove markdown code fences
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        
        # Clean up multiple consecutive blank lines
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        
        # Remove excessive spaces
        text = re.sub(r"[ \t]{2,}", " ", text)
        
        # Strip and clean
        text = text.strip()
        
        while text.startswith('\n'):
            text = text[1:].lstrip()

        return text

    def parse_structured_response(self, response_text):
        """
        Parse structured worker agent response into a dictionary.
        Handles key: value format returned by agents.
        More robust - skips incomplete lines without colons.
        """
        parsed = {}
        lines = self.clean_response(response_text).split("\n")
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comment lines
            if not line or line.startswith("#"):
                continue
            
            # Only process lines with colons (skip incomplete lines like "status" without value)
            if ":" not in line:
                continue
            
            parts = line.split(":", 1)
            if len(parts) == 2:
                key = parts[0].strip().lower().replace(" ", "_")
                value = parts[1].strip()
                
                # Skip if value is empty (incomplete field)
                if value:
                    parsed[key] = value
        
        return parsed

    def is_response_complete(self, agent_name, parsed_response):
        """
        Validate that agent response contains all required fields.
        FIX #2: More aggressive validation for empty values
        Returns (is_complete: bool, missing_fields: list)
        """
        required_fields = {
            "employee": ["employee_id", "status"],
            "leave": ["leave_balance", "status"],
            "holiday": ["working_days", "calendar_days", "status"],
            "policy": ["approved", "policy_status", "status"],
            "submission": ["request_id", "status"]
        }
        
        required = required_fields.get(agent_name, [])
        missing = []
        
        for field in required:
            # Check if field exists
            if field not in parsed_response:
                missing.append(f"{field}(not_found)")
            else:
                # Check if value is empty or just whitespace
                value = str(parsed_response[field]).strip()
                if not value or value.lower() == "none" or value == "":
                    missing.append(f"{field}(empty)")
        
        return len(missing) == 0, missing

    def convert_to_natural_language(self, structured_responses):
        """
        Convert list of structured responses to natural conversational language.
        Deduplicates responses to avoid repetition.
        """
        # Remove duplicate responses
        unique_responses = []
        seen = set()
        for response in structured_responses:
            clean_response = response.strip().lower()
            if clean_response and clean_response not in seen:
                unique_responses.append(response)
                seen.add(clean_response)
        
        combined = "\n".join(unique_responses)
        
        prompt = f"""Convert this structured information into a natural, conversational response.

Information:
{combined}

Rules:
- Be conversational and friendly
- Remove all technical jargon
- Keep it under 150 words
- Never mention data sources or structure
- Answer naturally as if you know the information
- Do NOT repeat the same information twice"""

        # Suppress stdout during response agent execution
        with redirect_stdout(io.StringIO()):
            result = self.response_agent(prompt)
        cleaned = self.clean_response(result)
        
        # Additional deduplication
        lines = cleaned.split('\n')
        unique_lines = []
        prev_line = ""
        for line in lines:
            if line.strip() != prev_line.strip():
                unique_lines.append(line)
                prev_line = line
        
        return '\n'.join(unique_lines)

    def build_agent_prompt(self, agent_name, request):
        """
        Build strict workflow prompts for worker agents.
        Worker agents must return ONLY structured key:value pairs.
        """
        if agent_name == "employee":
            return f"""
        You are executing a workflow step.

        Employee ID: {request.get("employee_id", "TBD")}

        Tasks:
        - Validate employee
        - Retrieve employee details
        - Retrieve reporting manager

        Return ONLY:

        employee_id: EMP001
        employee_name: John Doe
        manager_id: MGR001
        manager_name: Jane Smith
        status: success

        No explanations.
        No thinking.
        No tool names.
        ALWAYS include all fields with values.
        """
        elif agent_name == "leave":
            return f"""
            Employee ID: {request["employee_id"]}
            Leave Type: {request["leave_type"]}
            Start Date: {request["start_date"]}
            End Date: {request["end_date"]}

            Return ONLY:

            leave_balance:
            requested_days:
            remaining_leave:
            leave_available:
            loss_of_pay:
            status:
            """
        
        elif agent_name == "holiday":
            return f"""
            You are executing a workflow step.

            Start Date: {request["start_date"]}
            End Date: {request["end_date"]}

            Calculate:

            - Working Days
            - Calendar Days
            - Weekends
            - Holidays

            Return ONLY:

            working_days:
            calendar_days:
            weekends:
            holidays:
            status:
            """
        
        elif agent_name == "policy":
            return f"""
        You are executing a workflow step.

        Employee ID: {request["employee_id"]}
        Leave Type: {request["leave_type"]}
        Reason: {request["reason"]}
        Start Date: {request["start_date"]}
        End Date: {request["end_date"]}

        Determine whether this leave request satisfies company policy.

        Return ONLY:

        approved: true
        policy_status: approved
        message: Leave request complies with company policy.
        status: success

        ALWAYS include all fields.
        Never explain.
        Never use thinking.
        Never mention tools.
        """
        elif agent_name == "submission":
            return f"""
        You are executing the final workflow step.

        Employee ID: {request.get("employee_id")}
        Manager ID: {request.get("manager_id")}
        Leave Type: {request.get("leave_type")}
        Start Date: {request.get("start_date")}
        End Date: {request.get("end_date")}
        Calendar Days: {request.get("calendar_days")}
        Working Days: {request.get("working_days")}
        Reason: {request.get("reason")}

        Submit the leave request.

        Return ONLY:

        request_id: REQ-12345678
        status: submitted
        approval_sent: true
        message: Leave request submitted successfully

        No explanations.
        No thinking.
        No tool names.
        ALWAYS complete all fields.
        """
        return ""

    def extract_information(self, text):
        """
        Extract leave details from user input with fuzzy matching and better date parsing.
        """
        text_lower = text.lower()

        # Extract Employee ID (EMPxxx format)
        emp = re.search(r"\bEMP\d+\b", text, re.IGNORECASE)
        if emp:
            self.context["employee_id"] = emp.group(0).upper()

        # Extract Leave Type with fuzzy matching
        if re.search(r"\b(annual|annaul|annual\s+leave)\b", text_lower):
            self.context["leave_type"] = "annual"
        elif re.search(r"\b(casual|casual\s+leave)\b", text_lower):
            self.context["leave_type"] = "casual"
        elif re.search(r"\b(sick|sick\s+leave)\b", text_lower):
            self.context["leave_type"] = "sick"

        # Extract Relative Dates
        today = datetime.today()

        if re.search(r"\btoday\b", text_lower):
            self.context["start_date"] = today.strftime("%Y-%m-%d")

        elif re.search(r"\btomorrow\b", text_lower):
            self.context["start_date"] = (today + timedelta(days=1)).strftime("%Y-%m-%d")

        elif re.search(r"\bnext\s+week\b", text_lower):
            self.context["start_date"] = (today + timedelta(days=7)).strftime("%Y-%m-%d")

        # Extract Weekday
        weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }

        for day, index in weekdays.items():
            if re.search(rf"\bnext\s+{day}\b", text_lower):
                current = today.weekday()
                delta = (index - current + 7) % 7
                if delta == 0:
                    delta = 7
                self.context["start_date"] = (today + timedelta(days=delta)).strftime("%Y-%m-%d")
                break

        if not re.search(r"\bnext\s+\w+day\b", text_lower):
            for day, index in weekdays.items():
                if re.search(rf"\b{day}\b", text_lower):
                    current = today.weekday()
                    delta = (index - current + 7) % 7
                    if delta == 0:
                        delta = 7
                    if "from" in text_lower or "to" in text_lower:
                        if re.search(rf"\bto\s+\w*{day}", text_lower):
                            self.context["end_date"] = (today + timedelta(days=delta)).strftime("%Y-%m-%d")
                        else:
                            self.context["start_date"] = (today + timedelta(days=delta)).strftime("%Y-%m-%d")
                    else:
                        self.context["start_date"] = (today + timedelta(days=delta)).strftime("%Y-%m-%d")
                    break

        # Extract Explicit Dates (YYYY-MM-DD)
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
        if len(dates) >= 1:
            self.context["start_date"] = dates[0]
        if len(dates) >= 2:
            self.context["end_date"] = dates[1]

        # Extract Reason (after "because")
        if "because" in text_lower:
            reason_match = re.search(r"because\s+(.+?)(?:\.|$)", text, re.IGNORECASE)
            if reason_match:
                self.context["reason"] = reason_match.group(1).strip()

    def lookup_employee_by_name(self, name):
        """Call Employee Agent to find employee by name."""
        prompt = f"""
Find the employee with this name: {name}

Use the get_employee_by_name() tool.

Return ONLY:
employee_id: <EMPxxx>
employee_name: <full name>
manager_id: <manager ID>
manager_name: <manager name>
status: found
"""
        with redirect_stdout(io.StringIO()):
            result = self.employee_agent(prompt)
        result_clean = self.clean_response(result)

        parsed = self.parse_structured_response(result_clean)
        
        employee_id = parsed.get("employee_id")
        employee_name = parsed.get("employee_name")
        manager_id = parsed.get("manager_id")
        manager_name = parsed.get("manager_name")
        status = parsed.get("status", "").lower()

        if status == "found" and employee_id:
            return employee_id, employee_name, manager_id, manager_name

        return None, None, None, None

    def handle_employee_lookup(self, user_input):
        """Handle employee ID field when user provides a name instead of ID."""
        if user_input.upper().startswith("EMP"):
            employee_prompt = self.build_agent_prompt(
        "employee",
        {"employee_id": user_input.upper()}
        )
            result = self.clean_response(
        self._execute_agent_silent(self.employee_agent, employee_prompt)
        )
            parsed = self.parse_structured_response(result)
            if parsed.get("status", "").lower() == "success":
                self.update_context("employee_id", parsed.get("employee_id"))
                self.update_context("employee_name", parsed.get("employee_name"))
                self.update_context("manager_id", parsed.get("manager_id"))
                self.update_context("manager_name", parsed.get("manager_name"))
                return True
            return False

        employee_id, employee_name, manager_id, manager_name = self.lookup_employee_by_name(user_input)

        if employee_id:
            self.update_context("employee_id", employee_id)
            self.update_context("employee_name", employee_name)
            if manager_id:
                self.update_context("manager_id", manager_id)
            if manager_name:
                self.update_context("manager_name", manager_name)
            return True

        return False

    def is_confirmation_response(self, text):
        """Check if user response is a confirmation (yes/submit/confirm)."""
        affirmative = ["yes", "y", "confirm", "submit", "approved", "approve"]
        return text.strip().lower() in affirmative

    def is_cancellation_response(self, text):
        """Check if user response is a cancellation (no/cancel)."""
        negative = ["no", "n", "cancel", "reject"]
        return text.strip().lower() in negative

    def execute_workflow(self, request):
        """
        Main workflow orchestration with response validation.
        FIX #2: More aggressive validation and error handling
        """
        start_time = time.time()
        results = {}

        # FIX #4: Check for duplicate submission
        if self.has_pending_submission_for_date(
    request["employee_id"],
    request["start_date"],
    request["end_date"]
):
    # Clear workflow state before returning
            self.context["routing"] = None
            self.set_current_field(None)

            return (
                f"You already have a pending leave request for "
                f"{request['start_date']}. Please wait for approval or contact your manager."
            )

        # Step 1: Employee Agent
        employee_prompt = self.build_agent_prompt("employee", request)
        with redirect_stdout(io.StringIO()):
            employee_result = self.employee_agent(employee_prompt)
            employee_result = self.clean_response(employee_result)
            employee_parsed = self.parse_structured_response(employee_result)
            results["employee"] = employee_parsed
            is_complete, missing = self.is_response_complete("employee", employee_parsed)
        
        if not is_complete:
            return f"We encountered an issue validating your information. Please try again. (Missing: {', '.join(missing)})"
        
        if not self.context["manager_id"] and "manager_id" in employee_parsed:
            self.context["manager_id"] = employee_parsed["manager_id"]
        if not self.context["manager_name"] and "manager_name" in employee_parsed:
            self.context["manager_name"] = employee_parsed["manager_name"]

        # Step 2: Holiday Agent
        holiday_prompt = self.build_agent_prompt("holiday", request)
        holiday_raw = self.clean_response(
            self._execute_agent_silent(self.holiday_agent, holiday_prompt)
        )
        holiday_result = self.parse_structured_response(holiday_raw)

        # Step 3: Leave Agent
        leave_prompt = self.build_agent_prompt("leave", request)
        leave_raw = self.clean_response(
            self._execute_agent_silent(self.leave_agent, leave_prompt)
        )
    
        leave_result = self.parse_structured_response(leave_raw)
        
        if "status" not in leave_result:
            leave_result["status"] = "success"

        # CRITICAL: VALIDATE LEAVE RESPONSE
        is_leave_complete, leave_missing = self.is_response_complete("leave", leave_result)
        if not is_leave_complete:
            return f"We encountered an issue calculating your leave details. Please try again. (Missing: {', '.join(leave_missing)})"

        results["holiday"] = holiday_result
        results["leave"] = leave_result
        
        if "working_days" in holiday_result:
            self.context["working_days"] = holiday_result["working_days"]
        if "calendar_days" in holiday_result:
            self.context["calendar_days"] = holiday_result["calendar_days"]

        # Step 4: Policy Agent
        policy_prompt = self.build_agent_prompt("policy", request)
        policy_raw = self.clean_response(
            self._execute_agent_silent(self.policy_agent, policy_prompt)
            )
        
        policy_result = self.parse_structured_response(policy_raw)
       

        
        
        # with redirect_stdout(io.StringIO()):
        #     policy_result = self.policy_agent(policy_prompt)
        #     policy_result = self.clean_response(policy_result)
        #     policy_parsed = self.parse_structured_response(policy_result)
        #     results["policy"] = policy_parsed
        policy_parsed = policy_result
        results["policy"] = policy_parsed
        
        # VALIDATE POLICY RESPONSE
        is_policy_complete, policy_missing = self.is_response_complete("policy", policy_parsed)
        if not is_policy_complete:
            return f"We encountered an issue validating your request against company policy. Please try again. (Missing: {', '.join(policy_missing)})"
        
        # Stop workflow if policy rejected the leave
        approved = policy_parsed.get("approved", "").lower()
        if approved != "true":
            self.context["pending_submission"] = None
            self.context["awaiting_confirmation"] = False
            return (
                f"Your leave request cannot be submitted.\n\n"
                f"Reason: {policy_parsed.get('message', 'Policy validation failed.')}"
            )

        # Step 5: Store pending submission and await confirmation
        self.context["pending_submission"] = request
        self.context["awaiting_confirmation"] = True

        execution_time = round(time.time() - start_time, 2)
        results["execution_time"] = execution_time

        confirmation_message = self._format_confirmation_message(results)

        return confirmation_message

    def _execute_agent_silent(self, agent, prompt):
        """Execute agent with stdout suppression."""
        with redirect_stdout(io.StringIO()):
            return agent(prompt)

    def _format_confirmation_message(self, results):
        """Format a natural confirmation message before submission."""
        holiday_info = results.get("holiday", {})
        leave_info = results.get("leave", {})
        policy_info = results.get("policy", {})

        working_days = holiday_info.get('working_days', 'N/A')
        remaining_leave = leave_info.get('remaining_leave', 'N/A')
        policy_status = policy_info.get('policy_status', 'N/A')

        leave_type_display = self.context['leave_type'].capitalize() if self.context['leave_type'] else 'N/A'
        if self.context["employee_name"]:
            employee_name_display = (
        f"{self.context['employee_name']} "
        f"({self.context['employee_id']})"
        )
        else:
            employee_name_display = self.context["employee_id"]
        message = f"""Your leave request has been validated.
 
                ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                Employee
                {employee_name_display}

                Leave Type
                {leave_type_display}

                Dates
                {self.context['start_date']} to {self.context['end_date']}

                Reason
                {self.context['reason'] if self.context['reason'] else 'N/A'}

                ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                Processing Summary

                Working Days
                {working_days}

                Remaining Leave
                {remaining_leave}

                Policy Status
                {policy_status}

                ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                Would you like me to submit this leave request?

                Reply YES to submit, NO to cancel."""
        return message

    def handle_confirmation_response(self, user_response):
        """Handle user response to confirmation prompt."""
        if self.is_confirmation_response(user_response):
            request = self.context["pending_submission"].copy()
            request["manager_id"] = self.context["manager_id"]
            request["calendar_days"] = self.context["calendar_days"]
            request["working_days"] = self.context["working_days"]
            
            submission_prompt = self.build_agent_prompt("submission", request)
            with redirect_stdout(io.StringIO()):
                submission_result = self.submission_agent(submission_prompt)
                submission_result = self.clean_response(submission_result)
                submission_parsed = self.parse_structured_response(submission_result)

            submission_status = submission_parsed.get("status", "").lower().strip()
            message = submission_parsed.get("message", "").lower().strip()

            is_success = (
                submission_status in ["submitted", "success"] or
                "submitted successfully" in message or
                "successfully" in message and "leave request" in message
            )

            if is_success:
                request_id = submission_parsed.get("request_id", "N/A")
                response = f"""Your leave request has been submitted successfully.

Request ID: {request_id}

An approval request has been sent to your reporting manager.

You'll be notified once your manager approves or rejects your request."""
                
                # FIX: Reset context ONLY after successful submission
                self.reset_context()
                self.context["awaiting_confirmation"] = False
                self.context["pending_submission"] = None
            else:
                error_message = submission_parsed.get("error", submission_parsed.get("message", "Submission failed"))
                response = f"""We encountered an issue while submitting your leave request:

{error_message}

Please try again or contact your HR team for assistance."""

            return response

        elif self.is_cancellation_response(user_response):
            self.context["awaiting_confirmation"] = False
            self.context["pending_submission"] = None
            return "Leave request cancelled. You can apply again whenever you're ready."

        else:
            return "Please reply with YES to submit or NO to cancel."

    def run(self, request):
        """
        Main orchestration entry point.
        FIX #3: Check for pending field response BEFORE intent detection
        """
        self.add_history("user", request)
      


        # Handle greeting
        if self.is_greeting(request):
            response = self.handle_greeting()
            self.add_history("assistant", response)
            return response

        # Handle confirmation response if awaiting confirmation
        if self.context["awaiting_confirmation"]:
            response = self.handle_confirmation_response(request)
            self.add_history("assistant", response)
            return response

        # FIX #3: Check if we're waiting for a specific field response FIRST
        # This prevents the system from running intent detection on field responses
        if self.get_current_field():
            # We're waiting for a specific field
            current_field = self.get_current_field()
            
            if current_field == "employee_id":
                success = self.handle_employee_lookup(request)
                if not success:
                    response = "Employee not found. Please provide a valid Employee ID or name."
                    self.add_history("assistant", response)
                    return response
                self.set_current_field(None)
                if not self.all_information_collected():
                    field, question = self.get_next_missing_field()
                    self.set_current_field(field)
                    welcome = (
                        f"Employee verified.\n\n"
                        f"Welcome {self.context['employee_name']}!\n\n"
                        f"{question}"
                        )
                    self.add_history("assistant", welcome)
                    return welcome
            else:
                self.update_context(current_field, request)

            self.set_current_field(None)
            
            # Check if we can continue with workflow
            if not self.all_information_collected():
                field, question = self.get_next_missing_field()
                self.set_current_field(field)
                self.add_history("assistant", question)
                return question
            else:
                # All information collected - execute workflow
                request_obj = self.build_request()
                response = self.execute_workflow(request_obj)
                self.add_history("assistant", response)
                return response

        # Extract information early
        self.extract_information(request)

        # Detect intent
        if not self.context["routing"]:
            routing = detect_intent(request)
         
            self.context["routing"] = routing
        else:
            routing = self.context["routing"]

        # Handle unknown query
        if self.is_unknown_query(routing.get("intent")):
            response = self.handle_unknown_query()
            self.add_history("assistant", response)
            return response

        # Handle general questions (no workflow)
        if not routing.get("workflow", False):
            # Check if employee_id is needed
            intent = routing.get("intent", "")
            needs_employee_id = intent in ["employee", "leave", "policy"]
            query_lower = request.lower()
            lookup_by_name = (
                "my name is" in query_lower
                or "employee id by name" in query_lower
                or "find my employee id" in query_lower
                or "get my employee id" in query_lower
            )
            if needs_employee_id and not self.context["employee_id"] and not lookup_by_name:
                response = "May I know your Employee ID to retrieve this information?"
                self.context["routing"] = routing
                self.set_current_field("employee_id")
                self.add_history("assistant", response)
                return response
            response = self.route_request(routing, request)
            response = self.clean_response(response)
            self.context["routing"] = None
            self.set_current_field(None)
            self.add_history("assistant", response)
            return response

        # Leave Application Workflow
        if not self.all_information_collected():
            field, question = self.get_next_missing_field()
            self.set_current_field(field)
            self.add_history("assistant", question)
            return question

        # All information collected - execute workflow
        request_obj = self.build_request()
        response = self.execute_workflow(request_obj)

        self.add_history("assistant", response)

        return response