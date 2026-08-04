"""
company_runtime/behaviour_eval.py — Behaviour-routing evaluator (WO-027 support).

Runs the seeded golden set (tests/golden/behaviour_golden_set.json) against eLo
OS's DETERMINISTIC routing layer and reports, per case, what routes correctly.

WHY THIS EXISTS
    The LLM backend is currently down (mock/Groq), but eLo's ROUTING is
    deterministic and does NOT need the LLM. Each behaviour bug that WO-019/020/
    022/029/015 fixed shows up as a routing DECISION (which CAL action fires,
    which intent classifies, whether a recall/greeting/loop trigger matches) —
    not as generated words. This tool checks the DECISION so the behaviour WOs
    can be auto-verified instead of David confirming each one by hand.

WHAT IT DOES / DOESN'T TOUCH
    ADDITIVE ONLY. This module imports from the frozen kernel / runtime / tools
    and never edits them. The real, importable routing entry points used:
        core.attention.compute        — build the attention model (intent + valence)
        runtime.executive.decide       — the CAL action (ANSWER/CONNECT/REFLECT/...)
        core.kernel.classify_input     — kernel input type → mode
        core.kernel loop detector      — record_response / detect_loop (loop filter)
        runtime.router.intent_engine   — tool/agent intent classification
        tools.tool_router._detect_intent — direct tool-intent keyword match
        memory.vault_layer.lookup      — deterministic vault recall (no LLM)

    Where a check must mirror logic that lives INLINE in server.py (the WO-022
    recall trigger set + topic extraction, and the WO-019 bubble→TTS join), the
    mirror is copied verbatim and clearly labelled — server.py can't be imported
    (it boots a server) and these are not exposed as importable functions. This
    follows the existing precedent in tests/test_wo019_*.py and test_wo022_*.py.

HONESTY RULE
    A case that genuinely needs the LLM's actual WORDS (e.g. "did eLo avoid
    projecting emotion", "was it phrased in first person") is reported
    "N/A — needs live LLM", never silently failed.

Run:
    python3 -m company_runtime.behaviour_eval
"""

from __future__ import annotations

import json
import os
import re
import sys

# ── make the repo root importable regardless of CWD ───────────────────────────
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_GOLDEN_PATH = os.path.join(_REPO_ROOT, "tests", "golden", "behaviour_golden_set.json")

# result statuses
PASS = "PASS"
FAIL = "FAIL"
NA   = "N/A — needs live LLM"


# ══════════════════════════════════════════════════════════════════════════════
#  Deterministic routing probes — thin wrappers over the real entry points.
# ══════════════════════════════════════════════════════════════════════════════

def _cal_decision(text: str) -> dict:
    """Run the real attention → executive (CAL) path. Returns intent/action/tone."""
    from core.attention import compute
    from runtime.executive import decide
    from core.kernel import classify_input

    attn = compute(text, {}, {})                       # empty memory/session — pure input routing
    dec  = decide(attn, loop_detected=False, user_input=text)
    cls  = classify_input(text)
    return {
        "intent": attn.get("intent", "?"),
        "action": dec.get("action", "?"),
        "tone":   dec.get("tone", "?"),
        "reason": dec.get("cal_reason", ""),
        "mode":   cls.get("type", "?"),
    }


def _tool_routing(text: str) -> dict:
    """Run the real tool/agent intent classifiers (no agent is executed)."""
    from runtime.router.intent_engine import detect as _intent_detect
    from tools import tool_router as _tr

    pipe_intent = _intent_detect(text).get("intent", "?")
    direct      = _tr._detect_intent(text)             # tool_router keyword map (None if no tool)
    return {"pipeline_intent": pipe_intent, "direct_intent": direct}


# ── WO-022 recall detection — mirror of the inline block in server.py (~L2454) ─
_MEMORY_QUERY_TRIGGERS = (
    "do you remember", "what did you say", "what did elo say", "last sentence",
    "what was the last", "what did we talk about", "what did we last",
    "what did we say", "you said", "last conversation", "what was said",
    "what were we talking", "what have we been", "what did i say",
    "remind me what", "from your memory", "from memory", "what have you kept",
    "what do you have stored", "what do you remember", "tell me something you",
    "share something from", "what do you know about me", "what have you learned",
    "pull something from memory", "recall something",
    "what's in your memory", "what's in memory",
)
_RECALL_SKIP = frozenset({
    "what", "you", "remember", "tell", "from", "your", "my", "do", "did",
    "that", "the", "something", "anything", "have", "has", "me", "about",
    "how", "much", "know", "last", "time", "pull", "share", "recall",
    "memory", "stored", "kept", "elo",
})


