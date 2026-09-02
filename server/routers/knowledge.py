"""Knowledge management endpoints for E.D.I.T.H."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from memory.store import (
    add_fact, find_facts, delete_facts, replace_fact, dump_subject,
    list_entities, set_collection, get_collection, list_collections,
    add_collection_item, remove_collection_item, replace_collection_item,
    delete_collection, add_alias, get_aliases
)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


# ── Models ────────────────────────────────────────────────────

class Fact(BaseModel):
    """A fact (subject-relation-object triple)."""
    subject: str
    relation: str
    object: str


class Collection(BaseModel):
    """A named collection of items."""
    owner: str
    name: str
    items: List[str]


class Alias(BaseModel):
    """An alias mapping."""
    alias: str
    target: str


# ── Facts ─────────────────────────────────────────────────────

@router.get("/facts", response_model=List[Dict[str, str]])
async def get_facts(subject: Optional[str] = None, relation: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Query facts from the knowledge base.

    - **subject**: Optional subject to filter by
    - **relation**: Optional relation to filter by
    """
    return find_facts(subject=subject, relation=relation)


@router.post("/facts", response_model=Dict[str, str])
async def create_fact(fact: Fact) -> Dict[str, str]:
    """
    Add a new fact to the knowledge base.

    - **subject**: The subject of the fact
    - **relation**: The relation/property
    - **object**: The object/value
    """
    add_fact(fact.subject, fact.relation, fact.object)
    return {"message": f"Fact added for {fact.subject}"}


@router.put("/facts", response_model=Dict[str, str])
async def update_fact(fact: Fact) -> Dict[str, str]:
    """
    Replace an existing fact (delete old, add new).

    - **subject**: The subject of the fact
    - **relation**: The relation to update
    - **object**: The new value
    """
    replace_fact(fact.subject, fact.relation, fact.object)
    return {"message": f"Fact updated for {fact.subject}"}


@router.delete("/facts", response_model=Dict[str, str])
async def remove_fact(subject: str, relation: Optional[str] = None) -> Dict[str, str]:
    """
    Delete a fact or all facts for a subject.

    - **subject**: The subject whose facts to delete
    - **relation**: Optional specific relation to delete
    """
    deleted = delete_facts(subject=subject, relation=relation)
    if not deleted:
        raise HTTPException(status_code=404, detail="No facts found to delete")
    return {"message": f"Facts deleted for {subject}"}


# ── Entities ──────────────────────────────────────────────────

@router.get("/entities", response_model=List[str])
async def get_entities() -> List[str]:
    """Get all known entities."""
    return list_entities()


@router.get("/entities/{entity}", response_model=List[Dict[str, str]])
async def get_entity_profile(entity: str) -> List[Dict[str, str]]:
    """
    Get the complete profile of an entity.

    - **entity**: The entity name
    """
    facts = dump_subject(entity)
    if not facts:
        raise HTTPException(status_code=404, detail=f"No information found for {entity}")
    return facts


# ── Collections ───────────────────────────────────────────────

@router.post("/collections", response_model=Dict[str, str])
async def create_collection(collection: Collection) -> Dict[str, str]:
    """
    Create a named collection.

    - **owner**: The owner of the collection
    - **name**: The collection name
    - **items**: List of items in the collection
    """
    set_collection(collection.owner, collection.name, collection.items)
    return {"message": f"Collection '{collection.name}' created"}


@router.get("/collections", response_model=List[Dict[str, Any]])
async def get_collections(owner: str) -> List[Dict[str, Any]]:
    """
    Get all collections for an owner.

    - **owner**: The collection owner
    """
    return list_collections(owner=owner)


@router.get("/collections/{owner}/{name}", response_model=Dict[str, Any])
async def get_collection_details(owner: str, name: str) -> Dict[str, Any]:
    """
    Get a specific collection.

    - **owner**: The collection owner
    - **name**: The collection name
    """
    collection = get_collection(owner, name)
    if not collection:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")
    return collection


@router.post("/collections/{owner}/{name}/items", response_model=Dict[str, str])
async def add_item(owner: str, name: str, item: str) -> Dict[str, str]:
    """
    Add an item to a collection.

    - **owner**: The collection owner
    - **name**: The collection name
    - **item**: The item to add
    """
    add_collection_item(owner, name, item)
    return {"message": f"Item added to '{name}'"}


@router.put("/collections/{owner}/{name}/items", response_model=Dict[str, str])
async def update_item(owner: str, name: str, old: str, new: str) -> Dict[str, str]:
    """
    Replace an item in a collection.

    - **owner**: The collection owner
    - **name**: The collection name
    - **old**: The item to replace
    - **new**: The new item value
    """
    updated = replace_collection_item(owner, name, old, new)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found in collection")
    return {"message": f"Item updated in '{name}'"}


@router.delete("/collections/{owner}/{name}/items", response_model=Dict[str, str])
async def remove_item(owner: str, name: str, index: int) -> Dict[str, str]:
    """
    Remove an item from a collection by index.

    - **owner**: The collection owner
    - **name**: The collection name
    - **index**: The position of the item to remove (0-indexed)
    """
    removed = remove_collection_item(owner, name, index)
    if removed is None:
        raise HTTPException(status_code=404, detail="Item not found at that index")
    return {"message": f"Removed '{removed}' from '{name}'"}


@router.delete("/collections/{owner}/{name}", response_model=Dict[str, str])
async def remove_collection(owner: str, name: str) -> Dict[str, str]:
    """
    Delete an entire collection.

    - **owner**: The collection owner
    - **name**: The collection name
    """
    deleted = delete_collection(owner, name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Collection not found")
    return {"message": f"Collection '{name}' deleted"}


# ── Aliases ───────────────────────────────────────────────────

@router.get("/aliases", response_model=Dict[str, str])
async def get_all_aliases() -> Dict[str, str]:
    """Get all aliases in the system."""
    return get_aliases()


@router.post("/aliases", response_model=Dict[str, str])
async def create_alias(alias: Alias) -> Dict[str, str]:
    """
    Create an alias for an entity.

    - **alias**: The alias (short name)
    - **target**: The target entity
    """
    add_alias(alias.alias, alias.target)
    return {"message": f"Alias '{alias.alias}' -> '{alias.target}'"}
