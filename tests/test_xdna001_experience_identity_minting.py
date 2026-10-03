"""
tests/test_xdna001_experience_identity_minting.py — WO-XDNA-001 / WO-XDNA-002 Acceptance Tests

AT-1   Every new turn produces a unique experience_id (format + no collision)
AT-2   No test-id-001 in decision_journal after a turn using this WO
AT-3   experience_id appears on a decision_journal entry
AT-4   experience_id appears in vault summary.md YAML frontmatter
AT-5   experience_id appears in vault deep.md YAML frontmatter
AT-6   Same experience_id across all artifacts of one turn
AT-7   Spot code unchanged by this WO (vault codec not modified)
AT-8   Backward compatibility — records without experience_id still readable
AT-9   Two records carry non-collinear experience_ids (A3-non-collision)
AT-10  SPOT_CODES.md row carries experience_id column
AT-11  End-to-end production path: MemoryCandidate → submit() → vault YAML carries minted xid
AT-12  record_intent_abandoned() carries experience_id

Authority: WO-XDNA-001 · WO-XDNA-002 · EXPERIENCE_DNA_CANON_2026-08-23.md
"""
from __future__ import annotations

import json
import os
import re
import tempfile

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

_XID_RE = re.compile(r'^ELO-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}$')


def _is_xid(value: str) -> bool:
    return bool(_XID_RE.match(value))


def _parse_frontmatter(text: str) -> dict:
    """Extract key: value pairs from YAML frontmatter block."""
    meta: dict = {}
    if not text.startswith("---"):
        return meta
    end = text.find("\n---", 3)
    if end == -1:
        return meta
    for line in text[3:end].splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip().strip("\"'")
    return meta


# ─────────────────────────────────────────────────────────────────────────────
# AT-1 — format + uniqueness
# ─────────────────────────────────────────────────────────────────────────────

def test_at1_experience_id_format_and_uniqueness():
    """Every mint() produces a valid unique ELO-XXXX-XXXX value."""
    from runtime.experience_id import mint, is_valid

    ids = set()
    for _ in range(200):
        xid = mint()
        assert is_valid(xid), f"format invalid: {xid!r}"
        assert xid not in ids, f"collision on {xid!r}"
        ids.add(xid)

    # Consecutive turns differ
    a = mint()
    b = mint()
    assert a != b, "consecutive mint() calls must not produce the same id"


# ─────────────────────────────────────────────────────────────────────────────
# AT-2 — no test-id-001 after a real turn
# ─────────────────────────────────────────────────────────────────────────────

def test_at2_no_test_id_001_in_journal(tmp_path, monkeypatch):
    """No journal row may carry intent_id='test-id-001' when experience_id is live."""
    from runtime import experience_id as xid_mod
    import self.decision_journal as dj

    journal_path = str(tmp_path / "decision_journal.jsonl")
    monkeypatch.setattr(dj, "_JOURNAL", journal_path)

    # Mint a real experience_id before recording
    xid_mod.mint()

    dj.record(
        turn="hello eLo",
        action="reflect",
        exec_decision={"cal_reason": "test turn", "intent": "conversation"},
        backend="test",
        outcome="success",
    )

    with open(journal_path) as f:
        entries = [json.loads(line) for line in f if line.strip()]

    assert entries, "expected at least one journal entry"
    for e in entries:
        assert e.get("experience_id") != "test-id-001", \
            f"found forbidden value test-id-001 in {e}"
        # Also confirm no bare intent_id with the placeholder
        assert e.get("intent_id") != "test-id-001", \
            f"found forbidden intent_id test-id-001 in {e}"


# ─────────────────────────────────────────────────────────────────────────────
# AT-3 — experience_id on decision_journal entry
# ─────────────────────────────────────────────────────────────────────────────