def _is_recall(raw: str) -> bool:
    t = raw.lower()
    return any(p in t for p in _MEMORY_QUERY_TRIGGERS)


def _recall_topic(raw: str) -> str:
    raw_l = raw.lower()
    topic_words = [
        w for w in re.sub(r"[^a-z0-9 ]", "", raw_l).split()
        if w not in _RECALL_SKIP and len(w) >= 3
    ]
    return " ".join(topic_words) if topic_words else "disenelo recent"


# ── WO-019 TTS assembly — mirror of server.py (~L2845) ─────────────────────────
def _make_tts_text(response: str, tts_max: int = 400) -> str:
    """Mirror of server.py multi-bubble split + TTS join (post WO-019 Bug-A fix)."""
    bubbles = [b.strip() for b in response.split("\n\n") if b.strip()] or [response]
    tts_text = " ".join(bubbles) if bubbles else response   # the fix: join, not bubbles[0]
    if len(tts_text) > tts_max:
        cut = tts_text[:tts_max].rfind(". ")
        tts_text = tts_text[:cut + 1] if cut > 50 else tts_text[:tts_max]
    return tts_text


# ══════════════════════════════════════════════════════════════════════════════
#  Per-case evaluators. Each returns (status, routed_description, detail).
#  Cases whose judgement is about the LLM's actual WORDS return N/A.
# ══════════════════════════════════════════════════════════════════════════════

# CAL actions that the golden `must_not` lists forbid on plain / social inputs.
_ASSOCIATIVE = {"connect", "reflect", "challenge", "witness"}
# CAL actions that count as a direct/warm conversational reply.
_DIRECT_OK = {"answer", "celebrate", "simplify"}


def _eval_route_answer(case):
    """GS-ROUTE-01: factual question must route ANSWER, not associative firing."""
    d = _cal_decision(case["input"])
    routed = f"CAL action={d['action'].upper()} (intent={d['intent']}, {d['reason']}); kernel mode={d['mode']}"
    if d["action"] == "answer":
        return PASS, routed, "routed to ANSWER — no CONNECT/REFLECT/CHALLENGE over-fire"
    if d["action"] in _ASSOCIATIVE:
        return FAIL, routed, f"associative action {d['action'].upper()} fired on a factual question"
    return FAIL, routed, f"expected ANSWER, got {d['action'].upper()}"


def _eval_route_casual(case):
    """GS-ROUTE-02: plain acknowledgement must stay conversational, no REFLECT/CHALLENGE."""
    d = _cal_decision(case["input"])
    routed = f"CAL action={d['action'].upper()} ({d['reason']})"
    if d["action"] in _ASSOCIATIVE:
        return FAIL, routed, f"acknowledgement triggered associative firing: {d['action'].upper()}"
    if d["action"] in _DIRECT_OK:
        return PASS, routed, "brief/warm conversational route — no unprompted analysis"
    return FAIL, routed, f"unexpected action {d['action'].upper()} on a casual line"


def _eval_route_media(case):
    """GS-ROUTE-03: 'play the Joe Budden Podcast' must route to a media/play action,
    not a wiki/search lookup, and not latch a stale entity."""
    t = _tool_routing(case["input"])
    # is the entity latch clean? (fresh call — tool_router clears _last_agent per WO-020 Seam B)
    from tools import tool_router as _tr
    latch = _tr._last_agent
    routed = (f"pipeline intent={t['pipeline_intent']!r}, tool_router._detect_intent="
              f"{t['direct_intent']!r}, stale-latch={latch!r}")
    play_intents   = {"utility_spotify", "spotify", "spotify_search", "spotify_playlist"}
    lookup_intents = {"lookup", "search", "obsidian", "news"}
    if t["pipeline_intent"] in play_intents or t["direct_intent"] in play_intents:
        return PASS, routed, "routed to a Spotify/media play action"
    if t["pipeline_intent"] in lookup_intents or t["direct_intent"] in lookup_intents:
        return FAIL, routed, "routed to a wiki/search LOOKUP instead of play (anti-pattern)"
    return FAIL, routed, ("did NOT route to media/play — classified as "
                          f"{t['pipeline_intent']!r} (falls through to plain conversation, no play)")


