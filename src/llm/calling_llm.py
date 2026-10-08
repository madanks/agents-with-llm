import os
from openai import OpenAI, OpenAIError
import anthropic
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# --- 1. OPENAI (GPT-4, GPT-3.5) ---


def query_openai(prompt):
    """
    Connects to OpenAI's official API.
    """
    print("\n--- Querying OpenAI (GPT-4.1 Mini) ---")
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except OpenAIError as e:
        return f"OpenAI Error: {e}"


# --- 2. ANTHROPIC (Claude 3.5 Sonnet, Opus) ---

def query_anthropic(prompt):
    """
    Connects to Anthropic's official API.
    Note: Uses 'max_tokens' instead of 'max_completion_tokens' typically.
    """
    print("\n--- Querying Anthropic (Claude Haiku 4.5) ---")

    client = anthropic.Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))
    try:
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        # Anthropic response structure is different from OpenAI
        return message.content[0].text
    except anthropic.AnthropicError as e:
        return f"Anthropic Error: {e}"

# --- 3. GOOGLE (Gemini 3.5 Pro/Flash) ---


def query_gemini(prompt):
    """
    Connects to Google's Generative AI API.
    """
    print("\n--- Querying Google (Gemini 3.5 Flash) ---")
    try:
        client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=types.Part.from_text(text=prompt)
        )
        return response.text
    except genai.errors.APIError as e:
        return f"Gemini Error: {e}"


test_prompt = "What is the point of using nosql databases in engineering systems in under 3 sentences"

print(query_openai(test_prompt))
print(query_anthropic(test_prompt))
print(query_gemini(test_prompt))
