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
    # C2: word-boundary + content-word scoring. Stopwords stripped from multi-word verbs;
    # if no content words remain (e.g. "what is"), require near-exact phrase match.
    import re as _spine_re
    _CAP_STOPWORDS = frozenset({
        "what", "is", "are", "how", "do", "you", "it", "the", "a", "an",
        "in", "on", "at", "for", "to", "of", "and", "or", "my",
    })

    def _verb_score(verb: str, lower_input: str) -> int:
        v = verb.lower()
        words = v.split()
        content = [w for w in words if w not in _CAP_STOPWORDS]
        if not content:
            # all-stopword phrase (e.g. "what is") — near-exact match only
            clean = lower_input.strip().rstrip("?.!").strip()
            return 1 if clean == v else 0
        return sum(
            1 for w in content
            if _spine_re.search(r"\b" + _spine_re.escape(w) + r"\b", lower_input)
        )

    candidates = []
    try:
        from runtime.capabilities.registry import ALL_CAPABILITIES
        lower = meaning.lower()
        for cap in ALL_CAPABILITIES:
            if cap.future or not cap.enabled:
                continue
            score = sum(_verb_score(v, lower) for v in cap.verbs)
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
    # WO-106: assembled plan state — opens the seam so the Executive decides from
    # real world/working-memory/cognitive context, not just raw attention_model.
    world          = None,   # LiveWorldState from assemble_world_state()
    cognitive_state = None,  # CognitiveState from assemble_cognitive_state()
    working_memory  = None,  # WorkingMemory (competition result) from WM faculty
    affordances     = None,  # surface_affordances from CognitiveSnapshot
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

    # ── Ruling C (WO-CANON-VII): exec_decide called HERE, after assembly ────────
    # ── WO-106: open the seam — merge assembled plan state into attention_model ─
    # executive.py is FROZEN — we open the seam by enriching the dict it reads,
    # not by changing the function. When the freeze is lifted, exec_decide will
    # be able to use these fields directly.
    _attention_in = dict(attention) if attention else {}

    # Ruling B: working memory competition winner drives attention (not raw model)
    if working_memory is not None:
        _attn_state = getattr(working_memory, "attention", None)
        if _attn_state is not None:
            _attention_in["wm_winner"] = getattr(_attn_state, "winner", "")
            _attention_in["wm_mode"]   = getattr(_attn_state, "mode",   "reactive")
            _attention_in["wm_budget"] = getattr(_attn_state, "budget",  0.5)

    # World state — where eLo is, what the user is doing
    if world is not None:
        _desktop = getattr(world, "desktop", None)
        _route_hist = list(getattr(world, "route_history", ()) or ())
        _attention_in["world_state"] = {
            "surface":       getattr(_desktop, "surface",    "") if _desktop else "",
            "active_app":    getattr(_desktop, "active_app", "") if _desktop else "",
            "available":     getattr(_desktop, "available",   True) if _desktop else False,
            "degraded":      list(getattr(world, "degraded", [])),
            "route_history": _route_hist,   # WO-118 / Row 14 ROUTE
        }
    else:
        _log.warning("executive_faculty: plan.world absent — deciding without world context")

    # Focal thread from cognitive state
    if cognitive_state is not None:
        _attention_in["cognitive_state_focal"] = getattr(cognitive_state, "focal_thread", "")

    # Surface affordances — what actions are available in the current context
    if affordances:
        _attention_in["surface_affordances"] = (
            list(affordances) if not isinstance(affordances, list) else affordances
        )

    try:
        from runtime.executive import decide as _exec_decide_fn
        exec_out = _exec_decide_fn(_attention_in, loop_detected=False, user_input=raw)
        plan.conversation_action = exec_out.get("action",        "celebrate")
        plan.cal_reason          = exec_out.get("cal_reason",    "")
        plan.tone                = exec_out.get("tone",          "DIRECT")
        plan.max_sentences       = exec_out.get("max_sentences", 3)
        plan.response_goal       = exec_out.get("response_goal", "answer")
        plan.valence             = exec_out.get("valence",       "neutral")
        plan.momentum            = exec_out.get("momentum",      "stable")
        plan.mode                = exec_out.get("mode",          "")
        # WO-112: thread confidence from exec_out into plan (was lost, journalled as null)
        if "confidence" in exec_out:
            plan.confidence = float(exec_out["confidence"])
        if not plan.register:
            plan.register = exec_out.get("register", "")
    except Exception as e:
        _log.warning("executive_faculty/exec_decide FAILED: %s", e)

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
            _log.warning("executive_faculty/gate FAILED: %s", e)
            plan.system_immediate = True

    # ── Capability selection ──────────────────────────────────────────────────
    # Executive selects from candidates. Prefers high-score, available, no-confirm.
    if not plan.is_system_turn() and capabilities:
        for cap in capabilities:
            # A1: fail-closed on UNKNOWN — health_state has no producer; UNKNOWN must not pass
            if cap.get("health") in ("ONLINE", "OK", "HEALTHY", "AVAILABLE"):
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
            plan.direct_response = _srv._identity_response()
            plan.direct_backend  = "direct"
            return plan

        # ── CT4V-07: Structural claim-type gate — tiers only fall, never rise ──
        # Checks memory / capability / history sources before the LLM is called.
        # UNKNOWN tier → direct response returned, LLM not consulted. Rule 1 alarm logged.
        try:
            from runtime.claim_gate import classify_and_gate as _ct4v_gate
            _ct4v_type, _ct4v_resp = _ct4v_gate(raw)
            if _ct4v_resp is not None:
                plan.direct_response = _ct4v_resp
                plan.direct_backend  = "claim_gate"
                return plan
        except Exception as _ct4v_err:
            _log.warning("CT4V-07 gate error: %s", _ct4v_err)

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
        _log.warning("perceive_from_live_state FAILED: %s", _perc_err)

    # ── WO-CANON-XV: LiveWorldState — assembled FIRST, frozen, read by all faculties ─
    # Copies PerceptionResult fields into domain slices (Ch.3 §3.2 copy step).
    _world = None
    try:
        from world.live_world_state import assemble_world_state as _assemble_world
        _world = _assemble_world(turn_id=raw[:32] if raw else "", perception=_perception)
    except Exception as _world_err:
        _log.warning("assemble_world_state FAILED: %s", _world_err)

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
        _log.warning("working_memory FAILED: %s", _wm_err)

    # ── WO-052: CognitiveSnapshot — assembled BEFORE any faculty decides ──────
    _snapshot = None
    try:
        from runtime.cognitive_snapshot import build_snapshot as _build_snap
        _snapshot = _build_snap(attention=attention, pending_sit=pending_sit)
    except Exception as _snap_err:
        _log.warning("build_snapshot FAILED: %s", _snap_err)

    # ── v1.4 Language Faculty ─────────────────────────────────────────────────
    language = _language_faculty(raw)

    # ── v1.4 Relationship Faculty ─────────────────────────────────────────────
    relationship = None
    try:
        from runtime.spine.relationship_faculty import analyse as rel_analyse
        relationship = rel_analyse(raw, memory_pack)
    except Exception as e:
        _log.warning("relationship_faculty FAILED: %s", e)

    # ── Capability Faculty ────────────────────────────────────────────────────
    capabilities = _capability_faculty(language["meaning"], language["intent"])

    # ── System Faculty ────────────────────────────────────────────────────────
    system_det = _system_faculty(language["meaning"])

    # ── WO-CANON-XVI / ADR-Exec-006: Assemble unified cognitive state BEFORE Executive ──
    _cognitive_state = None
    try:
        _cognitive_state = assemble_cognitive_state(
            language, memory_pack, attention, capabilities, None, state,
            world_state=_world, working_memory=_wm,
        )
    except Exception as _cs_err:
        _log.warning("assemble_cognitive_state FAILED: %s", _cs_err)

    # ── Executive Faculty — ONE DECISION ─────────────────────────────────────
    # WO-106: pass assembled state so the Executive decides from real context
    plan = _executive_faculty(
        raw, language, attention, capabilities, system_det,
        world=_world,
        cognitive_state=_cognitive_state,
        working_memory=_wm,
        affordances=getattr(_snapshot, "surface_affordances", None) if _snapshot else None,
    )

    # ── WO-052: Store snapshot on plan (assembled before; now pinned to it) ───
    plan.snapshot = _snapshot
    # ── WO-CANON-XVI: Pin pre-assembled cognitive state to plan ──────────────
    plan.cognitive_state = _cognitive_state
    # ── WO-CANON-XV/XII: Store frozen world + perception on plan ──────────────
    plan.world = _world
    # ── WO-CANON-VI: Store frozen WorkingMemory on plan ───────────────────────
    plan.working_memory = _wm

    # ── v1.5 Executive Faculty enrichment (relationship + emotional vector) ───
    try:
        from runtime.spine.executive_faculty import enrich
        plan = enrich(plan, relationship, attention)
    except Exception as e:
        _log.warning("executive_faculty/enrich FAILED: %s", e)

    # AC-5: sync register into CognitiveState after enrich may have supplemented it.
    # Language faculty runs before exec, so cognitive_state is assembled with whatever
    # language detected; enrich (relationship) may later set plan.register to something
    # richer. Keep them consistent via dataclasses.replace on the frozen snapshot.
    if plan.cognitive_state is not None and plan.register and not plan.cognitive_state.register:
        try:
            from dataclasses import replace as _dc_replace
            plan.cognitive_state = _dc_replace(plan.cognitive_state, register=plan.register)
        except Exception as _e:
            _log.warning("cognitive_state register sync FAILED: %s", _e)

    # ── v1.8 Emotional Light Engine → Presence Plan ───────────────────────────
    try:
        from runtime.light_engine.light_engine import translate
        plan = translate(plan)
    except Exception as e:
        _log.warning("light_engine/translate FAILED: %s", e)

    # ── Presence Faculty — movement intent + triggers (after Light Engine) ───────
    try:
        from runtime.spine.presence_faculty import compute as _pf_compute
        _vision      = state.get("vision") if isinstance(state, dict) else None
        _session_min = 0   # conservative default (session_min used for 20-min calm gate only)
        plan = _pf_compute(plan, attention, vision=_vision, session_min=_session_min)
    except Exception as e:
        _log.warning("presence_faculty FAILED: %s", e)

    # ── Conversation Faculty — direct response if applicable ──────────────────
    # WO-097: conversation runs FIRST so direct_response is set before embodiment.
    # build_embodiment_state previously ran before _conversation_faculty, publishing
    # empty response_text / display_text / tts_text on every direct-response turn.
    plan = _conversation_faculty(plan)

    # ── S6: Build EmbodimentState ─────────────────────────────────────────────
    # WO-097: runs AFTER conversation so response_text / display_text / tts_text
    # are populated when the body reads them.
    try:
        plan.embodiment_state = build_embodiment_state(plan)
        if getattr(plan, "direct_response", None) and not getattr(
            plan.embodiment_state, "response_text", None
        ):
            _log.warning(
                "build_embodiment_state: response_text empty on direct-response turn"
            )
    except Exception as e:
        _log.warning("build_embodiment_state FAILED: %s", e)
        plan.embodiment_state = None

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
