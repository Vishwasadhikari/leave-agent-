from concurrent.futures import ThreadPoolExecutor
import time

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

    # --------------------------------------------------
    # Temporary execution wrapper
    # Replace this with the proper Strands invocation.
    # --------------------------------------------------

    def execute_agent(self, agent, request):

        print(f"\nRunning {agent.name}...")

        # TODO:
        # Replace this with the correct Strands call.
        #
        # Example (depending on SDK):
        #
        # result = agent.run(request)
        # result = agent.invoke(request)
        #
        # For now we return a placeholder.

        return {
            "agent": agent.name,
            "status": "completed"
        }

    # --------------------------------------------------
    # Human Confirmation
    # --------------------------------------------------

    def human_confirmation(self):

        print("\n========== Human Confirmation ==========\n")

        while True:

            choice = input("Approve Leave Submission? (yes/no): ").lower()

            if choice in ["yes", "y"]:
                return True

            if choice in ["no", "n"]:
                return False

            print("Please enter yes or no.")

    # --------------------------------------------------
    # Sequential Execution
    # --------------------------------------------------

    def run_sequential(self, request):

        start_time = time.time()

        print("\n======================================")
        print(" SEQUENTIAL EXECUTION")
        print("======================================")

        employee = self.execute_agent(
            self.employee_agent,
            request
        )

        holiday = self.execute_agent(
            self.holiday_agent,
            request
        )

        leave = self.execute_agent(
            self.leave_agent,
            request
        )

        policy = self.execute_agent(
            self.policy_agent,
            {
                "employee": employee,
                "holiday": holiday,
                "leave": leave
            }
        )

        if self.human_confirmation():

            submission = self.execute_agent(
                self.submission_agent,
                request
            )

        else:

            submission = {

                "status": "Cancelled by user"

            }

        execution_time = time.time() - start_time

        return {

            "mode": "Sequential",

            "employee": employee,

            "holiday": holiday,

            "leave": leave,

            "policy": policy,

            "submission": submission,

            "execution_time": round(execution_time, 2)

        }

    # --------------------------------------------------
    # Parallel Execution
    # --------------------------------------------------

    def run_parallel(self, request):

        start_time = time.time()

        print("\n======================================")
        print(" PARALLEL EXECUTION")
        print("======================================")

        employee = self.execute_agent(
            self.employee_agent,
            request
        )

        with ThreadPoolExecutor(max_workers=3) as executor:

            holiday_future = executor.submit(
                self.execute_agent,
                self.holiday_agent,
                request
            )

            leave_future = executor.submit(
                self.execute_agent,
                self.leave_agent,
                request
            )

            policy_future = executor.submit(
                self.execute_agent,
                self.policy_agent,
                request
            )

            holiday = holiday_future.result()

            leave = leave_future.result()

            policy = policy_future.result()

        print("\nMerging Parallel Results...")

        merged = {

            "employee": employee,

            "holiday": holiday,

            "leave": leave,

            "policy": policy

        }

        if self.human_confirmation():

            submission = self.execute_agent(
                self.submission_agent,
                merged
            )

        else:

            submission = {

                "status": "Cancelled by user"

            }

        execution_time = time.time() - start_time

        return {

            "mode": "Parallel",

            "results": merged,

            "submission": submission,

            "execution_time": round(execution_time, 2)

        }

    # --------------------------------------------------
    # Main Entry Point
    # --------------------------------------------------

    def run(self, request, execution_mode="sequential"):

        execution_mode = execution_mode.lower()

        if execution_mode == "parallel":

            return self.run_parallel(request)

        return self.run_sequential(request)