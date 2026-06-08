# Compatibility shim — canonical location is core/memory_engine.py
from core.memory_engine import *
from core.memory_engine import (
    load_registry, resolve_project, store_interaction, retrieve,
    retrieve_by_project, retrieve_structured, build_memory_influence,
    export_memory, load_long_term_memory, load_session,
    _load_store, _STORE_PATH, _REGISTRY_PATH, _EXPORT_PATH, _SESSION_PATH,
    _detect_concepts, _query_words,
)
