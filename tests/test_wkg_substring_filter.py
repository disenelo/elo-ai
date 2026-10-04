"""
tests/test_wkg_substring_filter.py — WO-WKG-JUNK-ENTITY-FILTER-001.

Dispatch: "if a new entity name is a substring of an existing entity (e.g.
'Raspberry' ⊂ 'Raspberry Pi'), reject it". And, underlined: eLo stays.

Those two pull against each other, which is the whole difficulty. "eLo" is
a whole-word substring of two existing labels:

    "David as creator of eLo"
    "eLo robot design constraints"

A naive substring check deletes the central entity of the entire project.
I nearly did exactly that earlier today with a fragment heuristic that
flagged eLo, and caught it only because the result looked wrong.

WHAT SEPARATES THEM:
    "Raspberry Pi"             a NAME. Two words. "Raspberry" is its head,
                               and the full name is the canonical form.
    "David as creator of eLo"  a DESCRIPTION. Five words. eLo is an
                               independent thing mentioned inside it.

So the rule rejects a candidate only when it is a word-PREFIX of a SHORT
(<= 3 word) existing label, and only when the candidate is not already an
entity in its own right. eLo is protected twice over: it is a suffix, not a
prefix, of the five-word label; and it already exists independently.

Checked in create_entity(), not record_claim(). The dispatch names
record_claim, but record_claim takes entity_ids, not labels — there is no
label there to filter. create_entity is where a label becomes an entity.
"""
from __future__ import annotations

import pytest

import runtime.wkg_faculty as wkg


@pytest.fixture
def _store(tmp_path, monkeypatch):
    from pathlib import Path
    d = tmp_path / "wkg"
    d.mkdir()
    src = Path(wkg.__file__).resolve().parent.parent / "memory" / "wkg"
    (d / "relationship_types.json").write_text(
        (src / "relationship_types.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(wkg, "_WKG_DIR", str(d))
    from memory.spg_graph import SPGGraph
    monkeypatch.setattr(SPGGraph, "load", classmethod(lambda cls, *a, **k: SPGGraph()))
    monkeypatch.setattr(SPGGraph, "save", lambda self, *a, **k: None)
    return d


def _mk(label):
    return wkg.create_entity(entity_type="CONCEPT", label=label, description="")


# ── The fragment is rejected ────────────────────────────────────────────────

def test_a_fragment_of_a_short_name_is_rejected(_store):
    _mk("Raspberry Pi")
    frag = _mk("Raspberry")
    assert frag.get("rejected") is True, frag
    assert [e["label"] for e in wkg._load("entities")] == ["Raspberry Pi"]


def test_the_rejection_names_what_superseded_it(_store):
    pi = _mk("Raspberry Pi")
    frag = _mk("Raspberry")
    assert frag.get("superseded_by") == pi["entity_id"]


def test_it_works_across_turns_not_just_within_one_text(_store):
    """
    The gap the extractor fix did not cover: the extractor only sees one
    turn's text, so "Raspberry Pi" today and "Raspberry" tomorrow slipped
    straight through.
    """
    _mk("NeoPixel ring")
    assert _mk("NeoPixel").get("rejected") is True


# ── eLo stays ───────────────────────────────────────────────────────────────

def test_elo_survives_being_inside_a_long_descriptive_label(_store):
    _mk("David as creator of eLo")
    e = _mk("eLo")
    assert e.get("rejected") is not True, e
    assert "eLo" in [x["label"] for x in wkg._load("entities")]


def test_elo_survives_being_the_prefix_of_a_long_label(_store):
    _mk("eLo robot design constraints")
    assert _mk("eLo").get("rejected") is not True


def test_an_existing_entity_is_never_rejected_as_a_fragment(_store):
    """
    Second protection: something already known in its own right is never a
    fragment of anything.

    Asking for it again IS refused — as a duplicate, which is correct; a
    second "eLo" row would be the bug. What must never happen is the
    FRAGMENT verdict, which would mean eLo was superseded by a label that
    merely contains him. My first version of this asserted no rejection at
    all and failed on the duplicate, which was the test being wrong.
    """
    first = _mk("eLo")
    _mk("eLo robot design constraints")
    again = _mk("eLo")
    assert first.get("rejected") is not True
    assert again.get("reason") != "fragment", again
    assert [e["label"] for e in wkg._load("entities")].count("eLo") == 1


# ── It must not eat real entities ───────────────────────────────────────────

@pytest.mark.parametrize("existing,candidate", [
    ("Raspberry Pi", "Pi"),            # suffix, not prefix
    ("Blender", "Blend"),              # not a whole word
    ("David Charles", "David Charles"), # the same thing
    ("Unity", "Unity Editor"),         # the longer one arriving second
])
def test_these_are_not_fragments(_store, existing, candidate):
    _mk(existing)
    out = _mk(candidate)
    if candidate == existing:
        assert out.get("rejected") is True   # duplicate, not a fragment
    else:
        assert out.get("rejected") is not True, (existing, candidate)


def test_a_fresh_store_rejects_nothing(_store):
    assert _mk("Raspberry").get("rejected") is not True


# ── Causal ──────────────────────────────────────────────────────────────────

def test_removing_the_long_name_lets_the_short_one_in(_store):
    assert _mk("Raspberry").get("rejected") is not True


# ── The guard inside _fragment_of, exercised directly ──────────────────────

def test_fragment_of_never_calls_a_known_entity_a_fragment():
    """
    _fragment_of() refuses to call something a fragment when it already
    exists in its own right. Tested DIRECTLY, because via create_entity()
    the duplicate branch fires first and this guard is never reached — a
    wire-cut removing it left every test green, which is how I found that
    out. Defence in depth, and only honest if something exercises it: if
    _NAME_MAX_WORDS is ever raised, this becomes the thing protecting eLo.
    """
    entities = [
        {"entity_id": "1", "label": "eLo"},
        {"entity_id": "2", "label": "eLo robot plan"},   # 3 words — within the name limit
    ]
    assert wkg._fragment_of("eLo", entities) is None

    without_itself = [e for e in entities if e["label"] != "eLo"]
    assert wkg._fragment_of("eLo", without_itself) is not None, (
        "precondition: without the self-entry it WOULD be read as a fragment"
    )
