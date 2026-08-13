# DIAGNOSIS — conversation regression (David live transcript, Fri 2026-08-07)

**Source:** David's live chat with eLo, pasted 2026-08-07. Architect diagnosis, code-grounded. NOT a code fix — relay to owning seats.

## ✅ What LANDED (visible wins — do not touch)
- **Semantic sit + situated self:** "Come sit with me" → *"I'm already perched on the bottom edge of Pages, ready to sit beside you."* Sit intent fired AND the situated self answered from state (knows the surface = Pages). David: "a good improvement on before." WO-035b + WO-059/052A working live.
- **Sit-linger (Designer, this session):** engagement now counts while David is IN the chat (input focused / half-typed draft / replying); rises only after click-away + ~25s quiet; a move command or pick-up stands him instantly. This is the CORRECT hold model. Sit-hold = RESOLVED.

## 🔴 ROOT CAUSE (confirmed in code, not inferred): eLo was on the MOCK backend
The degraded line *"Can't reach my thinking right now — running on backup"* is gated at **`server.py:2939`**:
`_bh_degraded = (_llm_turn and backend_used == "mock" and _bh_expected != "mock" and ELO_BACKEND != "mock")`
→ it fires ONLY on genuine degradation: a real backend was expected but the call fell through to the mock.
It fired **≥2×** in the transcript → **eLo was genuinely answering from the MockBackend during the session.**
The mock is the source of the whole degraded feel:
- flowery mirroring ("your greeting landed like a tiny tap on the screen" · "a quiet high-five")
- commenting on the USER's typos ("I saw you wrote 'Hows' without the apostrophe")
- dictionary answer: "What is happening?" → "A happening is a performance-art event…"
- **hallucinated the wrong company:** "The Company for Doing is a 'doing' agency…" — that is NOT DISENELO.

**Why there's no real backend to fall to:** Builder outbox (WO-032 Part A) — OpenAI quota/billing exhausted + Groq SDK not installed → nothing to route to → drops to mock. **This is the #1 blocker; everything below is unfairly judged until a stable real backend is live.**

▶ **BUILDER — PREREQUISITE #1 (unblock WO-032 Part A):** get a real backend live and stable — either David restores OpenAI billing, OR install the Groq SDK + key (WO-032b) and pin `ELO_BACKEND=groq`. Then write `backend_health.json` and confirm `backend_used` != mock on a normal turn. Until then, conversation quality is the mock's, not eLo's.

## 🟠 SECONDARY (real, but CONFIRM on a real backend first — may be mock artifacts)
1. **Engage-not-mirror regressed** — narrating the exchange + commenting on typos instead of answering substance (Vision Spine: conversation is engagement, not reflection; WO-036). If it persists on a REAL backend → strengthen the deterministic mirror/narration scrub. ▶ Builder (confirm-then-fix).
2. **Company-awareness — two distinct faults:**
   a. **Hallucination** ("Company for Doing") — mock artifact; re-check on real backend. But eLo must answer DISENELO from the company World Model / `company_state.json`, NEVER generation (Reality Before Narrative). ▶ Builder: wire "what is the company / what does it do" to real company state, honest "I don't have that" if absent.
   b. **"What's on the board?" dumped raw backlog** ("5 ready: Finish Volume V… Tee mockups…") instead of the Presentable FOCUS — this is the **WO-061** bug (surface COMPANY_FOCUS, not the first ready-P1 rows). Independent of backend. ▶ Builder: WO-061 close.
3. **Intent misroute** — "What is happening?" → dictionary definition (garble/intent family, WO-039). Confirm on real backend; if it persists, the system-intent classifier needs the conversational read. ▶ Builder.

## 🔁 Clean cross-lane handoff (Designer → Builder, from the sit-linger fix)
Bulletproof linger wants the brain to publish `last_user_ts` to `blender_state.json` (Designer notes the brain already tracks it at **`server.py:1405`** but doesn't write it out). ▶ **Builder: write `last_user_ts` into `blender_state.json`** so the Designer can hold sit purely on real user-activity time instead of inferring focus. Small, one field.

## Order to work it
1. **Builder:** real backend live + stable (WO-032 Part A / WO-032b) — nothing else is judgeable until this.
2. Re-run the SAME transcript on the real backend → see which of the secondary faults survive.
3. Then: WO-061 (board focus) · company-state wiring · engage-not-mirror scrub · garble — in that order, each with a test.
4. Builder: publish `last_user_ts` (one field) for the Designer's bulletproof linger.
