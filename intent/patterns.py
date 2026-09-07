import re

# Pre-compile for speed
_PATTERNS = [
    # ── Conversational ──────────────────────────────────────────────
    (re.compile(r"^(hi|hello|hey|wake up)( edith)?$", re.I), 
     lambda m: {"action": "greeting"}),
    
    (re.compile(r"^(goodbye|bye|sleep|go to sleep)( edith)?$", re.I), 
     lambda m: {"action": "farewell"}),
     
    (re.compile(r"^(how are you|are you there|status report)\??$", re.I), 
     lambda m: {"action": "social"}),

    # ── Quick Facts (User) ──────────────────────────────────────────
    (re.compile(r"^my name is (.+)$", re.I), 
     lambda m: {"action": "store_fact", "subject": "user", "relation": "name", "object": m.group(1).strip(), "replace": True}),
     
    (re.compile(r"^what( is|'s) my name\??$", re.I), 
     lambda m: {"action": "query_fact", "subject": "user", "relation": "name"}),
     
    (re.compile(r"^(forget|delete) my (.+)$", re.I), 
     lambda m: {"action": "delete_fact", "subject": "user", "relation": m.group(2).strip()}),

    # ── Collections ─────────────────────────────────────────────────
    (re.compile(r"^(what is|what's) on my (.+) (list|collection)\??$", re.I),
     lambda m: {"action": "query_collection", "owner": "user", "name": m.group(2).strip()}),

    # ── Meta / What I Know ──────────────────────────────────────────
    (re.compile(r"^(what do you know|what do you know about me|edith what do you know|who do you know)\??$", re.I),
     lambda m: {"action": "list_knowledge"}),

    (re.compile(r"^(tell me about|who is) ([a-z]+)\??$", re.I),
     lambda m: {"action": "query_entity", "subject": m.group(2).strip()}),

    (re.compile(r"^(list|show) (all )?(people|entities|friends|contacts)\??$", re.I),
     lambda m: {"action": "list_entities"}),

    # ── Calendar ────────────────────────────────────────────────────
    (re.compile(r"^(add|schedule|create) an? event[:\s]+(.+)$", re.I),
     lambda m: {"action": "calendar_add", "title": m.group(2).strip()}),

    (re.compile(r"^(show|what'?s? on|view) (my )?(calendar|schedule|events?)\??$", re.I),
     lambda m: {"action": "calendar_list"}),

    (re.compile(r"^(delete|remove|cancel) (the )?(event|meeting)\s+(.+)$", re.I),
     lambda m: {"action": "calendar_delete", "title": m.group(4).strip()}),

    (re.compile(r"^(update|edit|change|modify) (the )?(event|meeting)\s+(.+)$", re.I),
     lambda m: {"action": "calendar_edit", "title": m.group(4).strip()}),
]

def match_pattern(user_input: str) -> dict | None:
    """Returns an action dict if a regex matches, else None."""
    clean_in = user_input.strip()
    for pattern, builder in _PATTERNS:
        match = pattern.match(clean_in)
        if match:
            return builder(match)
    return None