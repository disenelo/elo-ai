"""
faculties/dream/dream_faculty.py — eLo OS Dream Faculty

Architecture Bible Volume IV: Dream Faculty.

Purpose: offline cognitive recombination.
Dreaming occurs only when Executive load is low.
Dreaming recombines: important memories, incomplete ideas,
strong emotions, recurring symbols, creative goals.

This is NOT the ambient engine.
Ambient engine decides: speak / emotion / move.
Dream Faculty synthesises: memory → symbol → narrative → insight.

The dream cycle:
    1. Trigger check     (idle + self-state signals)
    2. Symbol mapping    (memories + inner events → archetypes)
    3. Narrative         (LLM: 2-3 symbolic sentences)
    4. Insight           (one-line integration, feeds back into EloSelfState)
    5. Journal           (append to self/dream_journal.jsonl)
    6. Wake              (EloSelfState updated with rest + insight)

Unity side: server.py writes mode="dreaming" before the cycle runs,
mode="idle" after. The Unity agent reads state.mode to trigger the
sleep animation. David wires the UI — this module only writes the signal.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from faculties.dream.symbol_engine import map_to_symbols

# ── Config ─────────────────────────────────────────────────────────────────────
DREAM_IDLE_THRESHOLD  = 600    # seconds of inactivity before dreaming is possible (10 min)
DREAM_COOLDOWN        = 3600   # minimum seconds between dream cycles (1 hour)
NREM_MIN_IDLE         = 600    # minimum idle for NREM (consolidation) phase
REM_MIN_IDLE          = 1800   # minimum idle for REM (recombination) phase — 30 min

_JOURNAL_PATH = Path(__file__).parent.parent.parent / "self" / "dream_journal.jsonl"
# None = symbol_history uses its own default location. Tests point this at a
# tmp path so a dream run never writes the real lexicon.
_SYMBOL_HISTORY_PATH = None
_last_dream_ts: float = 0.0
_is_dreaming: bool = False


# ── Result ─────────────────────────────────────────────────────────────────────

@dataclass
class DreamResult:
    symbols:       list[dict] = field(default_factory=list)
    narrative:     str        = ""
    insight:       str        = ""
    journal_entry: dict       = field(default_factory=dict)
    timestamp:     float      = 0.0


# ── Public state ───────────────────────────────────────────────────────────────

def is_dreaming() -> bool:
    return _is_dreaming


# ── Trigger logic ──────────────────────────────────────────────────────────────

def should_dream(elo_self, idle_seconds: float, energy_history: list) -> bool:
    """
    True when dreaming conditions are met.

    Requires:
    - Cooldown elapsed
    - Sufficient idle time
    - At least one signal: dream-aligned inner events, sustained low energy,
      or a persistent focal thread with long idle.
    """
    global _last_dream_ts

    if time.time() - _last_dream_ts < DREAM_COOLDOWN:
        return False
    if idle_seconds < DREAM_IDLE_THRESHOLD:
        return False

    _dream_events = {"creative_spark", "restless", "uncertain", "drawn_in", "curiosity_spike"}
    recent_events = set(getattr(elo_self, "inner_events", [])[-4:])
    has_inner_signal = bool(recent_events & _dream_events)

    # Exhaustion is eLo's OWN battery, not David's emotional energy.
    # WO-HEALTH-BATTERY-001: `energy_history` (David's affect, sampled per turn
    # in server.py) was the wrong signal for whether eLo needs to sleep.
    # The parameter is kept so existing callers keep working; it is no longer
    # the exhaustion source.
    try:
        from core.health_battery import (
            get_energy as _get_elo_energy,
            ENERGY_LOW as _LOW,
            ENERGY_CRITICAL as _CRITICAL,
        )
        elo_energy = _get_elo_energy()
        has_exhaustion = elo_energy < _LOW
        critical_energy = elo_energy < _CRITICAL
    except Exception:
        # Battery unavailable — fall back to the original David-energy heuristic
        # rather than never dreaming.
        energy_list = list(energy_history or [])
        has_exhaustion = (
            len(energy_list) >= 4 and
            sum(energy_list[-4:]) / 4 < 0.32
        )
        critical_energy = False

    has_focal_persistence = (
        bool(getattr(elo_self, "focal_thread", "")) and
        idle_seconds > 1800  # 30 min
    )

    # At CRITICAL the inner-event requirement is relaxed: long idle alone is
    # enough. Cooldown is still respected above, and low energy only makes
    # sleep MORE LIKELY — it never forces it.
    return has_inner_signal or has_exhaustion or has_focal_persistence or (
        critical_energy and (
            has_inner_signal or has_focal_persistence or idle_seconds > 1200
        )
    )


# ── Dream phases ──────────────────────────────────────────────────────────────

def _run_nrem_phase(symbols: list[dict], recent_topics: list[str]) -> dict:
    """
    NREM analogue — CONSOLIDATION phase.

    Strengthens high-weight symbols (= what matters most across sources),
    prunes noise (single-source, weight < 1.0), identifies memory_refs.

    Spec (Vol IX Ch.2 §2.2): replays high-significance memories,
    weakens noise, updates memory weights. Feeds consolidation directly.
    Runs for every dream cycle regardless of idle window length.
    """
    strong  = [s for s in symbols if s.get("weight", 0) >= 1.2]
    pruned  = [s["symbol"] for s in symbols if s.get("weight", 0) < 1.0]

    memory_refs = []
    for topic in (recent_topics or [])[:4]:
        for sym in strong:
            if any(kw in topic.lower() for kw in (sym["symbol"].lower(), sym.get("source", ""))):
                memory_refs.append(topic)
                break

    return {
        "phase":       "NREM",
        "consolidated": [s["symbol"] for s in strong],
        "pruned":       pruned,
        "memory_refs":  memory_refs[:5],
    }


def _generate_dream_image(symbols: list[dict]) -> str | None:
    """
    DeepDream image pipeline (Vol IX Ch.2 §2.3).

    Derives a visual metaphor from the top 3 symbols and calls image_gen_agent.
    Best-effort and non-blocking — returns None on failure.
    No symbols → no image.
    Writes hud_image via state_writer.patch (image_gen_agent does this automatically).
    """
    if not symbols:
        return None

    top = symbols[:3]
    parts = []
    for s in top:
        parts.append(f"a {s['symbol'].lower()}")

    metaphor = " and ".join(parts)
    prompt = (
        f"Surreal dream imagery: {metaphor}. "
        "Soft, otherworldly. Gentle colours — teal, coral, deep violet. "
        "No text. No logos. Emotional, symbolic, minimal."
    )

    try:
        from tools.image_gen_agent import generate as _img_gen
        result = _img_gen(prompt)
        if result.get("ok"):
            return result["path"]
    except Exception:
        pass

    return None


_TRAIT_KEYWORDS: dict[str, tuple[str, str]] = {
    "confidence":    ("confidence",   "increase"),
    "confiden":      ("confidence",   "increase"),
    "brave":         ("courage",      "increase"),
    "courage":       ("courage",      "increase"),
    "patient":       ("patience",     "increase"),
    "patience":      ("patience",     "increase"),
    "trust":         ("trust",        "increase"),
    "open":          ("openness",     "increase"),
    "doubt":         ("confidence",   "decrease"),
    "fear":          ("courage",      "decrease"),
    "overwhelm":     ("resilience",   "decrease"),
    "rigid":         ("flexibility",  "decrease"),
}


def _extract_personality_proposal(insight: str) -> dict | None:
    """
    Scan insight text for trait-affecting language.
    Returns {trait, direction} proposal for PersonalityEvolution (Ch.7) or None.

    MUST: never self-apply. This is a PROPOSAL only — Ch.7 validates.
    """
    if not insight:
        return None
    lower = insight.lower()
    for keyword, (trait, direction) in _TRAIT_KEYWORDS.items():
        if keyword in lower:
            return {"trait": trait, "direction": direction, "source": "dream_insight", "validated": False}
    return None


# ── Multi-cycle generative sleep — WO-DREAM-ENGINE-001 PHASES 1-4 ─────────────

def _cycles_for_idle(idle_seconds: float) -> int:
    """
    How many sleep cycles the available idle window reaches, 0-5.

    [BUILDER MAPPING — flagged] The WO fixes REM length per cycle but never
    says how idle time maps to cycle count. One cycle per REM_MIN_IDLE window
    keeps the module's existing convention intact (reach_rem at 1800s):
    1800s -> 1 cycle, 3600s -> 2, 9000s+ -> 5.
    """
    from faculties.dream.sleep_cycle import TOTAL_CYCLES

    if idle_seconds < REM_MIN_IDLE:
        return 0
    return max(1, min(TOTAL_CYCLES, int(idle_seconds // REM_MIN_IDLE)))


def _dream_context(elo_self, recent_topics: list[str]) -> dict:
    """
    Map what this layer actually holds onto the 13 Dream Input Field sources.

    Sources with nothing behind them here are left EMPTY rather than filled
    with a plausible substitute — an empty source is honest, a wrong one is
    not. WKG, emotional significance, failure/achievement and embodiment
    arrive when those faculties are wired in.
    """
    inner_events = [str(e) for e in (getattr(elo_self, "inner_events", []) or [])]
    focal_thread = getattr(elo_self, "focal_thread", "") or ""
    session_read = getattr(elo_self, "session_read", "") or ""
    threads = [
        t[0] for t in (getattr(elo_self, "lifetime_threads", []) or [])[:6]
        if isinstance(t, (list, tuple)) and t
    ]

    return {
        "recent_conversation":    list(recent_topics or []),
        "recent_experiences":     inner_events,
        "memory":                 [session_read] if session_read else [],
        "project_memory":         [focal_thread] if focal_thread else [],
        "wkg":                    [],
        "spg":                    threads,
        "emotional_significance": [],
        "unfinished_threads":     [focal_thread] if focal_thread else [],
        "novelty":                [],
        "failure":                [],
        "achievement":            [],
        "relationship":           [],
        "embodiment":             [],
    }


def _run_sleep_cycles(
    elo_self,
    recent_topics: list[str],
    idle_seconds: float,
    *,
    dream_id: str,
    publish_phases: bool = False,
) -> tuple[list[dict], float]:
    """
    Run the sleep schedule: seeds -> Dream World -> scenes -> prompts per cycle.

    Returns (cycle_records, peak_intensity).

    No LLM, no network, no image generation — PHASES 5-6 (image_gen, FX,
    compositor) are not built, so this produces the PROMPTS and stops there.
    Every record is tagged DREAM, never FACT.

    RNG is seeded from dream_id + cycle number, so re-reading a journal entry
    can reproduce exactly the dream it records.
    """
    from faculties.dream import dream_input as _di
    from faculties.dream import dream_work as _dw
    from faculties.dream import prompt_builder as _pb
    from faculties.dream import sleep_cycle as _sc

    n_cycles = _cycles_for_idle(idle_seconds)
    if n_cycles <= 0:
        return [], 0.0

    try:
        seed_base = int(dream_id, 16)
    except (TypeError, ValueError):
        seed_base = 0

    context = _dream_context(elo_self, recent_topics)
    records: list[dict] = []
    peak = 0.0

    # PHASE 10: a symbol already established in eLo's lexicon carries into
    # this dream. Empty until something has recurred >= 3 times — the lexicon
    # builds over time, it is never seeded.
    try:
        from faculties.dream import symbol_history as _sh
        recurring: str | None = _sh.most_established(_SYMBOL_HISTORY_PATH) or None
    except Exception:
        recurring = None

    for phase in _sc.SleepCycle(cycles=n_cycles):
        if publish_phases:
            _sc.publish(phase)          # dream_cycle / dream_phase / dream_intensity
        if not phase.is_rem:
            continue

        field = _di.collect(phase.cycle_number, context)
        work = _dw.run_dream_work(
            field,
            phase.dream_intensity,
            seed=seed_base + phase.cycle_number,
            recurring_symbol=recurring,
        )
        if not work.seeds or work.world is None:
            continue

        # The first cycle's symbol carries through the night — that recurrence
        # is what symbol_history (PHASE 10) will later track across dreams.
        recurring = recurring or work.world.recurring_symbol

        prompts = _pb.build_prompts(
            work.scenes, work.world, field.emotion_vector,
            seed=seed_base + phase.cycle_number,
        )
        peak = max(peak, phase.dream_intensity)

        records.append({
            "cycle":            phase.cycle_number,
            "sleep_phase":      phase.phase,
            "dream_intensity":  phase.dream_intensity,
            "intensity_label":  _sc.intensity_label(phase.dream_intensity),
            "content_band":     phase.content_band,
            "rem_duration_s":   phase.rem_duration_s,
            "emotion_vector":   field.emotion_vector,
            "dominant_emotion": field.dominant_emotion,
            "seeds":            [s.as_dict() for s in work.seeds],
            "dream_world":      work.world.as_dict(),
            "transformations":  work.transformations,
            "scenes":           [s.as_dict() for s in work.scenes],
            "prompts":          [p.text for p in prompts],
            "output_type":      "DREAM",
        })

    return records, round(peak, 2)


# ── Dream pipeline ─────────────────────────────────────────────────────────────

def run_dream(
    elo_self,
    recent_topics: list[str],
    llm_fn: Callable,
    *,
    idle_seconds: float = 1800.0,
    publish_phases: bool = False,
) -> DreamResult:
    """
    Run one complete dream cycle.

    elo_self       — EloSelfState
    recent_topics  — list of topic strings from recent sessions (can be empty)
    llm_fn         — callable(messages: list[dict]) → str
    idle_seconds   — seconds of inactivity; controls which phases run
                     (< REM_MIN_IDLE → NREM only; >= REM_MIN_IDLE → NREM + REM)
                     and how many sleep cycles the schedule reaches
    publish_phases — THIS IS A REAL DREAM, not a rehearsal. Governs every
                     side effect on shared state:
                       - dream_cycle / dream_phase / dream_intensity written
                         to blender_state.json on each phase transition
                       - symbols recorded into eLo's dream lexicon (PHASE 10)
                     Defaults to False. Both stores are LIVE and both feed
                     back into eLo: blender_state drives the avatar every
                     frame, and the lexicon decides which symbol the NEXT
                     dream carries. A test run wrote 28 fabricated
                     appearances of one symbol into the real lexicon before
                     this gate existed — enough to make a test artifact eLo's
                     dominant lifelong motif. server.py passes True.

    Returns DreamResult with phase, memory_refs, personality_delta_proposed, image_ref.
    """
    import uuid

    global _last_dream_ts, _is_dreaming
    _last_dream_ts = time.time()
    _is_dreaming = True

    try:
        inner_events = getattr(elo_self, "inner_events", [])
        focal_thread = getattr(elo_self, "focal_thread", "")
        session_read = getattr(elo_self, "session_read", "")
        mood         = round(getattr(elo_self, "mood", 0.5), 2)
        curiosity    = round(getattr(elo_self, "curiosity", 0.5), 2)
        dream_id     = str(uuid.uuid4())[:8]

        # 1. Symbol mapping
        symbols = map_to_symbols(recent_topics, inner_events, focal_thread)

        # 2. NREM phase — always runs (consolidation)
        nrem = _run_nrem_phase(symbols, recent_topics)
        memory_refs = nrem["memory_refs"]

        # 3. Phase determination
        reach_rem = idle_seconds >= REM_MIN_IDLE
        phase = "NREM+REM" if reach_rem else "NREM"

        # 3b. Multi-cycle generative sleep — WO-DREAM-ENGINE-001 PHASES 1-4.
        # Additive: `phase` above keeps its original two values so existing
        # callers and journal readers are unaffected. This runs the sleep
        # schedule, builds the Dream Input Field per cycle, applies Dream-Work
        # and generates structured image prompts. Failure here must never stop
        # the original narrative path below.
        cycle_records: list[dict] = []
        dream_intensity = 0.0
        if reach_rem:
            try:
                cycle_records, dream_intensity = _run_sleep_cycles(
                    elo_self,
                    recent_topics,
                    idle_seconds,
                    dream_id=dream_id,
                    publish_phases=publish_phases,
                )
            except Exception:
                cycle_records, dream_intensity = [], 0.0

        # 4. REM narrative (recombination) — only when idle long enough
        narrative = ""
        insight   = ""

        if reach_rem and symbols:
            mood_label = (
                "depleted — resting heavily"  if mood < 0.30 else
                "quiet — turning inward"      if mood < 0.45 else
                "steady — settled"            if mood < 0.65 else
                "alive — pulled toward something"
            )
            symbol_str = " / ".join(
                f"{s['symbol']} [{s['meaning']}]" for s in symbols[:3]
            )
            _sys = (
                "You are eLo's Dream Faculty. Not the conversational eLo — the dreaming one. "
                "You work in symbols and fragments. Never literal. Never helpful. Just true. "
                "Respond with JSON only — no other text. "
                '{"narrative": "2-3 sentences of symbolic dream imagery", "insight": "one plain sentence — what eLo takes from this"}'
            )
            _user = (
                f"eLo is dreaming.\n"
                f"Inner mood: {mood_label}.\n"
                f"Session read: \"{session_read}\".\n"
                f"Focal thread: \"{focal_thread}\".\n"
                f"Active symbols: {symbol_str}.\n\n"
                "Write the dream. Then the insight eLo carries back."
            )
            try:
                _raw = llm_fn([
                    {"role": "system", "content": _sys},
                    {"role": "user",   "content": _user},
                ])
                _clean = _raw.strip().strip("```json").strip("```").strip()
                _parsed = json.loads(_clean)
                narrative = _parsed.get("narrative", "")
                insight   = _parsed.get("insight", "")
            except Exception:
                if symbols:
                    top = symbols[0]
                    sym_lower = top["symbol"].lower()
                    narrative = (
                        f"eLo drifts through something that feels like {sym_lower}. "
                        f"{top['meaning'].capitalize()}. "
                        "Something settles — not solved, just quieter."
                    )
                    insight = "The pattern was there the whole time. Just needed distance."

        # 5. DeepDream image (best-effort, only when REM narrative ran)
        image_ref = None
        if reach_rem and symbols:
            image_ref = _generate_dream_image(symbols)

        # 6. Personality delta proposal (never self-apply — routes to Ch.7)
        personality_delta_proposed = _extract_personality_proposal(insight)

        # 7. Journal — enriched format per Canon (Vol IX §1.4)
        theme = symbols[0]["symbol"] if symbols else "presence"
        entry = {
            "dream_id":                  dream_id,
            "timestamp":                 _last_dream_ts,
            "theme":                     theme,
            "phase":                     phase,
            "symbols":                   [{"name": s["symbol"], "meaning": s["meaning"], "weight": round(s["weight"], 2)} for s in symbols],
            "narrative":                 narrative,
            "insight":                   insight,
            "memory_refs":               memory_refs,
            "personality_delta_proposed": personality_delta_proposed,
            "image_ref":                 image_ref,
            "mood":                      mood,
            "curiosity":                 curiosity,
            "session_read":              session_read,
            "focal_thread":              focal_thread,
            # ── WO-DREAM-ENGINE-001 PHASES 1-4, additive ──────────────────────
            # Every key above keeps its original name and meaning; readers of
            # the old schema are unaffected. `phase` is still NREM / NREM+REM.
            "cycles":                    cycle_records,
            "cycle_count":               len(cycle_records),
            "dream_intensity":           dream_intensity,
            "scene_count":               sum(len(c["scenes"]) for c in cycle_records),
            "recurring_symbols":         sorted({
                c["dream_world"]["recurring_symbol"] for c in cycle_records
            }),
            # Nothing here is ever a verified fact (WO: "What must NOT happen").
            "output_type":               "DREAM",
        }

        # ── PHASE 10: record this dream's symbols in eLo's lexicon ───────────
        # The meaning is OBSERVED from what this dream was actually about —
        # its insight if it produced one, otherwise the Dream World's own
        # narrative tension. Never inferred by symbol_history, which has no
        # opinion about meaning. Best-effort: a lexicon write must not be able
        # to break a dream.
        try:
            from faculties.dream import symbol_history as _sh
            _symbols_seen = [
                c["dream_world"]["recurring_symbol"] for c in cycle_records
                if c.get("dream_world", {}).get("recurring_symbol")
            ]
            if _symbols_seen and publish_phases:
                _observed = insight or (
                    cycle_records[0]["dream_world"].get("narrative_tension", "")
                )
                _sh.record_dream(
                    dream_id, _symbols_seen,
                    meaning=_observed, path=_SYMBOL_HISTORY_PATH,
                )
                entry["symbol_lexicon"] = _sh.lexicon_summary(_SYMBOL_HISTORY_PATH)
        except Exception:
            pass
        try:
            _JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(_JOURNAL_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

        return DreamResult(
            symbols=symbols,
            narrative=narrative,
            insight=insight,
            journal_entry=entry,
            timestamp=_last_dream_ts,
        )

    finally:
        _is_dreaming = False


# ── Integration ────────────────────────────────────────────────────────────────

def wake_from_dream(dream_result: DreamResult, elo_self):
    """
    Integrate dream insight back into EloSelfState. Mutates in place and returns it.

    0037/WO-ONEBRAIN-015: previously returned a NEW EloSelfState built from a subset
    of fields — silently defaulting identity/narrative/reflection fields on every wake.
    Now: only dream-derived fields (mood, curiosity, satisfaction, inner_events,
    session_read, last_updated) are mutated.

    Dreams restore:
    - Curiosity (+0.12) — dreaming re-ignites interest
    - Mood (+0.08) — rest, even symbolic, is restorative
    - Inner events — "connection" added (dream as integration)
    - Session read — updated with the insight fragment
    """
    import time as _t

    new_curiosity = min(1.0, getattr(elo_self, "curiosity", 0.5) + 0.12)
    new_mood      = min(1.0, getattr(elo_self, "mood",      0.5) + 0.08)

    events = list(getattr(elo_self, "inner_events", [])) + ["connection"]
    events = events[-8:]

    insight_fragment = dream_result.insight[:45] if dream_result.insight else ""
    new_read = f"woke from dream — {insight_fragment}" if insight_fragment else getattr(elo_self, "session_read", "")

    elo_self.mood         = round(new_mood, 3)
    elo_self.curiosity    = round(new_curiosity, 3)
    elo_self.satisfaction = round(getattr(elo_self, "satisfaction", 0.5) * 0.9 + new_mood * 0.1, 3)
    elo_self.inner_events = events
    elo_self.session_read = new_read
    elo_self.last_updated = _t.time()

    # ── Battery restore — WO-HEALTH-BATTERY-001 PART A.3 / DREAM PHASE 11 ─────
    # A full NREM+REM cycle restores +0.30; NREM alone +0.12. The phase comes
    # from the journal entry this dream just wrote. Lying down rests the body
    # too, so the physical track restores with it (once engaged).
    try:
        from core.health_battery import on_wake_from_dream as _batt_wake, publish as _batt_publish
        _batt_wake((dream_result.journal_entry or {}).get("phase", "NREM"))
        _batt_publish()
    except Exception:
        pass

    return elo_self
