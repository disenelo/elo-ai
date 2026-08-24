"""
runtime/executive_context.py — WO-ONEBRAIN-012: Executive Consumption Contract

Canonical schema for the context the Executive receives each turn.

DERIVATION RULE (CA verbatim, 2026-08-14):
  "The schema must be DERIVED FROM EXISTING CANON, not invented."
  Sources: runtime/contracts.py · runtime/cognitive_snapshot.py
           docs/architecture/Volume_V §1 CONTRACTS
           docs/architecture/Volume_VII Ch.2 Executive Assembly

FREEZE_V1_LOCK: executive.py is FROZEN — this module enriches the dict that
  exec_decide() reads, not executive.py itself. When executive.py is unfrozen,
  it will receive ExecutiveContext directly.

NEW ASSUMPTION LIST (flagged to CA per W5 instructions):
  agency       — not in any current contract or volume; P2 per 0036 (CA: "don't
                 build autonomous agency yet"); field left as None placeholder.
  epistemic_state — Vol VII Ch.3 describes epistemic tiers for SPEECH LICENSING,
                 not as a structured cognitive-state field; no contract defines it;
                 flag before adding.
  significance — Vol V §1.5 defines significance_score (0→1) and memory_action;
                 significance_faculty.py does NOT EXIST; cannot populate without
                 building a new component; field stubbed as None pending CA ruling.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutiveContext:
    """
    The canonical cognitive decision context the Executive must receive.

    Each field traces to an existing contract or volume entry.
    Fields absent from canon are marked # NEW ASSUMPTION and left None.
    executive.py (FROZEN) reads this as a flat dict via as_dict().
    """

    # ── intent ─────────────────────────────────────────────────────────────────
    # Source: CognitiveState.intent_signal (contracts.py §Language Faculty)
    #         executive.decide() reads attention_model["intent"]
    intent: str = "conversation"

    # ── emotion ────────────────────────────────────────────────────────────────
    # Source: CognitiveState.emotional_context (contracts.py §Attention Faculty)
    #         {inferred_state, valence, momentum, closure, energy, tension}
    #         executive.decide() reads attention_model["emotional_context"]
    emotion: dict = field(default_factory=dict)

    # ── world ──────────────────────────────────────────────────────────────────
    # Source: CognitiveState.world_state (contracts.py §World Faculty / WO-CANON-XV)
    #         Assembled as LiveWorldState; passed to exec_decide as world_state dict.
    world: dict = field(default_factory=dict)

    # ── attention ──────────────────────────────────────────────────────────────
    # Source: CognitiveState.attention_scores / attention_state (contracts.py §Attention)
    #         CognitiveSnapshot.intent, valence, momentum (cognitive_snapshot.py)
    #         wm_winner / wm_mode / wm_budget from WorkingMemory.attention
    attention: dict = field(default_factory=dict)

    # ── working_memory ─────────────────────────────────────────────────────────
    # Source: CognitiveState.working_memory (contracts.py §Working Memory / WO-CANON-VI)
    #         Compressed: wm_winner (str), wm_mode (str), wm_budget (float)
    working_memory: dict = field(default_factory=dict)

    # ── capabilities ────────────────────────────────────────────────────────────
    # Source: CognitiveState.capability_candidates (contracts.py §Capability Faculty)
    #         Spine builds this via _capability_faculty(meaning, intent)
    capabilities: list = field(default_factory=list)

    # ── memory ─────────────────────────────────────────────────────────────────
    # Source: CognitiveState.vault_context / high_priority_memories / vault_context
    #         (contracts.py §Memory Faculty)
    memory: dict = field(default_factory=dict)

    # ── identity ───────────────────────────────────────────────────────────────
    # Source: CognitiveState relationship fields (contracts.py §Relationship Faculty):
    #         person_id, relationship_type, familiarity, trust, expression_posture
    #         Plus CognitiveSnapshot.self_mood / self_curiosity (eLo's own state)
    identity: dict = field(default_factory=dict)

    # ── lessons ────────────────────────────────────────────────────────────────
    # Card 0075 (D3 · Option A · David L3 2026-08-21).
    # Source: self.lesson_store.recall() — CONFIRMED lessons only, filtered at
    # the gate to ADR-Exec-005 D1: only lessons with at least one VERIFIED
    # evidence entry (executed action with verified outcome). Language-only
    # lessons and pure-numeric process-id session evidence are rejected here.
    # Compliance with ADR-Exec-005 D6: this is a value READ by whichever
    # consumer chooses to consult it; no learning logic lives inside the
    # Executive. Empty list is the honest default when nothing clears the bar.
    lessons: list = field(default_factory=list)

    # ── agency ─────────────────────────────────────────────────────────────────
    # NEW ASSUMPTION — not in any current contract.
    # CA: "don't build autonomous agency yet — otherwise we'll create another orphan"
    # (0036 §P2). Field reserved; do not populate until CA rules.
    agency: None = None

    # ── significance ────────────────────────────────────────────────────────────
    # PARTIAL SOURCE — schema defined in Vol V §1.5 (significance_score: float,
    # memory_action: str) but significance_faculty.py does not exist.
    # Cannot populate from running code. CA ruling required before building.
    significance: None = None

    # ── epistemic_state ─────────────────────────────────────────────────────────
    # NEW ASSUMPTION — Vol VII Ch.3 describes epistemic tiers for speech licensing
    # but no contract defines this as a structured cognitive-state field.
    # CA ruling required before adding a field.
    epistemic_state: None = None

    def as_dict(self) -> dict:
        """
        Flatten to the dict format exec_decide() currently reads.

        Keys already consumed by executive.decide() (FROZEN):
          intent, emotional_context, wm_winner, world_state
        New keys added here are readable when executive.py is unfrozen.
        """
        d = {
            # keys the FROZEN executive.decide() already reads
            "intent":            self.intent,
            "emotional_context": self.emotion,
            "wm_winner":         self.attention.get("wm_winner", ""),
            "wm_mode":           self.attention.get("wm_mode", "reactive"),
            "wm_budget":         self.attention.get("wm_budget", 0.5),
            "world_state":       self.world,
            "cognitive_state_focal": self.attention.get("focal_thread", ""),
            "surface_affordances":   self.attention.get("surface_affordances", []),
            # canonical additions — readable when executive.py unfreezes
            "ec_capabilities": self.capabilities,
            "ec_memory":       self.memory,
            "ec_identity":     self.identity,
            # Card 0075 (D3 · Option A): lessons exposed at TOP-LEVEL key
            # `lessons` so the frozen executive.decide() would find it if it
            # were written to read it. The frozen file currently contains zero
            # references to "lesson" (verified: grep -c lesson runtime/executive.py = 0),
            # so the empirical answer to "does executive.py read this key?" is NO.
            # That is the honest, useful result — LOOP-7 stays UNKNOWN until the
            # Executive is unfrozen behind a Learning Faculty consult (ADR-Exec-005 D6).
            "lessons":         self.lessons,
            # NEW ASSUMPTION placeholders — not yet populated
            "ec_agency":            None,
            "ec_significance":      None,
            "ec_epistemic_state":   None,
        }
        return d


def _filter_lesson_for_executive(row: dict) -> bool:
    """
    Card 0075 D1 gate (ADR-Exec-005 D1 verbatim):
      "Language alone is never evidence. Only executed actions with verified
       consequences influence future policy."

    A lesson may only enter ExecutiveContext.lessons when at least ONE evidence
    entry is BOTH:
      - verified == True   (executed action reached a verified outcome), AND
      - session_id is non-empty and NOT a pure-numeric string
        (pure numbers = process IDs — a promotion artefact, not evidence
         of a real session; called out explicitly in card 0075).
    """
    ev = row.get("evidence", []) or []
    for e in ev:
        if not e.get("verified"):
            continue
        sid = str(e.get("session_id", "") or "")
        if not sid:
            continue
        if sid.isdigit():
            continue
        return True
    return False


def build_executive_context(
    intent:         str,
    emotional_context: dict,
    world,          # LiveWorldState | None
    working_memory, # WorkingMemory | None
    capabilities:   list,
    cognitive_state, # CognitiveState | None (contracts.py)
    affordances,    # surface_affordances sequence | None
    attention:      dict,  # raw attention_model from server.py
    lessons:        list | None = None,  # Card 0075 D3 · Option A: filtered lessons
) -> ExecutiveContext:
    """
    Assemble ExecutiveContext from the canonical sources available at the
    _executive_faculty call site in spine.py.

    Every field traces to a canonical source. NEW ASSUMPTIONs stay None.
    Failures are swallowed individually — a missing source degrades gracefully.
    """

    # ── world ──────────────────────────────────────────────────────────────────
    # D2 ruling (Card 0035): DesktopState.surface renamed to DesktopState.platform.
    # The platform label is exposed as `platform` here; "where eLo is" lives on
    # EloSelfState.surface (a different authority — Ruling D2).
    world_dict: dict = {}
    if world is not None:
        _desktop = getattr(world, "desktop", None)
        # SP-37 (WO-NAV-005): current embodiment — try EloSelfState, default "desktop"
        _current_embodiment = "desktop"
        try:
            from self.elo_self_model import load as _load_self_emb
            _current_embodiment = getattr(_load_self_emb(), "embodiment", "desktop") or "desktop"
        except Exception:
            pass
        world_dict = {
            "platform":           getattr(_desktop, "platform",   "") if _desktop else "",
            "active_app":         getattr(_desktop, "active_app", "") if _desktop else "",
            "available":          getattr(_desktop, "available",   True) if _desktop else False,
            "degraded":           list(getattr(world, "degraded", [])),
            "route_history":      list(getattr(world, "route_history", ()) or ()),
            # SP-6 (WO-NAV-003): live gaze target — win_id from GazeState via elo_spatial.json
            "gaze_win_id":        getattr(getattr(world, "gaze", None), "win_id", 0),
            # SP-37 (WO-NAV-005): embodiment scope filter input
            "current_embodiment": _current_embodiment,
        }

    # ── attention (wm competition + raw attention) ─────────────────────────────
    attn_dict: dict = dict(attention) if attention else {}
    if working_memory is not None:
        _attn_state = getattr(working_memory, "attention", None)
        if _attn_state is not None:
            attn_dict["wm_winner"] = getattr(_attn_state, "winner", "")
            attn_dict["wm_mode"]   = getattr(_attn_state, "mode",   "reactive")
            attn_dict["wm_budget"] = getattr(_attn_state, "budget",  0.5)
    if cognitive_state is not None:
        focal = getattr(cognitive_state, "focal_thread", "")
        if not focal:
            focal = ""
        attn_dict["focal_thread"] = focal
    if affordances:
        attn_dict["surface_affordances"] = (
            list(affordances) if not isinstance(affordances, list) else affordances
        )

    # ── working_memory ─────────────────────────────────────────────────────────
    wm_dict: dict = {
        "wm_winner": attn_dict.get("wm_winner", ""),
        "wm_mode":   attn_dict.get("wm_mode", "reactive"),
        "wm_budget": attn_dict.get("wm_budget", 0.5),
    }

    # ── capabilities ────────────────────────────────────────────────────────────
    # Source: _capability_faculty output (contracts.py CognitiveState.capability_candidates)
    caps: list = list(capabilities) if capabilities else []

    # ── memory ─────────────────────────────────────────────────────────────────
    # Source: CognitiveState.vault_context / high_priority_memories (contracts.py §Memory)
    mem_dict: dict = {}
    if cognitive_state is not None:
        vault = getattr(cognitive_state, "vault_context", "")
        high  = list(getattr(cognitive_state, "high_priority_memories", ()) or ())
        mem_dict = {"vault_context": vault, "high_priority_memories": high}

    # ── identity ───────────────────────────────────────────────────────────────
    # Source: CognitiveState relationship fields (contracts.py §Relationship Faculty)
    identity_dict: dict = {}
    if cognitive_state is not None:
        identity_dict = {
            "person_id":          getattr(cognitive_state, "person_id",          "david"),
            "relationship_type":  getattr(cognitive_state, "relationship_type",  "creator"),
            "familiarity":        getattr(cognitive_state, "familiarity",         0.55),
            "trust":              getattr(cognitive_state, "trust",               0.60),
            "expression_posture": getattr(cognitive_state, "expression_posture",  "warm"),
            "register":           getattr(cognitive_state, "register",            ""),
        }

    # ── lessons ────────────────────────────────────────────────────────────────
    # Card 0075 D3 · Option A · D1 gate: caller passes recall() output; we apply
    # the ADR-Exec-005 D1 verified-evidence filter here so no path skips it.
    lessons_in: list = list(lessons) if lessons else []
    lessons_out: list = [r for r in lessons_in if _filter_lesson_for_executive(r)]

    return ExecutiveContext(
        intent=intent,
        emotion=emotional_context,
        world=world_dict,
        attention=attn_dict,
        working_memory=wm_dict,
        capabilities=caps,
        memory=mem_dict,
        identity=identity_dict,
        lessons=lessons_out,
        # agency, significance, epistemic_state remain None — NEW ASSUMPTION
    )
