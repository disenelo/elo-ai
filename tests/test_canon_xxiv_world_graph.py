"""
tests/test_canon_xxiv_world_graph.py — WO-CANON-XXIV: One World Graph

Assertions (per Ruling A 2026-08-10):
  AT-0: graph_loader reads from relationships/world_graph.json (canonical path)
  AT-1: retrieve() returns ranked results carrying confidence + kind + evidence + score
  AT-2: retrieve() returns [] for unknown input (never backfills)
  AT-3: identity/world_graph.json is marked _retired: true
  AT-4: core/continuity.py reads canonical path not identity/world_graph.json

Run: python3 tests/test_canon_xxiv_world_graph.py
"""
from __future__ import annotations
import sys, os, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_passed = _failed = 0


def ok(label: str):
    global _passed
    _passed += 1
    print(f"  ✅ {label}")


def fail(label: str, err):
    global _failed
    _failed += 1
    print(f"  ❌ {label}: {err}")


_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REL_GRAPH = os.path.join(_BASE, "relationships", "world_graph.json")
_ID_GRAPH  = os.path.join(_BASE, "identity",      "world_graph.json")


# ── AT-0: graph_loader uses relationships/world_graph.json ───────────────────
try:
    from knowledge import graph_loader as _gl
    assert os.path.normpath(_gl._GRAPH_PATH) == os.path.normpath(_REL_GRAPH), (
        f"graph_loader._GRAPH_PATH is {_gl._GRAPH_PATH!r}, expected {_REL_GRAPH!r}"
    )
    ok(f"AT-0: graph_loader reads canonical relationships/world_graph.json")
except AssertionError as e:
    fail("AT-0", e)
except Exception as e:
    fail("AT-0", e)


# ── AT-1: retrieve() returns ranked results with required fields ──────────────
try:
    from knowledge.graph_loader import retrieve

    results = retrieve("eLo the main character explorer presence")
    assert isinstance(results, list),          "retrieve() must return a list"
    assert len(results) > 0,                   "retrieve() returned empty for a known entity"
    first = results[0]
    assert "label"      in first,              "result missing 'label'"
    assert "content"    in first,              "result missing 'content'"
    assert "confidence" in first,              "result missing 'confidence'"
    assert "kind"       in first,              "result missing 'kind'"
    assert "evidence"   in first,              "result missing 'evidence'"
    assert "score"      in first,              "result missing 'score'"
    assert isinstance(first["confidence"], float), "confidence must be float"
    assert isinstance(first["evidence"], list),    "evidence must be list"
    # Results should be ranked: first item should have highest score
    if len(results) > 1:
        assert results[0]["score"] >= results[1]["score"], (
            f"results not ranked: {results[0]['score']} < {results[1]['score']}"
        )
    ok(f"AT-1: retrieve() returns ranked results with confidence+kind+evidence (top: {first['label']!r})")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: retrieve() returns [] for unknown input (no backfill) ───────────────
try:
    results_unknown = retrieve("xyzzy zorkmid frobnicate unknown gibberish 12345abc")
    assert results_unknown == [], (
        f"retrieve() should return [] for unknown input, got {results_unknown}"
    )
    ok("AT-2: retrieve() returns [] for unknown input — no backfill")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: identity/world_graph.json marked _retired ──────────────────────────
try:
    with open(_ID_GRAPH, encoding="utf-8") as f:
        id_data = json.load(f)
    assert id_data.get("_retired") is True, (
        f"identity/world_graph.json must have _retired: true, got {id_data.get('_retired')}"
    )
    assert "_successor" in id_data, "identity/world_graph.json missing _successor field"
    ok("AT-3: identity/world_graph.json marked _retired:true with _successor pointer")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: core/continuity.py reads from relationships/ not identity/ ──────────
try:
    from core import continuity as _ct
    assert "relationships" in _ct._WORLD_GRAPH_PATH, (
        f"continuity._WORLD_GRAPH_PATH still points to identity/: {_ct._WORLD_GRAPH_PATH!r}"
    )
    assert "identity" not in _ct._WORLD_GRAPH_PATH, (
        f"continuity._WORLD_GRAPH_PATH still includes identity/: {_ct._WORLD_GRAPH_PATH!r}"
    )
    ok(f"AT-4: continuity.py reads canonical relationships/world_graph.json")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 62)
print(f"WO-CANON-XXIV world graph   {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
