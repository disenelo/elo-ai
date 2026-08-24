"""
tests/test_wo102_person_place_event.py — WO-102: Person / Place / Event stores

AT-1: a seeded test Person is retrievable through retrieve()
AT-2: a seeded test Place is retrievable through retrieve()
AT-3: a seeded test Event is retrievable through retrieve()
AT-4: unknown input returns [] — no confabulation
AT-5: out-of-set entity type is rejected (not loaded), Rule 1 alarm
AT-6: Ruling A — exactly one graph is read; identity/world_graph.json not loaded
AT-7: type closed set: person/place/event are valid types in _ALLOWED_ENTITY_TYPES
AT-8: sensitivity=private entries are excluded from open retrieval (Vol XXIII)

Run: python3 tests/test_wo102_person_place_event.py
"""
from __future__ import annotations
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

_passed = _failed = 0


def ok(label: str) -> None:
    global _passed
    _passed += 1
    print(f"  ✅ {label}")


def fail(label: str, err) -> None:
    global _failed
    _failed += 1
    print(f"  ❌ {label}: {err}")


def _reset_loader() -> None:
    """Clear graph_loader's module-level cache so the next call reloads from patched paths."""
    import knowledge.graph_loader as _gl
    _gl._graph = {}
    _gl._concepts = {}
    _gl._viewpoints = {}


def _tmp_json(data: dict) -> str:
    f = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8")
    json.dump(data, f)
    f.close()
    return f.name


# ── AT-1: seeded Person is retrievable ────────────────────────────────────────
try:
    import knowledge.graph_loader as _gl

    _orig_pp = _gl._PEOPLE_PATH
    _orig_pl = _gl._PLACES_PATH
    _orig_ev = _gl._EVENTS_PATH

    people_file = _tmp_json({
        "people": [{
            "id":            "person_test_ally",
            "name":          "Ally",
            "also_known_as": ["ally", "test ally"],
            "relation":      "friend",
            "relation_note": "closest collaborator",
            "facts":         [{"fact": "lives in London", "since": "2020-01-01",
                               "source": "david_stated", "confidence": 1.0}],
            "salience":      0.8,
            "sensitivity":   "normal",
            "keywords":      ["ally", "test ally", "friend"],
        }],
    })
    _gl._PEOPLE_PATH = people_file
    _gl._PLACES_PATH = _tmp_json({"places": []})
    _gl._EVENTS_PATH = _tmp_json({"events": []})
    _reset_loader()

    from knowledge.graph_loader import retrieve
    results = retrieve("ally friend collaborator")
    hits = [r for r in results if "ally" in r["label"].lower() or r["kind"] == "person"]
    assert hits, f"Expected at least one person hit, got {results}"
    assert hits[0]["kind"] == "person", f"kind should be 'person', got {hits[0]['kind']}"
    ok("AT-1: seeded Person is retrievable through retrieve()")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)
finally:
    _gl._PEOPLE_PATH = _orig_pp
    _gl._PLACES_PATH = _orig_pl
    _gl._EVENTS_PATH = _orig_ev
    _reset_loader()


# ── AT-2: seeded Place is retrievable ─────────────────────────────────────────
try:
    _orig_pp = _gl._PEOPLE_PATH
    _orig_pl = _gl._PLACES_PATH
    _orig_ev = _gl._EVENTS_PATH

    _gl._PEOPLE_PATH = _tmp_json({"people": []})
    _gl._PLACES_PATH = _tmp_json({
        "places": [{
            "id":           "place_test_studio",
            "name":         "the test studio",
            "kind":         "studio",
            "locality":     "Bristol",
            "address":      None,
            "significance": "where creative work happens",
            "salience":     0.7,
            "sensitivity":  "normal",
            "keywords":     ["test studio", "studio", "bristol"],
        }],
    })
    _gl._EVENTS_PATH = _tmp_json({"events": []})
    _reset_loader()

    results = retrieve("test studio bristol creative work")
    hits = [r for r in results if r["kind"] == "place"]
    assert hits, f"Expected place hit, got {results}"
    ok("AT-2: seeded Place is retrievable through retrieve()")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)
finally:
    _gl._PEOPLE_PATH = _orig_pp
    _gl._PLACES_PATH = _orig_pl
    _gl._EVENTS_PATH = _orig_ev
    _reset_loader()