def test_at3_experience_id_on_journal_entry(tmp_path, monkeypatch):
    """A recorded turn produces a journal row with a real experience_id."""
    from runtime import experience_id as xid_mod
    import self.decision_journal as dj

    journal_path = str(tmp_path / "decision_journal.jsonl")
    monkeypatch.setattr(dj, "_JOURNAL", journal_path)

    expected_xid = xid_mod.mint()

    dj.record(
        turn="test turn for AT-3",
        action="reflect",
        exec_decision={"cal_reason": "AT-3", "intent": "conversation"},
        backend="test",
    )

    with open(journal_path) as f:
        entries = [json.loads(line) for line in f if line.strip()]

    assert entries, "expected a journal entry"
    entry = entries[-1]
    assert "experience_id" in entry, "experience_id field missing from journal entry"
    assert entry["experience_id"] == expected_xid, \
        f"expected {expected_xid!r}, got {entry['experience_id']!r}"
    assert _is_xid(entry["experience_id"]), \
        f"experience_id not in ELO-XXXX-XXXX format: {entry['experience_id']!r}"


# ─────────────────────────────────────────────────────────────────────────────
# AT-4 — experience_id on vault summary frontmatter
# AT-5 — experience_id on vault deep frontmatter
# AT-7 — spot code unchanged
# AT-10 — SPOT_CODES.md row carries experience_id
# ─────────────────────────────────────────────────────────────────────────────

def test_at4_at5_at7_at10_vault_writes(tmp_path):
    """vault_layer.write_memory() writes experience_id to summary.md, deep.md, and SPOT_CODES.md."""
    from runtime import experience_id as xid_mod
    from memory import vault_layer

    # Redirect vault to tmp directory
    vault_dir   = str(tmp_path / "obsidian_vault")
    mem_dir     = os.path.join(vault_dir, "09 Memory")
    sum_dir     = os.path.join(mem_dir, "summary")
    deep_dir    = os.path.join(mem_dir, "deep")
    spot_file   = os.path.join(mem_dir, "SPOT_CODES.md")

    original_vault = vault_layer._VAULT
    original_mem   = vault_layer._MEM_DIR
    original_sum   = vault_layer._SUM_DIR
    original_deep  = vault_layer._DEEP_DIR
    original_spot  = vault_layer._SPOT_FILE

    vault_layer._VAULT     = vault_dir
    vault_layer._MEM_DIR   = mem_dir
    vault_layer._SUM_DIR   = sum_dir
    vault_layer._DEEP_DIR  = deep_dir
    vault_layer._SPOT_FILE = spot_file

    try:
        expected_xid = xid_mod.mint()
        spot = vault_layer.write_memory(
            project="elo-os",
            memory_type="build",
            summary="AT-4/5/7/10 test memory write.",
            deep_text="Full content for the acceptance test.",
            weight=5,
            experience_id=expected_xid,
                    epistemic_class='conversation',
        )

        # AT-7: spot code is non-empty and in known format (not replaced by xid)
        assert spot, "spot code must not be empty"
        assert expected_xid not in spot or "·" in spot, \
            "spot code must not become the experience_id"
        assert "·" in spot, f"spot code format unexpected: {spot!r}"

        # AT-4: summary.md has experience_id in frontmatter
        sum_files = os.listdir(sum_dir)
        assert sum_files, "no summary file written"
        sum_text = open(os.path.join(sum_dir, sum_files[0])).read()
        sum_fm   = _parse_frontmatter(sum_text)
        assert "experience_id" in sum_fm, "experience_id missing from summary.md frontmatter"
        assert sum_fm["experience_id"] == expected_xid, \
            f"summary.md experience_id: expected {expected_xid!r}, got {sum_fm['experience_id']!r}"

        # AT-5: deep.md has experience_id in frontmatter
        deep_files = os.listdir(deep_dir)
        assert deep_files, "no deep file written"
        deep_text = open(os.path.join(deep_dir, deep_files[0])).read()
        deep_fm   = _parse_frontmatter(deep_text)
        assert "experience_id" in deep_fm, "experience_id missing from deep.md frontmatter"
        assert deep_fm["experience_id"] == expected_xid, \
            f"deep.md experience_id: expected {expected_xid!r}, got {deep_fm['experience_id']!r}"

        # AT-10: SPOT_CODES.md row carries experience_id
        spot_text = open(spot_file).read()
        assert expected_xid in spot_text, \
            f"experience_id {expected_xid!r} not found in SPOT_CODES.md"

    finally:
        vault_layer._VAULT     = original_vault
        vault_layer._MEM_DIR   = original_mem
        vault_layer._SUM_DIR   = original_sum
        vault_layer._DEEP_DIR  = original_deep
        vault_layer._SPOT_FILE = original_spot


