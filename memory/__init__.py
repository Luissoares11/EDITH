from .store import (
    init_db, 
    add_fact, find_facts, replace_fact, delete_facts, dump_subject, list_entities,
    set_collection, get_collection, list_collections, add_collection_item, 
    remove_collection_item, replace_collection_item, delete_collection,
    add_alias, get_aliases
)
from .context import make_context
from .resolver import (
    resolve_entity, 
    infer_entity_from_relation_target, 
    push_entity
)