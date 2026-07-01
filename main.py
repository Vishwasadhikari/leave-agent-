from app.agents.orchestrator import LeaveOrchestrator


def main():

    print("=" * 60)
    print("Leave Management Multi-Agent System")
    print("=" * 60)

    print("\nExecution Mode")

    print("1. Sequential")

    print("2. Parallel")

    choice = input("\nEnter choice (1/2): ").strip()

    if choice == "2":

        execution_mode = "parallel"

    else:

        execution_mode = "sequential"

    print("\nEnter Leave Details\n")

    employee_id = input("Employee ID : ")

    manager_id = input("Manager ID : ")

    leave_type = input("Leave Type (annual/casual/sick): ")

    start_date = input("Start Date (YYYY-MM-DD): ")

    end_date = input("End Date (YYYY-MM-DD): ")

    reason = input("Reason : ")

    request = {

        "employee_id": employee_id,

        "manager_id": manager_id,

        "leave_type": leave_type,

        "start_date": start_date,

        "end_date": end_date,

        "reason": reason

    }

    orchestrator = LeaveOrchestrator()

    result = orchestrator.run(

        request=request,

        execution_mode=execution_mode

    )

    print("\n")

    print("=" * 60)

    print("Execution Completed")

    print("=" * 60)

    print(result)


if __name__ == "__main__":

    main()