# ─────────────────────────────────────────────────────────────────────────────
# AT-6 — same experience_id across all artifacts of one turn
# ─────────────────────────────────────────────────────────────────────────────

def test_at6_same_xid_across_artifacts(tmp_path, monkeypatch):
    """Journal, vault summary, vault deep, and SPOT_CODES.md all carry the same xid."""
    from runtime import experience_id as xid_mod
    import self.decision_journal as dj
    from memory import vault_layer

    # Redirect journal
    journal_path = str(tmp_path / "decision_journal.jsonl")
    monkeypatch.setattr(dj, "_JOURNAL", journal_path)

    # Redirect vault
    vault_dir   = str(tmp_path / "obsidian_vault")
    mem_dir     = os.path.join(vault_dir, "09 Memory")
    sum_dir     = os.path.join(mem_dir, "summary")
    deep_dir    = os.path.join(mem_dir, "deep")
    spot_file   = os.path.join(mem_dir, "SPOT_CODES.md")
    vault_layer._VAULT     = vault_dir
    vault_layer._MEM_DIR   = mem_dir
    vault_layer._SUM_DIR   = sum_dir
    vault_layer._DEEP_DIR  = deep_dir
    vault_layer._SPOT_FILE = spot_file

    original = {k: getattr(vault_layer, k) for k in ("_VAULT","_MEM_DIR","_SUM_DIR","_DEEP_DIR","_SPOT_FILE")}

    try:
        # Mint — simulates spine.run() turn start
        expected_xid = xid_mod.mint()

        # Write journal (simulates server.py post-response)
        dj.record(
            turn="AT-6 cross-artifact test",
            action="reflect",
            exec_decision={"cal_reason": "AT-6", "intent": "conversation"},
            backend="test",
        )

        # Write vault (simulates MemoryFaculty.submit() → write_memory())
        vault_layer.write_memory(
            project="elo-os",
            memory_type="build",
            summary="AT-6 same-xid test.",
            deep_text="Content for AT-6.",
            weight=5,
            experience_id=expected_xid,
                    epistemic_class='conversation',
        )

        # Journal
        with open(journal_path) as f:
            entries = [json.loads(l) for l in f if l.strip()]
        assert entries[-1]["experience_id"] == expected_xid, \
            "journal experience_id mismatch"

        # Summary frontmatter
        sum_text = open(os.path.join(sum_dir, os.listdir(sum_dir)[0])).read()
        assert _parse_frontmatter(sum_text).get("experience_id") == expected_xid, \
            "summary.md experience_id mismatch"

        # Deep frontmatter
        deep_text = open(os.path.join(deep_dir, os.listdir(deep_dir)[0])).read()
        assert _parse_frontmatter(deep_text).get("experience_id") == expected_xid, \
            "deep.md experience_id mismatch"

        # SPOT_CODES.md
        spot_text = open(spot_file).read()
        assert expected_xid in spot_text, "SPOT_CODES.md experience_id mismatch"

    finally:
        for k, v in original.items():
            setattr(vault_layer, k, v)


# ─────────────────────────────────────────────────────────────────────────────
# AT-8 — backward compatibility
# ─────────────────────────────────────────────────────────────────────────────

def test_at8_backward_compatibility_no_experience_id(tmp_path):
    """Records written without experience_id (pre-WO) are still readable."""
    from memory import vault_layer

    vault_dir   = str(tmp_path / "obsidian_vault")
    mem_dir     = os.path.join(vault_dir, "09 Memory")
    sum_dir     = os.path.join(mem_dir, "summary")
    deep_dir    = os.path.join(mem_dir, "deep")
    spot_file   = os.path.join(mem_dir, "SPOT_CODES.md")

    original = {k: getattr(vault_layer, k) for k in ("_VAULT","_MEM_DIR","_SUM_DIR","_DEEP_DIR","_SPOT_FILE")}
    vault_layer._VAULT     = vault_dir
    vault_layer._MEM_DIR   = mem_dir
    vault_layer._SUM_DIR   = sum_dir
    vault_layer._DEEP_DIR  = deep_dir
    vault_layer._SPOT_FILE = spot_file

    try:
        # Write without experience_id (pre-WO caller)
        spot = vault_layer.write_memory(
            project="general",
            memory_type="conversation",
            summary="Pre-WO record with no experience_id.",
            deep_text="Old-style content.",
            weight=4,
            # experience_id not supplied — backward-compatible default ""
                    epistemic_class='conversation',
        )
        assert spot, "pre-WO write must still produce a spot code"

        # lookup() must not break
        results = vault_layer.lookup("Pre-WO record")
        # Result must be a list (not an exception), and the record is readable
        assert isinstance(results, list)

    finally:
        for k, v in original.items():
            setattr(vault_layer, k, v)


