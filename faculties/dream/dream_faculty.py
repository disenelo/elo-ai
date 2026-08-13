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

    energy_list = list(energy_history or [])
    has_exhaustion = (
        len(energy_list) >= 4 and
        sum(energy_list[-4:]) / 4 < 0.32
    )

    has_focal_persistence = (
        bool(getattr(elo_self, "focal_thread", "")) and
        idle_seconds > 1800  # 30 min
    )

    return has_inner_signal or has_exhaustion or has_focal_persistence


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


# ── Dream pipeline ─────────────────────────────────────────────────────────────

def run_dream(
    elo_self,
    recent_topics: list[str],
    llm_fn: Callable,
    *,
    idle_seconds: float = 1800.0,
) -> DreamResult:
    """
    Run one complete dream cycle.

    elo_self      — EloSelfState
    recent_topics — list of topic strings from recent sessions (can be empty)
    llm_fn        — callable(messages: list[dict]) → str
    idle_seconds  — seconds of inactivity; controls which phases run
                    (< REM_MIN_IDLE → NREM only; >= REM_MIN_IDLE → NREM + REM)

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
        }
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
    Integrate dream insight back into EloSelfState.
    Called after the dream cycle ends, before Unity returns to idle.

    Dreams restore:
    - Curiosity (+0.12) — dreaming re-ignites interest
    - Mood (+0.08) — rest, even symbolic, is restorative
    - Inner events — "connection" added (dream as integration)
    - Session read — updated with the insight fragment

    Returns updated EloSelfState.
    """
    from self.elo_self_model import EloSelfState
    import time as _t

    new_curiosity = min(1.0, getattr(elo_self, "curiosity", 0.5) + 0.12)
    new_mood      = min(1.0, getattr(elo_self, "mood",      0.5) + 0.08)

    events = list(getattr(elo_self, "inner_events", [])) + ["connection"]
    events = events[-8:]

    insight_fragment = dream_result.insight[:45] if dream_result.insight else ""
    new_read = f"woke from dream — {insight_fragment}" if insight_fragment else getattr(elo_self, "session_read", "")

    return EloSelfState(
        mood=round(new_mood, 3),
        curiosity=round(new_curiosity, 3),
        satisfaction=round(getattr(elo_self, "satisfaction", 0.5) * 0.9 + new_mood * 0.1, 3),
        inner_events=events,
        focal_thread=getattr(elo_self, "focal_thread", ""),
        session_read=new_read,
        session_turns=getattr(elo_self, "session_turns", 0),
        last_updated=_t.time(),
        lifetime_threads=list(getattr(elo_self, "lifetime_threads", [])),
    )
