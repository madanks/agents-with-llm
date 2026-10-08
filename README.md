# agents-with-llm : LLM Provider Calls & Tool-Using Agents

A hands-on project for building LLM-powered agents with OpenAI function calling. It starts with calling OpenAI, Anthropic and Gemini from one script, then builds two tool-using agents on top of simulated business data: a CRM lead qualifier and a Level 1 IT incident responder.

---

## What's Inside

| Module | Description |
| --- | --- |
| `src/llm/calling_llm.py` | Query helpers for OpenAI, Anthropic (Claude) and Google (Gemini), each with provider-specific error handling. |
| `src/agents/crm_lead_qualifier_agent.py` | Takes a lead's email, looks up company info and CRM history, scores the lead High/Medium/Low, and writes a summary for the sales rep. |
| `src/agents/it_support_Agent.py` | First-responder agent for server incidents: checks health and logs, restarts a service when CPU is critical (> 90%), and escalates to a human for complex issues such as a "Payment Gateway Error". |
| `src/agents/schema/` | JSON tool schemas the agents pass to the model. |
| `src/agents/data/` | Simulated CRM, company, server-metrics and log data as JSON. |

---

## Key Learning Objectives

- **Multi-Provider LLM Calls:** Call the OpenAI, Anthropic and Gemini APIs from one codebase and handle each SDK's errors specifically.
- **Function Calling & Tool Schemas:** Describe Python tools to the model as JSON schemas (description, when to use it, parameters) and map tool names to real functions.
- **The Agent Loop:** Implement the Think -> Act -> Observe cycle, feeding each tool result back to the model until it can answer directly.
- **Decision Rules in Prompts:** Steer an agent to investigate, act (restart) or escalate to a human using a system prompt and tool descriptions.
- **Data-Driven Design:** Keep simulated data and tool schemas in JSON files so they can change without touching agent logic.
- **Safe Configuration:** Load API keys from a `.env` file and keep secrets out of the code.

---

## Quick Start

### Prerequisites

- **Python 3.xx**
- An active **OpenAI API Key**

### Setup Instructions

#### 1. Clone & Set Up Virtual Environment

**macOS / Linux:**

```bash
git clone <repo-url>
cd agents-with-llm
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**

```powershell
git clone <your-repo-url>
cd agents-with-llm
py -3 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

#### 2. Install Dependencies

```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Environment Configuration

Copy the template configuration file:

```bash
# macOS/Linux:
cp .env.example .env

# Windows (PowerShell):
Copy-Item .env.example .env
```

Set your API credentials in `.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
CLAUDE_API_KEY=your_claude_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

#### 4. Run the Modules

Run everything from the `src/` folder so the `llm` and `agents` imports resolve:

```bash
cd src
python3 -m llm.calling_llm
python3 -m agents.crm_lead_qualifier_agent
python3 -m agents.it_support_Agent
```
