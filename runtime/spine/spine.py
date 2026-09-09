"""
runtime/spine/spine.py — The Cognitive Spine

One brain. One decision per turn.

The Spine orchestrates all faculties in sequence.
No faculty decides independently. All feed the Executive.
The Executive produces ONE CognitivePlan.
That plan drives conversation, avatar, desktop, and future embodiments.

Faculty order (spine-internal):
    Language → Relationship → Desktop → Capability → Executive → Gate
Note: Memory (memory_pack_builder) and Attention (memory_relevance_filter) are
pre-computed in server.py before spine.run() is called and passed in as arguments.
"""
from __future__ import annotations
import logging

from runtime.spine.plan import CognitivePlan

_log = logging.getLogger(__name__)

# WO-CANON-III: session-level sequence counter for EmbodimentState staleness detection.
# Monotonically increasing per session (never resets within one server.py lifetime).
# Vol III §1.4 / ST-III-1g: subscribers use published_at + sequence_id to detect staleness.
_EMBODIMENT_SEQUENCE = 0

# WO-SPINE-002: prior-turn state carriers — updated after each turn completes.
_prev_embodiment_state = None   # EmbodimentState from the prior turn
_prev_execution_report = None   # ExecutionReport from the prior turn

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
        # D1 ruling (Card 0035): intent_engine outputs a CAPABILITY-ROUTER hint
        # (file_ops|memory|system|utility_*|…), NOT the cognitive intent.
        # Store it as `capability_hint`, not `intent`. `plan.intent` is filled
        # from the cognitive classifier (core/attention._classify_intent) in run().
        result["capability_hint"] = intent_result["intent"]
        result["intent_chain"]    = intent_result.get("chain", [])
        result["confidence"]      = min(result["confidence"],
                                        intent_result.get("confidence", 0.8))
    except Exception as e:
        _log.debug("language_faculty/intent: %s", e)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# CAPABILITY FACULTY — advertise what's possible
# Never chooses which capability to use. Lists candidates.
# ─────────────────────────────────────────────────────────────────────────────

