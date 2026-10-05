"""
tests/test_dream_epistemic_tag.py — WO-DREAM-EPISTEMIC-TAG-001.

The WO's gap: "eLo has no mechanism to answer 'was that from a dream?'"

The cause is sharper than the WO's diagnosis. record_claim() ACCEPTS
memory_origin and uses it as the dream write-gate (WO-DREAM-VERIFY-001) — and
then drops it. It was never a key on the claim. Every claim passed an origin
check whose answer nothing kept.

The WO proposes adding DREAM_DERIVED / DREAM_HYPOTHESIS to EpistemicClass.
Not done, deliberately: MemoryOrigin already IS the origin vocabulary
(DREAM_SIMULATION / DREAM_INSIGHT, Four-Layer Identity Model 2026-08-31), and
a second one means two places to ask the same question. epistemic_class says
how much to trust a claim; origin says where it came from. Folding one into
the other needs a DREAM_ twin of every class, forever. Raised for David/Board
rather than decided quietly.
"""
from __future__ import annotations

import pytest

import runtime.wkg_faculty as wkg
from runtime.memory_origin import MemoryOrigin


@pytest.fixture(autouse=True)
def _own_store(tmp_path, monkeypatch):
    """
    Never the live WKG store — that leak class cost a graph once already.

    The vocabulary files live in the same directory as the data, so redirecting
    the store also empties relationship_types and every claim is rejected as
    unknown. The vocabulary is copied in; only the DATA starts empty.
    """
    import json
    import os
    import shutil

    live = os.path.join(os.path.dirname(wkg.__file__), "..", "memory", "wkg")
    for vocab in ("relationship_types.json", "entity_types.json"):
        src = os.path.join(live, vocab)
        if os.path.exists(src):
            shutil.copy2(src, tmp_path / vocab)
    for data in ("claims.json", "entities.json", "sources.json"):
        (tmp_path / data).write_text(json.dumps([]))

    monkeypatch.setattr(wkg, "_WKG_DIR", str(tmp_path))
    monkeypatch.setattr(wkg, "_link_claim_to_spg", lambda claim: None)


def _entities():
    # create_entity(entity_type, label) — type first. It can also REFUSE a
    # fragment of a name already held, so the ids are read defensively.
    a = wkg.create_entity("PERSON", "Dreamer Testsubject")
    b = wkg.create_entity("CONCEPT", "Testable Notion")
    assert "entity_id" in a, a
    assert "entity_id" in b, b
    return a["entity_id"], b["entity_id"]


def test_a_claims_origin_survives_being_written():
    subj, obj = _entities()
    claim = wkg.record_claim(
        subj, "ASSOCIATED_WITH", obj,
        epistemic_class="HYPOTHESIS",
        source_id="dream:test",
        memory_origin=MemoryOrigin.DREAM_INSIGHT.value,
    )

    assert claim["memory_origin"] == "dream_insight", (
        "the origin was checked at the gate and thrown away"
    )
    assert wkg.get_memory_origin(claim["claim_id"]) == "dream_insight"


def test_was_that_from_a_dream_is_answerable():
    """The WO's acceptance, stated as the question it names."""
    subj, obj = _entities()
    dreamt = wkg.record_claim(
        subj, "ASSOCIATED_WITH", obj,
        epistemic_class="HYPOTHESIS", source_id="dream:1",
        memory_origin=MemoryOrigin.DREAM_INSIGHT.value,
    )
    said = wkg.record_claim(
        subj, "ASSOCIATED_WITH", obj,
        epistemic_class="HYPOTHESIS", source_id="conversation:1",
        memory_origin=MemoryOrigin.REAL_EXPERIENCE.value,
    )

    # Same epistemic_class — indistinguishable without origin. That was the gap.
    assert dreamt["epistemic_class"] == said["epistemic_class"]

    dream_origins = {MemoryOrigin.DREAM_SIMULATION.value,
                     MemoryOrigin.DREAM_INSIGHT.value}
    assert wkg.get_memory_origin(dreamt["claim_id"]) in dream_origins
    assert wkg.get_memory_origin(said["claim_id"]) not in dream_origins


def test_a_legacy_claim_says_unknown_rather_than_guessing():
    subj, obj = _entities()
    claim = wkg.record_claim(
        subj, "ASSOCIATED_WITH", obj,
        epistemic_class="HYPOTHESIS", source_id="conversation:1",
    )
    assert claim["memory_origin"] is None, (
        "an unrecorded origin must read as unknown, not as not-a-dream"
    )


def test_the_dream_write_gate_still_blocks_unearned_dream_content():
    """Storing the origin must not weaken the boundary that reads it."""
    subj, obj = _entities()
    with pytest.raises(ValueError, match="not eligible"):
        wkg.record_claim(
            subj, "ASSOCIATED_WITH", obj,
            epistemic_class="HYPOTHESIS", source_id="dream:raw",
            memory_origin=MemoryOrigin.DREAM_SIMULATION.value,
        )


# ── the production chain ────────────────────────────────────────────────────
#
# Storing the origin only helps if the writers pass one. There is exactly ONE
# production path into record_claim — server.py's two live-turn claim writers —
# and neither passed memory_origin, so every live claim recorded None and
# "was that from a dream?" answered unknown for all of them.
#
# Both are conversation-derived, which is the enum's own definition of
# REAL_EXPERIENCE: "from actual conversation / events".

import pathlib


def _server_source() -> str:
    return (pathlib.Path(__file__).resolve().parent.parent / "server.py").read_text()


def test_every_live_claim_records_where_it_came_from():
    code = _server_source()
    assert code.count("memory_origin=_MemoryOrigin.REAL_EXPERIENCE.value") == 2, (
        "both live-turn claim writers must record an origin — a claim with "
        "origin None cannot be told apart from a dream-derived one"
    )


def test_the_origin_the_server_passes_is_a_real_enum_member():
    """A typo'd origin string raises inside record_claim's MemoryOrigin(...)."""
    assert MemoryOrigin.REAL_EXPERIENCE.value == "real_experience"


def test_a_conversation_claim_is_not_mistaken_for_a_dream():
    """The end of the chain, with the value the server actually sends."""
    subj, obj = _entities()
    claim = wkg.record_claim(
        subj, "ASSOCIATED_WITH", obj,
        epistemic_class="SOURCE_ATTRIBUTED",
        source_id="interaction:answer",
        confidence=0.7,
        memory_origin=MemoryOrigin.REAL_EXPERIENCE.value,
    )
    origin = wkg.get_memory_origin(claim["claim_id"])

    assert origin == "real_experience"
    assert origin not in {MemoryOrigin.DREAM_SIMULATION.value,
                          MemoryOrigin.DREAM_INSIGHT.value}
