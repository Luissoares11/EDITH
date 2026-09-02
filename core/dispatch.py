from core.errors import EdithError, InternalError
from memory.store import (
    add_fact, find_facts, delete_facts, replace_fact, dump_subject,
    list_entities, set_collection, get_collection, list_collections,
    add_collection_item, remove_collection_item, replace_collection_item,
    delete_collection, add_alias, get_aliases
)
from memory.resolver import resolve_entity, infer_entity_from_relation_target, push_entity
from reasoning import (
    check_conflict, store_pending_conflict, infer_implicit_facts, resolve_transitive
)
from relations import (
    REL_NAME, REL_AGE, REL_RELATIONSHIP, REL_BIRTHDAY,
    REL_OCCUPATION, REL_LOCATION, REL_NATIONALITY, relation_display
)
from personality import say
from utils import clean_text, title_name, fuzzy_collection_name


# ── formatters ────────────────────────────────────────────────

def format_fact_list(facts):
    if not facts:
        return say("unknown")
    return "\n".join(f"- {fact['object']}" for fact in facts)


def format_collection(collection):
    if not collection or not collection["items"]:
        return say("unknown")
    return "\n".join(f"- {item}" for item in collection["items"])


def format_entity_profile(entity_name, facts):
    if not facts:
        return say("unknown")

    display_name = title_name(entity_name)

    if entity_name == "user":
        lines = []
        for fact in facts:
            if fact["relation"] == REL_NAME:
                lines.append(f"Your name is {fact['object']}.")
            elif fact["relation"] == REL_AGE:
                lines.append(f"You are {fact['object']} years old.")
            elif fact["relation"] == REL_BIRTHDAY:
                lines.append(f"Your birthday is {fact['object']}.")
            elif fact["relation"] == REL_OCCUPATION:
                lines.append(f"You are a {fact['object']}.")
            elif fact["relation"] == REL_LOCATION:
                lines.append(f"You live in {fact['object']}.")
            elif fact["relation"] == REL_NATIONALITY:
                lines.append(f"You are from {fact['object']}.")
            else:
                lines.append(f"- {relation_display(fact['relation'])}: {fact['object']}")
        return "\n".join(lines)

    relationship = None
    age = None
    other = []

    for fact in facts:
        if fact["relation"] == REL_RELATIONSHIP:
            relationship = fact["object"]
        elif fact["relation"] == REL_AGE:
            age = fact["object"]
        else:
            other.append(fact)

    if relationship and age and not other:
        return f"{display_name} is your {relationship} and is {age} years old."

    lines = [f"{display_name}:"]
    for fact in facts:
        lines.append(f"  - {relation_display(fact['relation'])}: {fact['object']}")
    return "\n".join(lines)


def format_knowledge():
    entities = list_entities()
    user_facts = find_facts(subject="user")
    user_collections = list_collections(owner="user")

    fact_names = []
    for fact in user_facts:
        if fact["relation"] == REL_NAME:
            fact_names.append("my name")
        elif fact["relation"] == REL_AGE:
            fact_names.append("my age")

    collection_names = [c["name"] for c in user_collections]
    items = sorted(set(entities + fact_names + collection_names))

    if not items:
        return "I don't know anything yet."

    return "\n".join(f"- {item}" for item in items)


def _position_to_index(position: str, length: int):
    mapping = {"first": 0, "second": 1, "third": 2, "last": length - 1}
    return mapping.get(position)


# ── handlers: conversational ─────────────────────────────────

def _handle_empty(a, ctx):
    return say("empty")


def _handle_greeting(a, ctx):
    return say("greeting")


def _handle_social(a, ctx):
    return say("social")


def _handle_farewell(a, ctx):
    return say("farewell")


# ── handlers: debug (scaffold only — commands added later) ────

def _handle_debug_command(a, ctx):
    name = a.get("name", "")
    # Individual debug commands (facts, aliases, context, collections,
    # learned, history, last_error) are wired up separately.
    return say("unknown")


def _handle_debug_dump_subject(a, ctx):
    subject = resolve_entity(a["subject"])
    facts = dump_subject(subject)
    if not facts:
        return "Nothing stored for that subject."
    return format_entity_profile(subject, facts)


# ── handlers: knowledge/entities ───────────────────────────────

def _handle_list_entities(a, ctx):
    entities = list_entities()
    if not entities:
        return "I don't know anyone yet."
    return "\n".join(f"- {entity}" for entity in entities)


def _handle_list_knowledge(a, ctx):
    return format_knowledge()


def _handle_batch_store(a, ctx):
    for item in a["items"]:
        handle_action(item, ctx)
    return f"{say('confirm')} I will remember that."


