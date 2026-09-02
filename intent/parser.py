from .patterns import match_pattern
from .llm import interpret_with_llm
from .clarify import check_needs_clarification

def interpret(user_input: str, ctx: dict = None) -> dict:
    """
    The main intent parsing pipeline.
    1. Try exact regex patterns (fast, free).
    2. Fallback to LLM (smart, handles nuance).
    3. Check if the resulting action needs clarification before returning.
    """
    ctx = ctx or {}
    
    # 1. Fast Pattern Match
    action_data = match_pattern(user_input)
    
    # 2. LLM Fallback
    if not action_data:
        action_data = interpret_with_llm(user_input, ctx)
        
    # 3. Clarification Check
    clarification = check_needs_clarification(action_data)
    if clarification:
        return {
            "action": "trigger_clarification",
            "clarification_state": clarification,
            "response": clarification["question"]
        }
        
    return action_data