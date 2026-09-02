import re

from .dispatch import handle_action
from ..intent.llm import interpret
from ..memory.context import make_context
from ..utils import clean_text


_DEBUG_COMMANDS = {
    "edith facts", "edith aliases", "edith context",
    "edith collections", "edith learned", "edith history",
    "edith last error",
}


def process_input(user_input: str, ctx: dict = None) -> dict:
    if ctx is None:
        ctx = make_context()

    raw = user_input.strip()

    if not raw:
        return handle_action({"action": "empty"}, ctx)

    lowered = raw.lower()

    if lowered in _DEBUG_COMMANDS:
        return handle_action({"action": "debug_command", "name": lowered}, ctx)

    m = re.match(r"^edith dump (.+)$", lowered)
    if m:
        return handle_action({"action": "debug_dump_subject", "subject": m.group(1).strip()}, ctx)

    if ctx.get("pending_conflict"):
        t = lowered
        if t in {"yes", "yeah", "yep", "correct", "confirm", "sure", "do it", "update it"}:
            return handle_action({"action": "confirm_conflict"}, ctx)
        if t in {"no", "nope", "nah", "cancel", "keep it", "leave it"}:
            return handle_action({"action": "reject_conflict"}, ctx)

    if ctx.get("pending_clarification"):
        # Resolution logic for an outstanding clarification question goes
        # here once intent/clarify.py is built — placeholder for now.
        pass

    action_data = interpret(raw)
    action_data["raw"] = raw

    result = handle_action(action_data, ctx)

    return result