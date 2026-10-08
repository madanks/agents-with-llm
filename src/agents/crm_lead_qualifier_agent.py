# =============================================================================
# CRM Lead Qualifier Agent
# =============================================================================
#
# GOAL
#   Build an AI agent that automatically enriches a new sales lead (identified
#   by an email address) by:
#     - gathering publicly available company information,
#     - checking for prior engagement in the internal CRM, and
#     - assigning a preliminary qualification score.
#
# CONTEXT
#   Sales reps spend valuable time manually researching leads and
#   cross-referencing internal systems before a discovery call. This process is
#   slow, inconsistent, and often leads to a poorly prepared first interaction.
#
# AGENT FUNCTIONALITY (the agent must be able to)
#   1. Extract Domain
#        Take the email address and extract the company domain name.
#        e.g., jane@acmecorp.com -> acmecorp.com
#   2. Enrich Company Data
#        Use the domain to look up (simulated) company details such as
#        industry, size, and annual revenue.
#   3. Check CRM History
#        Search the internal (simulated) CRM for any past contact or notes
#        associated with the lead's email.
#   4. Calculate Lead Score
#        Synthesize all gathered data to assign a qualitative priority score
#        (e.g., High, Medium, Low).
#   5. Final Summary
#        Present a concise, actionable summary of all findings to the sales
#        representative.
#
# TECHNICAL IMPLEMENTATION
#   Use the OpenAI client's Function Calling capability to define and execute
#   the necessary business logic tools in a structured loop.
# =============================================================================
import json
import os
from pathlib import Path
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
SCHEMA_PATH = BASE_DIR / "schema" / "crm_tools_schema.json"
DOMAIN_INFO_PATH = BASE_DIR / "data" / "domain_info.json"
CRM_HISTORY_PATH = BASE_DIR / "data" / "crm_history.json"


def load_json(path: Path):
    """Reads and parses a JSON file."""
    with open(path, encoding="utf-8") as json_file:
        return json.load(json_file)


# --- 1. Initialize OpenAI Client ---
try:
    client = OpenAI(api_key=os.getenv('OPENAI_APIKEY'))
except OpenAIError as e:
    print(f"Error initializing OpenAI client: {e}")
    print("Please ensure your OPENAI_API_KEY is set in your environment variables.")


def lookup_domain_info(domain: str) -> str:
    """
    Looks up and returns mock company information based on its domain.
    In a real system, this would call an external API.
    """
    print(f"-> TOOL ACTIVATED: Looking up domain info for {domain}...")

    # Mock database for demonstration / query an API in real time
    mock_data = load_json(DOMAIN_INFO_PATH)
    info = mock_data.get(
        domain, {"industry": "Unknown", "size": "N/A", "revenue": "N/A"})

    # Return the data as a JSON string for the AI model to parse easily
    return json.dumps(info)


def check_crm_history(email: str) -> str:
    """
    Checks the internal CRM system for past engagement history with the lead.
    In a real system, this would query a PostgreSQL database or a CRM API (e.g., Salesforce).
    """
    print(f"-> TOOL ACTIVATED: Checking CRM history for {email}...")

    # Mock database for demonstration
    mock_data = load_json(CRM_HISTORY_PATH)
    history = mock_data.get(email, mock_data["default"])
    return json.dumps(history)


def calculate_lead_score(domain_info: str, crm_history: str) -> str:
    """
    Analyzes the collected data (domain and CRM history) to assign a lead score (High/Medium/Low).
    This function simulates a complex scoring algorithm.
    """
    print("-> TOOL ACTIVATED: Calculating lead score...")

    domain_data = json.loads(domain_info)
    crm_data = json.loads(crm_history)
    score = "Low"

    if domain_data.get("revenue", "").startswith("$1B+"):
        score = "High"
    elif crm_data.get("status") == "Active Opportunity":
        score = "High"
    elif domain_data.get("revenue", "").startswith("$50M"):
        score = "Medium"

    return json.dumps({"lead_score": score})


# Map of available function names to the actual Python functions
AVAILABLE_FUNCTIONS = {
    "lookup_domain_info": lookup_domain_info,
    "check_crm_history": check_crm_history,
    "calculate_lead_score": calculate_lead_score,
}


# --- 2. Tool Schema: the agent's "menu" ---
# The LLM can't see our Python functions, so each tool is described to it as a
# JSON schema covering:
#   - Description: what the tool does
#   - Context: when the model should reach for it
#   - Parameters: the arguments it expects
# This list is passed via the `tools` parameter of the API call, giving the
# model a menu of actions it can choose from.
tools_schema = load_json(SCHEMA_PATH)


# --- 3. The Agent Loop: Think -> Act -> Observe ---
# run_agent is the core of the app: a feedback loop that lets the model work
# through the task step by step on its own.
#
# Pieces of the loop:
#   - Memory (collected_data): a dictionary created before the loop starts,
#     holding results that need to persist across steps.
#   - Think: send the conversation so far to the model
#     (client.chat.completions.create).
#   - Act: if the model asks for a tool, run the matching Python function.
#   - Observe: add the tool's result to the conversation as a new message so
#     the model can see it on the next turn.
#   - Repeat: keep cycling until the model has enough information and replies
#     to the user directly instead of requesting another tool.
def tool_message(tool_call_id: str, content: str) -> dict:
    """Builds a tool-result message for the conversation history."""
    return {"role": "tool", "tool_call_id": tool_call_id, "content": content}


def run_agent(user_prompt: str):
    """
    The main execution loop for the CRM Lead Qualifier Agent.
    """
    print("\n--- Running Lead Qualifier Agent ---")

    system_prompt = (
        "You are an expert CRM Lead Qualifier Agent. Your sole task is to analyze a sales lead "
        "provided via email address."
        "Find the domain for the lead their history of interaction"
        "Then calculate the lead score for the lead"
        "Finally, synthesize all information (domain info, CRM history, and score) "
        "into a single, easy-to-read summary for a busy sales rep."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for _ in range(10):
        print("\n[AI Thinking...]")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools_schema,
            tool_choice="auto",
        )

        response_message = response.choices[0].message
        messages.append(response_message)

        if not response_message.tool_calls:
            print("\n--- FINAL AGENT SUMMARY ---")
            print(response_message.content)
            break

        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_to_call = AVAILABLE_FUNCTIONS.get(function_name)

            if not function_to_call:
                print(f"Error: Unknown function {function_name}")
                messages.append(tool_message(
                    tool_call.id,
                    json.dumps(
                        {"error": f"Unknown function: {function_name}"}),
                ))
                continue

            try:
                function_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError as e:
                messages.append(tool_message(
                    tool_call.id,
                    json.dumps({"error": f"Invalid arguments JSON: {e}"}),
                ))
                continue

            # Execute the function with model-supplied arguments directly
            function_result = function_to_call(**function_args)

            # Append the tool result as a NEW message
            messages.append(tool_message(tool_call.id, function_result))


SCENARIOS = [
    # High-value lead (large company, needs scoring)
    "Please qualify this lead for my call tomorrow: jane@acmecorp.com",
    # Medium-value lead (active opportunity, needs scoring)
    "Can you run an analysis on this lead: bob@widgetco.net",
]


def main():
    """Runs each demo scenario through the agent."""
    for index, prompt in enumerate(SCENARIOS):
        if index:
            print("\n" + "=" * 80 + "\n")
        run_agent(prompt)


main()