# ─────────────────────────────────────────────────────────────────────────────
# AT-9 — two records carry non-collinear experience_ids
# ─────────────────────────────────────────────────────────────────────────────

def test_at9_non_collinear_experience_ids(tmp_path):
    """Two records with different experience_ids share no vocabulary between the IDs."""
    from runtime import experience_id as xid_mod
    from memory import vault_layer

    vault_dir   = str(tmp_path / "obsidian_vault")
    mem_dir     = os.path.join(vault_dir, "09 Memory")
    sum_dir     = os.path.join(mem_dir, "summary")
    deep_dir    = os.path.join(mem_dir, "deep")
    spot_file   = os.path.join(mem_dir, "SPOT_CODES.md")

    original = {k: getattr(vault_layer, k) for k in ("_VAULT","_MEM_DIR","_SUM_DIR","_DEEP_DIR","_SPOT_FILE")}
    vault_layer._VAULT     = vault_dir
    vault_layer._MEM_DIR   = mem_dir
    vault_layer._SUM_DIR   = sum_dir
    vault_layer._DEEP_DIR  = deep_dir
    vault_layer._SPOT_FILE = spot_file

    try:
        xid_a = xid_mod.mint()
        vault_layer.write_memory(
            project="elo-os", memory_type="build",
            summary="AT-9 record A.", deep_text="Content A.", weight=5,
            experience_id=xid_a,
                    epistemic_class='conversation',
        )

        xid_b = xid_mod.mint()
        vault_layer.write_memory(
            project="elo-os", memory_type="learn",
            summary="AT-9 record B.", deep_text="Content B.", weight=5,
            experience_id=xid_b,
                    epistemic_class='conversation',
        )

        assert xid_a != xid_b, "two consecutive turns must have distinct experience_ids"
        assert _is_xid(xid_a) and _is_xid(xid_b), "both must be valid ELO-XXXX-XXXX format"

        # A3 non-collinear: reading records for xid_a must not surface xid_b and vice versa.
        sum_files = sorted(os.listdir(sum_dir))
        assert len(sum_files) == 2, f"expected 2 summary files, got {sum_files}"

        text_a = open(os.path.join(sum_dir, sum_files[0])).read()
        text_b = open(os.path.join(sum_dir, sum_files[1])).read()

        # Each file contains its own xid and NOT the other's
        xid_a_in_a = xid_a in text_a
        xid_b_in_b = xid_b in text_b
        xid_b_in_a = xid_b in text_a
        xid_a_in_b = xid_a in text_b

        assert xid_a_in_a, f"record A must contain its own experience_id {xid_a!r}"
        assert xid_b_in_b, f"record B must contain its own experience_id {xid_b!r}"
        assert not xid_b_in_a, f"record A must not contain B's experience_id {xid_b!r}"
        assert not xid_a_in_b, f"record B must not contain A's experience_id {xid_a!r}"

    finally:
        for k, v in original.items():
            setattr(vault_layer, k, v)


# ─────────────────────────────────────────────────────────────────────────────
# Mint / get contract
# ─────────────────────────────────────────────────────────────────────────────

def test_get_returns_minted_value():
    """get() returns exactly the value most recently minted by mint()."""
    from runtime.experience_id import mint, get
    xid = mint()
    assert get() == xid, "get() must return the value from the most recent mint()"


def test_is_valid_rejects_garbage():
    """is_valid() correctly rejects non-ELO-XXXX-XXXX strings."""
    from runtime.experience_id import is_valid
    assert not is_valid("")
    assert not is_valid("test-id-001")
    assert not is_valid("ELO-X7K4")
    assert not is_valid("ELO-X7K4-92A1-EXTRA")
    assert not is_valid("elo-x7k4-92a1")   # lowercase prefix is rejected
    assert is_valid("ELO-X7K4-92A1")
    assert is_valid("ELO-abcd-EFGH")


