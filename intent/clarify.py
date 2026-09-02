# A map of action types to the fields they absolutely require to function.
_REQUIRED_FIELDS = {
    "store_fact": ["subject", "relation", "object"],
    "query_fact": ["subject", "relation"],
    "query_entity": ["subject"],
    "query_collection": ["owner", "name"],
    "set_collection": ["owner", "name", "items"],
    "add_to_last_collection": ["item"],
    "delete_fact": ["subject", "relation"],
}

# Human-readable prompts to ask the user when a field is missing.
_CLARIFICATION_PROMPTS = {
    "store_fact": {
        "subject": "Who are we storing this fact about?",
        "relation": "What exactly is the relationship or attribute?",
        "object": "What is the value you want me to store for that?"
    },
    "query_fact": {
        "subject": "Whose information did you want to look up?",
        "relation": "What specific detail are you looking for?"
    },
    "query_collection": {
        "name": "Which list or collection do you want me to check?"
    }
}

def check_needs_clarification(action_data: dict) -> dict | None:
    """
    Checks if an action dictionary is missing required fields.
    Returns a clarification state dictionary if missing fields are found, else None.
    """
    action = action_data.get("action")
    if action not in _REQUIRED_FIELDS:
        return None
        
    for field in _REQUIRED_FIELDS[action]:
        # If the field is missing, or is explicitly empty (like an empty string)
        val = action_data.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            
            # Look up a specific question, or fall back to a generic one
            prompts_for_action = _CLARIFICATION_PROMPTS.get(action, {})
            question = prompts_for_action.get(field, f"Could you clarify the {field}?")
            
            return {
                "original_action_data": action_data,
                "missing_field": field,
                "question": question
            }
            
    return None

def merge_clarification(user_input: str, clarification_state: dict) -> dict:
    """
    Takes the user's answer to a clarification question and merges it 
    into the originally pending action data.
    """
    action_data = clarification_state["original_action_data"]
    missing_field = clarification_state["missing_field"]
    
    # Just take their raw input as the missing value
    action_data[missing_field] = user_input.strip()
    return action_data