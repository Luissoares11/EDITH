import json
import re
import anthropic

from config import ANTHROPIC_API_KEY

SYSTEM_PROMPT = """You are the intent parser for EDITH, an AI assistant.
Analyze the user's input and return a SINGLE JSON object representing the action to take.
Do NOT output markdown formatting (like ```json). Just the raw JSON object.

Available actions and their required keys:
- greeting
- social
- farewell
- store_fact: { "action": "store_fact", "subject": "...", "relation": "...", "object": "...", "replace": true/false }
- query_fact: { "action": "query_fact", "subject": "...", "relation": "..." }
- query_entity: { "action": "query_entity", "subject": "..." }
- set_collection: { "action": "set_collection", "owner": "...", "name": "...", "items": ["..."] }
- query_collection: { "action": "query_collection", "owner": "...", "name": "..." }
- add_to_last_collection: { "action": "add_to_last_collection", "item": "..." }
- delete_fact: { "action": "delete_fact", "subject": "...", "relation": "..." }
- unknown: { "action": "unknown" }

Rules:
1. If the user refers to themselves, the subject/owner is "user".
2. If the user refers to an item to add to a list but doesn't name the list (e.g., "add milk too"), use "add_to_last_collection".
3. "relation" should be a simple noun (e.g., "age", "location", "brother", "favorite color").
"""

def interpret_with_llm(user_input: str, ctx: dict) -> dict:
    if not ANTHROPIC_API_KEY:
        return {"action": "unknown", "detail": "Missing Anthropic API key"}

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    # We pass recent context so the LLM can resolve pronouns like "how old is HE?"
    context_str = f"Recent entities discussed: {ctx.get('recent_entities', [])}\n\n" if ctx.get("recent_entities") else ""
    user_prompt = f"{context_str}User input: {user_input}"

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=256,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.0
        )
        
        raw_text = response.content[0].text.strip()
        # Clean markdown codeblocks if Claude hallucinates them despite instructions
        cleaned_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.IGNORECASE).strip()
        
        data = json.loads(cleaned_text)
        if isinstance(data, dict) and "action" in data:
            return data
            
        return {"action": "unknown"}
        
    except json.JSONDecodeError:
        return {"action": "unknown", "detail": "LLM returned invalid JSON"}
    except Exception as e:
        return {"action": "unknown", "detail": str(e)}