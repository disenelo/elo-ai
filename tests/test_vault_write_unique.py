"""
tests/test_vault_write_unique.py — WO-VAULT-UNIQUE: vault write collision fix

Root cause confirmed: encode() produces EO·CV·2609·3 for all writes with the same
(project, type, month, weight). spot_to_filename() maps this to one file, so every
subsequent write silently overwrites the previous one. 6743 SPOT_CODES rows → 29 files.

Fix: write_memory() appends a 5-char nanosecond-derived hex suffix to the spot code
so every write gets its own unique file.

AT-1  Two write_memory() calls produce different spot codes (no collision)
AT-2  Two write_memory() calls produce two distinct deep files on disk
AT-3  Two write_memory() calls produce two distinct summary files on disk
AT-4  Two write_memory() calls append two distinct rows to SPOT_CODES.md
AT-5  MemoryFaculty.submit() end-to-end: submit two candidates → two vault files written
AT-6  Old-format spot codes (no suffix) still decode cleanly via vault_codec.decode()
AT-7  py_compile clean on vault_layer.py + vault_codec.py + memory_faculty.py
"""
import os
import sys
import py_compile
import tempfile
import shutil

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _fresh_vault(tmp_dir: str):
    """Return a patched env pointing vault writes at tmp_dir."""
    import memory.vault_layer as vl
    old_vault  = vl._VAULT
    old_mem    = vl._MEM_DIR
    old_sum    = vl._SUM_DIR
    old_deep   = vl._DEEP_DIR
    old_spot   = vl._SPOT_FILE

    vl._VAULT     = tmp_dir
    vl._MEM_DIR   = os.path.join(tmp_dir, "09 Memory")
    vl._SUM_DIR   = os.path.join(vl._MEM_DIR, "summary")
    vl._DEEP_DIR  = os.path.join(vl._MEM_DIR, "deep")
    vl._SPOT_FILE = os.path.join(vl._MEM_DIR, "SPOT_CODES.md")

    return old_vault, old_mem, old_sum, old_deep, old_spot