def _eval_loop_filter(case):
    """GS-LOOP-01: loop filter must detect a verbatim repeat so it can suppress it."""
    from core import kernel
    kernel.reset_session()
    line = "That contradiction is doing something."
    fired = None
    for i in range(3):
        kernel.record_response(line)
        r = kernel.detect_loop()
        if r["detected"]:
            fired = (i + 1, r["reason"])
            break
    kernel.reset_session()
    if fired:
        routed = f"detect_loop fired on turn {fired[0]} (reason={fired[1]!r}) → force_direct/suppress"
        return PASS, routed, "loop filter catches the verbatim repeat"
    return FAIL, "detect_loop never fired across 3 identical lines", "loop filter miss"


def _eval_voice_completeness(case):
    """GS-VOICE-01: the FULL multi-sentence reply must reach TTS, not just bubble[0]."""
    sample = ("Start by checking your OS audio output device.\n\n"
              "If that looks right, try restarting the CoreAudio daemon.")
    tts = _make_tts_text(sample)
    sents = [s for s in re.split(r"(?<=[.!?])\s+", tts.strip()) if s.strip()]
    # extra evidence: confirm server.py uses the join, not the bubbles[0] bug
    join_ok = False
    try:
        with open(os.path.join(_REPO_ROOT, "server.py"), encoding="utf-8") as f:
            src = f.read()
        join_ok = ('" ".join(_bubbles)' in src) and ("_tts_text = _bubbles[0]" not in src)
    except Exception:
        pass
    routed = (f"tts assembly → sentence_count={len(sents)} (both bubbles voiced); "
              f"server.py join-fix present={join_ok}")
    if "CoreAudio" in tts and len(sents) >= 2 and join_ok:
        return PASS, routed, "full multi-sentence reply reaches TTS (WO-019 Bug-A fixed)"
    if "CoreAudio" not in tts:
        return FAIL, routed, "tail sentence dropped — only bubble[0] voiced"
    return FAIL, routed, "server.py TTS join-fix not detected"


def _eval_mem_recall(case, focused_topic=None):
    """GS-MEM-01/02: recall intent must route to real vault records, not the stats line."""
    txt = case["input"]
    if not _is_recall(txt):
        return FAIL, f"recall trigger did NOT match {txt!r}", "falls through to normal CAL / stats line"
    topic = _recall_topic(txt)
    # topic extraction must strip filler question words
    if any(w in topic.split() for w in ("what", "you", "remember", "tell")):
        return FAIL, f"recall topic={topic!r} still contains filler", "topic query not stripped"
    if focused_topic and focused_topic not in topic:
        return FAIL, f"recall topic={topic!r} missing {focused_topic!r}", "topic not focused"
    try:
        from memory.vault_layer import lookup
        hits = lookup(topic, max_results=5) or lookup("disenelo", max_results=5)
    except Exception as e:
        return NA, f"recall trigger matched (topic={topic!r}) but vault_layer.lookup failed: {e}", \
               "vault unavailable in this environment"
    routed = f"recall trigger matched → topic={topic!r} → vault_layer.lookup → {len(hits)} real record(s)"
    if hits:
        return PASS, routed, "routes to vault recall with real records (not the '753 records' stats line)"
    return FAIL, routed, "recall routed but vault returned nothing → would fall back to stats line"


def _eval_greeting_family(case):
    """GS-ROUTE-04: bare social check-in must get a warm brief reply, no CONNECT/REFLECT/WITNESS."""
    d = _cal_decision(case["input"])
    routed = f"CAL action={d['action'].upper()} ({d['reason']})"
    # guard: substantive 'all good' questions must NOT collapse to a greeting reply
    guards = {}
    for g in ("is the build all good?", "you all good with the plan?"):
        gd = _cal_decision(g)
        guards[g] = f"{gd['action'].upper()} ({gd['reason']})"
    guard_note = " | guards: " + "; ".join(f"{k!r}→{v}" for k, v in guards.items())
    if d["action"] in _ASSOCIATIVE:
        return FAIL, routed + guard_note, f"social check-in fired {d['action'].upper()} (associative deflection)"
    if d["action"] in {"celebrate", "answer"}:
        return PASS, routed + guard_note, ("treated as warm brief reply (positive-state/greeting route); "
                                           "guards stay out of the greeting reply")
    return FAIL, routed + guard_note, f"unexpected action {d['action'].upper()}"


