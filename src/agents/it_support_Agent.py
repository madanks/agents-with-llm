# =============================================================================
# IT Support Agent (Level 1 Incident Responder)
# =============================================================================
#
# OVERVIEW
#   Coding assignment: build an AI agent that serves as the first responder
#   when someone reports a server problem.
#
# PREREQUISITES
#   - The openai library is installed.
#   - An API key is available under the name OPENAI_APIKEY (in the original
#     notebook setup, a secret variable with access enabled).
#
# WHAT THE AGENT SHOULD DO
#   1. Investigate
#        When an issue is reported, look at server health and the logs.
#   2. Act
#        If CPU usage is critical (above 90%), restart the service.
#   3. Escalate
#        Hand off to a human if the problem looks complex or the logs contain
#        "Payment Gateway Error".
# =============================================================================
import json
import os
from functools import lru_cache
from pathlib import Path
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv

load_dotenv()

SERVER_METRICS_PATH = Path(__file__).parent / "data" / "server_metrics.json"
SERVER_LOGS_PATH = Path(__file__).parent / "data" / "server_logs.json"
TOOLS_SCHEMA_PATH = Path(__file__).parent / "schema" / \
    "it_support_tools_schema.json"


@lru_cache(maxsize=None)
def load_json(path: Path):
    """Reads and parses a JSON file (cached, so each file is read once)."""
    with open(path, encoding="utf-8") as json_file:
        return json.load(json_file)


# Initialize Client
try:
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
except OpenAIError as e:
    print(f"Error initializing OpenAI client: {e}")
    print("Please ensure your OPENAI_API_KEY is set in your environment variables.")


def get_server_health(server_id: str) -> str:
    """Returns CPU and Memory usage for a given server."""
    print(f"-> TOOL: Checking health for {server_id}...")

    result = load_json(SERVER_METRICS_PATH).get(
        server_id, {"error": "Server not found. Check the ID."})
    return json.dumps(result)


def fetch_recent_logs(server_id: str, lines: int = 5) -> str:
    """Returns the last N lines of logs."""
    print(f"-> TOOL: Fetching last {lines} log lines for {server_id}...")

    # Different logs per server trigger different agent behaviors
    server_logs = load_json(SERVER_LOGS_PATH)
    logs = server_logs.get(
        server_id, ["[INFO] System stable", "[INFO] Heartbeat signal received"])
    return json.dumps({"logs": logs[:lines]})


def restart_service(server_id: str) -> str:
    """Simulates a service restart."""
    print(f"-> TOOL: Restarting service {server_id}...")

    # In a real scenario, this would run API call
    return json.dumps({
        "server_id": server_id,
        "status": "success",
        "message": "Service restart command issued successfully.",
    })


def escalate_to_engineer(summary: str) -> str:
    """Simulates sending an alert to a human."""
    print(f"-> TOOL: Escalating to human engineer. Reason: {summary}")

    # In a real scenario, this would send a realtime alert
    return json.dumps({
        "status": "escalated",
        "ticket_id": "INC-999",
        "assigned_to": "On-Call Engineer",
    })


# Map of tool names (as the model calls them) to the Python functions
AVAILABLE_FUNCTIONS = {
    "get_server_health": get_server_health,
    "fetch_recent_logs": fetch_recent_logs,
    "restart_service": restart_service,
    "escalate_to_engineer": escalate_to_engineer,
}

tools_schema = load_json(TOOLS_SCHEMA_PATH)


SYSTEM_PROMPT = (
    "You are a Level 1 IT Responder. Investigate server issues. "
    "If CPU or Memory is > 90%, restart the service. If logs show critical "
    "dependency errors (like connection refused) that a restart won't fix, "
    "escalate to an engineer."
)


def run_it_agent(user_issue: str):
    """Runs the think/act/observe loop for a single reported incident."""
    print(f"\n--- New Incident: {user_issue} ---")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_issue},
    ]

    for _ in range(5):
        print("\n[AI Thinking...]")
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            tools=tools_schema,
            tool_choice="auto",
        )

        response_msg = response.choices[0].message
        messages.append(response_msg)

        if not response_msg.tool_calls:
            print(f"\n[FINAL RESPONSE]: {response_msg.content}")
            break

        for tool_call in response_msg.tool_calls:
            func_name = tool_call.function.name
            function_to_call = AVAILABLE_FUNCTIONS.get(func_name)

            if function_to_call:
                func_args = json.loads(tool_call.function.arguments)
                tool_output = function_to_call(**func_args)
            else:
                tool_output = json.dumps(
                    {"error": f"Unknown function: {func_name}"})

            # Link the output to its request via tool_call_id
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": func_name,
                "content": tool_output,
            })


def main():
    """Runs the demo scenario"""
    # Should trigger a restart (CPU is 98%)
    run_it_agent("The payment-server-01 is extremely slow and timing out.")

    # This is a healthy case
    run_it_agent("Something is wrong with db-node-02")

    # Agent should see Memory 95% + OutOfMemoryError logs -> Restart
    run_it_agent("Users are reporting login failures on auth-service-03.")

    # Agent should see healthy CPU but "Connection Refused" logs -> Escalate
    run_it_agent("Search isn't working. Can you check search-index-09?")

    # Agent should see normal stats and 200 OK logs -> Do nothing / Report healthy
    run_it_agent("Check frontend-node-04")


main()
