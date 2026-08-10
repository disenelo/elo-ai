"""
runtime/spine/spine.py — The Cognitive Spine

One brain. One decision per turn.

The Spine orchestrates all faculties in sequence.
No faculty decides independently. All feed the Executive.
The Executive produces ONE CognitivePlan.
That plan drives conversation, avatar, desktop, and future embodiments.

Faculty order:
    Language → Memory → Attention → Relationship → Desktop → Capability → Executive → Gate
"""
from __future__ import annotations
import logging

from runtime.spine.plan import CognitivePlan

_log = logging.getLogger(__name__)
_log.addHandler(logging.NullHandler())
_log.propagate = False


# ─────────────────────────────────────────────────────────────────────────────
# LANGUAGE FACULTY — understand what was said
# Never chooses. Only interprets.
# ─────────────────────────────────────────────────────────────────────────────

def _language_faculty(raw: str) -> dict:
    """
    Normalise, repair typos, detect register and social intent.
    Returns: {original, meaning, register, social, intent, confidence}
    """
    result = {
        "original": raw,
        "meaning":  raw,
        "register": "",
        "social":   "",
        "intent":   "conversation",
        "confidence": 1.0,
    }
    try:
        from runtime.router.meaning_engine import normalise
        norm = normalise(raw)
        result["meaning"] = norm["cleaned"]
        result["social"]  = norm["social"]
        result["confidence"] = min(result["confidence"], norm["confidence"])
    except Exception as e:
        _log.debug("language_faculty/normalise: %s", e)

    try:
        from runtime.router.typo_engine import repair
        repaired = repair(result["meaning"])
        if repaired["confidence"] >= 0.80:
            result["meaning"] = repaired["interpretation"]
        result["confidence"] = min(result["confidence"], repaired["confidence"])
    except Exception as e:
        _log.debug("language_faculty/typo: %s", e)

    try:
        from runtime.router.intent_engine import detect as detect_intent
        intent_result = detect_intent(result["meaning"])
        result["intent"]      = intent_result["intent"]
        result["intent_chain"]= intent_result.get("chain", [])
        result["confidence"]  = min(result["confidence"],
                                    intent_result.get("confidence", 0.8))
    except Exception as e:
        _log.debug("language_faculty/intent: %s", e)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# CAPABILITY FACULTY — advertise what's possible
# Never chooses which capability to use. Lists candidates.
# ─────────────────────────────────────────────────────────────────────────────

def _capability_faculty(meaning: str, intent: str) -> list[dict]:
    """
    Returns candidate capabilities that could handle this input.
    The Executive decides which (if any) to invoke.
    """
    candidates = []
    try:
        from runtime.capabilities.registry import ALL_CAPABILITIES
        lower = meaning.lower()
        for cap in ALL_CAPABILITIES:
            if cap.future or not cap.enabled:
                continue
            score = sum(1 for v in cap.verbs if v.lower() in lower)
            if score > 0:
                candidates.append({
                    "id":       cap.id,
                    "category": cap.category,
                    "score":    score,
                    "requires_confirmation": cap.requires_confirmation,
                    "health":   cap.health_state,
                })
        candidates.sort(key=lambda x: x["score"], reverse=True)
    except Exception as e:
        _log.debug("capability_faculty: %s", e)

    # Also query the agent_router for its selection
    try:
        from runtime.router.agent_router import route as agent_route
        chain = None
        routed = agent_route(intent, meaning, chain=chain)
        # Merge with capability candidates
        routed_ids = {a[0] for a in routed}
        for cap in candidates:
            if cap["id"] in routed_ids:
                cap["score"] += 5  # boost router-confirmed caps
        candidates.sort(key=lambda x: x["score"], reverse=True)
    except Exception as e:
        _log.debug("capability_faculty/agent_route: %s", e)

    return candidates[:4]  # top 4 max


# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM FACULTY — detect system control intents
# ─────────────────────────────────────────────────────────────────────────────

