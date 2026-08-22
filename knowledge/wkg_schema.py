"""
knowledge/wkg_schema.py — WKG Phase 1: schema, write gate, dual-classification mapping.

Authority: David L3, 2026-08-22
Contract:  docs/architecture/WKG_BUILD_CONTRACT_AMENDED_2026-08-22.md
Carve-out: docs/architecture/FREEZE_V1_CARVEOUT_WKG_2026-08-22.md

Phase 1 scope:
  - §3  Amendment A — 8 epistemic classes + dual-classification mapping table
  - §5  Amendment A — Claim schema with wkg_epistemic_class field
  - §5  Amendment C — schema extends existing Volume XXIV graph (no new store)
  - §6  — relationship vocabulary (19 types)
  - §14 Amendment B — write gate (governs when claims enter the graph)
  - §17 Amendment D — wkg: namespace is governed FREEZE V1 carve-out

What is NOT here:
  - No wkg_graph.json (Amendment C)
  - No wkg_loader.py (Amendment C)
  - No new CAL action (FREEZE_V1_LOCK — all 9 actions frozen)
  - No corpus data (Phase 2+)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ── §3: 8 WKG epistemic classes ───────────────────────────────────────────────

class WKGEpistemicClass(str, Enum):
    """
    The 8 epistemic classes every WKG Claim must carry.
    Stored in wkg_epistemic_class on every Claim node.
    """
    VERIFIED          = "VERIFIED"
    HISTORICAL        = "HISTORICAL"
    SOURCE_ATTRIBUTED = "SOURCE_ATTRIBUTED"
    SYMBOLIC          = "SYMBOLIC"
    HYPOTHESIS        = "HYPOTHESIS"
    SPECULATIVE       = "SPECULATIVE"
    DISPUTED          = "DISPUTED"
    UNKNOWN           = "UNKNOWN"


# ── §6: relationship vocabulary ────────────────────────────────────────────────

class WKGRelationshipType(str, Enum):
    """19 WKG relationship types. Use SYMBOLISES/INTERPRETED_AS where IS would mislead."""
    IS                          = "IS"
    PART_OF                     = "PART_OF"
    DERIVED_FROM                = "DERIVED_FROM"
    REPRESENTS                  = "REPRESENTS"
    SYMBOLISES                  = "SYMBOLISES"
    CORRESPONDS_TO              = "CORRESPONDS_TO"
    ASSOCIATED_WITH             = "ASSOCIATED_WITH"
    CAUSES                      = "CAUSES"
    INFLUENCES                  = "INFLUENCES"
    CONTRADICTS                 = "CONTRADICTS"
    SUPPORTS                    = "SUPPORTS"
    CHALLENGES                  = "CHALLENGES"
    ANALOGOUS_TO                = "ANALOGOUS_TO"
    TEMPORALLY_PRECEDES         = "TEMPORALLY_PRECEDES"
    DERIVED_MATHEMATICALLY_FROM = "DERIVED_MATHEMATICALLY_FROM"
    OBSERVED_AS                 = "OBSERVED_AS"
    PROPOSED_BY                 = "PROPOSED_BY"
    INTERPRETED_AS              = "INTERPRETED_AS"
    HYPOTHESISED_AS             = "HYPOTHESISED_AS"


# ── Amendment A: dual-classification mapping ──────────────────────────────────
# Maps each WKG epistemic class to Vol XXIV kind + confidence at the retrieval
# boundary. This is a schema constant — defined in Phase 1, never deferred.
# Executive reasons using kind + confidence. wkg_epistemic_class remains
# available for display and domain reasoning.
#
# Source: WKG_BUILD_CONTRACT_AMENDED_2026-08-22.md §3 dual-classification table.

EPISTEMIC_TO_VOL_XXIV: dict[str, dict] = {
    "VERIFIED":          {"kind": "fact",        "confidence": 0.95,  "provisional": False},
    "HISTORICAL":        {"kind": "fact",         "confidence": 0.75,  "provisional": False},
    "SOURCE_ATTRIBUTED": {"kind": "perspective",  "confidence": None,  "provisional": False},
    "SYMBOLIC":          {"kind": "perspective",  "confidence": None,  "provisional": False},
    "HYPOTHESIS":        {"kind": "inference",    "confidence": 0.50,  "provisional": True},
    "SPECULATIVE":       {"kind": "inference",    "confidence": 0.30,  "provisional": True},
    "DISPUTED":          {"kind": "inference",    "confidence": None,  "provisional": True},
    "UNKNOWN":           {"kind": "unknown",      "confidence": None,  "provisional": True},
}


def map_to_vol_xxiv(wkg_epistemic_class: str) -> dict:
    """
    Amendment A: map a WKG epistemic class to Vol XXIV kind + confidence.

    Returns dict: {"kind": str, "confidence": float|None, "provisional": bool}.
    Unrecognised classes fall back to UNKNOWN mapping.
    """
    return EPISTEMIC_TO_VOL_XXIV.get(
        wkg_epistemic_class,
        EPISTEMIC_TO_VOL_XXIV["UNKNOWN"],
    )


# ── Amendment B: write gate ───────────────────────────────────────────────────

class WriteGateDecision(str, Enum):
    """Possible outcomes of the write gate evaluation (Amendment B, ADR-Exec-005)."""
    WRITE                  = "WRITE"               # full Claim node — write permitted
    WRITE_AS_PERSPECTIVE   = "WRITE_AS_PERSPECTIVE" # kind:perspective — provenance preserved
    PROPOSED_PENDING_L3    = "PROPOSED_PENDING_L3"  # proposed_claim only; David L3 required
    WRITE_BOTH_CONTRADICTS = "WRITE_BOTH_CONTRADICTS"  # DISPUTED — write both + CONTRADICTS
    NEEDS_EVIDENCE         = "NEEDS_EVIDENCE"        # VERIFIED/HISTORICAL but no evidence pointer


@dataclass(frozen=True)
class WriteGateResult:
    decision: WriteGateDecision
    reason:   str


def evaluate_write_gate(claim: dict) -> WriteGateResult:
    """
    Amendment B: evaluate whether a proposed claim may enter the graph.

    Pipeline stages SOURCE → EXTRACT → CLASSIFY → NORMALISE → CONNECT →
    CROSS-CHECK → CONTRADICTION DETECTION → HYPOTHESIS are proposal stages only.
    No graph write occurs at any proposal stage. This function is the write
    boundary.

    Language-only processing is never evidence (ADR-Exec-005 D1). 'evidence'
    must be a non-empty list of checkable source pointers for VERIFIED/HISTORICAL.

    Returns WriteGateResult(decision, reason).
    """
    cls = claim.get("wkg_epistemic_class", "UNKNOWN")
    evidence = claim.get("evidence") or []

    if cls in ("VERIFIED", "HISTORICAL"):
        if evidence:
            return WriteGateResult(
                decision=WriteGateDecision.WRITE,
                reason=f"{cls}: evidence pointer present — write to graph permitted",
            )
        return WriteGateResult(
            decision=WriteGateDecision.NEEDS_EVIDENCE,
            reason=f"{cls}: evidence pointer required before graph write; language processing alone is not evidence",
        )

    if cls in ("SOURCE_ATTRIBUTED", "SYMBOLIC"):
        return WriteGateResult(
            decision=WriteGateDecision.WRITE_AS_PERSPECTIVE,
            reason=f"{cls}: stance or interpretation — write as kind:perspective; provenance preserved; no truth claim asserted",
        )

    if cls in ("HYPOTHESIS", "SPECULATIVE"):
        return WriteGateResult(
            decision=WriteGateDecision.PROPOSED_PENDING_L3,
            reason=f"{cls}: written as proposed_claim node only; requires David L3 confirmation before promotion to full Claim",
        )

    if cls == "DISPUTED":
        return WriteGateResult(
            decision=WriteGateDecision.WRITE_BOTH_CONTRADICTS,
            reason="DISPUTED: both claims written immediately with CONTRADICTS relationship (§10 Contradiction Engine — no gate)",
        )

    # UNKNOWN or unrecognised class — safest path
    return WriteGateResult(
        decision=WriteGateDecision.PROPOSED_PENDING_L3,
        reason=f"UNKNOWN/unrecognised class {cls!r}: written as proposed_claim pending further classification",
    )


# ── Schema: provenance ────────────────────────────────────────────────────────

@dataclass
class WKGProvenance:
    """Mandatory provenance fields — every non-derived WKG claim (§4)."""
    author:           str
    title:            str
    extraction_date:  str              # ISO date: when the claim was extracted
    source_type:      str = "external_corpus"
    volume:           Optional[str] = None
    chapter:          Optional[str] = None
    page:             Optional[str] = None
    edition:          Optional[str] = None
    publication_date: Optional[str] = None


# ── Schema: Source node (§5) ──────────────────────────────────────────────────

@dataclass
class WKGSource:
    """
    Source node. Stored in world_graph.json → wkg_sources[].
    id must carry wkg: namespace prefix, e.g. "wkg:source:Joseph:BookOfWisdom".
    """
    id:                str
    author:            str
    title:             str
    source_type:       str
    created_at:        str
    edition:           Optional[str] = None
    publication_date:  Optional[str] = None
    location:          Optional[str] = None
    page_chapter:      Optional[str] = None
    reliability_notes: Optional[str] = None


# ── Schema: Claim node (§5, Amendment A) ─────────────────────────────────────

@dataclass
class WKGClaim:
    """
    Claim node. Stored in world_graph.json → wkg_claims[] (full claims) or
    wkg_proposed_claims[] (HYPOTHESIS/SPECULATIVE pending David L3).

    id must carry wkg: namespace prefix, e.g. "wkg:Joseph:Moon-subconscious".
    wkg_epistemic_class is mandatory on every Claim (Amendment A).

    Vol XXIV kind + confidence are computed at retrieval time via map_to_vol_xxiv();
    they are NOT stored in the graph.
    """
    id:                  str
    subject:             str               # entity id, wkg: prefixed
    predicate:           str               # WKGRelationshipType value
    object:              str               # entity id or literal, wkg: prefixed
    source:              str               # WKGSource.id
    wkg_epistemic_class: str               # one of WKGEpistemicClass — mandatory
    created_at:          str
    updated_at:          str
    epistemic_status:    str = "active"    # active | proposed | superseded
    confidence:          Optional[float] = None
    evidence:            list = field(default_factory=list)
    interpretation:      Optional[str] = None
    temporal_scope:      Optional[str] = None
    notes:               Optional[str] = None
    provenance:          Optional[dict] = None   # WKGProvenance serialised to dict
    proposed_claim:      bool = False
    promotion_requires:  Optional[str] = None    # set when proposed_claim=True

    def vol_xxiv_kind(self) -> str:
        """Amendment A: Vol XXIV kind at retrieval boundary."""
        return map_to_vol_xxiv(self.wkg_epistemic_class)["kind"]

    def vol_xxiv_confidence(self) -> Optional[float]:
        """Amendment A: Vol XXIV confidence at retrieval boundary."""
        return map_to_vol_xxiv(self.wkg_epistemic_class)["confidence"]


# ── JSON field contracts (for validation in tests) ────────────────────────────

#: Required fields in every wkg_claims[] entry in world_graph.json.
WKG_CLAIM_REQUIRED_FIELDS: frozenset[str] = frozenset({
    "id", "subject", "predicate", "object",
    "source", "wkg_epistemic_class", "created_at", "updated_at",
})

#: Required fields in every wkg_sources[] entry in world_graph.json.
WKG_SOURCE_REQUIRED_FIELDS: frozenset[str] = frozenset({
    "id", "author", "title", "source_type", "created_at",
})

#: wkg: namespace — all WKG-originated nodes use this prefix.
WKG_NAMESPACE_PREFIX: str = "wkg:"

#: Proposed-claim status string.
WKG_PROPOSED_CLAIM_STATUS: str = "proposed_claim"
