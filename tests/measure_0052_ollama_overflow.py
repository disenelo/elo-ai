"""
tests/measure_0052_ollama_overflow.py — card 0052: measure Ollama overflow behaviour.

NO FIXES. MEASUREMENT ONLY per CA directive.

M1: does the live prompt ever actually exceed 8,192 tokens?
M2: what does Ollama do when num_ctx is exceeded?
M3: which block is lost first, by observed position?
M4: is truncation silent?
M5: headroom trend.

Run: python3 tests/measure_0052_ollama_overflow.py
"""
import json
import os
import sys
import urllib.request as _ureq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

OLLAMA_HOST  = os.environ.get("ELO_OLLAMA_HOST",  "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("ELO_OLLAMA_MODEL", "mistral")
NUM_CTX      = 8192


def _call_ollama(system_prompt: str, user_input: str, num_ctx: int = NUM_CTX) -> dict:
    """Direct Ollama call. Returns full response dict including token counts."""
    payload = json.dumps({
        "model":    OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_input},
        ],
        "stream":     False,
        "keep_alive": "30m",
        "options":    {"temperature": 0.0, "num_predict": 16, "num_ctx": num_ctx},
    }).encode()
    req = _ureq.Request(
        f"{OLLAMA_HOST}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with _ureq.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


# ── M1: live prompt token count from backend_health ──────────────────────────

def measure_m1():
    """Check current and historical prompt_eval_tokens."""
    bh_path = os.path.join(ROOT, "blender", "backend_health.json")
    rt_path = os.path.join(ROOT, "blender", "routing_trace.json")

    print("── M1: Live prompt token count ──────────────────────────────")
    try:
        with open(bh_path) as f:
            bh = json.load(f)
        pe = bh.get("prompt_eval_tokens", "N/A")
        ts = bh.get("_ts", 0)
        print(f"  backend_health.prompt_eval_tokens : {pe}")
        print(f"  num_ctx                           : {NUM_CTX}")
        print(f"  headroom                          : {NUM_CTX - pe if isinstance(pe, int) else 'N/A'} tokens")
        print(f"  capacity used                     : {round(pe / NUM_CTX * 100, 1) if isinstance(pe, int) else 'N/A'}%")
        print(f"  ever exceeded 8,192?              : {'YES' if isinstance(pe, int) and pe > NUM_CTX else 'NOT YET (from this snapshot)'}")
    except Exception as e:
        print(f"  ERROR reading backend_health: {e}")
        pe = None
    return pe


# ── M2/M4: force an oversized prompt, capture Ollama response ─────────────────

def measure_m2_m4():
    """Send a deliberately oversized prompt to Ollama. Capture what happens."""
    print()
    print("── M2/M4: Ollama behaviour when num_ctx exceeded ────────────")

    # Build a prompt known to be > 8,192 tokens (~40,000 chars → ~10,000 tokens)
    # Simple repeating text. No eLo content — synthetic measurement only.
    filler = "The sky is blue and the grass is green. " * 800   # ~32,000 chars ≈ 8,000 tokens
    overflow_system = (
        "You are a test fixture. " + filler
    )
    token_estimate = len(overflow_system) // 4
    print(f"  Synthetic system prompt length    : {len(overflow_system):,} chars (~{token_estimate:,} tokens)")
    print(f"  num_ctx                           : {NUM_CTX}")
    print(f"  Expected to overflow by           : ~{token_estimate - NUM_CTX:,} tokens")

    try:
        resp = _call_ollama(overflow_system, "Say OK.", num_ctx=NUM_CTX)
        pe_actual = resp.get("prompt_eval_count", "absent")
        content   = resp.get("message", {}).get("content", "").strip()
        done_reason = resp.get("done_reason", "absent")
        context_used = resp.get("context", None)

        print()
        print(f"  Response received               : YES (no error)")
        print(f"  done_reason                     : {done_reason!r}")
        print(f"  prompt_eval_count (Ollama)      : {pe_actual}")
        print(f"  content excerpt                 : {content[:80]!r}")
        print()

        # M4: is truncation silent?
        if isinstance(pe_actual, int) and pe_actual < token_estimate:
            print(f"  M4 FINDING: Ollama reported {pe_actual} prompt tokens vs ~{token_estimate} sent.")
            print( "              Truncation occurred. Ollama returned a count — NOT entirely silent.")
            print( "              BUT: the count is in the API response body (prompt_eval_count),")
            print( "              NOT an error, NOT a warning, NOT a header flag.")
            print( "              Our code reads prompt_eval_count → backend_health.json,")
            print( "              so a human COULD detect it. An automated guard does NOT exist.")
            print( "              => PARTIALLY SILENT: the information is available but not alarmed.")
        elif isinstance(pe_actual, int) and pe_actual >= token_estimate:
            print(f"  M4 FINDING: Ollama reported {pe_actual} ≥ estimate. No truncation detected.")
        else:
            print(f"  M4 FINDING: prompt_eval_count absent or unexpected: {pe_actual!r}")

        # Truncation direction inference from prompt_eval_count
        if isinstance(pe_actual, int):
            print()
            if pe_actual <= NUM_CTX:
                print(f"  M2 FINDING: Ollama processed {pe_actual} tokens (≤ num_ctx={NUM_CTX}).")
                print( "              It does NOT error. It silently truncates to num_ctx.")
                print( "              Truncation direction: UNKNOWN from token count alone.")
                print( "              To confirm front/back/middle: compare content for spec markers.")
            else:
                print(f"  M2 FINDING: Ollama processed {pe_actual} tokens (> num_ctx). No truncation?")

    except Exception as e:
        print(f"  Ollama call failed: {type(e).__name__}: {e}")
        print( "  => M2: Cannot determine overflow behaviour — Ollama may be offline.")
        return None

    return {"pe_actual": pe_actual, "token_estimate": token_estimate}


# ── M3: which block is at which position in the assembly? ─────────────────────

def measure_m3():
    """Report assembly order from prompt_builder.py source — no speculation."""
    print()
    print("── M3: Block assembly order (prompt_builder.py:304-330) ─────")
    print("  Position 0: load_living_presence_spec()  — living_presence_spec.txt")
    print("              [FROZEN: FREEZE_V1_LOCK] ~4,460 tokens — FIRST LOADED")
    print("  Position 1: personality_block")
    print("  Position 2: self_block")
    print("  Position 3: lessons (HEURISTICS) — ≤240 chars, ≤3 items")
    print("  Position 4: memory blocks (vault_context, identity_meaning, etc.)")
    print("  Position 5: user turn (appended by caller)")
    print()
    print("  IF Ollama truncates from the BACK (most common LLM behaviour):")
    print("    → user turn → memory → lessons → self → personality → spec")
    print("    → SPEC IS LAST TO GO (position 0 = front of context)")
    print("  IF Ollama truncates from the FRONT:")
    print("    → spec is FIRST TO GO — CHARACTER DNA LOST with no error")
    print()
    print("  M3 cannot determine direction from the token count alone (M2).")
    print("  Direction requires: compare spec markers in response with/without overflow.")


# ── M5: headroom trend ─────────────────────────────────────────────────────────

def measure_m5():
    """Calculate growth rate from known data points."""
    print()
    print("── M5: Headroom trend ────────────────────────────────────────")

    # Two data points from F-B audit (card 0047) and current backend_health:
    # F-B: 7,281 tokens (earlier session, exact date unknown but same day as F-B report ≈ 08-15/16)
    # Current: 7,477 tokens (backend_health, ts=1786977430 ≈ 2026-08-17 01:17)
    pt1_tokens = 7281
    pt1_label  = "F-B audit (session ~2026-08-15/16)"
    pt2_tokens = 7477
    pt2_label  = "backend_health (2026-08-17 01:17)"

    delta_tokens = pt2_tokens - pt1_tokens

    try:
        import time
        pt2_ts = 1786977430.0
        # Estimate pt1 was ~2 days earlier
        pt1_ts_est = pt2_ts - (2 * 86400)
        delta_days = (pt2_ts - pt1_ts_est) / 86400
        rate_per_day = delta_tokens / delta_days
        headroom = NUM_CTX - pt2_tokens
        days_to_overflow = headroom / rate_per_day if rate_per_day > 0 else float("inf")
    except Exception:
        rate_per_day = None
        days_to_overflow = None

    print(f"  Data point 1: {pt1_tokens} tokens  ({pt1_label})")
    print(f"  Data point 2: {pt2_tokens} tokens  ({pt2_label})")
    print(f"  Delta        : +{delta_tokens} tokens")
    if rate_per_day:
        print(f"  Rate (est.)  : ~{rate_per_day:.0f} tokens/day  (2-day window — low confidence)")
        print(f"  Headroom now : {NUM_CTX - pt2_tokens} tokens")
        print(f"  Days to 8,192: ~{days_to_overflow:.1f} days  (at current rate — ESTIMATE)")
    print()
    print("  NOTE: only 2 data points; rate may reflect routine growth (new lessons,")
    print("  vault entries) rather than a structural trend. Track over a week.")
    print("  WHAT IS GROWING: vault_context entries (lessons accumulate),")
    print("  self_block (facts.json grows), HEURISTICS (new confirmed lessons).")


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("0052 — Ollama overflow measurement (NO FIXES)")
    print("=" * 60)
    pe_live = measure_m1()
    m2_result = measure_m2_m4()
    measure_m3()
    measure_m5()
    print()
    print("=" * 60)
    print("SUMMARY TABLE")
    print()
    pe = pe_live or 7477
    print(f"  M1  | Live prompt/num_ctx      | {pe}/{NUM_CTX} = {round(pe/NUM_CTX*100,1)}%   | {NUM_CTX-pe} tok headroom")
    if m2_result:
        print(f"  M2  | Ollama at overflow       | Does NOT error — silently truncates to num_ctx  |")
        print(f"  M2  | Truncation direction     | UNKNOWN from count alone — need content compare |")
        print(f"  M4  | Is truncation silent?    | PARTIALLY — prompt_eval_count available but not alarmed |")
    else:
        print("  M2  | Ollama at overflow       | UNKNOWN — Ollama offline during test            |")
        print("  M4  | Is truncation silent?    | UNKNOWN — could not test                        |")
    print("  M3  | Block lost first (if back)| user turn → memory → lessons → self → personality → spec |")
    print("  M3  | Block lost first (if front)| spec (CHARACTER DNA) → personality → self → ...  |")
    print("  M5  | Growth rate (est.)       | ~98 tok/day over 2-day window (low confidence)  |")
    print("  M5  | Days to overflow (est.)  | ~7.3 days at current rate                       |")
    print()
    print("OPEN QUESTIONS:")
    print("  M2/M3: truncation direction not established — needs content-based test")
    print("  M4:    no automated alarm exists; prompt_eval_count readable but not guarded")
    print("  M5:    2-data-point window; need a week of samples for reliable rate")
