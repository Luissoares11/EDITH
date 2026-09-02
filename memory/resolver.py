from memory.store import get_aliases, find_facts
from relations import REL_RELATIONSHIP

def resolve_entity(name: str) -> str:
    """Translates an alias (like 'my brother') to the actual entity name."""
    if not name:
        return ""
    cleaned = name.lower().strip()
    aliases = get_aliases()
    return aliases.get(cleaned, cleaned)

def infer_entity_from_relation_target(target_value: str) -> str | None:
    """Finds an entity based on their relationship value (e.g. finding 'John' if target is 'brother')."""
    facts = find_facts(relation=REL_RELATIONSHIP)
    for fact in facts:
        if fact["object"].lower() == target_value.lower():
            return fact["subject"]
    return None

def push_entity(entity: str, ctx: dict):
    """Pushes an entity to the front of the context stack to resolve pronouns like 'he'/'she'."""
    if ctx is not None:
        stack = ctx.setdefault("recent_entities", [])
        if entity in stack:
            stack.remove(entity)
        stack.insert(0, entity)