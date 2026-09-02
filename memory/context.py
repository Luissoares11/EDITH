def make_context() -> dict:
    """Creates a fresh conversational state dictionary."""
    return {
        "recent_entities": [],
        "last_action": None,
        "last_entity_facts": None,
        "last_question_type": None,
        "last_collection_owner": None,
        "last_collection_name": None,
        "pending_conflict": None,
        "pending_clarification": None,
        "last_error": None,
    }