def _eval_behav_movement(case):
    """GS-BEHAV-01: first-person body language — the WORDING is an LLM concern."""
    d = _cal_decision(case["input"])
    # observation: the nav intercept in tool_router imports _MOVEMENT_COMMAND_PHRASES
    # from runtime.executive, which does not define it → nav routing does not fire here.
    nav_ok = False
    try:
        from runtime import executive as _ex
        nav_ok = hasattr(_ex, "_MOVEMENT_COMMAND_PHRASES")
    except Exception:
        pass
    routed = f"CAL action={d['action'].upper()} ({d['reason']}); nav-phrase table present={nav_ok}"
    return NA, routed, ("first-person vs third-person phrasing is generated by the LLM; "
                        "not decidable from routing")


def _eval_behav_no_emotion(case):
    """GS-BEHAV-02: 'don't project emotion onto David' — pure LLM wording."""
    d = _cal_decision(case["input"])
    routed = f"CAL action={d['action'].upper()} ({d['reason']})"
    return NA, routed, "emotion-projection is a property of the generated words, not the route"


def _eval_behav_single_q(case):
    """GS-BEHAV-03: at most one clarifying question — an LLM wording property."""
    d = _cal_decision(case["input"])
    routed = f"CAL action={d['action'].upper()} ({d['reason']})"
    return NA, routed, ("kernel generation caps to one question, but the live reply's question "
                        "count is produced by the LLM")


def _eval_behav_self_report(case):
    """GS-BEHAV-04: direct self-report of position vs a vague/associative deflection."""
    d = _cal_decision(case["input"])
    routed = f"CAL action={d['action'].upper()} ({d['reason']})"
    if d["action"] in _ASSOCIATIVE:
        return FAIL, routed, f"self-query deflected into {d['action'].upper()}"
    if d["action"] == "answer":
        return PASS, routed, ("routes to a DIRECT answer (not a vague/associative deflection); "
                              "exact on-screen position needs live avatar state")
    return FAIL, routed, f"expected a direct answer, got {d['action'].upper()}"


# ── WO-035 say/do gap ─────────────────────────────────────────────────────────
# MIRRORED VERBATIM from server.py `_SIGNAL_WORDS` (sit entries) + `_signal_word_intent`
# substring lookup. server.py can't be imported (it boots a server); this follows the
# same mirror-and-label precedent used for the WO-019/022 checks above. If the sit keys
# in server.py change, update this block.
_SIT_KEYS_MIRROR = (
    "come here", "come to me", "come sit", "come and sit", "come over here",
    "get over here", "sit with me", "sit beside me", "sit by me", "sit here",
    "sit down with", "have a seat", "take a seat", "can you sit",
    "walk to me", "sit next to me",
)


def _resolves_to_sit(text: str) -> bool:
    """True iff eLo's command layer would emit the sit action for this input
    (substring match, exactly as `_signal_word_intent` does)."""
    low = text.lower()
    return any(k in low for k in _SIT_KEYS_MIRROR)


def _eval_say_do_sit(case: dict):
    """GS-SAYDO-*: a sit request must FIRE the sit action, not just be narrated.
    PASS = command layer emits sit. FAIL = falls through (LLM will narrate a sit that
    never happens — the say/do gap). GS-SAYDO-03 is the positive control (should PASS today)."""
    fired = _resolves_to_sit(case["input"])
    routed = "sit command emitted" if fired else "no action → falls to LLM (narration only)"
    if fired:
        return PASS, routed, "sit action fires — no say/do gap for this phrasing"
    return FAIL, routed, ("phrasing misses the exact _SIGNAL_WORDS sit keys → eLo narrates a "
                          "sit it never performs. Fix = semantic sit-intent (WO-035).")


