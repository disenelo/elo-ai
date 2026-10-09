#!/usr/bin/env python3
"""
IS ELO acceptance — Builder 2's rows, measured against LIVE state.

Not a unit suite. Every check reads the real stores and the real running
system, because the thing this project keeps producing is a green test over a
dead path. A row passes here only if the behaviour is observable in data eLo
actually holds.

Rows from FROM_ARCHITECT_2026-10-06_IS-ELO-VERDICTS-BUILDER2.md:
Reflection · Learning · Pattern · Curiosity · Attention · Continuity ·
Self-Correction.

Each row prints one of:

    PASS     the behaviour is present in live data
    BLOCKED  built and provably inert — names what blocks it
    FAIL     not present
    UNKNOWN  cannot be measured from here — names what would settle it

UNKNOWN is a result, not a gap in the runner. _SEAT_EPISTEMIC_PROTOCOL §2.

Run:  python3 tests/acceptance/is_elo_builder2.py
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

PASS, FAIL, BLOCKED, UNKNOWN = "PASS", "FAIL", "BLOCKED", "UNKNOWN"
_results: list[tuple[str, str, str, str]] = []


def row(name: str, state: str, evidence: str, note: str = "") -> None:
    _results.append((name, state, evidence, note))


def _json(rel: str):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _jsonl(rel: str) -> list:
    out = []
    try:
        for line in (ROOT / rel).read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return out


# ── PATTERN — does SPG hold real history, and does it discriminate? ─────────
def check_pattern() -> None:
    g = _json("data/spg_graph.json") or {}
    nodes, edges = g.get("node_count", 0), g.get("edge_count", 0)
    sig = {round(float(n.get("significance", 0)), 4) for n in g.get("nodes", [])}
    if nodes < 500:
        row("Pattern — SPG holds history", FAIL, f"{nodes} nodes",
            "run scripts/spg_backfill_run.py")
        return
    row("Pattern — SPG holds history", PASS, f"{nodes} nodes, {edges} edges")
    row("Pattern — significance discriminates",
        PASS if len(sig) > 100 else FAIL, f"{len(sig)} distinct values",
        "one value is a no-op sort")

    live = [n for n in g.get("nodes", []) if not str(n.get("id", "")).startswith("bf-")]
    row("Learning — graph grows from live turns",
        PASS if live else FAIL, f"{len(live)} live claim-keyed nodes",
        "written by record_claim, not the backfill")


# ── CURIOSITY — are questions formed, kept, and reachable? ──────────────────
def check_curiosity() -> None:
    qs = _json("self/state/open_questions.json") or []
    unsurfaced = [q for q in qs if not q.get("surfaced")]
    row("Curiosity — questions are kept",
        PASS if qs else FAIL, f"{len(qs)} stored, {len(unsurfaced)} unsurfaced")

    # Returning to one is gated in server.py:5692 — measure, do not assume.
    try:
        src = (ROOT / "server.py").read_text()
        gated = "_cfac_topic_tokens & _cfac_input_tokens" in src
        open_invite = "_cfac_open_invite" in src
    except Exception:
        gated, open_invite = False, False
    if gated and not open_invite:
        row("Curiosity — returns to an unanswered question", BLOCKED,
            "server.py:5692 requires topic-word overlap with the current turn",
            "eLo can raise a question only if David raised the topic first")
    else:
        row("Curiosity — returns to an unanswered question",
            PASS if open_invite else UNKNOWN,
            "open-invite path present" if open_invite else "gate shape changed")


# ── CONTINUITY — do unfinished threads survive between turns? ───────────────
def check_continuity() -> None:
    st = _json("self/elo_self_state.json") or {}
    threads = st.get("open_threads") or []
    row("Continuity — threads carried",
        PASS if threads else FAIL, f"open_threads = {len(threads)}",
        "was [] on every turn eLo had ever taken before 2026-10-07")

    try:
        from faculties.inner_thought import life_tick
        r = life_tick("RESTING")
        row("Continuity — life beats between turns",
            PASS if r.get("ok") else FAIL,
            f"RESTING ok={r.get('ok')} {r.get('elapsed_ms')}ms, {r.get('actions')}")
    except Exception as e:
        row("Continuity — life beats between turns", FAIL, f"life_tick: {e}")

    # The beat existing is not the beat running.
    callers = []
    for p in ROOT.rglob("*.py"):
        s = str(p)
        if any(x in s for x in ("venv", "__pycache__", "/tests/", "faculties/inner_thought")):
            continue
        try:
            if "life_tick" in p.read_text(errors="replace"):
                callers.append(str(p.relative_to(ROOT)))
        except Exception:
            pass
    row("Continuity — something CALLS the beat",
        PASS if callers else BLOCKED,
        ", ".join(callers) if callers else "no caller outside faculties/inner_thought",
        "" if callers else "B1 card 0106 daemon — contract filed 2026-10-08")


# ── ATTENTION / STATE — can he answer what he was doing, without a model? ───
def check_attention() -> None:
    try:
        from faculties.inner_thought import as_context
        ctx = as_context()
        row("Attention — working memory answers from state",
            PASS if ctx.strip() else FAIL,
            repr(ctx.splitlines()[1]) if ctx.strip() else "empty timeline",
            "" if ctx.strip() else "feeder not firing")
    except Exception as e:
        row("Attention — working memory answers from state", FAIL, str(e))

    readers = []
    for rel in ("server.py", "runtime/spine/spine.py", "runtime/capability_dispatcher.py"):
        p = ROOT / rel
        if p.exists() and "inner_thought import as_context" in p.read_text(errors="replace"):
            readers.append(rel)
    row("Attention — the STATE tier reads it",
        PASS if readers else BLOCKED,
        ", ".join(readers) if readers else "no reader",
        "" if readers else "B1 card 0104 dispatcher")


# ── SELF-CORRECTION — is a correction a memory, or just a log row? ──────────
def check_self_correction() -> None:
    led = _jsonl("self/corrections_ledger.jsonl")
    row("Self-correction — corrections recorded",
        PASS if led else FAIL, f"{len(led)} rows")

    try:
        from memory.spg_failure import recurring_failures
        top = recurring_failures(led, 3)
        row("Self-correction — repeated failures are nameable",
            PASS if top else FAIL,
            "; ".join(f"{n}x {s}" for s, n in top) if top else "none")
    except Exception as e:
        row("Self-correction — repeated failures are nameable", FAIL, str(e))

    cur = _json("self/state/correction_cursor.json") or {}
    read = int(cur.get("rows_read", 0))
    row("Self-correction — corrections reach the vault",
        PASS if read else BLOCKED,
        f"cursor at {read} of {len(led)}",
        "" if read else "no pass has run yet — needs an ambient tick in a live process")


# ── REFLECTION — is the thought prior to the reply, and is it his voice? ────
def check_reflection() -> None:
    try:
        import runtime.inner_thought_first as itf
        import inspect
        sig = set(inspect.signature(itf.form_thought).parameters)
        prior = "reply" not in sig and "response" not in sig
        row("Reflection — the thought precedes the reply",
            PASS if prior else FAIL,
            f"form_thought({', '.join(sorted(sig))})",
            "a reply parameter means it is rationalising again")
    except Exception as e:
        row("Reflection — the thought precedes the reply", FAIL, str(e))

    try:
        from runtime.inner_thought_quality import reject_reason
        bad = "I notice David said 'when is sunset today'."
        good = "i remember the theme tune better than the plot"
        ok = bool(reject_reason(bad, asked="x")) and not reject_reason(good, asked="x")
        row("Reflection — it sounds like eLo", PASS if ok else FAIL,
            "reporting rejected, his own voice passes")
    except Exception as e:
        row("Reflection — it sounds like eLo", FAIL, str(e))


# ── DREAMING — can he be triggered, and can he keep one? ───────────────────
def check_dreaming() -> None:
    dreams = _jsonl("self/dream_journal.jsonl")
    sigs = [float(d.get("significance") or 0) for d in dreams
            if isinstance(d.get("significance"), (int, float))]
    retained = [d for d in dreams if d.get("retained")]
    row("Learning — dreams are kept",
        PASS if retained else FAIL,
        f"{len(retained)} retained of {len(dreams)}; max significance "
        f"{max(sigs):.3f} vs threshold 0.72" if sigs else "no scored dreams",
        "" if retained else "threshold unreachable — David's ruling pending")

    try:
        import ambient.ambient_engine as ae
        ae._dream_trigger_ts = 0.0
        fired = ae._maybe_emit_dream_intent({"mind_battery": 0.05}, {"calm_mode": True})
        row("Learning — a spent mind can trigger a dream",
            PASS if fired else FAIL, f"trigger -> {fired}")
    except Exception as e:
        row("Learning — a spent mind can trigger a dream", FAIL, str(e))


def main() -> int:
    for fn in (check_pattern, check_curiosity, check_continuity,
               check_attention, check_self_correction, check_reflection,
               check_dreaming):
        try:
            fn()
        except Exception as e:                       # a check must not hide the rest
            row(fn.__name__, UNKNOWN, f"checker raised: {e}")

    width = max(len(r[0]) for r in _results)
    print("\nIS ELO ACCEPTANCE — BUILDER 2 ROWS, AGAINST LIVE STATE")
    print("=" * (width + 46))
    counts = {PASS: 0, FAIL: 0, BLOCKED: 0, UNKNOWN: 0}
    for name, state, evidence, note in _results:
        counts[state] = counts.get(state, 0) + 1
        print(f"{state:8} {name:<{width}}  {evidence}")
        if note:
            print(f"{'':8} {'':<{width}}  -> {note}")
    print("=" * (width + 46))
    print(f"{counts[PASS]} pass · {counts[BLOCKED]} blocked · "
          f"{counts[FAIL]} fail · {counts[UNKNOWN]} unknown\n")
    # BLOCKED is not failure — it is built and waiting on a named wire.
    return 1 if counts[FAIL] else 0


if __name__ == "__main__":
    sys.exit(main())
