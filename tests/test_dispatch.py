from core.process import process_input
from memory.context import make_context

def test_process_input_simple_greeting():
    ctx = make_context()
    # "hi" matches regex, gets dispatched to _handle_greeting
    result = process_input("hi", ctx)
    assert result["ok"] is True
    # Assumes personality.say("greeting") is hooked up

def test_conflict_resolution_flow():
    ctx = make_context()
    
    # 1. Manually set a pending conflict in the context
    ctx["pending_conflict"] = {
        "subject": "user",
        "relation": "location",
        "new": "Tokyo",
        "existing": "Paris"
    }
    
    # 2. Say "yes" to confirm the overwrite
    result = process_input("yes, update it", ctx)
    
    assert result["ok"] is True
    assert ctx["pending_conflict"] is None  # Conflict resolved
    
def test_debug_commands_intercepted():
    ctx = make_context()
    result = process_input("edith facts", ctx)
    
    # Should instantly bypass NLP and hit debug handler
    assert ctx["last_action"] == "debug_command"