def _system_faculty(meaning: str) -> tuple[str, str] | None:
    """Returns (action, arg) if a system action is present, else None."""
    try:
        from tools.system_agent import detect
        return detect(meaning)
    except Exception as e:
        _log.debug("system_faculty: %s", e)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# EXECUTIVE FACULTY — the only decision maker
# Receives all faculty outputs. Produces ONE CognitivePlan.
# ─────────────────────────────────────────────────────────────────────────────

def _executive_faculty(
    raw:          str,
    language:     dict,
    attention:    dict,
    capabilities: list[dict],
    system_det:   tuple | None,
) -> CognitivePlan:
    """
    The Executive is the only entity permitted to make decisions.
    All other faculties contribute information. Only Executive decides.
    """
    plan = CognitivePlan(
        raw=raw,
        meaning=language.get("meaning", raw),
        intent=language.get("intent", "conversation"),
        register=language.get("register", ""),
        social=language.get("social", ""),
        confidence=language.get("confidence", 0.7),
    )

    # ── Executive decision from existing executive.py ─────────────────────────
    # executive.decide() is the identity/personality layer — do not replace it.
    try:
        exec_out = attention.get("_exec_decision", {})
        plan.conversation_action = exec_out.get("action",        "celebrate")
        plan.cal_reason          = exec_out.get("cal_reason",    "")
        plan.tone                = exec_out.get("tone",          "DIRECT")
        plan.max_sentences       = exec_out.get("max_sentences", 3)
        plan.response_goal       = exec_out.get("response_goal", "answer")
        plan.valence             = exec_out.get("valence",       "neutral")
        plan.momentum            = exec_out.get("momentum",      "stable")
        plan.mode                = exec_out.get("mode",          "")
        # register from exec takes precedence if language didn't detect one
        if not plan.register:
            plan.register = exec_out.get("register", "")
    except Exception as e:
        _log.debug("executive_faculty/exec_out: %s", e)

    # ── System action decision ────────────────────────────────────────────────
    if system_det:
        action, arg = system_det
        plan.system_action = action
        plan.system_arg    = arg
        try:
            from runtime.router.execution_gate import gate
            g = gate(action, arg)
            plan.system_immediate = g["execute"]
            plan.system_pending   = not g["execute"]
            plan.system_desc      = g.get("confirmation", "")
        except Exception as e:
            _log.debug("executive_faculty/gate: %s", e)
            plan.system_immediate = True

    # ── Capability selection ──────────────────────────────────────────────────
    # Executive selects from candidates. Prefers high-score, available, no-confirm.
    if not plan.is_system_turn() and capabilities:
        for cap in capabilities:
            if cap.get("health") not in ("OFFLINE", "AUTH_REQUIRED", "DISABLED"):
                agent_name = cap["id"]
                plan.capabilities = [(agent_name, plan.meaning)]
                break  # one capability per turn (two for chains)

    # Chain: if intent_engine found a 2-agent chain, honour it
    chain = language.get("intent_chain", [])
    if len(chain) == 2 and not plan.is_system_turn():
        plan.capabilities = [(chain[0], plan.meaning), (chain[1], plan.meaning)]

    return plan


# ─────────────────────────────────────────────────────────────────────────────
# CONVERSATION FACULTY — direct response for social/system turns
# Only fires for turns where no LLM is needed.
# ─────────────────────────────────────────────────────────────────────────────

