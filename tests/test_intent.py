from intent.parser import interpret
from memory.context import make_context

def test_fast_pattern_matching_bypasses_llm(monkeypatch):
    # If the LLM is called, this will raise an error and fail the test
    monkeypatch.setattr("intent.llm.interpret_with_llm", lambda *a, **kw: 1/0)
    
    # "hi" should hit the regex pattern in patterns.py instantly
    res = interpret("hi")
    assert res["action"] == "greeting"

def test_llm_fallback(mock_llm):
    # Mock the LLM returning a proper action for a complex query
    mock_llm({"action": "query_fact", "subject": "tony", "relation": "project"})
    
    # A phrase that patterns.py won't catch
    res = interpret("what is tony working on?")
    assert res["action"] == "query_fact"
    assert res["subject"] == "tony"

def test_clarification_interception(mock_llm):
    # Mock the LLM returning an action that is MISSING a required field ("object")
    mock_llm({"action": "store_fact", "subject": "user", "relation": "favorite color"})
    
    res = interpret("my favorite color is")
    
    # The pipeline should intercept it and trigger clarification instead of crashing
    assert res["action"] == "trigger_clarification"
    assert "clarification_state" in res
    assert res["clarification_state"]["missing_field"] == "object"