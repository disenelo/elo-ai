"""
tests/test_ea2_7_company_memory.py — Acceptance tests for WO EA2-7 (Company Memory store)

Company-level memory: decisions / completions / milestones / notes.
Append-only JSONL, keyword recall, time-based recency (canon D-SESSIONS), timeline digest.

All tests use a TEMP store in /tmp — never touch the real blender/ or memory/.

6 tests:
    AT-1  remember() appends a valid record; file grows + parses as JSONL
    AT-2  recall(kind=...) returns only that kind
    AT-3  recall(wo=...) returns records for that WO
    AT-4  recall(since_days=...) filters by real time (days), not sessions
    AT-5  recall(query=...) ranks a matching record above a non-matching one
    AT-6  malformed input (missing kind/summary) → graceful, no crash/corruption

Run: python3 tests/test_ea2_7_company_memory.py
"""
import sys
import os
import json
import time
import tempfile

sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


from company_runtime.company_memory import remember, recall, timeline


# ── AT-1: remember() appends a valid record; file grows + parses as JSONL ─────

with tempfile.TemporaryDirectory() as _tmp:
    _store = os.path.join(_tmp, "company_memory.jsonl")
    try:
        assert not os.path.exists(_store), "store should not exist yet"
        _rec = remember("decision", "Adopt append-only JSONL for company memory",
                        detail="Durability > cleverness.", wo="EA2-7", actor="david",
                        tags=["architecture", "durable"], store_path=_store)
        assert _rec is not None, "remember() returned None on valid input"
        assert os.path.exists(_store), "store file was not created"
        _size1 = os.path.getsize(_store)

        _rec2 = remember("completion", "EA2-7 module written", store_path=_store)
        assert _rec2 is not None, "second remember() returned None"
        _size2 = os.path.getsize(_store)
        assert _size2 > _size1, "file did not grow on second append"

        # parses as JSONL — one dict per line
        with open(_store, encoding="utf-8") as _f:
            _lines = [ln for ln in _f.read().splitlines() if ln.strip()]
        assert len(_lines) == 2, f"expected 2 lines, got {len(_lines)}"
        _parsed = [json.loads(ln) for ln in _lines]
        _first = _parsed[0]
        for _k in ("ts", "iso", "kind", "summary"):
            assert _k in _first, f"record missing key {_k!r}"
        assert isinstance(_first["ts"], float), "ts must be float"
        assert _first["iso"].endswith("Z"), "iso must be ISO/UTC with Z"
        assert _first["kind"] == "decision", "kind not stored correctly"
        ok(f"AT-1: remember() appends valid JSONL — 2 records, {_size2} bytes, "
           f"iso={_first['iso']}")
    except AssertionError as e: fail("AT-1", e)


# ── AT-2: recall(kind=...) returns only that kind ─────────────────────────────

with tempfile.TemporaryDirectory() as _tmp:
    _store = os.path.join(_tmp, "company_memory.jsonl")
    remember("decision",   "chose plan A",     store_path=_store)
    remember("completion", "shipped feature X", store_path=_store)
    remember("decision",   "chose plan B",      store_path=_store)
    remember("milestone",  "v1 released",       store_path=_store)
    try:
        _dec = recall(kind="decision", store_path=_store)
        assert len(_dec) == 2, f"expected 2 decisions, got {len(_dec)}"
        assert all(r["kind"] == "decision" for r in _dec), "non-decision leaked into results"
        _mil = recall(kind="milestone", store_path=_store)
        assert len(_mil) == 1 and _mil[0]["kind"] == "milestone", "milestone filter wrong"
        ok(f"AT-2: recall(kind='decision') → {len(_dec)} records, all correct kind")
    except AssertionError as e: fail("AT-2", e)


# ── AT-3: recall(wo=...) returns records for that WO ──────────────────────────

with tempfile.TemporaryDirectory() as _tmp:
    _store = os.path.join(_tmp, "company_memory.jsonl")
    remember("completion", "did EA2-7 part 1", wo="EA2-7", store_path=_store)
    remember("completion", "did EA2-7 part 2", wo="EA2-7", store_path=_store)
    remember("completion", "did something else", wo="EA2-1", store_path=_store)
    remember("note",       "no wo attached",   store_path=_store)
    try:
        _got = recall(wo="EA2-7", store_path=_store)
        assert len(_got) == 2, f"expected 2 records for EA2-7, got {len(_got)}"
        assert all(r["wo"] == "EA2-7" for r in _got), "wrong WO leaked in"
        ok(f"AT-3: recall(wo='EA2-7') → {len(_got)} records, all for EA2-7")
    except AssertionError as e: fail("AT-3", e)