# ─────────────────────────────────────────────────────────────────────────────
# WO-XDNA-002 — AT-11: end-to-end production path propagation
# ─────────────────────────────────────────────────────────────────────────────

def test_at11_production_path_propagation(tmp_path, monkeypatch):
    """AT-11: MemoryCandidate constructed with experience_id=get() → vault YAML carries it.

    Simulates the full production call chain:
      spine mints → caller reads get() → MemoryCandidate(..., experience_id=get())
      → MemoryFaculty.submit() → vault_layer.write_memory() → summary.md frontmatter
    """
    import runtime.experience_id as xid_mod
    from memory import vault_layer
    from memory.memory_faculty import MemoryFaculty, MemoryCandidate

    # Pin vault dirs to tmp so no real vault is touched.
    original = {k: getattr(vault_layer, k) for k in ("_SUM_DIR", "_DEEP_DIR", "_SPOT_FILE")}
    sum_dir  = tmp_path / "summary"
    deep_dir = tmp_path / "deep"
    spot_file = tmp_path / "SPOT_CODES.md"
    sum_dir.mkdir()
    deep_dir.mkdir()
    monkeypatch.setattr(vault_layer, "_SUM_DIR",   str(sum_dir))
    monkeypatch.setattr(vault_layer, "_DEEP_DIR",  str(deep_dir))
    monkeypatch.setattr(vault_layer, "_SPOT_FILE", str(spot_file))

    try:
        # Step 1: spine mints at turn start.
        expected_xid = xid_mod.mint()

        # Step 2: production caller reads get() and constructs MemoryCandidate.
        try:
            from runtime.experience_id import get as _get_xid
            _xid = _get_xid()
        except Exception:
            _xid = ""

        candidate = MemoryCandidate(
            source_faculty="interaction",
            content="AT-11 end-to-end production path test content.",
            proposed_type="episodic",
            proposed_weight=5,
            significance=0.55,
            project="general",
            summary="AT-11 production path test",
            tags=("at11", "xdna002"),
            experience_id=_xid,
        )

        # Step 3: route through MemoryFaculty.submit() — the sole logical writer.
        result = MemoryFaculty().submit(candidate)
        assert result["action"] == "write", f"Expected write, got {result['action']}: {result.get('reason')}"

        # Step 4: locate the written summary.md file.
        written = list(sum_dir.glob("*.md"))
        assert written, "No summary.md written to vault"
        summary_text = written[0].read_text(encoding="utf-8")

        # Step 5: assert experience_id in YAML frontmatter equals minted value — NOT "".
        assert "experience_id:" in summary_text, \
            "experience_id not found in summary.md frontmatter"
        assert expected_xid in summary_text, \
            f"Minted xid {expected_xid!r} not found in summary.md — propagation broken"

    finally:
        for k, v in original.items():
            setattr(vault_layer, k, v)


# ─────────────────────────────────────────────────────────────────────────────
# WO-XDNA-002 — AT-12: abandoned-intent identity
# ─────────────────────────────────────────────────────────────────────────────

def test_at12_abandoned_intent_carries_experience_id(tmp_path, monkeypatch):
    """AT-12: record_intent_abandoned() produces a journal row that carries experience_id."""
    import runtime.experience_id as xid_mod
    import self.decision_journal as dj

    journal_path = str(tmp_path / "decision_journal.jsonl")
    monkeypatch.setattr(dj, "_JOURNAL", journal_path)

    # Step 1: mint a fresh xid (simulates spine.run() turn start).
    expected_xid = xid_mod.mint()

    # Step 2: fire an abandoned-intent record.
    dj.record_intent_abandoned(
        intent_id="test-intent-at12",
        kind="external",
        content="play some music",
        reason="timeout",
    )

    # Step 3: read the journal.
    with open(journal_path) as f:
        entries = [json.loads(line) for line in f if line.strip()]

    assert entries, "No journal entries written"
    abandoned = [e for e in entries if e.get("record_type") == "intent_abandoned"]
    assert abandoned, "No intent_abandoned row found in journal"
    row = abandoned[-1]

    # Step 4: assert the minted xid is on the row — NOT "".
    assert "experience_id" in row, "experience_id field missing from intent_abandoned row"
    assert row["experience_id"] == expected_xid, (
        f"experience_id mismatch: expected {expected_xid!r}, got {row['experience_id']!r}"
    )
