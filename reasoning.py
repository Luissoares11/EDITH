from typing import Optional, Dict, Any, List
from memory.store import find_facts

def check_conflict(subject: str, relation: str, new_object: str) -> Optional[Dict[str, Any]]:
    """Checks if a new fact contradicts an existing one."""
    facts = find_facts(subject=subject, relation=relation)
    if facts:
        existing = facts[0]
        if existing["object"].lower() != new_object.lower():
            return existing
    return None

def store_pending_conflict(subject: str, relation: str, new_val: str, existing_val: str):
    """Stub - State is tracked dynamically in context (ctx) within dispatch.py."""
    pass

def infer_implicit_facts(subject: str, relation: str, object_: str) -> List[Dict[str, Any]]:
    """Infers related metadata when a fact is added."""
    inferred = []
    # Future hook: If setting a birth year, calculate and return an age update
    return inferred

def resolve_transitive(subject: str, relation: str) -> Optional[Dict[str, Any]]:
    """
    Resolves multi-step queries (e.g. asking for the age of 'my brother' 
    returns the age of 'John' if John is stored as the brother).
    """
    return None  # Placeholder until advanced graph traversal is re-enabled