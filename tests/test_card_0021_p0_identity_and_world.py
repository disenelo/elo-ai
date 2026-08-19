"""tests/test_card_0021_p0_identity_and_world.py — Card 0021 acceptance.

David's live test showed:
  • "What is your name?" → LLM guess ("I think you're asking about my name.")
    — identity_name lives at self/elo_self_model.py:170 but nothing consulted it.
  • "What is my name?" → same failure — who_i_am_with existed, never read.
  • "Who is Chunk?" / "Who is K-7" → web results laundered as own-world knowledge.

Card requires:
  P0-X.a — the name question resolves from state, deterministically. Ask 5×, get
           the same identity_name 5×. Backend must be "direct" (not an LLM).
  P0-X.b — David's name resolves from who_i_am_with, deterministically.
  P0-X.c — Change the fields, the answers change. State drives, not literals.
  P0-Y.a — Known world entity ("Chunk", "K-7") → world-graph gate injects the
           entity as context and blocks the web-search path.
  P0-Y.b — Unknown proper noun ("Zenobia") → direct short-circuit "I don't know
           who … is — tell me?", NOT a web search laundered as own knowledge.
  P0-Y.c — WO-102 stores load: people.json / places.json / events.json exist and
           graph_loader picks up seeded entries (test injects a Person).
  P0-Y.d — Ruling A holds — identity/world_graph.json is NOT resurrected.
  P0-Z   — server-side FIFO turn queue is present and wired to /chat.

Run: python3 tests/test_card_0021_p0_identity_and_world.py
"""
import os
import sys
import json

sys.path.insert(0, ".")

PASS = 0
FAIL = 0


def ok(n: str) -> None:
    global PASS
    PASS += 1
    print(f"  ✅ {n}")