def _conversation_faculty(plan: CognitivePlan) -> CognitivePlan:
    """
    For pure social, greeting, and system-done turns: sets direct_response.
    For all other turns: leaves direct_response empty (LLM handles it).
    """
    reason = plan.cal_reason
    reg    = plan.register
    raw_lower = plan.raw.lower().strip().rstrip(".,!")

    try:
        import random
        import server as _srv

        # ── System immediate ─────────────────────────────────────────────────
        if plan.system_immediate and plan.system_action:
            if reg in ("PATOIS_MODE", "HYBRID_MODE"):
                plan.direct_response = random.choice(_srv._SYSTEM_DONE_POOL_PATOIS)
            elif reg == "SOUTH_LDN_MODE" or raw_lower in _srv._BARE_SLANG_GREETINGS:
                plan.direct_response = random.choice(_srv._SYSTEM_DONE_POOL_SOUTH_LDN)
            else:
                plan.direct_response = random.choice(_srv._SYSTEM_DONE_POOL)
            plan.direct_backend = "direct+system"
            return plan

        # ── System confirm ───────────────────────────────────────────────────
        if plan.system_pending:
            pool = (_srv._SYSTEM_CONFIRM_POOL_SOUTH_LDN
                    if reg in ("SOUTH_LDN_MODE", "PATOIS_MODE", "HYBRID_MODE")
                    else _srv._SYSTEM_CONFIRM_POOL)
            tmpl = random.choice(pool)
            plan.direct_response = tmpl.format(desc=plan.system_desc)
            plan.direct_backend  = "direct+system_gate"
            return plan

        # ── Rasta spiritual affirmations — "Jah!", "Rastafari!", "give thanks" etc.
        # Met with the same weight — mirrored back, not analysed.
        if raw_lower.rstrip("!. ") in _srv._RASTA_PHRASES or raw_lower in _srv._RASTA_PHRASES:
            key = raw_lower.rstrip("!. ")
            plan.direct_response = _srv._RASTA_RESPONSE_MAP.get(
                key, _srv._RASTA_RESPONSE_MAP.get(raw_lower, random.choice(_srv._RASTA_POOL))
            )
            plan.direct_backend = "direct"
            return plan

        # ── Farewell — "safe", "in a bit", "laters" etc. ────────────────────
        if raw_lower in _srv._BARE_FAREWELLS:
            plan.direct_response = random.choice(_srv._FAREWELL_POOL_SOUTH_LDN)
            plan.direct_backend  = "direct"
            return plan

        # ── Pure greeting ────────────────────────────────────────────────────
        if reason == "pure greeting":
            if raw_lower == "greetings":
                plan.direct_response = "Greetings."
            elif reg in ("PATOIS_MODE", "HYBRID_MODE"):
                plan.direct_response = random.choice(_srv._PURE_GREETING_POOL_PATOIS)
            elif reg == "SOUTH_LDN_MODE" or raw_lower in _srv._BARE_SLANG_GREETINGS:
                plan.direct_response = random.choice(_srv._PURE_GREETING_POOL_SOUTH_LDN)
            else:
                plan.direct_response = random.choice(_srv._PURE_GREETING_POOL)
            plan.direct_backend = "direct"
            return plan

        # ── How are you ──────────────────────────────────────────────────────
        if reason.startswith("how are you"):
            if reg in ("PATOIS_MODE", "HYBRID_MODE"):
                plan.direct_response = random.choice(_srv._HOW_ARE_YOU_POOL_PATOIS)
            elif reg == "SOUTH_LDN_MODE" or raw_lower in _srv._BARE_SLANG_GREETINGS:
                plan.direct_response = random.choice(_srv._HOW_ARE_YOU_POOL_SOUTH_LDN)
            else:
                plan.direct_response = random.choice(_srv._HOW_ARE_YOU_POOL)
            plan.direct_backend = "direct"
            return plan

        # ── Thank you ────────────────────────────────────────────────────────
        if raw_lower in _srv._THANK_YOU_TRIGGERS:
            if reg in ("PATOIS_MODE", "HYBRID_MODE"):
                plan.direct_response = random.choice(_srv._THANK_YOU_POOL_PATOIS)
            elif reg == "SOUTH_LDN_MODE" or raw_lower in _srv._BARE_SLANG_GREETINGS:
                plan.direct_response = random.choice(_srv._THANK_YOU_POOL_SOUTH_LDN)
            else:
                plan.direct_response = random.choice(_srv._THANK_YOU_POOL)
            plan.direct_backend = "direct"
            return plan

        # ── Identity ─────────────────────────────────────────────────────────
        if any(p in raw_lower for p in _srv._IDENTITY_TRIGGERS):
            plan.direct_response = random.choice(_srv._IDENTITY_POOL)
            plan.direct_backend  = "direct"
            return plan

        # ── Self-ref ─────────────────────────────────────────────────────────
        if any(p in raw_lower for p in _srv._SELF_REF_TRIGGERS):
            plan.direct_response = random.choice(_srv._SELF_REF_POOL)
            plan.direct_backend  = "direct"
            return plan

    except Exception as e:
        _log.debug("conversation_faculty: %s", e)

    return plan