def _handle_store_fact(a, ctx):
    subject  = resolve_entity(a["subject"])
    relation = a["relation"]
    object_  = a["object"]
    replace  = a.get("replace", False)

    if replace:
        conflict = check_conflict(subject, relation, object_)
        if conflict:
            store_pending_conflict(subject, relation, object_, conflict["object"])
            ctx["pending_conflict"] = {
                "subject":  subject,
                "relation": relation,
                "new":      object_,
                "existing": conflict["object"],
            }
            name = "your" if subject == "user" else subject.title() + "'s"
            return (
                f"I already have {name} {relation} as '{conflict['object']}'. "
                f"Do you want me to update it to '{object_}'?"
            )

    if replace:
        replace_fact(subject, relation, object_)
    else:
        add_fact(subject, relation, object_)

    inferred = infer_implicit_facts(subject, relation, object_)
    note = ""
    for inf in inferred:
        if inf["type"] == "implicit_relationship_age":
            note = f" I also know they are {inf['object']} years old."

    if subject == "user":
        return f"{say('confirm')} I will remember your {relation_display(relation)}.{note}"
    return f"{say('confirm')} I will remember {subject.title()}'s {relation_display(relation)}.{note}"


def _handle_store_person_relation(a, ctx):
    subject = clean_text(a["subject"])
    relation_value = a["relation_value"]

    replace_fact(subject, REL_RELATIONSHIP, relation_value)

    first_name = subject.split()[0]
    add_alias(first_name, subject)
    add_alias(f"my {relation_value}", subject)

    return f"{say('confirm')} I will remember {subject}."


def _handle_query_fact(a, ctx):
    subject  = resolve_entity(a["subject"])
    relation = a["relation"]

    facts = find_facts(subject=subject, relation=relation)

    if not facts:
        transitive = resolve_transitive(subject, relation)
        if transitive:
            age  = transitive["facts"][0]["object"]
            real = transitive["subject"].title()
            via  = transitive["via"]
            return f"{real} ({via}) is {age} years old."

    if not facts:
        if subject == "user" and relation == REL_AGE:
            return "I don't know your age yet."
        if relation == REL_AGE:
            return f"I know who {subject} is, but I don't know their age yet."
        return say("unknown")

    if subject != "user":
        push_entity(subject, ctx)

    ctx["last_question_type"] = "age" if relation == REL_AGE else None

    if relation == REL_AGE:
        age = facts[0]["object"]
        if subject == "user":
            return f"You are {age} years old."
        return f"{subject.title()} is {age} years old."

    return format_entity_profile(subject, facts)


def _handle_query_entity(a, ctx):
    subject = resolve_entity(a["subject"])
    facts   = find_facts(subject=subject)

    if not facts:
        return say("unknown")

    push_entity(subject, ctx)
    ctx["last_entity_facts"]  = facts
    ctx["last_question_type"] = "who"
    return format_entity_profile(subject, facts)


def _handle_query_by_relation_value(a, ctx):
    relation = a["relation"]
    object_  = a["object"]

    if relation == REL_RELATIONSHIP:
        entity = infer_entity_from_relation_target(object_)
        if entity:
            facts = find_facts(subject=entity)
            return format_entity_profile(entity, facts)

    return say("unknown")


def _handle_delete_fact(a, ctx):
    subject  = resolve_entity(a["subject"])
    relation = a["relation"]
    deleted  = delete_facts(subject=subject, relation=relation)

    if not deleted:
        return "I couldn't find that information."

    if subject == "user":
        return f"{say('confirm')} I forgot your {relation_display(relation)}."
    return f"{say('confirm')} I forgot {subject}'s {relation_display(relation)}."


def _handle_delete_entity(a, ctx):
    subject = resolve_entity(a["subject"])
    deleted = delete_facts(subject=subject)

    if not deleted:
        return say("unknown")

    return f"{say('confirm')} I forgot '{subject}'."


# ── handlers: collections ───────────────────────────────────────

def _handle_set_collection(a, ctx):
    set_collection(a["owner"], a["name"], a["items"])
    ctx["last_collection_owner"] = a["owner"]
    ctx["last_collection_name"]  = a["name"]
    return f"{say('confirm')} I will remember '{a['name']}'."


def _handle_query_collection(a, ctx):
    owner = a["owner"]
    name  = a["name"]

    known = [c["name"] for c in list_collections(owner=owner)]
    name  = fuzzy_collection_name(name, known)

    collection = get_collection(owner, name)
    if not collection:
        return say("not_found")

    ctx["last_collection_owner"] = owner
    ctx["last_collection_name"]  = name
    return format_collection(collection)


def _handle_delete_collection(a, ctx):
    deleted = delete_collection(a["owner"], a["name"])
    if not deleted:
        return say("unknown")
    return f"{say('confirm')} I forgot '{a['name']}'."


