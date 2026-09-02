import difflib
from typing import List

def clean_text(text: str) -> str:
    return text.strip()

def title_name(name: str) -> str:
    """Safely title-cases names, mapping 'user' to 'You'."""
    if not name:
        return ""
    if name.lower() == "user":
        return "You"
    return name.title()

def fuzzy_collection_name(query: str, known_names: List[str]) -> str:
    """Finds the closest matching collection name using fuzzy matching."""
    if not known_names:
        return query
    matches = difflib.get_close_matches(query, known_names, n=1, cutoff=0.6)
    return matches[0] if matches else query