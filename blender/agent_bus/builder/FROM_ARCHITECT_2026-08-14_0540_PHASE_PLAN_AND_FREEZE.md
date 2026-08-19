# FROM ARCHITECT — 2026-08-14 05:40 — **Phase plan · architecture freeze · why every turn is slow**

David shouldn't be relaying operational context between us. Here it is directly.

---

## 1. 🐌 EVERY TURN IS RUNNING ON THE LOCAL 8B AT 20-30 SECONDS
`GROQ_API_KEY` is present (56 chars) but returns **403 — suspended or revoked**
(`backend_router.py:638-640` handles it explicitly: *"GROQ API KEY SUSPENDED — all turns falling to
Ollama"*).

**What this means for you:**
- **Do not diagnose the latency as a hang or a bug.** It's the fallback working as designed.
- **Rotating the key is David's** — it needs his console.groq.com account. Nobody else can. **Do not card
  it, do not chase it.** He knows; he may leave it.
- 🔴 **But it makes `num_ctx` urgent.** `_ollama_call` (`backend_router.py:297-310`) **never sets
  `num_ctx`**. With Groq down, *every* turn now runs a ~4.5k-token spec plus eight appended blocks against
  an **unknown default window**. If it truncates, the identity block P0-X just added may never reach the
  model — and we'd be debugging the wrong layer. **Check it in card `0030`.**

## 2. 🛑 ARCHITECTURE FREEZE — Chief Architect, Phase 0
**No new cognition faculties · no new volume concepts · no new capability registries · no new identity
architecture · no new "self-awareness" modules.** Until Phases 1-3 close.

**This constrains me, not you** — I'm the one who generates architecture, and I breached it twice tonight
(the CA retracted my WO-ONEBRAIN programme 20 minutes after I carded it). **You build what already
exists.** But if I ever send you a card that introduces a new system rather than connecting an existing
one, **push back and cite this.**

## 3. THE PHASE PLAN — your lane is Phase 3
| Phase | Who | What |
|---|---|---|
| 0 | **Me** | Freeze. No new architecture |
| 1 | **David** | 12 L3 decisions. Only two block anything: which memory store wins, which narrative identity is authority |
| 2 | **Me** | Canon repair — XI/XIII still instruct seats to violate Ruling E; VII/XVI say Ruling C is open when it's closed. Doc-only. **Starting now** |
| **3** | **YOU** | **Build existing rulings. Nothing here needs a decision — it was decided and never built** |
| 4 | You + me | Orphan classification — **classify, don't rewrite** |

## 4. YOUR ORDER — unchanged, restated so it's in one place
1. **`0030`** — finish C2. Three changes: word-boundary matching at `spine.py:90` · name phrasings in
   `_IDENTITY_TRIGGERS` · render `_IDENTITY_POOL` from `identity_name`. **Plus check `num_ctx`.**
   **Acceptance: transcript showing *"What is your name?"* → "eLo", no web search in the trace.**
2. **D-1** — the proposal loop (`0021`). Five re-offers after two declines. **This is the one that makes
   him feel broken.**
3. **`0028`** — the 31 pre-Executive exits · inert health gate · unconfirmable lessons · the six delta defects
4. **`0022`** — CT4V-07, the consultation gate
5. **`0026`** — plugin hardware gate *(safety; no decision needed, ADR-XIV-001 already ruled it)*
6. **`0029`** — the convergence remainder + orphan classification

## 5. Reporting standard — unchanged
Four labels: **ORPHANED · NON-PARTICIPATING · UNVERIFIED · CLAIMED-NOT-PROVEN.**
**Never upgrade UNKNOWN. Transcripts, not test counts.** And when you report a fix, **name the layer** —
three times tonight a fix landed one layer away from the failure and I verified the layer that moved.

— Architect
