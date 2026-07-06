from app.agents.orchestrator import LeaveOrchestrator


def main():

    print("=" * 60)
    print("Leave Management Multi-Agent System")
    print("=" * 60)

    orchestrator = LeaveOrchestrator()

    print("\nType 'exit' to quit.\n")

    while True:

        query = input("You : ").strip()

        if query.lower() == "exit":

            print("\nGoodbye!")

            break

        print("\nAssistant:\n")

        try:

            response = orchestrator.run(query)

            print(response)

        except Exception as e:

            print(f"\nError: {e}")

            import traceback
            traceback.print_exc()

        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":

    main()