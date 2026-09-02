from memory.store import (
    add_fact, find_facts, replace_fact, delete_facts,
    set_collection, get_collection, add_collection_item, remove_collection_item
)

def test_add_and_find_fact():
    add_fact("user", "name", "Luis")
    add_fact("user", "age", "25")
    
    facts = find_facts("user", "name")
    assert len(facts) == 1
    assert facts[0]["object"] == "Luis"
    assert facts[0]["subject"] == "user"

def test_replace_fact():
    add_fact("user", "location", "Lisbon")
    replace_fact("user", "location", "Porto")
    
    facts = find_facts("user", "location")
    assert len(facts) == 1
    assert facts[0]["object"] == "Porto"

def test_collections_crud():
    # Create
    set_collection("user", "groceries", ["milk", "eggs"])
    coll = get_collection("user", "groceries")
    assert coll["items"] == ["milk", "eggs"]
    
    # Add item
    add_collection_item("user", "groceries", "bread")
    coll = get_collection("user", "groceries")
    assert "bread" in coll["items"]
    assert len(coll["items"]) == 3
    
    # Remove item
    remove_collection_item("user", "groceries", 1)  # removes 'eggs'
    coll = get_collection("user", "groceries")
    assert coll["items"] == ["milk", "bread"]