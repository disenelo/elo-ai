"""
memory/spg_significance.py — WO-SPG-PATTERN-001.

Board ruling 2026-10-04: backfill is HELD until a scoring function exists.
Three inputs, in priority order:

    1. Relationship type weight
    2. Recurrence — the same claim across multiple turns scores higher
    3. Confidence — tiebreaker only

DEVIATION, STATED. The Board's ordering is written as
"DECIDED > FACT > BELIEF > OBSERVATION > ASSOCIATED_WITH". Checked against
memory/wkg/relationship_types.json: DECIDED, FACT and BELIEF are not in the
19-type vocabulary, and OBSERVATION exists only as OBSERVED_AS. Only
ASSOCIATED_WITH is real — which is the same defect WO-SPG-LINK-002 found in
_CCM_DIM_RELEVANT_RELS, where 11 of 12 named types could not exist on a
claim and the filter silently selected nothing.

So the ORDERING is honoured and the names are mapped onto types that exist.
ASSOCIATED_WITH stays last, exactly as ruled. For the Board: the axis those
four words actually describe is `epistemic_class` — VERIFIED, HISTORICAL,
SOURCE_ATTRIBUTED, HYPOTHESIS, SPECULATIVE, DISPUTED — not relationship
type. If that is what was meant, say so and this becomes a four-line change.

WHY RECURRENCE CARRIES THE REAL SIGNAL HERE. Live store: 2226 claims across
just 36 distinct triples, the most frequent appearing 1118 times. Type
weight barely separates anything when 2212 claims share one relationship,
and confidence is 0.7 on 1914 of them. Recurrence is the only input with
genuine spread, which is why it is log-scaled rather than linear — the
difference between 1 and 10 occurrences matters far more than 1000 to 1100.

CONFIDENCE IS A TIEBREAKER AND IS WEIGHTED LIKE ONE. It contributes at most
0.05, so it can separate two otherwise-equal claims and can never outrank
type or recurrence. "Tiebreaker only" is a constraint on the weight, not a
label.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Iterable, Mapping

# Real types only, ordered by how much structure and commitment the relation
# carries. ASSOCIATED_WITH is last, per the ruling — it is the default any
# untyped mention falls into and it asserts almost nothing.
RELATIONSHIP_WEIGHT: dict[str, float] = {
    "CAUSES":                      0.95,
    "IS":                          0.90,
    "PART_OF":                     0.85,
    "DERIVED_MATHEMATICALLY_FROM": 0.85,
    "DERIVED_FROM":                0.80,
    "CONTRADICTS":                 0.75,
    "SUPPORTS":                    0.70,
    "PROPOSED_BY":                 0.70,
    "OBSERVED_AS":                 0.65,
    "CHALLENGES":                  0.60,
    "INFLUENCES":                  0.60,
    "REPRESENTS":                  0.55,
    "CORRESPONDS_TO":              0.50,
    "SYMBOLISES":                  0.50,
    "INTERPRETED_AS":              0.45,
    "ANALOGOUS_TO":                0.45,
    "TEMPORALLY_PRECEDES":         0.40,
    "HYPOTHESISED_AS":             0.30,
    "ASSOCIATED_WITH":             0.20,

    # Added to memory/wkg/relationship_types.json by WO-WKG-GRAPH-001
    # (28f9a76), another seat, after this map was written. The vocabulary went
    # 19 -> 26 and these seven had no weight, so every claim using one scored
    # as unknown. test_every_vocabulary_type_has_a_weight caught it, which is
    # the whole reason that test asserts over the live file rather than a
    # copy.
    #
    # Placed against the existing scale rather than given fresh numbers, so
    # the ordering stays one judgement and not two:
    "IS_A":                        0.88,   # taxonomic, just under IS (0.90)
    "CREATED_BY":                  0.75,   # provenance — who made it is structural
    "BELONGS_TO":                  0.70,   # membership, weaker than PART_OF (0.85)
    "AFFORDS":                     0.65,   # what a thing permits — embodiment-bearing
    "HAS_PROPERTY":                0.60,   # attribution, factual but mild
    "PRECEDES":                    0.40,   # same family as TEMPORALLY_PRECEDES (0.40)
    "CONNECTED_TO":                0.25,   # barely more committed than ASSOCIATED_WITH
}

# An unknown relationship scores as the weakest known one rather than zero.
# Zero would make a claim with a new, legitimate relation type invisible.
_UNKNOWN_WEIGHT = 0.20

W_TYPE, W_RECURRENCE, W_CONFIDENCE = 0.65, 0.30, 0.05

# Recurrence saturates: past this many occurrences, more adds nothing.
_RECURRENCE_CAP = 50


def triple(claim: Mapping) -> tuple:
    """The identity of a claim for recurrence purposes."""
    return (
        str(claim.get("subject_entity_id") or ""),
        str(claim.get("relationship_type") or ""),
        str(claim.get("object_entity_id") or ""),
    )


def recurrence_index(claims: Iterable[Mapping]) -> Counter:
    """How many times each triple appears."""
    return Counter(triple(c) for c in claims)


def _recurrence_score(count: int) -> float:
    """
    Log-scaled. The step from 1 occurrence to 10 means far more than 1000 to
    1100, and the live store's counts span 1 to 1118.
    """
    if count <= 1:
        return 0.0
    return min(1.0, math.log10(count) / math.log10(_RECURRENCE_CAP))


def score_claim(claim: Mapping, *, recurrence: int = 1) -> float:
    """Significance in 0.0–1.0 for one claim. Deterministic."""
    rel = str(claim.get("relationship_type") or "").strip().upper()
    type_w = RELATIONSHIP_WEIGHT.get(rel, _UNKNOWN_WEIGHT)

    try:
        conf = float(claim.get("confidence"))
    except (TypeError, ValueError):
        conf = 0.5
    conf = max(0.0, min(1.0, conf))

    raw = (W_TYPE * type_w
           + W_RECURRENCE * _recurrence_score(max(1, int(recurrence)))
           + W_CONFIDENCE * conf)
    return round(max(0.0, min(1.0, raw)), 4)


def score_all(claims: Iterable[Mapping]) -> dict[str, float]:
    """claim_id -> significance, with recurrence computed across the batch."""
    claims = list(claims)
    counts = recurrence_index(claims)
    out: dict[str, float] = {}
    for c in claims:
        cid = str(c.get("claim_id") or "")
        if cid:
            out[cid] = score_claim(c, recurrence=counts[triple(c)])
    return out