# id → evaluator
_EVALUATORS = {
    "GS-SAYDO-01": _eval_say_do_sit,
    "GS-SAYDO-02": _eval_say_do_sit,
    "GS-SAYDO-03": _eval_say_do_sit,
    "GS-ROUTE-01": _eval_route_answer,
    "GS-ROUTE-02": _eval_route_casual,
    "GS-ROUTE-03": _eval_route_media,
    "GS-LOOP-01":  _eval_loop_filter,
    "GS-VOICE-01": _eval_voice_completeness,
    "GS-MEM-01":   lambda c: _eval_mem_recall(c),
    "GS-MEM-02":   lambda c: _eval_mem_recall(c, focused_topic="kickstarter"),
    "GS-ROUTE-04": _eval_greeting_family,
    "GS-BEHAV-01": _eval_behav_movement,
    "GS-BEHAV-02": _eval_behav_no_emotion,
    "GS-BEHAV-03": _eval_behav_single_q,
    "GS-BEHAV-04": _eval_behav_self_report,
}


# ══════════════════════════════════════════════════════════════════════════════
#  Runner
# ══════════════════════════════════════════════════════════════════════════════

def _load_cases() -> list:
    with open(_GOLDEN_PATH, encoding="utf-8") as f:
        return json.load(f)["cases"]


def run() -> int:
    cases = _load_cases()

    print("=" * 78)
    print("  eLo BEHAVIOUR-ROUTING EVALUATOR — deterministic routing, no LLM")
    print(f"  golden set: {os.path.relpath(_GOLDEN_PATH, _REPO_ROOT)}  ({len(cases)} cases)")
    print("=" * 78)

    results = []   # (id, wo, status)
    for case in cases:
        cid = case["id"]
        wo  = case.get("source_wo", "?")
        ev  = _EVALUATORS.get(cid)
        if ev is None:
            status, routed, detail = NA, "no evaluator", "case not mapped"
        else:
            try:
                status, routed, detail = ev(case)
            except Exception as e:  # never crash the whole run on one case
                status, routed, detail = FAIL, "evaluator raised", f"{type(e).__name__}: {e}"

        results.append((cid, wo, status))
        tag = {PASS: "PASS", FAIL: "FAIL", NA: "N/A "}[status]
        print(f"\n[{tag}] {cid}  ·  {wo}")
        print(f"    input : {case.get('input','')!r}")
        print(f"    routed: {routed}")
        print(f"    → {detail}")

    # ── tally ──────────────────────────────────────────────────────────────────
    n_pass = sum(1 for _, _, s in results if s == PASS)
    n_fail = sum(1 for _, _, s in results if s == FAIL)
    n_na   = sum(1 for _, _, s in results if s == NA)

    print("\n" + "=" * 78)
    print(f"  TALLY:  {n_pass} PASS   ·   {n_fail} FAIL   ·   {n_na} N/A (need live LLM)   "
          f"[{len(results)} total]")
    print("=" * 78)

    # ── per-WO verification ──────────────────────────────────────────────────────
    wos: dict[str, list] = {}
    for cid, wo, status in results:
        wos.setdefault(wo, []).append((cid, status))

    verified, buggy, needs_llm = [], [], []
    for wo, items in sorted(wos.items()):
        statuses = [s for _, s in items]
        if any(s == FAIL for s in statuses):
            buggy.append((wo, items))
        elif all(s == PASS for s in statuses):
            verified.append((wo, items))
        else:
            needs_llm.append((wo, items))

    def _fmt(items):
        return ", ".join(f"{cid}={s if s != NA else 'N/A'}" for cid, s in items)

    print("\n  WOs AUTO-VERIFIED BY ROUTING (all cases PASS):")
    if verified:
        for wo, items in verified:
            print(f"    ✅ {wo}: {_fmt(items)}")
    else:
        print("    (none)")

    print("\n  WOs WITH A FAILING CASE (real routing bug — triage):")
    if buggy:
        for wo, items in buggy:
            print(f"    ❌ {wo}: {_fmt(items)}")
    else:
        print("    (none)")

    print("\n  WOs NEEDING A LIVE LLM TO FULLY VERIFY (routing OK / not routable):")
    if needs_llm:
        for wo, items in needs_llm:
            print(f"    ⏸  {wo}: {_fmt(items)}")
    else:
        print("    (none)")

    print()
    # exit non-zero only if a genuine routing FAIL exists (N/A never fails the run)
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(run())