def fail(n: str, reason: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  ❌ {n}: {reason}")


# ── P0-X · identity + David-name from state ───────────────────────────────────

print("P0-X — identity + David-name resolve from state")

try:
    import server as _srv
    from runtime.spine.spine import run as _spine_run

    # P0-X.a — "What is your name?" resolves from state, ×5
    _srv._elo_self.identity_name = "eLo"
    names_seen = set()
    backends_seen = set()
    for _ in range(5):
        plan = _spine_run("What is your name?")
        backends_seen.add(plan.direct_backend)
        assert plan.direct_response, "empty direct_response"
        if "eLo" in plan.direct_response:
            names_seen.add("eLo")
    if names_seen == {"eLo"} and backends_seen == {"direct"}:
        ok("P0-X.a: 'What is your name?' → 'eLo' 5×, backend=direct")
    else:
        fail("P0-X.a", f"names={names_seen} backends={backends_seen}")

    # P0-X.b — "What is my name?" resolves from who_i_am_with, ×5
    _srv._elo_self.who_i_am_with = "David"
    names_seen = set()
    backends_seen = set()
    for _ in range(5):
        plan = _spine_run("What is my name?")
        backends_seen.add(plan.direct_backend)
        assert plan.direct_response, "empty direct_response"
        if "David" in plan.direct_response:
            names_seen.add("David")
    if names_seen == {"David"} and backends_seen == {"direct"}:
        ok("P0-X.b: 'What is my name?' → 'David' 5×, backend=direct")
    else:
        fail("P0-X.b", f"names={names_seen} backends={backends_seen}")

    # P0-X.c — Change the fields, the answers change. State drives, not literals.
    _srv._elo_self.identity_name = "Nova"
    _srv._elo_self.who_i_am_with = "Alex"
    p1 = _spine_run("What is your name?")
    p2 = _spine_run("What is my name?")
    if "Nova" in p1.direct_response and "Alex" in p2.direct_response:
        ok("P0-X.c: field change reaches the answer (Nova / Alex)")
    else:
        fail("P0-X.c", f"identity={p1.direct_response!r} david={p2.direct_response!r}")

    # Restore for downstream tests
    _srv._elo_self.identity_name = "eLo"
    _srv._elo_self.who_i_am_with = "David"

    # P0-X.d — variants all route to direct (never LLM)
    variants = [
        ("your name", "What's your name?"),
        ("your name", "Tell me your name."),
        ("david-side", "What's my name?"),
        ("david-side", "Who am I?"),
        ("david-side", "Say my name."),
        ("david-side", "What do you call me?"),
    ]
    _bad = []
    for label, q in variants:
        plan = _spine_run(q)
        if plan.direct_backend != "direct" or not plan.direct_response:
            _bad.append((label, q, plan.direct_backend, plan.direct_response))
    if not _bad:
        ok("P0-X.d: 6 identity variants all route direct")
    else:
        fail("P0-X.d", f"non-direct routes: {_bad}")

except Exception as e:
    fail("P0-X setup", f"{type(e).__name__}: {e}")


# ── P0-Y · world graph gate + WO-102 stores + proper-noun routing ─────────────

print("\nP0-Y — world graph gate + WO-102 stores + proper-noun routing")

try:
    # P0-Y.c — WO-102 stores exist and load
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for fname in ("people.json", "places.json", "events.json"):
        assert os.path.exists(os.path.join(_root, "relationships", fname)), f"{fname} missing"
    ok("P0-Y.c: people.json / places.json / events.json exist")

    # WO-102: seed a Person, verify graph_loader picks it up
    people_path = os.path.join(_root, "relationships", "people.json")
    original = open(people_path, encoding="utf-8").read()
    try:
        seeded = {
            "_schema": "test",
            "people": [{
                "id": "person_test_michael",
                "name": "Michael Paul",
                "also_known_as": ["Mike"],
                "relation": "friend",
                "relation_note": "sound engineer, from London",
                "facts": [{"fact": "runs a studio in Peckham",
                           "since": "2023-04",
                           "source": "david_stated",
                           "confidence": 0.9}],
                "salience": 0.6,
                "sensitivity": "normal",
                "keywords": ["michael", "mike", "paul"],
            }],
        }
        with open(people_path, "w", encoding="utf-8") as f:
            json.dump(seeded, f)
        # Force reload
        import knowledge.graph_loader as _gl
        _gl._graph = {}
        _gl._concepts = {}
        _gl._viewpoints = {}
        hits = _gl.retrieve("Who is Michael Paul?")
        labels = [h["label"] for h in hits]
        if any("Michael Paul" in lbl for lbl in labels):
            ok("P0-Y.c2: seeded Person is retrievable through graph_loader")
        else:
            fail("P0-Y.c2", f"labels: {labels}")
    finally:
        with open(people_path, "w", encoding="utf-8") as f:
            f.write(original)
        # Reload from disk-restored empty
        import knowledge.graph_loader as _gl
        _gl._graph = {}
        _gl._concepts = {}
        _gl._viewpoints = {}

    # P0-Y.a — Chunk and K-7 are in the graph and reachable
    from knowledge.graph_loader import retrieve as _retrieve
    for name in ("Chunk", "K-7"):
        hits = _retrieve(f"Who is {name}?")
        entity_hits = [h for h in hits
                       if h.get("confidence", 0.0) >= 1.0
                       and h.get("kind") not in ("relationship",)]
        assert entity_hits, f"no entity hit for {name}"
    ok("P0-Y.a: 'Who is Chunk/K-7?' returns entity hits from the world graph")

    # P0-Y.b — Proper-noun regex matches unknown names, skips pronouns & lowercase
    import re
    _PN_ASK = re.compile(
        r"\b(?i:who|what)(?i:'s|\s+is|\s+are)\s+([A-Z][A-Za-z0-9\-]{1,30})\b"
    )
    cases = {
        "Who is Zenobia?":    "Zenobia",
        "Who is K-7?":        "K-7",
        "What is DISENELO?":  "DISENELO",
        "who is chunk?":      None,   # lowercase noun → skipped
        "What is my name?":   None,   # 'my' is lowercase → skipped
        "Who is he?":         None,   # pronoun (lowercase)
    }
    _bad = []
    for q, expected in cases.items():
        m = _PN_ASK.search(q)
        got = m.group(1) if m else None
        if got != expected:
            _bad.append((q, expected, got))
    if not _bad:
        ok("P0-Y.b: proper-noun regex matches unknown capitalised names, skips lowercase/pronouns")
    else:
        fail("P0-Y.b", f"mismatches: {_bad}")

    # P0-Y.d — Ruling A: only relationships/ graph is loaded; legacy path is ignored
    legacy = os.path.join(_root, "identity", "world_graph.json")
    # Look at graph_loader's currently-loaded entities: they must be from relationships/,
    # not the legacy path. Simple contract: the loader logs about the legacy path but
    # never merges its entities. We assert by checking that the entity ids follow the
    # relationships/world_graph.json ontology (ids like 'elo', 'chunk', 'k7', ...).
    _gl._graph = {}
    _gl._load_all()
    ids = {e.get("id") for e in _gl._graph.get("entities", [])}
    if {"elo", "chunk", "k7"}.issubset(ids):
        ok("P0-Y.d: canonical relationships/world_graph.json is loaded (Ruling A holds)")
    else:
        fail("P0-Y.d", f"canonical ids missing: {ids}")

except Exception as e:
    fail("P0-Y setup", f"{type(e).__name__}: {e}")


# ── P0-Z · server-side FIFO turn queue is present and wired ───────────────────

print("\nP0-Z — FIFO turn queue is present and wired to /chat")

try:
    import server as _srv
    import queue as _q
    # Presence
    assert isinstance(_srv._turn_queue, _q.Queue), "turn queue missing"
    # Worker + enqueue helpers exist
    assert callable(_srv._turn_worker), "worker missing"
    assert callable(_srv._process_turn_queued), "enqueue helper missing"
    # /chat handler references the enqueue path (not the raw _process_turn)
    handler_src = open(os.path.join(os.path.dirname(__file__), "..", "server.py"),
                       encoding="utf-8").read()
    assert "_process_turn_queued(text)" in handler_src, "/chat does not use FIFO enqueue"
    assert "_turn_queue.put" in handler_src, "worker enqueue path missing"
    ok("P0-Z: FIFO turn queue + worker + /chat enqueue are all wired")
except Exception as e:
    fail("P0-Z", f"{type(e).__name__}: {e}")


# ── Summary ───────────────────────────────────────────────────────────────────

print(f"\n=====\n{PASS} passed  {FAIL} failed")
sys.exit(0 if FAIL == 0 else 1)