# ── AT-4: recall(since_days=...) filters by real time (days), not sessions ────

with tempfile.TemporaryDirectory() as _tmp:
    _store = os.path.join(_tmp, "company_memory.jsonl")
    # write two records, then hand-forge an OLD record (40 days ago) directly into JSONL
    remember("note", "recent event now",        store_path=_store)
    remember("note", "another recent event",    store_path=_store)
    _old_ts = time.time() - 40 * 86400.0
    _old = {
        "schema": "company_memory/v1", "ts": round(_old_ts, 3),
        "iso": "2000-01-01T00:00:00Z", "kind": "note",
        "summary": "ancient history 40 days back", "detail": "", "wo": None,
        "actor": None, "tags": [],
    }
    with open(_store, "a", encoding="utf-8") as _f:
        _f.write(json.dumps(_old) + "\n")
    try:
        _all = recall(since_days=None, store_path=_store)
        assert len(_all) == 3, f"expected 3 total, got {len(_all)}"
        _recent = recall(since_days=7, store_path=_store)
        assert len(_recent) == 2, f"since_days=7 should exclude the 40-day-old one, got {len(_recent)}"
        assert all("ancient" not in r["summary"] for r in _recent), "old record leaked past 7-day window"
        _wide = recall(since_days=60, store_path=_store)
        assert len(_wide) == 3, f"since_days=60 should include all 3, got {len(_wide)}"
        ok("AT-4: since_days filters by real time — 7d→2, 60d→3 (time-based, not sessions)")
    except AssertionError as e: fail("AT-4", e)


# ── AT-5: recall(query=...) ranks a matching record above a non-matching one ──

with tempfile.TemporaryDirectory() as _tmp:
    _store = os.path.join(_tmp, "company_memory.jsonl")
    remember("note", "The Kickstarter campaign budget was finalized today",
             detail="kickstarter kickstarter", store_path=_store)
    remember("note", "Team lunch was pleasant", store_path=_store)
    remember("note", "Unrelated engineering standup notes", store_path=_store)
    try:
        _hits = recall(query="kickstarter budget", store_path=_store)
        assert len(_hits) >= 1, "query returned no results"
        assert "Kickstarter" in _hits[0]["summary"], (
            f"top result should be the kickstarter record, got: {_hits[0]['summary']!r}"
        )
        # non-matching records should be excluded when a query is given
        assert all(("kickstarter" in r["summary"].lower() or "budget" in r["summary"].lower())
                   for r in _hits), "a non-matching record leaked into query results"
        ok(f"AT-5: query ranks matching record first — top={_hits[0]['summary'][:40]!r}")
    except AssertionError as e: fail("AT-5", e)


# ── AT-6: malformed input → graceful, no crash/corruption ─────────────────────

with tempfile.TemporaryDirectory() as _tmp:
    _store = os.path.join(_tmp, "company_memory.jsonl")
    _crashed = False
    _bad_returns = []
    try:
        _bad_returns.append(remember("", "", store_path=_store))          # no kind, no summary
        _bad_returns.append(remember("decision", "", store_path=_store))  # no summary
        _bad_returns.append(remember(None, None, store_path=_store))      # None/None
        _bad_returns.append(remember("weirdkind", "valid summary here", store_path=_store))  # bad kind → note
    except Exception as _exc:
        _crashed = True

    # a good write AFTER the bad ones, to prove no corruption
    _good = remember("milestone", "store still healthy", store_path=_store)
    try:
        assert not _crashed, "remember() raised on malformed input"
        # the three truly-empty-summary cases must return None
        assert _bad_returns[0] is None, "empty kind+summary should return None"
        assert _bad_returns[1] is None, "empty summary should return None"
        assert _bad_returns[2] is None, "None/None should return None"
        # bad kind but valid summary → stored as 'note'
        assert _bad_returns[3] is not None and _bad_returns[3]["kind"] == "note", (
            "unknown kind should coerce to 'note', not fail"
        )
        assert _good is not None, "good write after malformed input failed"

        # store must still be fully parseable JSONL (no corruption)
        if os.path.exists(_store):
            with open(_store, encoding="utf-8") as _f:
                for _ln in _f:
                    if _ln.strip():
                        json.loads(_ln)  # raises if corrupt
        # only 2 records should have landed (bad-kind coerced + good milestone)
        _final = recall(store_path=_store)
        assert len(_final) == 2, f"expected 2 stored records, got {len(_final)}"
        ok("AT-6: malformed input handled gracefully — no crash, no corruption, store parseable")
    except AssertionError as e: fail("AT-6", e)


print(f"\nResult: {PASS}/6 passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