# ─────────────────────────────────────────────────────────────────────────────
# SPINE — main entry point
# ─────────────────────────────────────────────────────────────────────────────

def run(
    raw:         str,
    state:       dict | None = None,
    memory_pack: dict | None = None,
    attention:   dict | None = None,
    pending_sit: dict | None = None,
) -> CognitivePlan:
    """
    The Cognitive Spine. One call. One plan.

    v1.8 aligned pipeline:
        [WO-052] CognitiveSnapshot (assembled first, pushed to Executive) →
        Language → Relationship → Capability → System →
        Executive → [COGNITIVE PLAN] →
        Executive Faculty (enrich: relationship + emotional vector) →
        Light Engine → [PRESENCE PLAN] →
        Conversation Faculty

    Args:
        raw         — unchanged user input
        state       — session state from memory
        memory_pack — pre-built memory context
        attention   — pre-computed attention model (from server.py)
        pending_sit — _PENDING_SIT dict from server.py (body schema)

    Returns: CognitivePlan — one plan, fully populated. All downstream reads from this.
    """
    if state is None:
        state = {}
    if attention is None:
        attention = {}

    # ── WO-CANON-XII: perceive() first — sensation caches → frozen PerceptionResult ─
    _perception = None
    try:
        from faculties.perception.perception_faculty import perceive_from_live_state as _perceive
        _perception = _perceive()
    except Exception as _perc_err:
        _log.debug("perceive_from_live_state: %s", _perc_err)

    # ── WO-CANON-XV: LiveWorldState — assembled FIRST, frozen, read by all faculties ─
    # Copies PerceptionResult fields into domain slices (Ch.3 §3.2 copy step).
    _world = None
    try:
        from world.live_world_state import assemble_world_state as _assemble_world
        _world = _assemble_world(turn_id=raw[:32] if raw else "", perception=_perception)
    except Exception as _world_err:
        _log.debug("assemble_world_state: %s", _world_err)

    # ── WO-CANON-VI: Working Memory + Attention — top-of-turn, before faculties ─
    # core/attention.py = candidate/signal supplier. WM competition = sole driver.
    _wm = None
    try:
        import time as _wm_time
        from runtime.working_memory import (
            seed_working_memory as _wm_seed,
            update_working_memory as _wm_update,
            run_attention_competition as _wm_attn,
            CognitiveFrame as _CogFrame,
            AttentionCandidate as _AttnCand,
            WorkingMemory as _WM,
            load_carry as _wm_load_carry,
        )
        _carry = _wm_load_carry()
        _wm = _wm_seed(
            current_task=_carry.get("current_task", ""),
            continuity_summary=_carry.get("rolling_summary", ""),
            open_threads=_carry.get("open_threads", []),
        )
        # Build candidates from core/attention supplier output
        _wm_candidates = []
        if raw:
            _wm_candidates.append(_AttnCand(item=raw[:80], novelty=0.5, importance=0.5, urgency=0.4))
        for _m in (attention or {}).get("high_priority_memory", [])[:4]:
            if _m:
                _wm_candidates.append(_AttnCand(item=str(_m)[:80], novelty=0.2, importance=0.7, urgency=0.2))
        _distress = (attention or {}).get("emotional_context", {}).get("inferred_state") == "distress"
        _attn_state = _wm_attn(_wm_candidates, budget=0.5, distress=_distress)
        # Append current frame then freeze with new attention state
        _frame = _CogFrame(
            frame_id=f"t{int(_wm_time.time() * 1000) % 1_000_000}",
            content=raw[:200] if raw else "",
            turn=0, significance=0.5,
        )
        _wm_updated = _wm_update(_wm, _frame)
        _wm = _WM(
            current_task=_wm_updated.current_task,
            active_goals=_wm_updated.active_goals,
            interruptions=_wm_updated.interruptions,
            open_threads=_wm_updated.open_threads,
            frames=_wm_updated.frames,
            pinned=_wm_updated.pinned,
            rolling_summary=_wm_updated.rolling_summary,
            attention=_attn_state,
            capacity=_wm_updated.capacity,
        )
    except Exception as _wm_err:
        _log.debug("working_memory: %s", _wm_err)

    # ── WO-052: CognitiveSnapshot — assembled BEFORE any faculty decides ──────
    _snapshot = None
    try:
        from runtime.cognitive_snapshot import build_snapshot as _build_snap
        _snapshot = _build_snap(attention=attention, pending_sit=pending_sit)
    except Exception as _snap_err:
        _log.debug("build_snapshot: %s", _snap_err)

    # ── v1.4 Language Faculty ─────────────────────────────────────────────────
    language = _language_faculty(raw)

    # ── v1.4 Relationship Faculty ─────────────────────────────────────────────
    relationship = None
    try:
        from runtime.spine.relationship_faculty import analyse as rel_analyse
        relationship = rel_analyse(raw, memory_pack)
    except Exception as e:
        _log.debug("relationship_faculty: %s", e)

    # ── Capability Faculty ────────────────────────────────────────────────────
    capabilities = _capability_faculty(language["meaning"], language["intent"])

    # ── System Faculty ────────────────────────────────────────────────────────
    system_det = _system_faculty(language["meaning"])

    # ── Executive Faculty — ONE DECISION ─────────────────────────────────────
    plan = _executive_faculty(raw, language, attention, capabilities, system_det)

    # ── WO-052: Store snapshot on plan (assembled before; now pinned to it) ───
    plan.snapshot = _snapshot
    # ── WO-CANON-XV/XII: Store frozen world + perception on plan ──────────────
    plan.world = _world
    # ── WO-CANON-VI: Store frozen WorkingMemory on plan ───────────────────────
    plan.working_memory = _wm

    # ── v1.5 Executive Faculty enrichment (relationship + emotional vector) ───
    try:
        from runtime.spine.executive_faculty import enrich
        plan = enrich(plan, relationship, attention)
    except Exception as e:
        _log.debug("executive_faculty/enrich: %s", e)

    # ── v1.8 Emotional Light Engine → Presence Plan ───────────────────────────
    try:
        from runtime.light_engine.light_engine import translate
        plan = translate(plan)
    except Exception as e:
        _log.debug("light_engine/translate: %s", e)

    # ── Presence Faculty — movement intent + triggers (after Light Engine) ───────
    try:
        from runtime.spine.presence_faculty import compute as _pf_compute
        _vision      = state.get("vision") if isinstance(state, dict) else None
        _session_min = 0   # conservative default (session_min used for 20-min calm gate only)
        plan = _pf_compute(plan, attention, vision=_vision, session_min=_session_min)
    except Exception as e:
        _log.debug("presence_faculty: %s", e)

    # ── S3: Assemble CognitiveState — after all plan mutations are complete ────
    try:
        lang_with_register = {**language, "register": plan.register}
        plan.cognitive_state = assemble_cognitive_state(
            lang_with_register, memory_pack, attention, capabilities, None, state,
            world_state=_world, working_memory=_wm,
        )
    except Exception as e:
        _log.debug("assemble_cognitive_state: %s", e)
        plan.cognitive_state = None

    # ── S6: Build EmbodimentState ─────────────────────────────────────────────
    try:
        plan.embodiment_state = build_embodiment_state(plan)
    except Exception as e:
        _log.debug("build_embodiment_state: %s", e)
        plan.embodiment_state = None

    # ── Conversation Faculty — direct response if applicable ──────────────────
    plan = _conversation_faculty(plan)

    return plan


