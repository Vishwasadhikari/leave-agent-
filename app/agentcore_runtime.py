from uuid import uuid4

from bedrock_agentcore import (
    BedrockAgentCoreApp,
    BedrockAgentCoreContext,
)

from app.agents.orchestrator import LeaveOrchestrator

app = BedrockAgentCoreApp()

# Store one orchestrator per session
orchestrators = {}


def get_orchestrator(session_id: str):
    if session_id not in orchestrators:
        orchestrators[session_id] = LeaveOrchestrator()
    return orchestrators[session_id]


@app.entrypoint
def invoke(payload: dict, context: BedrockAgentCoreContext):
    """
    Expected payload:
    {
        "prompt": "I want to apply for leave"
    }
    """

    prompt = payload.get("prompt", "")

    # Use AgentCore session id if available
    session_id = getattr(context, "session_id", None)

    if not session_id:
        session_id = str(uuid4())

    orchestrator = get_orchestrator(session_id)

    try:
        response = orchestrator.run(prompt)

        return {
            "session_id": session_id,
            "response": response
        }

    except Exception as e:
        return {
            "session_id": session_id,
            "response": f"Error: {str(e)}"
        }


if __name__ == "__main__":
    app.run()