import httpx
import config
from typing import Optional


class CalendarServiceError(Exception):
    """Raised when the calendar service is unreachable or returns an error."""
    pass


def _validate_config():
    """Ensure calendar service is properly configured."""
    if not config.CALENDAR_SERVICE_URL:
        raise CalendarServiceError(
            "Calendar service is not configured. Set CALENDAR_SERVICE_URL in your environment."
        )
    if not config.CALENDAR_API_TOKEN:
        raise CalendarServiceError(
            "Calendar API token is not configured. Set CALENDAR_API_TOKEN in your environment."
        )


def _headers() -> dict:
    """Generate authorization headers."""
    _validate_config()
    return {"Authorization": f"Bearer {config.CALENDAR_API_TOKEN}"}


def add_event(title: str, event_type: str, date: str, time: str = None, notes: str = None, recurrence: str = "none") -> dict:
    """Add a new event to the calendar."""
    payload = {
        "action": "add",
        "title": title,
        "type": event_type,
        "date": date,
        "recurrence": recurrence,
    }
    if time:
        payload["time"] = time
    if notes:
        payload["notes"] = notes

    try:
        response = httpx.post(
            f"{config.CALENDAR_SERVICE_URL}/events",
            json=payload,
            headers=_headers(),
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except httpx.ConnectError:
        raise CalendarServiceError("Cannot connect to calendar service. Is it running?")
    except httpx.TimeoutException:
        raise CalendarServiceError("Calendar service request timed out.")
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", str(e)) if e.response.text else str(e)
        raise CalendarServiceError(f"Calendar service error: {detail}")
    except httpx.HTTPError as e:
        raise CalendarServiceError(f"Calendar service error: {e}")


def list_events(days: int = 30) -> dict:
    """Retrieve upcoming events from the calendar."""
    try:
        response = httpx.get(
            f"{config.CALENDAR_SERVICE_URL}/events",
            params={"list": "true", "days": days},
            headers=_headers(),
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except httpx.ConnectError:
        raise CalendarServiceError("Cannot connect to calendar service. Is it running?")
    except httpx.TimeoutException:
        raise CalendarServiceError("Calendar service request timed out.")
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", str(e)) if e.response.text else str(e)
        raise CalendarServiceError(f"Calendar service error: {detail}")
    except httpx.HTTPError as e:
        raise CalendarServiceError(f"Calendar service error: {e}")


def edit_event(title: str, new_title: str = None, new_date: str = None, new_time: str = None) -> dict:
    """Update an existing event on the calendar."""
    payload = {"action": "edit", "title": title}
    if new_title:
        payload["new_title"] = new_title
    if new_date:
        payload["new_date"] = new_date
    if new_time:
        payload["new_time"] = new_time

    try:
        response = httpx.post(
            f"{config.CALENDAR_SERVICE_URL}/events/edit",
            json=payload,
            headers=_headers(),
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except httpx.ConnectError:
        raise CalendarServiceError("Cannot connect to calendar service. Is it running?")
    except httpx.TimeoutException:
        raise CalendarServiceError("Calendar service request timed out.")
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", str(e)) if e.response.text else str(e)
        raise CalendarServiceError(f"Calendar service error: {detail}")
    except httpx.HTTPError as e:
        raise CalendarServiceError(f"Calendar service error: {e}")


def delete_event(title: str) -> dict:
    """Delete an event from the calendar."""
    try:
        response = httpx.post(
            f"{config.CALENDAR_SERVICE_URL}/events/delete",
            json={"action": "delete", "title": title},
            headers=_headers(),
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except httpx.ConnectError:
        raise CalendarServiceError("Cannot connect to calendar service. Is it running?")
    except httpx.TimeoutException:
        raise CalendarServiceError("Calendar service request timed out.")
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", str(e)) if e.response.text else str(e)
        raise CalendarServiceError(f"Calendar service error: {detail}")
    except httpx.HTTPError as e:
        raise CalendarServiceError(f"Calendar service error: {e}")