def _handle_add_to_last_collection(a, ctx):
    owner = ctx.get("last_collection_owner")
    name  = ctx.get("last_collection_name")

    if not owner or not name:
        return "I don't know what collection you're referring to."

    add_collection_item(owner, name, a["item"])
    return f"{say('confirm')} Added '{a['item']}'."


def _handle_replace_in_last_collection(a, ctx):
    owner = ctx.get("last_collection_owner")
    name  = ctx.get("last_collection_name")

    if not owner or not name:
        return "I don't know what collection you're referring to."

    updated = replace_collection_item(owner, name, a["old"], a["new"])
    if not updated:
        return "I couldn't find that item."

    return f"{say('confirm')} Replaced '{a['old']}' with '{a['new']}'."


def _handle_remove_from_last_collection_by_position(a, ctx):
    owner = ctx.get("last_collection_owner")
    name  = ctx.get("last_collection_name")

    if not owner or not name:
        return "I don't know what collection you're referring to."

    collection = get_collection(owner, name)
    if not collection or not collection["items"]:
        return "There is nothing to remove."

    idx = _position_to_index(a["position"], len(collection["items"]))
    if idx is None or idx < 0 or idx >= len(collection["items"]):
        return "That position does not exist."

    removed = remove_collection_item(owner, name, index=idx)
    if removed is None:
        return "That position does not exist."

    return f"{say('confirm')} Removed '{removed}'."


# ── handlers: conflict resolution ─────────────────────────────

def _handle_confirm_conflict(a, ctx):
    pending = ctx.get("pending_conflict")
    if pending:
        replace_fact(pending["subject"], pending["relation"], pending["new"])
        ctx["pending_conflict"] = None
        return f"{say('confirm')} Updated."
    return say("unknown")


def _handle_trigger_clarification(a, ctx):
    """Parks the incomplete action on the context and asks the user for the
    missing field. core.process resumes it on the next turn."""
    state = a["clarification_state"]
    ctx["pending_clarification"] = state
    return state["question"]


def _handle_cancel_clarification(a, ctx):
    ctx["pending_clarification"] = None
    return "Never mind, then."


def _handle_reject_conflict(a, ctx):
    if ctx.get("pending_conflict"):
        ctx["pending_conflict"] = None
        return f"{say('confirm')} Keeping the existing value."
    return say("unknown")


# ── handlers: fallback ──────────────────────────────────────────

def _handle_unconnected(a, ctx):
    """Reached when an action isn't (yet) registered — features not
    reattached yet, or a genuinely unrecognized action."""
    return say("unknown")


# ── registry ──────────────────────────────────────────────────

_HANDLERS = {
    "empty":                                    _handle_empty,
    "greeting":                                 _handle_greeting,
    "social":                                   _handle_social,
    "farewell":                                 _handle_farewell,
    "debug_command":                            _handle_debug_command,
    "debug_dump_subject":                       _handle_debug_dump_subject,
    "list_entities":                            _handle_list_entities,
    "list_knowledge":                           _handle_list_knowledge,
    "batch_store":                              _handle_batch_store,
    "store_fact":                               _handle_store_fact,
    "store_person_relation":                    _handle_store_person_relation,
    "query_fact":                               _handle_query_fact,
    "query_entity":                             _handle_query_entity,
    "query_by_relation_value":                  _handle_query_by_relation_value,
    "delete_fact":                              _handle_delete_fact,
    "delete_entity":                            _handle_delete_entity,
    "set_collection":                           _handle_set_collection,
    "query_collection":                         _handle_query_collection,
    "delete_collection":                        _handle_delete_collection,
    "add_to_last_collection":                   _handle_add_to_last_collection,
    "replace_in_last_collection":               _handle_replace_in_last_collection,
    "remove_from_last_collection_by_position":  _handle_remove_from_last_collection_by_position,
    "confirm_conflict":                         _handle_confirm_conflict,
    "reject_conflict":                          _handle_reject_conflict,
    "trigger_clarification":                    _handle_trigger_clarification,
    "cancel_clarification":                     _handle_cancel_clarification,
}


# ── dispatch ──────────────────────────────────────────────────

def _ok(response: str) -> dict:
    return {"response": response, "ok": True, "error_type": None, "detail": None}


def _err(err: EdithError) -> dict:
    return {"response": err.user_message, "ok": False, "error_type": err.error_type, "detail": err.detail}


def handle_action(action_data: dict, ctx: dict) -> dict:
    action = action_data.get("action", "unknown")
    ctx["last_action"] = action

    handler = _HANDLERS.get(action, _handle_unconnected)

    try:
        response = handler(action_data, ctx)
        result = _ok(response)
    except EdithError as e:
        result = _err(e)
    except Exception as e:
        result = _err(InternalError(detail=str(e)))

    ctx["last_error"] = result if not result["ok"] else None
    return result