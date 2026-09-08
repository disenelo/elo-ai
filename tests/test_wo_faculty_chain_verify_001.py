"""
tests/test_wo_faculty_chain_verify_001.py — WO-FACULTY-CHAIN-VERIFY-001

Proves the One Brain faculty chain delivers non-null tiers to the Executive.
Root cause of C-01 audit gap: WKG claims stored as entity-relationship graph;
spine.py called _cl.get('claim','') which always returned '' → wkg_context always
empty → tier_snapshot all unknown.

Fix: WO-WKG-CONTEXT-FIX-001 (commit a61bbb1) — now builds claim text from graph.

AT-1: WKG context assembly produces non-empty string for a known entity.
AT-2: tier_fact() returns 'inferred' (not 'unknown') for a non-empty wkg_context value.
AT-3: Full TFR with mood + wkg_context → at least two tiers are non-'unknown'.
AT-4: Personality faculty returns non-empty trait dict (wonder, empathy, directness > 0).
AT-5: wkg._load('entities') is accessible for entity-id resolution (no AttributeError).

Run: ~/miniconda3/bin/python3 -m pytest tests/test_wo_faculty_chain_verify_001.py -v
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0; FAIL = 0


def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: WKG context assembly produces non-empty string ────────────────────
try:
    import runtime.wkg_faculty as _wkg
    _topic = "eLo"
    _entities = _wkg.search_entities(_topic)[:3]
    assert _entities, f"No entities found for topic '{_topic}' — WKG may be empty"

    _ent_map = {e["entity_id"]: e.get("label", "") for e in _wkg._load("entities")}
    _lines = []
    for _ent in _entities:
        _claims = _wkg.get_claims_about(_ent.get("entity_id", ""))[:2]
        for _cl in _claims:
            _subj = _ent_map.get(_cl.get("subject_entity_id", ""), _ent.get("label", ""))
            _obj  = _ent_map.get(_cl.get("object_entity_id", ""), "")
            _rel  = _cl.get("relationship_type", "").replace("_", " ").lower()
            _epi  = _cl.get("epistemic_class", "").upper()
            if _obj:
                _lines.append(f"[{_epi}] {_subj} {_rel} {_obj}")
    _wkg_context = "; ".join(_lines)

    assert _wkg_context, "wkg_context is empty after graph traversal — no obj-label resolved"
    assert "eLo" in _wkg_context or "SOURCE_ATTRIBUTED" in _wkg_context, \
        f"wkg_context doesn't mention eLo or epistemic class: {_wkg_context!r}"
    ok(f"AT-1: wkg_context assembled — {len(_wkg_context)} chars: {_wkg_context[:80]!r}…")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: tier_fact returns 'inferred' for non-empty wkg_context ────────────
try:
    from runtime.the_moment import tier_fact

    _tier_with_value  = tier_fact("eLo is persistent presence", source="inferred")
    _tier_with_empty  = tier_fact("", source="inferred")
    _tier_with_none   = tier_fact(None, source="inferred")

    assert _tier_with_value == "inferred", \
        f"Expected 'inferred' for non-empty value, got {_tier_with_value!r}"
    assert _tier_with_empty == "unknown", \
        f"Expected 'unknown' for empty string, got {_tier_with_empty!r}"
    assert _tier_with_none == "unknown", \
        f"Expected 'unknown' for None, got {_tier_with_none!r}"

    ok("AT-2: tier_fact → 'inferred' (non-empty) / 'unknown' (empty/None) — correct")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: Full TFR with mood + wkg_context → ≥2 non-unknown tiers ──────────
try:
    from runtime.tiered_faculty_reader import TieredFacultyReader as _TFR

    _world_dict = {
        "mood":        "neutral",
        "wkg_context": _wkg_context,
        "active_window": "",
        "vault_context": "",
        "capabilities": [],
        "pose": "",
        "nearby": "",
        "lessons": [],
    }
    _results, _licence = _TFR().evaluate(_world_dict, None)
    _non_unknown = [r for r in _results if r.tier not in ("unknown", "absent")]

    assert len(_non_unknown) >= 2, (
        f"Expected ≥2 non-unknown tiers after WKG fix; got {len(_non_unknown)}: "
        + str([(r.key, r.tier) for r in _results])
    )
    _tier_keys = {r.key: r.tier for r in _results}
    assert _tier_keys.get("wkg_context") == "inferred", \
        f"wkg_context tier should be 'inferred', got {_tier_keys.get('wkg_context')!r}"
    assert _tier_keys.get("mood") == "inferred", \
        f"mood tier should be 'inferred', got {_tier_keys.get('mood')!r}"

    ok(f"AT-3: TFR → {len(_non_unknown)} non-unknown tiers — wkg_context={_tier_keys.get('wkg_context')!r}, mood={_tier_keys.get('mood')!r}")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: Personality faculty returns non-empty trait dict ───────────────────
try:
    from faculties.personality.personality_evolution_faculty import (
        load_personality as _pv_load,
        get_trait_values as _pv_traits,
    )
    _pv = _pv_load()
    _traits = _pv_traits(_pv)

    assert isinstance(_traits, dict) and _traits, "personality traits is empty dict"
    _expected = ("curiosity", "empathy", "wonder", "directness")
    for _t in _expected:
        assert _t in _traits, f"Expected trait '{_t}' missing from personality dict"
        assert isinstance(_traits[_t], float) and _traits[_t] > 0, \
            f"Trait '{_t}' should be positive float, got {_traits[_t]!r}"

    _top = sorted(_traits.items(), key=lambda kv: kv[1], reverse=True)[:2]
    ok(f"AT-4: Personality traits loaded — {len(_traits)} traits; top 2: {[k for k,_ in _top]}")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: wkg._load('entities') accessible for entity-id resolution ─────────
try:
    import runtime.wkg_faculty as _wkg5
    _all_ents = _wkg5._load("entities")
    assert isinstance(_all_ents, list) and _all_ents, \
        f"_load('entities') returned empty: {_all_ents!r}"
    _ent_map = {e["entity_id"]: e.get("label", "") for e in _all_ents}
    assert _ent_map, "entity_id → label map is empty"
    ok(f"AT-5: wkg._load('entities') accessible — {len(_all_ents)} entities, map built")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 60)
print(f"WO-FACULTY-CHAIN-VERIFY-001   {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
