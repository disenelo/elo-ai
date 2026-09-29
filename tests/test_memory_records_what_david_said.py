"""
eLo's memory must record what David said, not what the pipeline prepended.

Found by David's causal test: "can the stored state be traced back to an
actual experience? can the experience be traced back to an actual event?"

Read straight out of the live vault, 2026-09-29:

  event: [projects,world] [WORLD_KNOWLEDGE — from eLo's own world (verified,
         confidence 1.0 — answer from this, not from web)] Chunk: A modular
         companion whose body is made of pieces...

David had said "The modular parts keep snapping together in the wrong order."
That sentence is nowhere in the record. The stored "experience" is a copy of
eLo's own injected context block.

Cause: server.py:3184 OVERWRITES `raw` with the [WORLD_KNOWLEDGE ...] block
before handing it to the model, and the episodic write path at :5842 read
`raw`. The F-5 remediation on 2026-08-21 found this exact class, fixed
state_manager.update at :6337 with _original_raw, and left the memory block.
"""
from __future__ import annotations

import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SERVER = os.path.join(_ROOT, "server.py")


def _src() -> str:
    return open(_SERVER, encoding="utf-8").read()


def _mem_block() -> str:
    """The episodic memory write block."""
    s = _src()
    i = s.index("_mem_registry    = _load_registry()")
    j = s.index("# WKG write path", i)
    return s[i:j]


def test_enrichment_still_happens():
    """
    The fix must not remove the world-knowledge enrichment — the model needs
    it. Only memory must stop recording it as David's words.
    """
    assert "[WORLD_KNOWLEDGE — from eLo's own world" in _src()


def test_memory_write_does_not_read_the_enriched_variable():
    block = _mem_block()
    offenders = re.findall(r"\b_resolve_project\(raw\b|\(raw \+ \" \"|_mem_summary = raw\[|"
                           r"_write_interaction\(raw\b", block)
    assert not offenders, (
        f"episodic memory still reads the enriched `raw`: {offenders}. "
        "That stores eLo's injected context as what David said."
    )


def test_memory_write_uses_the_pre_enrichment_capture():
    block = _mem_block()
    assert "_mem_said" in block
    assert "_original_raw" in block, "must source from the pre-enrichment capture"


def test_original_raw_is_captured_before_the_enrichment():
    """Order matters: capture at :2240 must precede the overwrite at :3184."""
    s = _src()
    capture = s.index("_original_raw = raw")
    overwrite = s.index('raw = f"[WORLD_KNOWLEDGE')
    assert capture < overwrite, (
        "_original_raw is captured after the enrichment — it would hold the "
        "contaminated text too"
    )


def test_the_august_remediation_is_still_in_place():
    """The sibling fix at :6337 must not regress while fixing this one."""
    s = _src()
    assert "_state, _original_raw, response," in s, (
        "state_manager.update no longer uses _original_raw — F-5 regressed"
    )


def test_interaction_log_also_records_the_real_words():
    assert "_write_interaction(_mem_said" in _src()