def _restore_vault(vl, saved):
    old_vault, old_mem, old_sum, old_deep, old_spot = saved
    vl._VAULT     = old_vault
    vl._MEM_DIR   = old_mem
    vl._SUM_DIR   = old_sum
    vl._DEEP_DIR  = old_deep
    vl._SPOT_FILE = old_spot


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_two_writes_produce_unique_spot_codes():
    """
    Two write_memory() calls with identical arguments must return different spot codes.
    Before the fix both returned e.g. 'EO·CV·2609·3' → collision → file overwrite.
    """
    import memory.vault_layer as vl
    tmp = tempfile.mkdtemp()
    saved = _fresh_vault(tmp)
    try:
        spot1 = vl.write_memory(
            project="elo-os", memory_type="conversation",
            summary="First write", deep_text="Content A", weight=3,
            epistemic_class='conversation',
        )
        spot2 = vl.write_memory(
            project="elo-os", memory_type="conversation",
            summary="Second write", deep_text="Content B", weight=3,
            epistemic_class='conversation',
        )
        assert spot1 != spot2, (
            f"AT-1 FAIL: two writes produced the same spot code {spot1!r} — "
            "vault collision bug not fixed"
        )
    finally:
        _restore_vault(vl, saved)
        shutil.rmtree(tmp, ignore_errors=True)


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_two_writes_produce_two_distinct_deep_files():
    """
    Each write_memory() call must create its own deep file — never overwrite.
    This is the core invariant: autobiographical history requires one file per memory.
    """
    import memory.vault_layer as vl
    tmp = tempfile.mkdtemp()
    saved = _fresh_vault(tmp)
    try:
        vl.write_memory(
            project="elo-os", memory_type="conversation",
            summary="Deep A", deep_text="Content A", weight=3,
            epistemic_class='conversation',
        )
        vl.write_memory(
            project="elo-os", memory_type="conversation",
            summary="Deep B", deep_text="Content B", weight=3,
            epistemic_class='conversation',
        )
        deep_files = os.listdir(vl._DEEP_DIR)
        assert len(deep_files) == 2, (
            f"AT-2 FAIL: expected 2 deep files, found {len(deep_files)}: {deep_files} — "
            "writes are still colliding (overwriting each other)"
        )
    finally:
        _restore_vault(vl, saved)
        shutil.rmtree(tmp, ignore_errors=True)


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_two_writes_produce_two_distinct_summary_files():
    """Each write must produce its own summary file alongside its deep file."""
    import memory.vault_layer as vl
    tmp = tempfile.mkdtemp()
    saved = _fresh_vault(tmp)
    try:
        vl.write_memory(
            project="elo-os", memory_type="conversation",
            summary="Summary A", deep_text="Content A", weight=5,
            epistemic_class='conversation',
        )
        vl.write_memory(
            project="elo-os", memory_type="conversation",
            summary="Summary B", deep_text="Content B", weight=5,
            epistemic_class='conversation',
        )
        sum_files = os.listdir(vl._SUM_DIR)
        assert len(sum_files) == 2, (
            f"AT-3 FAIL: expected 2 summary files, found {len(sum_files)}: {sum_files}"
        )
    finally:
        _restore_vault(vl, saved)
        shutil.rmtree(tmp, ignore_errors=True)


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_two_writes_append_two_rows_to_spot_codes():
    """
    SPOT_CODES.md must grow by one row per write — confirmed with two distinct rows
    for two writes. The index is append-only and each row must be unique.
    """
    import memory.vault_layer as vl
    tmp = tempfile.mkdtemp()
    saved = _fresh_vault(tmp)
    try:
        spot1 = vl.write_memory(
            project="elo-os", memory_type="conversation",
            summary="Row A", deep_text="Content A", weight=4,
            epistemic_class='conversation',
        )
        spot2 = vl.write_memory(
            project="elo-os", memory_type="conversation",
            summary="Row B", deep_text="Content B", weight=4,
            epistemic_class='conversation',
        )
        content = open(vl._SPOT_FILE, encoding="utf-8").read()
        # Both spot codes must appear as distinct rows
        assert spot1 in content, f"AT-4 FAIL: spot1 {spot1!r} not found in SPOT_CODES.md"
        assert spot2 in content, f"AT-4 FAIL: spot2 {spot2!r} not found in SPOT_CODES.md"
        assert spot1 != spot2,   f"AT-4 FAIL: spots not unique: {spot1!r}"
        # Two data rows (excluding header)
        data_rows = [l for l in content.splitlines() if l.startswith("| `")]
        assert len(data_rows) == 2, (
            f"AT-4 FAIL: expected 2 data rows in SPOT_CODES.md, found {len(data_rows)}"
        )
    finally:
        _restore_vault(vl, saved)
        shutil.rmtree(tmp, ignore_errors=True)


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_memory_faculty_end_to_end_two_candidates_two_files():
    """
    MemoryFaculty.submit() called twice with significance > DROP_THRESHOLD must
    produce two distinct vault files. This is the autobiographical history path —
    if MemoryFaculty submits silently drop or overwrite, history is lost.
    """
    import memory.vault_layer as vl
    from memory.memory_faculty import MemoryFaculty, MemoryCandidate
    tmp = tempfile.mkdtemp()
    saved = _fresh_vault(tmp)
    try:
        fac = MemoryFaculty()
        r1 = fac.submit(MemoryCandidate(
            source_faculty="interaction",
            content="eLo and David discussed the robot hand design.",
            proposed_type="episodic",
            proposed_weight=4,
            significance=0.55,
            project="elo-os",
            summary="Robot hand design discussion",
            tags=("robot", "design"),
        ))
        r2 = fac.submit(MemoryCandidate(
            source_faculty="interaction",
            content="David confirmed that the inflatable shell uses 4mm TPU walls.",
            proposed_type="semantic",
            proposed_weight=5,
            significance=0.60,
            project="elo-robot",
            summary="TPU shell wall thickness confirmed: 4mm",
            tags=("robot", "tpu", "spec"),
        ))

        assert r1["action"] == "write", (
            f"AT-5 FAIL: first submit returned action={r1['action']!r}, reason={r1['reason']!r}"
        )
        assert r2["action"] == "write", (
            f"AT-5 FAIL: second submit returned action={r2['action']!r}, reason={r2['reason']!r}"
        )
        assert r1["spot"] != r2["spot"], (
            f"AT-5 FAIL: both submits returned same spot {r1['spot']!r} — collision not fixed"
        )

        deep_files = os.listdir(vl._DEEP_DIR)
        assert len(deep_files) == 2, (
            f"AT-5 FAIL: expected 2 deep files after 2 submits, got {len(deep_files)}: {deep_files}"
        )
    finally:
        _restore_vault(vl, saved)
        shutil.rmtree(tmp, ignore_errors=True)


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_old_format_spot_codes_still_decode():
    """
    Old-format spot codes without the unique suffix must still decode cleanly.
    Existing records in the vault must remain readable — the fix is additive only.
    """
    from memory.vault_codec import decode
    old_spots = [
        "EO·BL·2607·9",
        "EB·CV·2607·5",
        "GN·CV·2608·3",
        "DV·LN·2608·6",
    ]
    for spot in old_spots:
        try:
            result = decode(spot)
            assert result["weight"] >= 0, f"AT-6 FAIL: decode returned bad weight for {spot!r}"
        except Exception as exc:
            pytest.fail(f"AT-6 FAIL: decode({spot!r}) raised: {exc}")


# ── AT-7 ──────────────────────────────────────────────────────────────────────

def test_at7_py_compile_clean():
    files = [
        os.path.join(_ROOT, "memory", "vault_layer.py"),
        os.path.join(_ROOT, "memory", "vault_codec.py"),
        os.path.join(_ROOT, "memory", "memory_faculty.py"),
    ]
    for path in files:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"AT-7 FAIL: {os.path.basename(path)} does not compile: {exc}")
