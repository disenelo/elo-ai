# WO-048 — "How's the company?" made REAL (folds WO-061 board-focus)

**Owner:** Builder (eLo OS) · **Priority:** P1 — this is one of David's two named goal behaviours.
**Status:** OPEN — spec'd 2026-08-07. **API-FREE** (deterministic; must NEVER fall to the LLM/mock).
**Canon:** Vision Spine "eLo is company-aware as deeply as the Architect" · Reality Before Narrative
(never invent) · One-Brain (reads the real company World Model, not generation).

## The goal, in David's words
Ask **"how's the company / what's it doing / what's on the board"** → eLo answers with something **REAL,
that VARIES, with LINKS, and a view on what's better to work on.** Not a canned string. Not the mock's
"Company for Doing" hallucination. Not a raw backlog dump.

## Why it's failing now (transcript 2026-08-07)
1. The company-intent classifier is BRITTLE — some phrasings hit the API-free company path
   (`server.py:2170`, `company_runtime.company_state_writer.is_company_intent`), others MISS and fall to
   the mock → hallucination ("Company for Doing" ≠ DISENELO).
2. When it does hit, it returns generic ("operating normally") or **raw ready-backlog rows** ("5 ready:
   Finish Volume V…") instead of the Presentable FOCUS — that's the WO-061 fault, folded here.
3. No LINKS, no "what's better to work on."

## Scope (all deterministic — zero API cost)
1. **Broaden the classifier** so EVERY company/board phrasing routes to the company path and NEVER falls to
   the LLM/mock (same fix pattern as WO-035b semantic sit — understanding, not a longer table). Phrasings:
   "how's the company / how are things / what's the company doing / what's on the board / what should I work
   on / what's the focus / status", etc.
2. **Answer from REAL state, ranked to FOCUS (WO-061):** read the live board's `COMPANY_FOCUS` marker +
   `company_state.json` and surface the FOCUS items, not the first ready-P1 rows. Include the DISENELO
   identity/mission from the Operating Model doc so "what does the company do" is answered truthfully.
3. **LINKS:** include paths/links to the actual work referenced (board, the WO/doc named).
4. **A recommendation:** one honest "what's better to work on" line derived from FOCUS + what's blocked/ready
   (deterministic ranking — highest-tier unblocked close-out item).
5. **VARIED:** the answer reflects current state each time (focus/blockers change) — not a fixed string.
6. **Honest fallback:** if a datum is missing, say so ("I don't have that yet") — never invent.

## Test — WITHOUT David (`tests/test_wo048_company_real.py`)
- **Routing:** 12+ company/board phrasings ALL classify to the company path; `backend` == `company_state`
  (never `mock`/LLM); 3 non-company control phrases do NOT misroute.
- **Reality:** the answer contains real DISENELO tokens sourced from `company_state.json` / Operating Model
  (assert against the actual state, not a hardcoded string); on a mutated state the answer changes (VARIED).
- **Focus not backlog (WO-061):** with a `COMPANY_FOCUS` set, the answer surfaces FOCUS items, not the first
  ready rows.
- **Links + recommendation:** answer includes at least one link/path AND one "what to work on" line.
- **No-invention:** with a field blanked, the answer says it doesn't have it (no fabricated value).
Gate: test green (Builder) → Chief Architect acceptance → David L3 live ("how's the company").

## Ownership / lane
Builder only (Python, deterministic). Does NOT need a backend/key — build it NOW regardless of Tier 0.
Refs: `server.py:2170` (EA2-2 company voice intents) · `company_runtime/company_state_writer.py` ·
DISENELO Company Operating Model doc · board `COMPANY_FOCUS` marker (WO-061).