def update_session(user_input: str, elo_response: str = "") -> None:
    """Call after each turn to keep conversational continuity."""
    try:
        from runtime.router.conversation_matrix import push
        push(user_input, elo_response)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# CONTRACT FACTORIES
# Assemble immutable runtime contracts from faculty outputs.
# ─────────────────────────────────────────────────────────────────────────────

_LED_FROM_EMOTIONAL_STATE = {
    "calm":      "teal",
    "neutral":   "teal",
    "curious":   "teal",
    "listening": "white",
    "focused":   "white",
    "thinking":  "amber",
    "alert":     "amber",
    "speaking":  "coral",
    "excited":   "coral",
    "joy":       "coral",
    "sad":       "violet",
    "distress":  "violet",
}


def assemble_cognitive_state(
    language:       dict,
    memory_result,
    attention:      dict,
    capabilities:   list,
    vault_result,
    prior_state,
    world_state=None,
    working_memory=None,
):
    """
    Assemble CognitiveState from all faculty outputs.
    Returns a frozen CognitiveState. Confidence degrades for missing faculties.
    """
    from runtime.contracts import CognitiveState

    conf = 1.0
    if not attention:
        conf -= 0.15
    if not capabilities:
        conf -= 0.05
    if memory_result is None:
        conf -= 0.05
    conf = max(0.0, min(1.0, conf))

    cap_candidates = tuple(
        (c.get("name") or c.get("id", "unknown"), c.get("available", True), c.get("latency_ms", 0))
        for c in (capabilities or [])
    )

    _attn_state = getattr(working_memory, "attention", None) if working_memory else None

    return CognitiveState(
        raw_input=language.get("original", ""),
        intent_signal=language.get("intent", "conversation"),
        register=language.get("register", ""),
        social_signal=language.get("social", ""),
        momentum=(attention or {}).get("momentum", "stable"),
        valence=(attention or {}).get("valence", "neutral"),
        assembly_confidence=conf,
        capability_candidates=cap_candidates,
        world_state=world_state,
        working_memory=working_memory,
        attention_state=_attn_state,
    )


def build_embodiment_state(plan, sequence_id: int = 0):
    """Build EmbodimentState from a completed CognitivePlan."""
    from runtime.contracts import EmbodimentState
    import datetime

    pp         = getattr(plan, "presence_plan", None) or {}
    es_name    = pp.get("emotional_state") or getattr(plan, "emotional_state", "calm") or "calm"
    led        = _LED_FROM_EMOTIONAL_STATE.get(es_name, "teal")
    resp       = getattr(plan, "direct_response", "") or ""
    ts         = datetime.datetime.utcnow().isoformat() + "Z"

    return EmbodimentState(
        response_text=resp,
        display_text=resp,
        tts_text=resp,
        emotional_state=es_name,
        motion_command=dict(pp),
        robot_led_state=led,
        sequence_id=sequence_id,
        published_at=ts,
    )


def build_execution_report(plan, **kwargs):
    """Build ExecutionReport from a completed CognitivePlan and execution results."""
    from runtime.contracts import ExecutionReport

    comp_state = kwargs.get("completion_state", "delivered")
    kwargs.setdefault("completed", comp_state in ("delivered", "partial"))
    kwargs.setdefault("planned_action", getattr(plan, "conversation_action", ""))
    return ExecutionReport(**kwargs)
