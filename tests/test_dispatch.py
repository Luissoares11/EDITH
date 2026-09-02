from core.dispatch import handle_action
from core.process import process_input
from memory.context import make_context
from memory.store import add_fact, find_facts

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
    
def test_conflict_rejection_flow():
    ctx = make_context()
    ctx["pending_conflict"] = {
        "subject": "user", "relation": "location",
        "new": "Tokyo", "existing": "Paris",
    }

    # "no" must win over the "update it" that follows it
    result = process_input("no, don't update it", ctx)

    assert result["ok"] is True
    assert ctx["pending_conflict"] is None

def test_debug_commands_intercepted():
    ctx = make_context()
    result = process_input("edith facts", ctx)

    # Should instantly bypass NLP and hit debug handler
    assert ctx["last_action"] == "debug_command"

def test_entity_query_pushes_onto_context_stack():
    # Regression: push_entity was called without ctx, so every non-user
    # lookup died as an internal error.
    add_fact("john", "age", "30")
    ctx = make_context()

    result = handle_action({"action": "query_entity", "subject": "john"}, ctx)

    assert result["ok"] is True
    assert ctx["recent_entities"][0] == "john"

def test_clarification_round_trip(mock_llm):
    # LLM returns a store_fact that is missing its object
    mock_llm({"action": "store_fact", "subject": "user", "relation": "favorite color"})
    ctx = make_context()

    asked = process_input("my favorite color is", ctx)

    assert asked["ok"] is True
    assert ctx["pending_clarification"] is not None
    assert ctx["pending_clarification"]["missing_field"] == "object"

    # The user's next turn answers the question and completes the action
    done = process_input("blue", ctx)

    assert done["ok"] is True
    assert ctx["pending_clarification"] is None
    facts = find_facts("user", "favorite color")
    assert [f["object"] for f in facts] == ["blue"]

def test_clarification_can_be_cancelled(mock_llm):
    mock_llm({"action": "store_fact", "subject": "user", "relation": "favorite color"})
    ctx = make_context()

    process_input("my favorite color is", ctx)
    result = process_input("never mind", ctx)

    assert result["ok"] is True
    assert ctx["pending_clarification"] is None
    assert find_facts("user", "favorite color") == []