REL_NAME = "name"
REL_AGE = "age"
REL_RELATIONSHIP = "relationship"
REL_BIRTHDAY = "birthday"
REL_OCCUPATION = "occupation"
REL_LOCATION = "location"
REL_NATIONALITY = "nationality"

_DISPLAY_NAMES = {
    REL_NAME: "name",
    REL_AGE: "age",
    REL_RELATIONSHIP: "relationship",
    REL_BIRTHDAY: "birthday",
    REL_OCCUPATION: "occupation",
    REL_LOCATION: "location",
    REL_NATIONALITY: "nationality",
}

def relation_display(rel: str) -> str:
    """Safely formats a relation for human-readable output."""
    return _DISPLAY_NAMES.get(rel.lower(), rel)