def _capability_faculty(meaning: str, intent: str, current_embodiment: str = "desktop") -> list[dict]:
    """
    Returns candidate capabilities that could handle this input, filtered to the current embodiment.
    The Executive decides which (if any) to invoke.
    SP-36 (WO-NAV-005): capabilities whose embodiment_scope does not include current_embodiment
    or 'any' are silently excluded before reaching the Executive.
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
            # SP-36 (WO-NAV-005): embodiment scope filter — applied before Executive sees list
            _scope = getattr(cap, "embodiment_scope", frozenset({"desktop"}))
            if "any" not in _scope and current_embodiment not in _scope:
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

    # WO-055: penalise capabilities that have failed repeatedly this session.
    # A cap with an active failure streak should sink in the ranking so the
    # Executive stops choosing it while it's still broken.
    try:
        from runtime.capability_learning import failure_streak as _fail_streak
        for cap in candidates:
            _streak = _fail_streak(cap["id"])
            if _streak >= 2:
                cap["score"] -= _streak * 2
                cap["failure_streak"] = _streak
        candidates.sort(key=lambda x: x["score"], reverse=True)
    except Exception as e:
        _log.debug("capability_faculty/failure_streak: %s", e)

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
    embodiment_state = None, # WO-SPINE-002: prior-turn EmbodimentState | None
    execution_report = None, # WO-SPINE-002: prior-turn ExecutionReport | None
    identity         = None, # WO-SOURCE-001: IdentityKernel | None — advisory context
) -> CognitivePlan:
    """
    The Executive is the only entity permitted to make decisions.
    All other faculties contribute information. Only Executive decides.
    """
    # D1 ruling (Card 0035): plan.intent = COGNITIVE intent (from core/memory_relevance_filter),
    # plan.capability_hint = router hint (from intent_engine). Two questions, two
    # answers, two names. The journal records the cognitive intent — the one the
    # Executive actually decides on.
    _cognitive_intent = (attention or {}).get("intent") or "conversation"
    plan = CognitivePlan(
        raw=raw,
        meaning=language.get("meaning", raw),
        intent=_cognitive_intent,
        capability_hint=language.get("capability_hint", ""),
        register=language.get("register", ""),
        social=language.get("social", ""),
        confidence=language.get("confidence", 0.7),
    )

    # ── Ruling C (WO-CANON-VII): exec_decide called HERE, after assembly ────────
    # ── WO-ONEBRAIN-012 (W5): ExecutiveContext — canonical schema, derived from ─
    # existing canon. executive.py is FROZEN — ExecutiveContext.as_dict() produces
    # the flat dict exec_decide() reads. When executive.py unfreezes, it will
    # receive ExecutiveContext directly. New fields (ec_*) are available then.
    # NEW ASSUMPTIONS (flagged to CA): agency · epistemic_state · significance.
    _attention_in = dict(attention) if attention else {}
    # SP-30 (WO-NAV-006): trigger_source annotation — default "user_message" for all turns
    _attention_in.setdefault("trigger_source", "user_message")

    # ── W6/Card 0075: lesson recall BEFORE ExecutiveContext assembly ─────────
    # Card 0075 D3 · Option A · David L3 2026-08-21: lessons must reach
    # ExecutiveContext (frozen executive.decide reads a flat dict, so the key
    # is available). The D1 verified-evidence filter is applied inside
    # build_executive_context — the raw recall() output is passed through.
    # No cal_reason amendment or lesson_id assignment happens here: those
    # are gated on the counterfactual proof below (identical input, different
    # action WITH vs WITHOUT lessons). Until that holds, lesson_id stays "".
    _recalled_lessons: list = []
    try:
        from self.lesson_store import recall as _ls_recall
        _recalled_lessons = _ls_recall(
            context={
                "focal_thread": getattr(cognitive_state, "focal_thread", "") if cognitive_state else "",
                "topic":        _attention_in.get("intent", ""),
            },
            k=3,
        ) or []
    except Exception as _lr_err:
        _log.debug("lesson recall failed (non-critical): %s", _lr_err)

    # ── LOOP-7 / ADR-Exec-005 D6: the Executive ASKS the Learning Faculty ──────
    # David 2026-08-21: "why is this still there?" — because nobody had built it.
    # D6 (ratified David L3 2026-08-06): "a Learning Faculty — a faculty the Executive
    # ASKS, like any other ... never inside the Executive."
    # It ADVISES on action preference only (D4). It never returns truth, never returns
    # speech permission, never decides. executive.py stays FROZEN and untouched.
    _learning_advice = None
    try:
        from faculties.learning import consult as _learn_consult
        _learning_advice = _learn_consult(
            lessons=_recalled_lessons,
            candidate_action="",          # asked before the action is chosen — advice, not override
            context={"intent": _attention_in.get("intent", ""),
                     "focal_thread": getattr(cognitive_state, "focal_thread", "") if cognitive_state else ""},
        )
        if _learning_advice and _learning_advice.preferences:
            _log.info("LOOP-7 learning advice: %s", _learning_advice.rationale)
    except Exception as _lf_err:
        _log.debug("learning faculty consult failed (non-critical): %s", _lf_err)

    # LOOP-7: hand the advice to the Executive on the channel it already reads.
    # It ASKS — this is the answer waiting for it. ADR-Exec-005 D6.
    if _learning_advice is not None:
        _attention_in["learning_advice"] = _learning_advice.as_dict()

    # ── LOOP-8 / WO-CREATIVE-001: Creative Imagination consultation ─────────────
    # Vol XXVI Ch.1+Ch.3: diverge generates candidates; evaluate scores them.
    # Proposes and scores only — Executive selects. Never calls executive_select().
    _creative_candidates: list = []
    try:
        from faculties.creative.creative_imagination import (
            diverge as _ci_diverge,
            evaluate as _ci_evaluate,
        )
        _ci_intent = _attention_in.get("intent", "")
        _ci_focal = getattr(cognitive_state, "focal_thread", "") if cognitive_state else ""
        if _ci_intent:
            _ci_seeds = [_ci_intent, _ci_focal] if _ci_focal else [_ci_intent]
            _ci_raw = _ci_diverge(goal=_ci_intent, seeds=_ci_seeds, breadth_budget=3)
            _creative_candidates = [
                {"candidate": c.to_dict(), "score": _ci_evaluate(c, goal=_ci_intent).to_dict()}
                for c in _ci_raw
            ] if _ci_raw else []
    except Exception as _ci_err:
        _log.debug("creative_imagination failed (non-critical): %s", _ci_err)

    if _creative_candidates:
        _attention_in["creative_candidates"] = _creative_candidates
        # WO-INNER-001 D-2: propagate to plan so server.py can inject [CREATIVE SEED]
        plan.creative_candidates = tuple(_creative_candidates)

    # WO-117 SELF-INTERPRET (card 0083): eLo reads his own record and says something
    # true about himself — assembly, not invention. ADR-Exec-005 D1: every claim
    # carries the count it came from. CT4V-03: reads only, never writes EloSelfState.
    _self_interpretation = None
    try:
        from self.elo_self_model import load as _load_self_state
        from runtime.self_interpret import interpret as _self_interpret
        _elo_self_state = _load_self_state()
        _self_interpretation = _self_interpret(_elo_self_state)
        if _self_interpretation and not _self_interpretation.is_empty():
            _log.info("WO-117 self-interpret: %s", _self_interpretation.text[:120])
    except Exception as _si_err:
        _log.debug("self_interpret failed (non-critical): %s", _si_err)

    if world is None:
        _log.warning("executive_faculty: plan.world absent — deciding without world context")

    try:
        from runtime.executive_context import build_executive_context as _build_ec
        _ec = _build_ec(
            intent=_attention_in.get("intent", "conversation"),
            emotional_context=_attention_in.get("emotional_context", {}),
            world=world,
            working_memory=working_memory,
            capabilities=capabilities,
            cognitive_state=cognitive_state,
            affordances=affordances,
            attention=_attention_in,
            lessons=_recalled_lessons,
        )
        _attention_in = _ec.as_dict()
    except Exception as _ec_err:
        # Degrade gracefully: fall back to the manual enrichment below
        _log.warning("build_executive_context FAILED: %s — using manual fallback", _ec_err)
        # Ruling B: working memory competition winner drives attention (not raw model)
        if working_memory is not None:
            _attn_state = getattr(working_memory, "attention", None)
            if _attn_state is not None:
                _attention_in["wm_winner"] = getattr(_attn_state, "winner", "")
                _attention_in["wm_mode"]   = getattr(_attn_state, "mode",   "reactive")
                _attention_in["wm_budget"] = getattr(_attn_state, "budget",  0.5)
        # World state — D2 ruling (Card 0035): DesktopState.surface → platform.
        if world is not None:
            _desktop = getattr(world, "desktop", None)
            _route_hist = list(getattr(world, "route_history", ()) or ())
            _cap_results = list(getattr(world, "capability_results", ()) or ())
            _attention_in["world_state"] = {
                "platform":           getattr(_desktop, "platform",   "") if _desktop else "",
                "active_app":         getattr(_desktop, "active_app", "") if _desktop else "",
                "available":          getattr(_desktop, "available",   True) if _desktop else False,
                "degraded":           list(getattr(world, "degraded", [])),
                "route_history":      _route_hist,
                "capability_results": _cap_results,  # WO-CAP-001
                "company_state":      dict(getattr(world, "company_state", {})),  # WO-EA2-NEW-A D-3
            }
        else:
            _log.warning("executive_faculty: plan.world absent — deciding without world context")
        if cognitive_state is not None:
            _attention_in["cognitive_state_focal"] = getattr(cognitive_state, "focal_thread", "")
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

        # ── WO-STABILITY-LAW-001: complexity scoring + P8/P9 gates ──────────
        # Complexity = count of active capabilities + significant contexts.
        _cap_count  = len(plan.capabilities)
        _ctx_weight = 1 if (cognitive_state and getattr(cognitive_state, "wkg_context", "")) else 0
        _score = float(_cap_count + _ctx_weight)
        plan.plan_complexity_score = _score
        if _score >= 6:
            plan.stability_law_active = True
            plan.leaf_on_water_active = False
            _log.debug("stability_law: triggered — stability_law_triggered=True score=%.1f", _score)
        elif 3 <= _score < 6:
            plan.leaf_on_water_active = True
            plan.stability_law_active = False
        else:
            plan.stability_law_active = False
            plan.leaf_on_water_active = False

        # ── WO-SOURCE-002: cognitive principles check (advisory, never blocks) ─
        try:
            from runtime.cognitive_principles import PRINCIPLES as _CP
            plan.principle_violations = _CP.check(plan)
            if plan.principle_violations:
                _log.debug("principle_violations: %s", plan.principle_violations)
        except Exception as _cp_err:
            _log.debug("cognitive_principles check failed (non-fatal): %s", _cp_err)

        # ── WO-INNER-CHILD-001: inner child mode (curiosity threshold) ────────
        # WO-AFFECTIVE-STATE-001: prefer AffectiveState.curiosity over SP-29 proxy
        _aff = getattr(cognitive_state, "affective_state", None) if cognitive_state else None
        _curiosity = getattr(_aff, "curiosity", None)
        if _curiosity is None:
            _curiosity = getattr(cognitive_state, "curiosity_score", 0.0) if cognitive_state else 0.0
        _is_play   = (plan.mode or "").upper() in ("PLAY", "EXPLORE")
        _is_dream  = plan.conversation_action in ("explore",)
        plan.cognitive_mode_inner_child = bool(_curiosity > 0.7 or (_is_play and _is_dream))

        # ── WO-OVERLOAD-PROTOCOL-001: detect overload → REDUCE TO ONE LINE ─────
        try:
            _ovl_aff = getattr(cognitive_state, "affective_state", None) if cognitive_state else None
            _ovl_sig = getattr(cognitive_state, "significance_score", 0.0) if cognitive_state else 0.0
            _ovl_tension = getattr(_ovl_aff, "tension", 0.0) if _ovl_aff else 0.0
            _ovl_agency = getattr(_ovl_aff, "agency", 1.0) if _ovl_aff else 1.0
            _ovl_threads = len(getattr(cognitive_state, "open_threads", ())) if cognitive_state else 0
            _ovl_topics = getattr(cognitive_state, "active_topic_depth", 0) if cognitive_state else 0

            _overload = (
                (_ovl_sig >= 0.90)
                or (_ovl_tension > 0.80 and _ovl_agency < 0.30)
                or (_ovl_threads >= 3)
            )
            plan.overload_protocol = _overload
            plan.inner_child_mode_active = False

            if _overload:
                plan.vessel_phase = "STABILISE"
                plan.stability_law_active = True
                _log.info("[OVERLOAD-PROTOCOL] triggered — sig=%.2f tension=%.2f agency=%.2f threads=%d",
                          _ovl_sig, _ovl_tension, _ovl_agency, _ovl_threads)
            elif plan.vessel_phase == "FEEL":
                # Inner child runtime: when uncertain and vessel=FEEL, fire inner child mode
                plan.inner_child_mode_active = True
        except Exception as _ovl_err:
            _log.warning("overload protocol check failed (non-fatal): %s", _ovl_err)

        # ── WO-VESSEL-LOOP-001 / WO-VESSEL-PHASE-001: vessel phase ───────────
        if not plan.vessel_phase or plan.vessel_phase == "FEEL":
            if plan.stability_law_active:
                plan.vessel_phase = "STABILISE"
            elif plan.conversation_action in ("build", "connect"):
                plan.vessel_phase = "TRANSFORM"
            elif plan.conversation_action in ("reflect", "witness", "answer", "greet"):
                plan.vessel_phase = "EXPRESS"
            elif plan.conversation_action == "ground":
                plan.vessel_phase = "STABILISE"
            elif plan.conversation_action == "rest":
                plan.vessel_phase = "REST"
            else:
                plan.vessel_phase = "EXPRESS"

    except Exception as e:
        _log.warning("executive_faculty/exec_decide FAILED: %s", e)

    # ── W6/Card 0075: lesson_id attribution gate ────────────────────────────
    # Card 0075 D3 · Option A: ExecutiveContext.lessons is now populated
    # BEFORE the exec_decide call above. The counterfactual proof required
    # to promote lesson_id off "" is: identical input, action WITH lesson
    # present differs from action WITHOUT. Because runtime/executive.py has
    # zero references to "lesson" (grep -c lesson runtime/executive.py = 0),
    # the counterfactual is FALSE by construction: the frozen logic does not
    # consult the key. Therefore lesson_id stays "" — LOOP-7 remains UNKNOWN.
    # This is the honest, useful result the card asked for.
    plan.lesson_id = ""

    # W6: lesson attribution — closes LOOP-7.
    # lesson_id is always set to the top recalled lesson's key when any lesson
    # was recalled this turn. cal_reason is only amended when the Executive
    # returned the default branch ("default — no stronger signal") — in that
    # case the lesson is the authoritative reason for the outcome.
    # ADR-Exec-005 D6: Executive ASKS — spine acts on what it asked for.
    if _recalled_lessons:
        _top = _recalled_lessons[0]
        plan.lesson_id = _top.get("lesson_key", "")
        if plan.cal_reason == "default — no stronger signal":
            plan.cal_reason = f"lesson: {_top.get('statement', '')}"

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

    # ── WO-TIER-FACULTY-001 D-2 + D-3: tier-ordered faculty read + speech gate ─
    try:
        from runtime.tiered_faculty_reader import TieredFacultyReader as _TFR
        _world_dict = {}
        if world is not None:
            _desktop = getattr(world, "desktop", None)
            _world_dict["active_window"] = getattr(_desktop, "active_app", "") if _desktop else ""
        if cognitive_state is not None:
            _world_dict["wkg_context"] = getattr(cognitive_state, "wkg_context", "")
            _et = getattr(cognitive_state, "emotional_tag", None)
            _world_dict["mood"] = getattr(_et, "dominant_emotion", "neutral") if _et else "neutral"
            # WO-TIER-POPULATION-001: populate missing tier fields so never_pretend_certainty
            # does not fire on every turn due to absent/unknown tiers
            _world_dict["vault_context"] = getattr(cognitive_state, "vault_context", "")
            _world_dict["capabilities"] = list(getattr(cognitive_state, "capability_candidates", ()) or ())
            _hp = list(getattr(cognitive_state, "high_priority_memories", ()) or ())
            _mp = list(getattr(cognitive_state, "medium_priority_memories", ()) or ())
            if _hp or _mp:
                _world_dict["lessons"] = _hp + _mp
            _world_dict["pose"] = (
                getattr(cognitive_state, "active_app", "") or
                getattr(cognitive_state, "desktop_activity", "")
            )
            _world_dict["nearby"] = getattr(cognitive_state, "nearby_entities", "") or ""
        # WO-TIER-POPULATION-001 root fix: active_window and nearby default to non-empty
        # values when no DesktopBuddy perch data is available.
        # Empty string → tier_fact("") → "unknown" tier → in violations → hedge fires on
        # every "answer" turn. Non-empty defaults → "observed"/"inferred" tier → removed from
        # violations → hedge reserved for genuinely uncertain external-sensor assertions only.
        if not _world_dict.get("active_window"):
            _world_dict["active_window"] = "desktop"   # eLo is on the desktop; no specific app tracked
        if not _world_dict.get("nearby"):
            _world_dict["nearby"] = "none_detected"    # no nearby entities visible without perch data
        _tfr_results, _speech_licence = _TFR().evaluate(_world_dict, cognitive_state)
        plan.speech_licence = _speech_licence
        if _speech_licence.violations:
            _log.debug("tier-gate violations: %s", _speech_licence.violations)
    except Exception as _tfr_err:
        _log.debug("tiered_faculty_reader failed (non-critical): %s", _tfr_err)

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

    # ── WO-RTR-020: infer expression_mode from intent/context signals ────────
    _mode_lower = (plan.mode or "").lower()
    _intent_lower = (plan.intent or "").lower()
    _action_lower = (plan.conversation_action or "").lower()
    _BUILDER_INTENTS = {"code", "debug", "draft", "creation", "vault_write", "planning", "build"}
    _BUILDER_MODE_KEYS = ("studio", "builder", "creat", "code", "debug")
    if (
        _intent_lower in _BUILDER_INTENTS or
        any(k in _mode_lower for k in _BUILDER_MODE_KEYS) or
        _action_lower == "build"
    ):
        plan.expression_mode = "builder"
    else:
        plan.expression_mode = "default"

    # ── WO-SC-NEW-001 D-2: infer storytelling_style from voice/mode context ──
    # Set unconditionally so every downstream path (direct or LLM) carries it.
    if any(k in _mode_lower for k in ("studio", "builder", "creat")):
        plan.storytelling_style = "collaborative"
    elif "imaginat" in _mode_lower or _intent_lower == "creation":
        plan.storytelling_style = "imaginative"
    elif any(k in _mode_lower for k in ("reflect", "review")):
        plan.storytelling_style = "reflective"
    elif "play" in _mode_lower:
        plan.storytelling_style = "playful"
    elif "learn" in _mode_lower or _intent_lower == "inquiry":
        plan.storytelling_style = "exploratory"
    elif _mode_lower:
        plan.storytelling_style = "direct"
    # else: no mode signal → stays None

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

        # ── Board directive 2026-08-24: other-AI identity hold ──────────────────
        # eLo is not another AI and cannot pretend to be one.
        # Check before LLM so the model never even attempts the roleplay.
        try:
            from runtime.identity_guard import is_other_ai_request as _ig_check
            from runtime.identity_guard import identity_hold_response as _ig_resp
            if _ig_check(plan.raw):
                plan.direct_response = _ig_resp()
                plan.direct_backend  = "direct+identity_hold"
                return plan
        except Exception as _ig_err:
            _log.debug("identity_guard check: %s", _ig_err)

        # ── 0021 P0-X: David's name resolves from who_i_am_with, not from an LLM guess
        if any(p in raw_lower for p in _srv._DAVID_NAME_TRIGGERS):
            plan.direct_response = _srv._david_name_response()
            plan.direct_backend  = "direct"
            return plan

        # ── CT4V-07: Structural claim-type gate — tiers only fall, never rise ──
        # Checks memory / capability / history sources before the LLM is called.
        # UNKNOWN tier → direct response returned, LLM not consulted. Rule 1 alarm logged.
        try:
            from runtime.claim_gate import classify_and_gate as _ct4v_gate
            # Vol XII Ch.3 §3.4: read capability state from the carrier, not the raw sensor.
            _ct4v_type, _ct4v_resp = _ct4v_gate(raw, world=getattr(plan, "world", None))
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
# WO-SELF-MODEL-001: _self_model_faculty
# Assembles SelfModel from existing faculty outputs. Observes; does not decide.
# ─────────────────────────────────────────────────────────────────────────────

def _self_model_faculty(
    wkg_context: str = "",
    affective_state=None,
    lessons=None,
):
    """
    Assemble lean SelfModel (v1) from existing data.
    Does not call any external service or make any decision.
    """
    from runtime.contracts import SelfModel
    try:
        # identity: pull WKG foundational claims as key-value summary
        _identity: dict = {}
        try:
            from runtime.wkg.wkg_faculty import WKGFaculty as _WKG
            _wkg = _WKG()
            _elo_ents = _wkg.search_entities("eLo")
            if _elo_ents:
                _eid = _elo_ents[0].get("entity_id", "")
                _claims = [c for c in _wkg.get_claims_about(_eid) if c.get("memory_type") == "foundational"][:5]
                _identity = {c.get("relationship_type", "property"): c.get("object", "") for c in _claims}
        except Exception:
            pass

        # current_state: AffectiveState dict + label
        _current_state: dict = {}
        if affective_state is not None:
            try:
                _current_state = affective_state.to_dict()
                _current_state["label"] = affective_state.label()
            except Exception:
                pass

        # autobiographical_summary: from wkg_context (pre-assembled earlier in pipeline)
        _auto_summary = wkg_context[:240] if wkg_context else ""

        # limitations: capability gaps from registry
        _limitations: list = []
        try:
            from runtime.capability_registry import CapabilityRegistry as _CR
            _reg = _CR()
            _all_caps = list(getattr(_reg, "_registry", {}).keys())
            _expected = {"WORLD_VOICE_OUTPUT", "WORLD_VOICE_INPUT", "WORLD_CREATE", "WORLD_SEARCH"}
            _missing = [c for c in _expected if c not in _all_caps]
            _limitations = _missing
        except Exception:
            pass

        # internal_preferences: top 3 lessons as preference summary
        _prefs: dict = {}
        try:
            from self.lesson_store import LessonStore as _LS
            _ls = _LS()
            _top = _ls.recall(limit=3)
            _prefs = {f"lesson_{i}": l.get("lesson", "") for i, l in enumerate(_top)}
        except Exception:
            pass

        # prediction_confidence: inverse of uncertainty from affective state
        _pred_conf = 0.5
        if affective_state is not None:
            try:
                _pred_conf = round(1.0 - getattr(affective_state, "uncertainty", 0.5), 2)
            except Exception:
                pass

        return SelfModel(
            identity=_identity,
            current_state=_current_state,
            autobiographical_summary=_auto_summary,
            limitations=_limitations,
            current_goal="",  # filled by Executive; unknown here
            prediction_confidence=_pred_conf,
            internal_preferences=_prefs,
        )
    except Exception:
        from runtime.contracts import SelfModel
        return SelfModel()


# ─────────────────────────────────────────────────────────────────────────────
# SPINE — main entry point
# ─────────────────────────────────────────────────────────────────────────────

def run(
    raw:             str,
    state:           dict | None = None,
    memory_pack:     dict | None = None,
    attention:       dict | None = None,
    pending_sit:     dict | None = None,
    intent_source:   str         = "david",   # WO-INGRESS-32: "david"|"self"|"reflex"
    internal_intent: dict | None = None,       # WO-INGRESS-32: cognitive proposal from internal_intents()
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

    # ── WO-DREAM-STATE: asleep check — before any faculty processing ─────────
    # When eLo is in dream/sleep state, dispatch to the executive dream window.
    # Output is NEVER surfaced to David — this is internal memory consolidation only.
    try:
        from runtime.executive import run_dream_window as _run_dream_window, _read_asleep as _is_asleep
        if _is_asleep():
            _dream_result = _run_dream_window(recent_topics=state.get("recent_topics"))
            _dream_plan = CognitivePlan()
            _dream_plan.action         = "dream"
            _dream_plan.direct_response = ""     # NEVER surfaced to David
            _dream_plan.direct_backend  = "dream"
            _dream_plan.response_goal   = "stabilise"
            _dream_plan.tone            = "silence_aware"
            _dream_plan.dream_window    = _dream_result
            return _dream_plan
    except Exception as _dream_gate_err:
        _log.warning("WO-DREAM-STATE gate FAILED (non-critical — continuing normal turn): %s", _dream_gate_err)

    # WO-XDNA-001: mint Experience DNA at turn start — before any faculty processing.
    try:
        from runtime.experience_id import mint as _mint_xid
        _turn_xid = _mint_xid()
    except Exception as _xid_err:
        _turn_xid = ""
        import logging as _logging
        _logging.getLogger(__name__).debug("experience_id.mint FAILED (non-critical): %s", _xid_err)

    # ── WO-CANON-XII: perceive() first — sensation caches → frozen PerceptionResult ─
    _perception = None
    try:
        from faculties.perception.perception_faculty import perceive_from_live_state as _perceive
        _perception = _perceive()
        # WO-CANON-XXII: faculty succeeded — mark its genome recovered.
        try:
            from runtime.faculty_health import mark_genome_recovered as _gh_recovered
            _gh_recovered("PerceptionFaculty")
        except Exception as _gh_rec_err:
            _log.warning("mark_genome_recovered(PerceptionFaculty) FAILED: %s", _gh_rec_err)
    except Exception as _perc_err:
        _log.warning("perceive_from_live_state FAILED: %s", _perc_err)
        try:
            from runtime.faculty_health import mark_genome_degraded as _gh_degraded
            _gh_degraded("PerceptionFaculty", str(_perc_err)[:120])
        except Exception as _gh_deg_err:
            _log.warning("mark_genome_degraded(PerceptionFaculty) FAILED: %s", _gh_deg_err)

    # ── WO-WORLD-001: Fast capability verb pre-sniff (Option A) ─────────────────
    # Keyword match against registry verbs — no LLM, no language faculty pass.
    # Produces capability_hint for assemble_world_state() so world-capability
    # domains (e.g. sun_events) are populated before the Executive reads world.
    _early_capability_hint = ""
    try:
        from runtime.capabilities.registry import all_enabled as _cap_all_enabled
        _raw_lower = raw.lower() if raw else ""
        for _cap in _cap_all_enabled():
            if any(_v in _raw_lower for _v in (_cap.verbs or [])):
                _early_capability_hint = _cap.id
                break
    except Exception as _hint_err:
        _log.warning("capability pre-sniff FAILED (non-critical): %s", _hint_err)

    # ── WO-CANON-XV: LiveWorldState — assembled FIRST, frozen, read by all faculties ─
    # Copies PerceptionResult fields into domain slices (Ch.3 §3.2 copy step).
    _world = None
    try:
        from world.live_world_state import assemble_world_state as _assemble_world, write_unified_state as _write_unified
        _world = _assemble_world(
            turn_id=raw[:32] if raw else "",
            perception=_perception,
            capability_hint=_early_capability_hint,
        )
        # WO-SPINE-003: publish world state to brain_state.json (Unity reads this)
        try:
            _write_unified(_world)
        except Exception as _wus_err:
            _log.warning("write_unified_state FAILED: %s", _wus_err)
    except Exception as _world_err:
        _log.warning("assemble_world_state FAILED: %s", _world_err)

    # ── WO-CANON-VI: Working Memory + Attention — top-of-turn, before faculties ─
    # core/memory_relevance_filter.py = candidate/signal supplier. WM competition = sole driver.
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
        # Build candidates from core/memory_relevance_filter supplier output
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

    # ── WO-CCM-SPINE: CCM enrichment — after Language Faculty, before Memory Faculty ──
    _ccm_context: dict = {}
    try:
        from faculties.ccm.ccm_enricher import enrich as _ccm_enrich
        _ccm_context = _ccm_enrich(raw, language, None)
    except Exception as _ccm_err:
        _log.warning("ccm_enricher FAILED: %s", _ccm_err)

    # ── v1.4 Relationship Faculty ─────────────────────────────────────────────
    relationship = None
    try:
        from runtime.spine.relationship_faculty import analyse as rel_analyse
        relationship = rel_analyse(raw, memory_pack)
        # WO-SPG-HOOKS-001: tap relationship state for SPG signal logger
        try:
            from memory.spg_capture import get_capture as _spg_rel_get
            _spg_rel_get().log(
                "relationship_shift",
                relationship=getattr(relationship, "relationship_mode", None)
                             or getattr(relationship, "register", None),
                edge_hint=getattr(relationship, "expression_posture", None),
            )
        except Exception as _spg_rel_err:
            _log.warning("SPG relationship tap failed (non-blocking): %s", _spg_rel_err)
    except Exception as e:
        _log.warning("relationship_faculty FAILED: %s", e)

    # ── Capability Faculty ────────────────────────────────────────────────────
    # D1 ruling: capability routing reads the intent_engine's `capability_hint`,
    # not the cognitive intent. The two answer different questions.
    # SP-36/SP-37 (WO-NAV-005): read current embodiment for scope filter
    _current_embodiment = "desktop"
    try:
        from self.elo_self_model import load as _load_self_emb
        _current_embodiment = getattr(_load_self_emb(), "embodiment", "desktop") or "desktop"
    except Exception as _emb_err:
        _log.warning("elo_self_model load FAILED (using default embodiment): %s", _emb_err)
    capabilities = _capability_faculty(language["meaning"], language.get("capability_hint", ""), current_embodiment=_current_embodiment)

    # ── System Faculty ────────────────────────────────────────────────────────
    system_det = _system_faculty(language["meaning"])

    # ── WO-CANON-XVI / ADR-Exec-006: Assemble unified cognitive state BEFORE Executive ──
    _cognitive_state = None
    try:
        _cognitive_state = assemble_cognitive_state(
            language, memory_pack, attention, capabilities, None, state,
            world_state=_world, working_memory=_wm,
            ccm_context=_ccm_context,
        )
    except Exception as _cs_err:
        _log.warning("assemble_cognitive_state FAILED: %s", _cs_err)

    # ── WO-CANON-VII Ch.5: Personality vector — trait values + affect baseline ─
    # Read on the response path (never mutated). Feeds the Emotion faculty's
    # baseline and lets the ExecutionReport carry an identity fingerprint.
    _personality_traits = {}
    _personality_baseline = {}
    _identity_hash = ""
    try:
        from faculties.personality.personality_evolution_faculty import (
            load_personality as _pv_load,
            get_trait_values as _pv_traits,
            get_affect_baseline as _pv_baseline,
            compute_identity_hash as _pv_hash,
        )
        _pv = _pv_load()
        _personality_traits = _pv_traits(_pv)
        _personality_baseline = _pv_baseline(_pv)
        _identity_hash = _pv_hash()
    except Exception as _pv_err:
        _log.warning("personality read FAILED: %s", _pv_err)

    # ── WO-006 Vol V Ch.4: Emotional Processing — AffectState BEFORE Executive ─
    # process_emotion reads CognitiveState + self-model, returns (AffectState, EmotionalTag).
    # Never raises; falls back to neutral. Attached to plan below.
    _affect_state = None
    _emotional_tag = None
    try:
        from faculties.emotion.emotional_processing_faculty import process_emotion as _process_emotion
        _prior_arousal = 0.20
        if isinstance(state, dict):
            _prior_affect = state.get("_prior_affect")
            if isinstance(_prior_affect, dict):
                _prior_arousal = float(_prior_affect.get("arousal", 0.20))
        _self_model = state.get("self_model_state") if isinstance(state, dict) else None
        _affect_state, _emotional_tag = _process_emotion(
            _cognitive_state,
            self_model_state=_self_model,
            prior_arousal=_prior_arousal,
        )
        try:
            from runtime.faculty_health import mark_genome_recovered as _gh_recovered
            _gh_recovered("EmotionFaculty")
        except Exception as _emo_rec_err:
            _log.warning("mark_genome_recovered(EmotionFaculty) FAILED: %s", _emo_rec_err)
    except Exception as _emo_err:
        _log.warning("process_emotion FAILED: %s", _emo_err)
        try:
            from runtime.faculty_health import mark_genome_degraded as _gh_degraded
            _gh_degraded("EmotionFaculty", str(_emo_err)[:120])
        except Exception as _emo_deg_err:
            _log.warning("mark_genome_degraded(EmotionFaculty) FAILED: %s", _emo_deg_err)

    # ── WO-PLANETARY-KERNEL: Mode selector — BUILD / PLAY / EXPLORE / REFINE ──
    _turn_mode: str = "EXPLORE"
    _planet_voice_pool: str = ""
    try:
        from faculties.planetary_kernel import PlanetaryKernel as _PK
        _sig_for_mode = getattr(_cognitive_state, "significance_score", 0.0) if _cognitive_state else 0.0
        _turn_mode, _planet_voice_pool = _PK().select_mode_with_pool(
            _cognitive_state,
            turn=raw, language_output=language,
            ccm_context=_ccm_context,
            significance_score=_sig_for_mode,
        )
    except Exception as _mode_err:
        _log.warning("planetary_kernel FAILED: %s", _mode_err)
    # WO-PLANETARY-KERNEL D-4: ValueFaculty (Venus register stub — future CP-003)
    try:
        from faculties.value_faculty import ValueFaculty as _VF  # noqa: F401
    except Exception as _vf_err:
        _log.warning("value_faculty import FAILED: %s", _vf_err)

    # ── Executive Faculty — ONE DECISION ─────────────────────────────────────
    # WO-106: pass assembled state so the Executive decides from real context
    # WO-CONSEQUENCE-REPORT-001: pass prior-turn ExecutionReport so Executive knows what happened
    global _prev_execution_report
    plan = _executive_faculty(
        raw, language, attention, capabilities, system_det,
        world=_world,
        cognitive_state=_cognitive_state,
        working_memory=_wm,
        affordances=getattr(_snapshot, "surface_affordances", None) if _snapshot else None,
        execution_report=_prev_execution_report,
    )

    # WO-CONSEQUENCE-REPORT-001: build consequence context from prior turn and store on plan
    if _prev_execution_report is not None:
        try:
            _er = _prev_execution_report
            _er_completed = getattr(_er, "completed", True)
            _er_action = getattr(_er, "planned_action", "") or ""
            _er_state = getattr(_er, "completion_state", "delivered") or "delivered"
            if _er_action:
                if _er_completed:
                    plan.llm_context = (
                        f"[CONSEQUENCE — previous turn] eLo {_er_action} → {_er_state}. "
                        "If relevant, eLo can acknowledge this naturally."
                    )
                else:
                    plan.llm_context = (
                        f"[CONSEQUENCE — previous turn] eLo attempted {_er_action} but did not complete ({_er_state}). "
                        "eLo is aware of this and can acknowledge it honestly."
                    )
        except Exception as _cons_err:
            _log.warning("consequence context build FAILED (non-fatal): %s", _cons_err)

    # ── WO-052: Store snapshot on plan (assembled before; now pinned to it) ───
    plan.snapshot = _snapshot
    # ── WO-PLANETARY-KERNEL: Pin turn mode (BUILD/PLAY/EXPLORE/REFINE) ───────
    if not getattr(plan, "mode", ""):
        plan.mode = _turn_mode
    # WO-PLANETARY-KERNEL: active_mode is the canonical kernel mode field
    plan.active_mode = _turn_mode
    # WO-LIVING-PRESENCE-UPDATE-001: pin planet voice pool for active mode
    plan.planet_voice_pool = _planet_voice_pool
    # ── WO-CANON-XVI: Pin pre-assembled cognitive state to plan ──────────────
    plan.cognitive_state = _cognitive_state
    # ── WO-CANON-XV/XII: Store frozen world + perception on plan ──────────────
    plan.world = _world
    # ── WO-CANON-VI: Store frozen WorkingMemory on plan ───────────────────────
    plan.working_memory = _wm
    # ── WO-006: Pin AffectState + EmotionalTag on plan (readable downstream) ──
    plan.affect_state  = _affect_state
    plan.emotional_tag = _emotional_tag
    # ── WO-CANON-VII Ch.5: Pin personality read on plan for downstream + report
    plan.personality_traits   = _personality_traits
    plan.personality_baseline = _personality_baseline
    plan.identity_hash        = _identity_hash
    # ── WO-XDNA-001: Pin minted experience_id to plan ────────────────────────────
    plan.experience_id        = _turn_xid
    # ── WO-INGRESS-32: Pin caller-supplied intent provenance ─────────────────────
    plan.intent_source        = intent_source
    if internal_intent:
        plan.internal_intent  = internal_intent

    # ── WO-CANON-XXV: Temporal Cognition Faculty ─────────────────────────────
    _temporal_frame = None
    try:
        from faculties.temporal import compute as _temporal_compute
        _last_ts = getattr(_world, "last_interaction_ts", 0.0) if _world else 0.0
        _idle_s  = getattr(_world, "idle_seconds", 0.0) if _world else 0.0
        _temporal_frame = _temporal_compute(
            world_state=_world,
            last_interaction_ts=_last_ts,
            idle_seconds=_idle_s,
        )
    except Exception as _tf_err:
        _log.warning("temporal_faculty FAILED: %s", _tf_err)
    plan.temporal_frame = _temporal_frame
    # ── F-7 SELF-INTERPRET: compute in run() scope and pin to plan ───────────────
    # _self_interpretation is defined inside _executive_faculty() (local scope only).
    # Re-run here so run() has the result. interpret() is idempotent and cheap.
    _self_interpretation = None
    try:
        from self.elo_self_model import load as _load_self_state
        from runtime.self_interpret import interpret as _self_interpret_fn
        _si_state = _load_self_state()
        _self_interpretation = _self_interpret_fn(_si_state)
        if _self_interpretation and not _self_interpretation.is_empty():
            _log.info("F-7 self-interpret: %s", _self_interpretation.text[:120])
    except Exception as _si_run_err:
        _log.warning("self_interpret (run scope) failed (non-critical): %s", _si_run_err)
    plan.self_interpretation = _self_interpretation.as_dict() if _self_interpretation else None

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

    # ── WO-AFFECTIVE-STATE-001: propagate AffectiveState + SelfModel from cognitive_state → plan ──
    try:
        _cs_aff = getattr(cognitive_state, "affective_state", None)
        if _cs_aff is not None:
            plan.affective_state = _cs_aff
        _cs_sm = getattr(cognitive_state, "self_model", None)
        if _cs_sm is not None:
            plan.self_model = _cs_sm
    except Exception as _aff_err:
        _log.warning("affective/self-model propagation failed (non-fatal): %s", _aff_err)

    # WO-AGENCY-FACULTY-001: propagate agency_level from cognitive_state → plan (refined with ExecutionReport)
    try:
        _cs_agency_raw = getattr(cognitive_state, "agency_level", 0.6)
        _aff_for_plan = getattr(plan, "affective_state", None)
        plan.agency_level = _agency_faculty(
            affective_state=_aff_for_plan,
            execution_report=_prev_execution_report,
            capability_count=len(getattr(plan, "capabilities", ())),
            relationship_mode=getattr(plan, "relationship_mode", ""),
        )
    except Exception as _ag_plan_err:
        _log.warning("agency_faculty plan propagation failed (non-fatal): %s", _ag_plan_err)

    # WO-QBODY-CONSEQUENCES-001 + WO-QMOVEMENT-001: propagate body + movement state → plan
    try:
        for _bf in (
            "body_moving", "body_gait", "body_heading", "body_on_window",
            "body_window", "body_edge", "body_embodiment",
            "movement_where_i_am", "movement_want_to_go",
            "movement_am_moving", "movement_arrived", "movement_what_happened",
        ):
            _bv = getattr(cognitive_state, _bf, None)
            if _bv is not None:
                setattr(plan, _bf, _bv)
    except Exception as _body_prop_err:
        _log.warning("body/movement propagation failed (non-fatal): %s", _body_prop_err)

    # ── S6: Build EmbodimentState ─────────────────────────────────────────────
    # WO-097: runs AFTER conversation so response_text / display_text / tts_text
    # are populated when the body reads them.
    try:
        global _EMBODIMENT_SEQUENCE
        _EMBODIMENT_SEQUENCE += 1
        plan.embodiment_state = build_embodiment_state(plan, sequence_id=_EMBODIMENT_SEQUENCE)
        if getattr(plan, "direct_response", None) and not getattr(
            plan.embodiment_state, "response_text", None
        ):
            _log.warning(
                "build_embodiment_state: response_text empty on direct-response turn"
            )
    except Exception as e:
        _log.warning("build_embodiment_state FAILED: %s", e)
        plan.embodiment_state = None

    # ── Vol III §Metadata: ExecutionReport — produced at end of every turn ────
    # The report is the honesty record for what happened this turn: completion
    # state, planned action, backend used. Attached to the plan and published
    # on the Faculty Bus so downstream honesty/learning gates can read the
    # same authoritative record instead of re-deriving from log tails.
    try:
        _completion = "delivered" if getattr(plan, "direct_response", None) or getattr(
            plan, "conversation_action", ""
        ) else "partial"
        plan.execution_report = build_execution_report(
            plan,
            completion_state=_completion,
            llm_backend_used=getattr(plan, "direct_backend", ""),
        )
        try:
            from core.faculty_bus import get_bus as _get_bus
            _get_bus().publish("Spine", "execution_report", {
                "planned_action":   plan.execution_report.planned_action,
                "completed":        plan.execution_report.completed,
                "completion_state": plan.execution_report.completion_state,
                "llm_backend_used": plan.execution_report.llm_backend_used,
            })
        except Exception as _er_inner:
            _log.warning("build_execution_report inner publish FAILED: %s", _er_inner)
        # WO-SPG-HOOKS-001: tap ExecutionReport completion for SPG signal logger
        try:
            from memory.spg_capture import get_capture as _spg_er_get
            _spg_er_get().log(
                "memory_write",
                edge_hint=plan.execution_report.planned_action,
            )
        except Exception as _spg_er_err:
            _log.warning("SPG execution_report tap failed (non-blocking): %s", _spg_er_err)
    except Exception as _er_err:
        _log.warning("build_execution_report FAILED: %s", _er_err)

    # WO-CONSEQUENCE-REPORT-001: persist this turn's report for the next turn's context
    try:
        if getattr(plan, "execution_report", None) is not None:
            _prev_execution_report = plan.execution_report
    except Exception as _cons_persist_err:
        _log.warning("consequence_report persist FAILED (non-fatal): %s", _cons_persist_err)

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

# ── WO-ENVIRONMENT-FACULTY-001: app → activity mapping ───────────────────────
_APP_TO_ACTIVITY: dict[str, str] = {
    "visual studio code": "coding", "cursor": "coding", "xcode": "coding",
    "pycharm": "coding", "intellij": "coding", "android studio": "coding",
    "blender": "creating", "figma": "creating", "sketch": "creating",
    "photoshop": "creating", "illustrator": "creating", "after effects": "creating",
    "word": "writing", "pages": "writing", "google docs": "writing",
    "notion": "writing", "obsidian": "writing", "bear": "writing",
    "brave browser": "browsing", "safari": "browsing", "chrome": "browsing",
    "firefox": "browsing", "arc": "browsing",
    "terminal": "terminal", "iterm": "terminal", "warp": "terminal",
}


def _environment_faculty() -> dict:
    """
    WO-ENVIRONMENT-FACULTY-001: Observe desktop environment state from perch/presence files.
    Returns {active_app, active_window, desktop_activity}. Observe only — no decisions.
    Gracefully returns empty dict if files are absent or unreadable.
    """
    import json as _json
    import pathlib as _pathlib

    _BLENDER_DIR = _pathlib.Path(__file__).parent.parent.parent / "blender"
    result: dict = {}
    try:
        _perch = _json.loads((_BLENDER_DIR / "perch_state.json").read_text())
        result["active_app"] = _perch.get("app", "")
    except Exception:
        result["active_app"] = ""

    try:
        _pres = _json.loads((_BLENDER_DIR / "presence_state.json").read_text())
        result["active_window"] = _pres.get("frontWindowName", "")
    except Exception:
        result["active_window"] = ""

    _app_lower = result.get("active_app", "").lower()
    result["desktop_activity"] = next(
        (act for key, act in _APP_TO_ACTIVITY.items() if key in _app_lower),
        "unknown",
    )
    return result


def _agency_faculty(
    affective_state=None,
    execution_report=None,
    capability_count: int = 0,
    relationship_mode: str = "",
) -> float:
    """
    WO-AGENCY-FACULTY-001: compute eLo's current agency level (0.0–1.0).
    High agency → eLo initiates, proposes, takes lead.
    Low agency → eLo checks in, defers, waits.
    Observe only — no decisions.
    """
    _base = float(getattr(affective_state, "agency", 0.6))

    # Boost from recent successful ExecutionReport
    _er_boost = 0.0
    try:
        if execution_report is not None:
            _completed = getattr(execution_report, "completed", False)
            if _completed:
                _er_boost = 0.12
    except Exception:
        pass

    # Capability availability: more caps available → more agency
    _cap_boost = min(0.15, capability_count * 0.03)

    # Relationship mode modifiers
    _rel_mod = 0.0
    if relationship_mode in ("established", "close"):
        _rel_mod = 0.08
    elif relationship_mode in ("new", "in_conflict"):
        _rel_mod = -0.08

    _agency = min(1.0, max(0.0, _base + _er_boost + _cap_boost + _rel_mod))
    return round(_agency, 3)


def _body_faculty() -> dict:
    """
    WO-QBODY-CONSEQUENCES-001 + WO-QMOVEMENT-001: read elo_spatial.json and return
    Q-BODY proprioception + Q-MOVEMENT five-state lifecycle. Observe only — no decisions.
    Gracefully returns empty dict if file is absent or unreadable.
    """
    import json as _json
    import pathlib as _pathlib

    _SPATIAL = _pathlib.Path(__file__).parent.parent.parent / "blender" / "elo_spatial.json"
    try:
        _s = _json.loads(_SPATIAL.read_text())
    except Exception:
        return {}

    # Q-BODY
    _moving = bool(_s.get("moving", False))
    _gait = str(_s.get("gait", "idle"))
    _heading = str(_s.get("heading", "none"))
    _x = float(_s.get("x", 0.0))
    _y = float(_s.get("y", 0.0))
    _on_window = bool(_s.get("on_window", False))
    _window_name = str(_s.get("window", ""))
    _edge = str(_s.get("edge", ""))
    _embodiment = str(_s.get("embodiment", "desktop"))

    # Q-MOVEMENT WHERE I AM
    _where = f"window:{_window_name} edge:{_edge}" if _window_name else ""

    # Q-MOVEMENT WANT TO GO
    _goal = _s.get("goal", -1)
    if _goal is None:
        _goal = -1

    # Q-MOVEMENT AM MOVING
    _am_moving = _moving

    # Q-MOVEMENT ARRIVED + WHAT HAPPENED — from last_move
    _last = _s.get("last_move") or {}
    _arrived = bool(_last.get("arrived", False))
    _what = str(_last.get("outcome", "none")) if _last else "none"

    return {
        "body_moving": _moving,
        "body_gait": _gait,
        "body_heading": _heading,
        "body_position_x": _x,
        "body_position_y": _y,
        "body_on_window": _on_window,
        "body_window": _window_name,
        "body_edge": _edge,
        "body_embodiment": _embodiment,
        "movement_where_i_am": _where,
        "movement_want_to_go": int(_goal) if isinstance(_goal, (int, float)) else -1,
        "movement_am_moving": _am_moving,
        "movement_arrived": _arrived,
        "movement_what_happened": _what,
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
    ccm_context:    dict | None = None,
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

    # WO-MEMORY-TURN-TYPES: tag this turn with canonical memory categories
    _raw_input = language.get("original", "")
    try:
        from memory.category_tagger import tag_turn as _tag_turn
        _mem_categories = tuple(_tag_turn(_raw_input))
    except Exception:
        _mem_categories = ()

    # WO-CONV-001: WKG claims relevant to this turn
    _wkg_context = ""
    try:
        import runtime.wkg_faculty as _wkg
        _topic = language.get("intent", "") or language.get("meaning", "")[:60]
        if _topic:
            _entities = _wkg.search_entities(_topic)[:3]
            if _entities:
                # Build entity-id → label map for resolving object labels in the graph
                _ent_map = {e["entity_id"]: e.get("label", "") for e in _wkg._load("entities")}
                _lines = []
                for _ent in _entities:
                    # WO-VESSEL-CONTRADICT-001: filter out claims that have been contradicted
                    _claims = [c for c in _wkg.get_claims_about(_ent.get("entity_id", ""))
                               if not c.get("contradicted_by")][:2]
                    for _cl in _claims:
                        _subj = _ent_map.get(_cl.get("subject_entity_id", ""), _ent.get("label", ""))
                        _obj  = _ent_map.get(_cl.get("object_entity_id", ""), "")
                        _rel  = _cl.get("relationship_type", "").replace("_", " ").lower()
                        _epi  = _cl.get("epistemic_class", "").upper()
                        if _obj:
                            _line = f"[{_epi}] {_subj} {_rel} {_obj}"
                            # WO-MEMORY-TRACE-001: include affective_snapshot label if present
                            _aff_snap = _cl.get("affective_snapshot")
                            if _aff_snap and isinstance(_aff_snap, dict):
                                from runtime.contracts import AffectiveState as _AffS
                                try:
                                    _aff_obj = _AffS(**{k: v for k, v in _aff_snap.items() if hasattr(_AffS, k)})
                                    _aff_label = _aff_obj.label()
                                    if _aff_label:
                                        _line += f" [felt: {_aff_label}]"
                                except Exception:
                                    pass
                            _lines.append(_line)
                _wkg_context = "; ".join(_lines)
    except Exception:
        pass

    # WO-SP29: compute per-turn significance score from world state
    _significance_score: float = 0.0
    _sig_result: dict = {}
    try:
        from runtime.significance_faculty import compute_significance as _csig_sp29
        _world_delta_sp29: dict = {}
        try:
            from world.world_delta import compute_delta as _wd_compute_sp29
            _world_delta_sp29 = _wd_compute_sp29() or {}
        except Exception:
            pass
        _sig_result = _csig_sp29(_world_delta_sp29, text_input=_raw_input or "")  # WO-SP29-CONV-SIGNIFICANCE-001
        _significance_score = float(_sig_result.get("overall", 0.0))
    except Exception:
        _significance_score = 0.0

    # WO-ENVIRONMENT-FACULTY-001: observe desktop environment state
    _env = {}
    try:
        _env = _environment_faculty()
    except Exception as _env_err:
        _log.warning("_environment_faculty failed (non-fatal): %s", _env_err)

    # WO-QBODY-CONSEQUENCES-001 + WO-QMOVEMENT-001: read proprioception + movement lifecycle
    _body = {}
    try:
        _body = _body_faculty()
    except Exception as _body_err:
        _log.warning("_body_faculty failed (non-fatal): %s", _body_err)

    # WO-AFFECTIVE-STATE-001: derive 13-dim AffectiveState from significance scores
    _affective_state = None
    try:
        from runtime.significance_faculty import derive_affective_state as _das
        _affective_state = _das(_sig_result, text_input=_raw_input or "")
    except Exception:
        pass

    # WO-AGENCY-FACULTY-001: compute agency level from affective + relationship
    _agency_level_cs = 0.6
    try:
        _cs_rel_mode = (prior_state.relationship_type if prior_state and hasattr(prior_state, "relationship_type") else "")
        _agency_level_cs = _agency_faculty(
            affective_state=_affective_state,
            execution_report=None,  # not available at assemble_cognitive_state time
            capability_count=len(capabilities) if capabilities else 0,
            relationship_mode=_cs_rel_mode,
        )
    except Exception as _ag_err:
        _log.warning("_agency_faculty failed in assemble (non-fatal): %s", _ag_err)

    # WO-SELF-MODEL-001: assemble lean SelfModel from existing faculty outputs
    _self_model = None
    try:
        _self_model = _self_model_faculty(
            wkg_context=_wkg_context,
            affective_state=_affective_state,
            lessons=None,  # populated from lesson_store if available in full turn
        )
    except Exception:
        pass

    # D1 ruling (Card 0035): intent_signal is the COGNITIVE intent that the
    # Executive decides on — sourced from core/memory_relevance_filter (attention_model["intent"]).
    # The intent_engine's router hint travels as `capability_hint`, elsewhere.
    return CognitiveState(
        raw_input=_raw_input,
        intent_signal=(attention or {}).get("intent") or language.get("intent") or "conversation",
        register=language.get("register", ""),
        social_signal=language.get("social", ""),
        momentum=(attention or {}).get("momentum", "stable"),
        valence=(attention or {}).get("valence", "neutral"),
        assembly_confidence=conf,
        capability_candidates=cap_candidates,
        world_state=world_state,
        working_memory=working_memory,
        attention_state=_attn_state,
        memory_categories=_mem_categories,
        significance_score=_significance_score,
        wkg_context=_wkg_context,
        ccm_context=ccm_context or {},
        affective_state=_affective_state,
        self_model=_self_model,
        active_app=_env.get("active_app", ""),
        active_window=_env.get("active_window", ""),
        desktop_activity=_env.get("desktop_activity", "unknown"),
        # WO-AGENCY-FACULTY-001: computed agency level
        agency_level=_agency_level_cs,
        # WO-QBODY-CONSEQUENCES-001: Q-BODY proprioception
        body_moving=_body.get("body_moving", False),
        body_gait=_body.get("body_gait", "idle"),
        body_heading=_body.get("body_heading", "none"),
        body_position_x=_body.get("body_position_x", 0.0),
        body_position_y=_body.get("body_position_y", 0.0),
        body_on_window=_body.get("body_on_window", False),
        body_window=_body.get("body_window", ""),
        body_edge=_body.get("body_edge", ""),
        body_embodiment=_body.get("body_embodiment", "desktop"),
        # WO-QMOVEMENT-001: Q-MOVEMENT five lifecycle states
        movement_where_i_am=_body.get("movement_where_i_am", ""),
        movement_want_to_go=_body.get("movement_want_to_go", -1),
        movement_am_moving=_body.get("movement_am_moving", False),
        movement_arrived=_body.get("movement_arrived", False),
        movement_what_happened=_body.get("movement_what_happened", "none"),
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

    # ── WO-PLANETARY-KERNEL + WO-BUILDER-EXPRESSION: register + mode shaping ──
    if resp:
        try:
            from kernel.language_register import filter_response as _fr, shape_for_mode as _sfm
            _mode = getattr(plan, "mode", "") or ""
            resp = _fr(resp)
            if _mode:
                resp = _sfm(resp, _mode)
        except Exception as _lre:
            _log.debug("language_register shaping FAILED (non-critical): %s", _lre)

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
