_RESPONSES = {
    "empty": "I'm listening.",
    "greeting": "Hello. What can I do for you?",
    "social": "I am operating normally. All systems go.",
    "farewell": "Goodbye. Shutting down active listening.",
    "unknown": "I'm not sure how to handle that.",
    "confirm": "Done.",
    "not_found": "I couldn't find a record of that.",
}

def say(key: str) -> str:
    """Returns the standardized EDITH voice string for a given key."""
    return _RESPONSES.get(key, _RESPONSES["unknown"])