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

    # ── prediction_error_state (WO-PREDICTION-ERROR-EXEC-WIRE-001) ───────────
    # Source: memory.expectation_tracker.score_expectation(edge_hint).
    # Keys: prediction_error (float 0–1), surprise_level (str).
    # surprise_level "strong" injects a "witness" preference into learning_advice
    # so the frozen executive.decide() steers toward witness instead of answer.
    prediction_error_state: dict = field(default_factory=dict)

    # ── temporal_state (WO-TEMPORAL-EXEC-WIRE-001) ────────────────────────────
    # Source: faculties.temporal.compute() — computed BEFORE _executive_faculty()
    # so the Executive sees temporal context when deciding.
    # Keys: circadian_phase (str), interaction_gap_hours (float),
    #       has_deferred_threads (bool).
    # interaction_gap_hours >= 24 → injects "celebrate" preference via learning_advice.
    # has_deferred_threads → injects "reflect" preference.
    temporal_state: dict = field(default_factory=dict)

    # ── self_state (WO-SELF-MODEL-EXEC-WIRE-001) ──────────────────────────────
    # Source: self.elo_self_model.EloSelfState (loaded live each turn).
    # Keys: curiosity (float), mood (float), lifecycle_state (str).
    # Influences executive action preference via curiosity_cal_bias injected into
    # learning_advice when curiosity >= 0.7 and no competing wm_winner.
    # Readable by executive.py when unfrozen — currently reaches it via the
    # learning_advice channel that executive.py already reads.
    self_state: dict = field(default_factory=dict)

    # ── correction_alert (WO-CORRECTION-EXEC-WIRE-001) ───────────────────────────
    # Source: self_improvement.correction_store.search_corrections(raw_input).
    # Keys: category (str — why-prefix derived), frequency (int — count of
    #       matching corrections for this input), top_correction (dict | None).
    # frequency >= 5 → injects "reflect" at 0.80 via learning_advice.
    # frequency >= 3 → injects "reflect" at 0.65 (advisory, does not force).
    # FREEZE_V1_LOCK: executive.py untouched; channel is learning_advice.
    correction_alert: dict = field(default_factory=dict)

    # ── faculty_conflict (WO-FACULTY-CONFLICT-EXEC-SIGNAL-001) ──────────────────
    # Source: build_executive_context() structural pre-executive conflict detector.
    # Keys: detected (bool), severity ("none"|"moderate"|"high"),
    #       conflicting_faculties (list[str]).
    # Proxy for Memory-WKG divergence: recall/inquiry intent + strong prediction
    # surprise → Memory expected an answer it couldn't confirm; WKG diverges.
    # High severity injects "reflect" at 0.82 via the learning_advice channel so
    # the frozen executive.decide() pauses rather than committing immediately.
    # FREEZE_V1_LOCK: executive.py untouched.
    faculty_conflict: dict = field(default_factory=dict)

    # ── WO-SPINE-002: structured objects passed through from spine assembly ──────
    cognitive_state:  Any = None
    embodiment_state: Any = None
    execution_report: Any = None

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
            # WO-106: executive.decide() line 563 reads significance_score at TOP LEVEL
            # of attention_model. Before this fix it was only inside world_state, so
            # _sig_overall was always 0.0 and SP29 gates (memory_worthy,
            # self_init_eligible) were never set. Forward it explicitly here.
            "significance_score": self.world.get("significance_score", {}),
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
            "ec_significance":      self.world.get("significance_score", {}),
            "ec_epistemic_state":   None,
            # WO-SPINE-002: structured objects from spine assembly
            "ec_cognitive_state":   self.cognitive_state,
            "ec_embodiment_state":  self.embodiment_state,
            "ec_execution_report":  self.execution_report,
            # WO-SELF-MODEL-EXEC-WIRE-001: self_state for transparency + unfreeze readiness
            "ec_self_state":   self.self_state,
        }

        # WO-SELF-MODEL-EXEC-WIRE-001: forward learning_advice from attention dict.
        # Bug fix: spine injects learning_advice into _attention_in BEFORE as_dict() is
        # called; as_dict() was dropping it. Preserve it so executive.decide() sees it.
        _la = self.attention.get("learning_advice")
        if _la is not None:
            d["learning_advice"] = _la

        # WO-SELF-MODEL-EXEC-WIRE-001: curiosity CAL bias.
        # If curiosity >= 0.7 and no competing wm_winner, blend a bias toward
        # "challenge" and "connect" into learning_advice so the frozen executive
        # experiences self-state influence via the channel it already reads.
        # Bias weight 0.72 — intentionally below the default "answer" confidence (0.8)
        # so curiosity tips the scale on ambiguous turns rather than always overriding.
        _curiosity = float(self.self_state.get("curiosity", 0.0))
        _mood      = str(self.self_state.get("mood_label", self.self_state.get("mood", "")))
        _wm_winner = self.attention.get("wm_winner", "")
        if _curiosity >= 0.7 and _wm_winner not in ("creation", "build"):
            _existing_la: dict = d.get("learning_advice") or {}
            _existing_prefs: dict = dict(_existing_la.get("preferences") or {})
            # Only boost if the existing lesson advice doesn't already prefer these actions
            # at a higher weight (lesson evidence takes precedence over self-state bias).
            _BIAS_W = round(0.62 + (_curiosity - 0.7) * 0.33, 3)  # 0.62 at 0.7, 0.72 at 1.0
            for _act in ("challenge", "connect"):
                if _existing_prefs.get(_act, 0.0) < _BIAS_W:
                    _existing_prefs[_act] = _BIAS_W
            _bias_la = dict(_existing_la)
            _bias_la["preferences"] = _existing_prefs
            if "confidence" not in _bias_la or _bias_la["confidence"] < 0.55:
                _bias_la["confidence"] = 0.55
            if not _bias_la.get("rationale"):
                _bias_la["rationale"] = (
                    f"eLo's curiosity ({_curiosity:.2f}) leans toward challenge and connect"
                )
            d["learning_advice"] = _bias_la

        # Downweight "create" and "connect" when mood is depleted (mood_val < 0.35).
        _mood_val = float(self.self_state.get("mood", 0.55))
        if _mood_val < 0.35 and "learning_advice" in d:
            _la_low = dict(d["learning_advice"])
            _prefs_low = dict(_la_low.get("preferences") or {})
            for _act in ("create", "connect"):
                if _prefs_low.get(_act, 0.0) > 0.0:
                    _prefs_low[_act] = max(0.0, _prefs_low[_act] - 0.25)
            _la_low["preferences"] = _prefs_low
            d["learning_advice"] = _la_low

        # WO-PREDICTION-ERROR-EXEC-WIRE-001: strong surprise → prefer "witness".
        # A strong prediction_error (>= 0.75) means this turn was genuinely unexpected.
        # Inject "witness" at weight 0.90 into learning_advice so the frozen executive
        # chooses to hold and observe rather than immediately answering or building.
        # "build" downgrade: weight 0.80 only overrides build at 0.65 (momentum case),
        # not 0.90 (explicit build phrase) — avoids silencing genuine creative intent.
        d["ec_prediction_error"] = self.prediction_error_state
        _pe_level = str(self.prediction_error_state.get("surprise_level", "none"))
        _pe_val   = float(self.prediction_error_state.get("prediction_error", 0.0))
        if _pe_level == "strong_surprise" and _pe_val >= 0.75:
            _pe_la   = dict(d.get("learning_advice") or {})
            _pe_prefs = dict(_pe_la.get("preferences") or {})
            if _pe_prefs.get("witness", 0.0) < 0.90:
                _pe_prefs["witness"] = 0.90
            _pe_la["preferences"] = _pe_prefs
            if "confidence" not in _pe_la or _pe_la["confidence"] < 0.75:
                _pe_la["confidence"] = 0.75
            _pe_la["rationale"] = (
                _pe_la.get("rationale") or
                f"strong prediction error ({_pe_val:.2f}) — witness before committing"
            )
            d["learning_advice"] = _pe_la

        # WO-TEMPORAL-EXEC-WIRE-001: temporal state → learning_advice channel.
        # interaction_gap_hours >= 24 → prefer "celebrate" (long reunion).
        # has_deferred_threads → prefer "reflect" (pick up open threads).
        # FREEZE_V1_LOCK: executive.py is frozen — channel is learning_advice.
        d["ec_temporal_state"] = self.temporal_state
        _gap_h = float(self.temporal_state.get("interaction_gap_hours", 0.0))
        _deferred = bool(self.temporal_state.get("has_deferred_threads", False))
        if _gap_h >= 24.0 or _deferred:
            _tm_la    = dict(d.get("learning_advice") or {})
            _tm_prefs = dict(_tm_la.get("preferences") or {})
            if _gap_h >= 24.0 and _tm_prefs.get("celebrate", 0.0) < 0.82:
                _tm_prefs["celebrate"] = 0.82
            if _deferred and _tm_prefs.get("reflect", 0.0) < 0.70:
                _tm_prefs["reflect"] = 0.70
            _tm_la["preferences"] = _tm_prefs
            if "confidence" not in _tm_la or _tm_la["confidence"] < 0.60:
                _tm_la["confidence"] = 0.60
            if not _tm_la.get("rationale"):
                _parts = []
                if _gap_h >= 24.0:
                    _parts.append(f"long gap ({_gap_h:.0f}h) → celebrate reunion")
                if _deferred:
                    _parts.append("open threads → reflect")
                _tm_la["rationale"] = "; ".join(_parts)
            d["learning_advice"] = _tm_la

        # WO-CORRECTION-EXEC-WIRE-001: correction history → lower confidence / reflect.
        # frequency >= 5: inject "reflect" at 0.80 (recurring error pattern — pause).
        # frequency >= 3: inject "reflect" at 0.65 (advisory — note concern without
        #   forcing; other stronger signals can still override).
        # FREEZE_V1_LOCK: executive.py untouched; channel is learning_advice.
        d["ec_correction_alert"] = self.correction_alert
        _ca_freq = int(self.correction_alert.get("frequency", 0))
        _ca_cat  = str(self.correction_alert.get("category", ""))
        if _ca_freq >= 3:
            _ca_la    = dict(d.get("learning_advice") or {})
            _ca_prefs = dict(_ca_la.get("preferences") or {})
            _ca_weight = 0.80 if _ca_freq >= 5 else 0.65
            if _ca_prefs.get("reflect", 0.0) < _ca_weight:
                _ca_prefs["reflect"] = _ca_weight
            _ca_la["preferences"] = _ca_prefs
            if "confidence" not in _ca_la or _ca_la["confidence"] < 0.60:
                _ca_la["confidence"] = 0.60
            _ca_la["rationale"] = (
                _ca_la.get("rationale") or
                f"correction pattern ({_ca_cat!r}, ×{_ca_freq}) — reflect before repeating error"
            )
            d["learning_advice"] = _ca_la

        # WO-FACULTY-CONFLICT-EXEC-SIGNAL-001: Memory-WKG conflict → prefer "reflect".
        # High-severity structural conflict (recall/inquiry intent + strong prediction
        # surprise) means Memory and WKG are diverging — inject "reflect" at 0.82 so
        # the frozen executive pauses before committing. Moderate severity is logged
        # only (ec_faculty_conflict key) without overriding action preference.
        # FREEZE_V1_LOCK: executive.py untouched; channel is learning_advice.
        d["ec_faculty_conflict"] = self.faculty_conflict
        _fc_detected = bool(self.faculty_conflict.get("detected", False))
        _fc_severity = str(self.faculty_conflict.get("severity", "none"))
        if _fc_detected and _fc_severity == "high":
            _fc_la    = dict(d.get("learning_advice") or {})
            _fc_prefs = dict(_fc_la.get("preferences") or {})
            if _fc_prefs.get("reflect", 0.0) < 0.82:
                _fc_prefs["reflect"] = 0.82
            _fc_la["preferences"] = _fc_prefs
            if "confidence" not in _fc_la or _fc_la["confidence"] < 0.70:
                _fc_la["confidence"] = 0.70
            _fc_la["rationale"] = (
                _fc_la.get("rationale") or
                "faculty conflict ({}) — reflect before committing".format(
                    ", ".join(self.faculty_conflict.get("conflicting_faculties", []))
                )
            )
            d["learning_advice"] = _fc_la

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
    embodiment_state = None,  # WO-SPINE-002: prior-turn EmbodimentState | None
    execution_report = None,  # WO-SPINE-002: prior-turn ExecutionReport | None
    edge_hint: str = "",      # WO-PREDICTION-ERROR-EXEC-WIRE-001: used to score prediction_error
    temporal: dict | None = None,  # WO-TEMPORAL-EXEC-WIRE-001: {circadian_phase, interaction_gap_hours, has_deferred_threads}
    raw_input: str = "",     # WO-CORRECTION-EXEC-WIRE-001: raw user input for correction search
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
        # SP-27/SP-28/SP-29 (WO-NAV-006): load previous world + compute delta before assembly
        _previous_world: dict = {}
        _world_delta: dict = {}
        try:
            from runtime.world_delta import load_previous_world as _lpw
            _previous_world = _lpw()
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
            # SP-27 (WO-NAV-006): previous turn's world summary (read-only for Executive)
            "previous_world":     _previous_world,
            # SP-7 (WO-NAV-004): surfaces count for delta computation
            "surfaces_count":     len(getattr(world, "surfaces", ()) or ()),
        }

        # SP-28 (WO-NAV-006): compute world delta comparing previous and current
        try:
            from runtime.world_delta import compute_delta as _cdelta
            _world_delta = _cdelta(_previous_world, world_dict)
        except Exception:
            pass
        world_dict["world_delta"] = _world_delta

        # SP-29 schema layer (WO-NAV-006): compute significance score from delta
        _significance_score: dict = {}
        try:
            from runtime.significance_faculty import compute_significance as _csig
            _significance_score = _csig(_world_delta)
        except Exception:
            pass
        world_dict["significance_score"] = _significance_score

        # SP-27 (WO-NAV-006): save current world summary for next turn's delta
        try:
            from runtime.world_delta import save_world_summary as _sws
            _sws(world)
        except Exception:
            pass

        # SP-13 (WO-NAV-012): candidate_surfaces — reachable surfaces from current body position
        # Filtered to reachable=True, sorted route_confidence DESC then horizontal_gap ASC, capped at 10.
        # Empty list when body_win_id=-1 (mid-hop / L3-NAV-3).
        _candidate_surfaces: list = []
        try:
            from world.navigation import generate_candidates as _gen_cands
            _all_cands = _gen_cands(
                body_win_id=getattr(world, "body_win_id", -1),
                surface_edges=getattr(world, "surface_edges", ()),
                surface_index=getattr(world, "win_id_to_surface", {}),
                jump_px=getattr(world, "jump_px", 0),
                route_history=list(getattr(world, "route_history", ()) or ()),
            )
            _reachable = [c for c in _all_cands if c.reachable]
            _reachable.sort(key=lambda c: (-c.route_confidence, c.horizontal_gap))
            _candidate_surfaces = [
                {
                    "target_win_id":    c.target_win_id,
                    "horizontal_gap":   c.horizontal_gap,
                    "euclidean_gap_px": c.euclidean_gap_px,
                    "requires_verb":    c.requires_verb,
                    "route_confidence": c.route_confidence,
                }
                for c in _reachable[:10]
            ]
        except Exception:
            pass
        world_dict["candidate_surfaces"] = _candidate_surfaces

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

    # ── self_state (WO-SELF-MODEL-EXEC-WIRE-001) ──────────────────────────────
    # Load EloSelfState live. Read-only — never write here (CT4V-03 compliant).
    self_state_dict: dict = {}
    try:
        from self.elo_self_model import load as _load_self_state_wire
        _ess = _load_self_state_wire()
        self_state_dict = {
            "curiosity":       round(float(getattr(_ess, "curiosity",       0.60)), 3),
            "mood":            round(float(getattr(_ess, "mood",            0.55)), 3),
            "lifecycle_state": str(getattr(_ess, "lifecycle_state", "awake")),
        }
    except Exception:
        pass

    # ── prediction_error_state (WO-PREDICTION-ERROR-EXEC-WIRE-001) ───────────
    # Score the incoming edge_hint (or intent as proxy) against learned expectations.
    # Degrades gracefully — empty dict means no violation data available.
    prediction_error_state_dict: dict = {}
    _pe_hint = edge_hint or intent or ""
    if _pe_hint:
        try:
            from memory.expectation_tracker import score_expectation as _score_exp
            _viol = _score_exp(_pe_hint)
            prediction_error_state_dict = {
                "prediction_error": round(float(_viol.prediction_error), 4),
                "surprise_level":   str(_viol.level),
            }
        except Exception:
            pass

    # ── temporal_state (WO-TEMPORAL-EXEC-WIRE-001) ─────────────────────────────
    temporal_state_dict: dict = dict(temporal) if temporal else {}

    # ── correction_alert (WO-CORRECTION-EXEC-WIRE-001) ───────────────────────────
    # Search corrections for the raw input. If >= 3 corrections match, alert.
    # Category is derived from the why-field prefix of the top match.
    # Degrades gracefully — empty dict when store unreachable or no matches.
    correction_alert_dict: dict = {}
    if raw_input and raw_input.strip():
        try:
            from self_improvement.correction_store import search_corrections as _srch_corr
            _matches = _srch_corr(raw_input, top_k=6)
            if len(_matches) >= 3:
                # Derive category from the why field of the top match
                _top_why = str((_matches[0] or {}).get("why", "")) if _matches else ""
                _cat = _top_why.split(":")[0].strip() if ":" in _top_why else _top_why[:40].strip()
                correction_alert_dict = {
                    "category":       _cat or "unknown",
                    "frequency":      len(_matches),
                    "top_correction": _matches[0] if _matches else None,
                }
        except Exception:
            pass

    # ── faculty_conflict (WO-FACULTY-CONFLICT-EXEC-SIGNAL-001) ──────────────────
    # Structural pre-executive conflict detector — works from attention model fields
    # already available here. Text-based detect_conflicts() runs later in server.py
    # (line 5103, system-prompt level) and cannot reach the executive.
    # Proxy signal: recall/inquiry intent + strong prediction surprise → Memory was
    # expected to have an answer but the edge violated its expectations → likely
    # Memory-WKG divergence requiring reflection rather than immediate commitment.
    faculty_conflict_dict: dict = {
        "detected": False, "severity": "none", "conflicting_faculties": []
    }
    _recall_intent_fc = intent in ("recall", "inquiry", "clarify")
    _pe_level_fc      = str(prediction_error_state_dict.get("surprise_level", "none"))
    _pe_val_fc        = float(prediction_error_state_dict.get("prediction_error", 0.0))
    _wm_win_fc        = attn_dict.get("wm_winner", "")
    if _recall_intent_fc and _pe_level_fc == "strong_surprise" and _pe_val_fc >= 0.75:
        faculty_conflict_dict = {
            "detected": True,
            "severity": "high",
            "conflicting_faculties": ["memory", "wkg"],
        }
    elif (_recall_intent_fc and _wm_win_fc == "memory"
          and _pe_level_fc == "moderate_surprise" and _pe_val_fc >= 0.40):
        faculty_conflict_dict = {
            "detected": True,
            "severity": "moderate",
            "conflicting_faculties": ["memory", "wkg"],
        }

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
        self_state=self_state_dict,
        prediction_error_state=prediction_error_state_dict,
        temporal_state=temporal_state_dict,
        correction_alert=correction_alert_dict,
        faculty_conflict=faculty_conflict_dict,
        # agency, significance, epistemic_state remain None — NEW ASSUMPTION
        cognitive_state=cognitive_state,
        embodiment_state=embodiment_state,
        execution_report=execution_report,
    )