# ── AT-3: seeded Event is retrievable ─────────────────────────────────────────
try:
    _orig_pp = _gl._PEOPLE_PATH
    _orig_pl = _gl._PLACES_PATH
    _orig_ev = _gl._EVENTS_PATH

    _gl._PEOPLE_PATH = _tmp_json({"people": []})
    _gl._PLACES_PATH = _tmp_json({"places": []})
    _gl._EVENTS_PATH = _tmp_json({
        "events": [{
            "id":       "event_test_launch",
            "what":     "test product launch event",
            "when":     {"date": "2026-01-01", "precision": "day", "recurring": "none"},
            "who":      [],
            "where":    None,
            "outcome":  "successful launch, widely celebrated",
            "valence":  0.9,
            "salience": 0.8,
            "sensitivity": "normal",
            "source":   "david_stated",
            "keywords": ["test product launch", "launch event"],
        }],
    })
    _reset_loader()

    results = retrieve("test product launch event celebration")
    hits = [r for r in results if r["kind"] == "event"]
    assert hits, f"Expected event hit, got {results}"
    ok("AT-3: seeded Event is retrievable through retrieve()")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)
finally:
    _gl._PEOPLE_PATH = _orig_pp
    _gl._PLACES_PATH = _orig_pl
    _gl._EVENTS_PATH = _orig_ev
    _reset_loader()


# ── AT-4: unknown input returns [] (no confabulation) ─────────────────────────
try:
    _orig_pp = _gl._PEOPLE_PATH
    _orig_pl = _gl._PLACES_PATH
    _orig_ev = _gl._EVENTS_PATH

    _gl._PEOPLE_PATH = _tmp_json({"people": []})
    _gl._PLACES_PATH = _tmp_json({"places": []})
    _gl._EVENTS_PATH = _tmp_json({"events": []})
    _reset_loader()

    results = retrieve("xyzzy no match quux fnord")
    assert results == [], f"Expected [] for unknown input, got {results}"
    ok("AT-4: unknown input returns [] — no confabulation")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)
finally:
    _gl._PEOPLE_PATH = _orig_pp
    _gl._PLACES_PATH = _orig_pl
    _gl._EVENTS_PATH = _orig_ev
    _reset_loader()


# ── AT-5: out-of-set type is rejected (not loaded) — Rule 1 alarm ─────────────
try:
    import logging

    _orig_pp = _gl._PEOPLE_PATH
    _orig_pl = _gl._PLACES_PATH
    _orig_ev = _gl._EVENTS_PATH

    # person_to_entity always returns type="person" which IS in the set
    # To test rejection, inject a raw entity with an invalid type directly
    # via a temp world_graph.json. But since people/places/events always project to
    # valid types, test via a Person node that has a bogus type field bypassed.
    # The closed set check happens after projection — projection always returns
    # type="person"/"place"/"event". Test the _ALLOWED_ENTITY_TYPES set directly.
    assert "person" in _gl._ALLOWED_ENTITY_TYPES, "person missing from _ALLOWED_ENTITY_TYPES"
    assert "place"  in _gl._ALLOWED_ENTITY_TYPES, "place missing from _ALLOWED_ENTITY_TYPES"
    assert "event"  in _gl._ALLOWED_ENTITY_TYPES, "event missing from _ALLOWED_ENTITY_TYPES"
    assert "freeform_hack" not in _gl._ALLOWED_ENTITY_TYPES, "out-of-set type should not be allowed"

    # Verify warning is emitted for an entity with bad type by patching _load_all
    # internals: inject a projector that returns a bad type
    warned = []
    orig_warn = None

    class _CapturingHandler(logging.Handler):
        def emit(self, record):
            warned.append(self.format(record))

    handler = _CapturingHandler()
    loader_log = logging.getLogger("knowledge.graph_loader")
    loader_log.addHandler(handler)
    loader_log.setLevel(logging.WARNING)

    _gl._PEOPLE_PATH = _tmp_json({
        "people": [{
            "id": "person_test_bad",
            "name": "Bogus",
            "also_known_as": [],
            "relation": "friend",
            "relation_note": "",
            "facts": [],
            "salience": 0.1,
            "sensitivity": "normal",
            "keywords": [],
        }],
    })
    _gl._PLACES_PATH = _tmp_json({"places": []})
    _gl._EVENTS_PATH = _tmp_json({"events": []})

    # Temporarily patch _person_to_entity to return an invalid type
    _orig_pte = _gl._person_to_entity
    def _bad_projector(p):
        e = _orig_pte(p)
        e["type"] = "freeform_hack"
        return e
    _gl._person_to_entity = _bad_projector
    _reset_loader()

    _gl._load_all()

    # Verify: entity with bad type was NOT loaded into _graph
    bad_entities = [e for e in _gl._graph.get("entities", []) if e.get("type") == "freeform_hack"]
    assert not bad_entities, f"Bad-type entity was loaded — should have been rejected: {bad_entities}"
    # Verify: warning was emitted
    assert any("WO-102" in w and "out-of-set" in w for w in warned), \
        f"Expected WO-102 out-of-set warning, got: {warned}"

    ok("AT-5: out-of-set type rejected and warning logged — Rule 1 alarm works")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)
