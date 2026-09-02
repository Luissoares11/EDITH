"""Learning endpoints — correction tracking and preference management."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from memory.store import (
    log_correction, get_corrections, get_correction_patterns,
    set_preference, get_preference, get_preferences,
    confirm_preference, delete_preference
)

router = APIRouter(prefix="/api/learning", tags=["learning"])


# ── Models ────────────────────────────────────────────────────

class CorrectionLog(BaseModel):
    """A logged correction."""
    message_id: int
    intent: str
    field: str
    edith_value: Optional[str] = None
    corrected_value: str
    context: Optional[str] = None


class Preference(BaseModel):
    """A learned or stated preference."""
    category: str
    key: str
    value: str
    learned_from: str = "explicit"
    confidence: float = 1.0


# ── Corrections ───────────────────────────────────────────────

@router.post("/corrections", response_model=Dict[str, int])
async def record_correction(correction: CorrectionLog) -> Dict[str, int]:
    """
    Log a correction when EDITH gets something wrong.

    This is the raw signal for learning — every correction goes here,
    and patterns are mined from this log.

    **Example:** EDITH suggested priority "medium" for a work task,
    but you corrected it to "high".

    - **message_id**: The message ID that prompted this correction
    - **intent**: What EDITH was trying to do (e.g., "create_task")
    - **field**: What field was wrong (e.g., "priority")
    - **edith_value**: What EDITH suggested
    - **corrected_value**: What you changed it to
    - **context**: Optional context (task name, meeting details, etc.)
    """
    correction_id = log_correction(
        message_id=correction.message_id,
        intent=correction.intent,
        field=correction.field,
        corrected_value=correction.corrected_value,
        edith_value=correction.edith_value,
        context=correction.context
    )
    return {"correction_id": correction_id}


@router.get("/corrections", response_model=List[Dict[str, Any]])
async def list_corrections(
    intent: Optional[str] = None,
    field: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get the correction log.

    - **intent**: Filter by intent (e.g., "create_task")
    - **field**: Filter by field (e.g., "priority")
    - **limit**: Maximum number of results (default 100)
    """
    return get_corrections(intent=intent, field=field, limit=limit)


@router.get("/patterns/{intent}", response_model=Dict[str, Any])
async def get_patterns(intent: str) -> Dict[str, Any]:
    """
    Analyze corrections for an intent to find patterns.

    This shows you what EDITH keeps getting wrong and what you
    consistently correct it to — the basis for learning preferences.

    **Example response:**
    ```json
    {
      "intent": "create_task",
      "total_corrections": 15,
      "patterns": [
        {
          "field": "priority",
          "most_corrected_to": "high",
          "frequency": 12,
          "total_corrections": 15
        }
      ]
    }
    ```
    """
    return get_correction_patterns(intent)


# ── Preferences ───────────────────────────────────────────────

@router.post("/preferences", response_model=Dict[str, int])
async def create_preference(pref: Preference) -> Dict[str, int]:
    """
    Create or update a preference.

    Preferences can be **explicit** (you tell EDITH) or **inferred**
    (EDITH learned from corrections). Confidence defaults to 1.0
    for explicit, lower for inferred.

    **Example:** You tell EDITH "I always want high priority for work tasks"

    - **category**: Group (e.g., "tasks", "scheduling", "communication")
    - **key**: Preference name (e.g., "work_priority")
    - **value**: Preference value (e.g., "high")
    - **learned_from**: "explicit" (you said it) or "inferred" (learned from corrections)
    - **confidence**: 1.0 for explicit, 0-1 for inferred (higher = more confident)
    """
    pref_id = set_preference(
        category=pref.category,
        key=pref.key,
        value=pref.value,
        learned_from=pref.learned_from,
        confidence=pref.confidence
    )
    return {"preference_id": pref_id}


@router.get("/preferences", response_model=List[Dict[str, Any]])
async def list_preferences(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all learned/stated preferences.

    - **category**: Optional filter (e.g., "tasks", "scheduling")
    """
    return get_preferences(category=category)


@router.get("/preferences/{category}/{key}", response_model=Dict[str, Any])
async def get_preference_detail(category: str, key: str) -> Dict[str, Any]:
    """Get a specific preference."""
    pref = get_preference(category, key)
    if not pref:
        raise HTTPException(status_code=404, detail=f"Preference {category}/{key} not found")
    return pref


@router.post("/preferences/{category}/{key}/confirm", response_model=Dict[str, str])
async def confirm_pref(category: str, key: str) -> Dict[str, str]:
    """
    Confirm an inferred preference.

    When EDITH infers a preference from corrections but you want to
    explicitly validate it, confirm it here. This sets confidence to 1.0.

    **Use case:** EDITH inferred "you prefer high priority for work tasks"
    based on corrections, and you say "yes, that's right."
    """
    confirmed = confirm_preference(category, key)
    if not confirmed:
        raise HTTPException(status_code=404, detail=f"Preference {category}/{key} not found")
    return {"message": f"Confirmed {category}/{key}"}


@router.delete("/preferences/{category}/{key}", response_model=Dict[str, str])
async def remove_preference(category: str, key: str) -> Dict[str, str]:
    """Delete a preference."""
    deleted = delete_preference(category, key)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Preference {category}/{key} not found")
    return {"message": f"Deleted {category}/{key}"}
