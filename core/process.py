import re
from core.dispatch import handle_action
from intent import interpret, check_needs_clarification, merge_clarification
from memory.context import make_context
from utils import clean_text


_DEBUG_COMMANDS = {
    "edith facts", "edith aliases", "edith context",
    "edith collections", "edith learned", "edith history",
    "edith last error",
}

_AFFIRMATIVE = {
    "yes", "yeah", "yep", "yup", "correct", "confirm", "sure",
    "do it", "update it", "ok", "okay", "y",
}

_NEGATIVE = {
    "no", "nope", "nah", "cancel", "keep it", "leave it",
    "never mind", "nevermind", "n",
}


def _phrases(text: str):
    """Splits an utterance into the whole string plus its clause-level parts,
    so 'yes, update it' can match on 'yes'."""
    parts = [p.strip() for p in re.split(r"[,.!;]+", text) if p.strip()]
    return [text, *parts]


def _is_affirmative(text: str) -> bool:
    return any(p in _AFFIRMATIVE for p in _phrases(text))


def _is_negative(text: str) -> bool:
    return any(p in _NEGATIVE for p in _phrases(text))


def process_input(user_input: str, ctx: dict = None) -> dict:
    if ctx is None:
        ctx = make_context()

    raw = clean_text(user_input)

    if not raw:
        return handle_action({"action": "empty"}, ctx)

    lowered = raw.lower()

    if lowered in _DEBUG_COMMANDS:
        return handle_action({"action": "debug_command", "name": lowered}, ctx)

    m = re.match(r"^edith dump (.+)$", lowered)
    if m:
        return handle_action({"action": "debug_dump_subject", "subject": m.group(1).strip()}, ctx)

    if ctx.get("pending_conflict"):
        # Check the negative first so 'no, update it' isn't read as consent.
        if _is_negative(lowered):
            return handle_action({"action": "reject_conflict"}, ctx)
        if _is_affirmative(lowered):
            return handle_action({"action": "confirm_conflict"}, ctx)

    if ctx.get("pending_clarification"):
        return _resume_clarification(raw, lowered, ctx)

    action_data = interpret(raw, ctx)
    action_data["raw"] = raw

    return handle_action(action_data, ctx)


def _resume_clarification(raw: str, lowered: str, ctx: dict) -> dict:
    """Feeds the user's answer back into the action that was waiting on it."""
    state = ctx["pending_clarification"]
    ctx["pending_clarification"] = None

    if _is_negative(lowered):
        return handle_action({"action": "cancel_clarification"}, ctx)

    merged = merge_clarification(raw, state)
    merged["raw"] = raw

    # The answer may still leave another required field empty — ask again.
    followup = check_needs_clarification(merged)
    if followup:
        return handle_action(
            {"action": "trigger_clarification", "clarification_state": followup}, ctx
        )

    return handle_action(merged, ctx)