finally:
    _gl._person_to_entity = _orig_pte
    loader_log.removeHandler(handler)
    _gl._PEOPLE_PATH = _orig_pp
    _gl._PLACES_PATH = _orig_pl
    _gl._EVENTS_PATH = _orig_ev
    _reset_loader()


# ── AT-6: Ruling A — identity/world_graph.json not loaded ─────────────────────
try:
    import inspect
    src = inspect.getsource(_gl._load_all)
    identity_path_canonical = os.path.join("identity", "world_graph.json")
    # The load function must warn about legacy path, not load it
    assert "identity" in src and ("IGNORED" in src or "not load" in src.lower() or "warning" in src.lower()), \
        "graph_loader._load_all() should warn about identity/ but not load it"
    # _GRAPH_PATH must point to relationships/, not identity/
    assert "identity" not in _gl._GRAPH_PATH, \
        f"_GRAPH_PATH points to identity/: {_gl._GRAPH_PATH}"
    assert "relationships" in _gl._GRAPH_PATH, \
        f"_GRAPH_PATH must point to relationships/: {_gl._GRAPH_PATH}"
    ok("AT-6: Ruling A holds — identity/world_graph.json not loaded; one canonical graph")
except AssertionError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)


# ── AT-7: closed type set includes person/place/event ─────────────────────────
try:
    required = {"person", "place", "event", "project", "brand"}
    missing = required - _gl._ALLOWED_ENTITY_TYPES
    assert not missing, f"Types missing from _ALLOWED_ENTITY_TYPES: {missing}"
    assert isinstance(_gl._ALLOWED_ENTITY_TYPES, frozenset), \
        "_ALLOWED_ENTITY_TYPES should be a frozenset (immutable closed set)"
    ok("AT-7: closed type set is frozenset and includes person/place/event")
except AssertionError as e:
    fail("AT-7", e)
except Exception as e:
    fail("AT-7", e)


# ── AT-8: sensitivity=private excluded from open retrieval ────────────────────
try:
    _orig_pp = _gl._PEOPLE_PATH
    _orig_pl = _gl._PLACES_PATH
    _orig_ev = _gl._EVENTS_PATH

    _gl._PEOPLE_PATH = _tmp_json({
        "people": [{
            "id":            "person_private_test",
            "name":          "PrivateTestPerson",
            "also_known_as": ["privatetestperson"],
            "relation":      "family",
            "relation_note": "",
            "facts":         [],
            "salience":      0.9,
            "sensitivity":   "private",
            "keywords":      ["privatetestperson", "private test person"],
        }],
    })
    _gl._PLACES_PATH = _tmp_json({"places": []})
    _gl._EVENTS_PATH = _tmp_json({"events": []})
    _reset_loader()

    results = retrieve("privatetestperson private test person")
    hits = [r for r in results if "privatetestperson" in r.get("label", "").lower()
                                 or "privatetestperson" in r.get("content", "").lower()]
    assert not hits, \
        f"sensitivity=private entity should NOT appear in retrieve() results, got {hits}"
    ok("AT-8: sensitivity=private excluded from open retrieval (Vol XXIII)")
except AssertionError as e:
    fail("AT-8", e)
except Exception as e:
    fail("AT-8", e)
finally:
    _gl._PEOPLE_PATH = _orig_pp
    _gl._PLACES_PATH = _orig_pl
    _gl._EVENTS_PATH = _orig_ev
    _reset_loader()


# ── summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 62)
print(f"WO-102 person/place/event   {_passed} passed   {_failed} failed")
