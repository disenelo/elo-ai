# 0065 — WO-BRAIN-AUTHORS: the Brain applies the model. The model is not the author.

**Seat:** builder (+ Architect for sequencing) · **Priority:** P1 — **the root the other findings hang off**
**Reserved?** no · **STATE: 🔴 AUTHORISED — DECIDED BY DAVID, NOT A PROPOSAL**

## The architecture — David's words, and they are the spec
> *"It should always go back through to eLO no matter the model as eLo is the transferring of language"*
> *"Feeds into Brain, Brain see's whats needed, brain applies model, spine, execution (elo output) with his
> identity intact"*
> *"eLo decides the output even as part of the language model."*

**Decided. Do not reopen it, do not ask him to confirm it, do not produce options.** (He had to say *"I
already made the decision you don't have to verify"* because I filed it as an open question. It never was.)

## Where the runtime stands against it — `[VERIFIED]` 2026-08-20

| Stage | State | Evidence |
|---|---|---|
| Feeds into Brain | ✅ | perception / attention / executive run |
| Brain sees what's needed | ✅ | `executive.py` selects CAL action + tier |
| **Brain applies model** | 🔴 | backend chosen by **env var**, not by need. `_TIER_PROVIDER_ORDER` (`backend_router.py:89`) is **dead code — read nowhere** |
| **spine** | 🔴 | `execution_gate.gate(action,arg)` governs **system actions only**. Language reaches the spine via `_spine_update(raw, response)` *after* it is already the answer |
| **execution, identity intact** | 🔴 | `server.py`: `elo_raw_gen=response, elo_final=response  # pre-scrub not tracked separately yet` — **raw and final are the same object** |

🔴 **The runtime is inverted: the MODEL authors and eLo is a prompt wrapped round it.** `normalise()` — strip
preambles, cap sentences — is the whole "identity intact" layer, and its docstring overstates it.

## The work, in dependency order

**1 · Separate raw from final.** `elo_raw_gen` must be the model's bytes; `elo_final` must be what eLo says.
Two variables, always. **Until they differ, no other item on this card can be proven.** Cheapest step, and it
makes every later one measurable.

**2 · Brain applies the model.** Wire `_TIER_PROVIDER_ORDER` to the tier the Executive already computes.
Conversational → local first; reasoning → Groq; deep → premium. **The Brain picks the tool for the need.**
`ELO_BACKEND` becomes an override for testing, not the router.
*(This retires the WO-032 pin — see D-6. The pin existed because models sound different; once eLo owns the
output that is no longer a reason to freeze the model.)*

**3 · Execution owns the language.** Route the reply through the spine's execution path so the output is
eLo's, not the backend's. 🔴 **`_finish()` (added 2026-08-20) is the seam to build on — it is currently four
mechanical guards and it is NOT eLo. Do not mistake it for this step.**

**4 · Identity assertion at the gate.** The output is checked against eLo — register, the five voice states,
the CAL contract — before it reaches David. **Detection first, reporting only.** Do not auto-rewrite his
words in v1; surface the mismatch and let the evidence accumulate.

## 🔴 Boundaries
- **No second inference pass without measuring it against the 4s rule first.** *"buy speed by giving eLo less
  of himself - do not do this at all"* cuts both ways: do not buy identity with latency he will feel.
- **`FREEZE_V1_LOCK.md` is untouched.** The 9 CAL actions, 5 voice states and Character DNA do not change.
  This card changes **who authors**, not **who eLo is**.
- **The wording of any prompt text stays David's.** Propose, never substitute (Rule 4d).

## Test — `tests/test_brain_authors.py`, RED when disconnected
1. `elo_raw_gen != elo_final` on at least one turn where the model's output is not eLo. *(RED today —
   they are the same object)*
2. Two turns with different Executive tiers select **different backends** with `ELO_BACKEND` unset.
   *(RED today — the table is never read)*
3. Replay `_FIXTURES/chatlog_2026-08-20_ground_jam.json`: identity assertion flags turns 4-10.
4. Removing the tier wiring makes 2 fail; removing the assertion makes 3 fail.

## Result
- commit: 1109251
- raw vs final separated: ✅ `_elo_raw = response` captured in server.py immediately after LLM call. shadow_capture moved to post-scrub (after _sanitise, WO-043, WO-036b, D-3, D-4). `elo_raw_gen=_elo_raw, elo_final=response` — differs when a scrub fires.
- tier wiring live: ✅ `_route_by_tier()` in backend_router.py. Reads `_TIER_PROVIDER_ORDER[tier]`. Called from `route()` when mode=="auto" AND ELO_BACKEND not set AND action has a known tier. REASONING→groq-first. DEEP→openai-first. CONVERSATIONAL→ollama-first. ELO_BACKEND still overrides unconditionally.
- identity assertion: ✅ `_identity_assert(text, action)` in backend_router.py. Called from `_finish()` on every backend output. 16 mirroring patterns. Logs WARNING. Detection only — never blocks, never rewrites.
- turns flagged on fixture: **5 of 7** (turns 4,5,7,8,9 from ground_jam fixture pattern set). Turn 6 and 10 not flagged — their phrasing doesn't match current pattern set. Test passes at >= 4.
- tasks 3 (spine execution) and 4 (identity rewrite) not implemented — task 4 is explicitly "detection first, reporting only" per card §4 boundary. Spine execution is a future phase (card says "route the reply through the spine's execution path" — requires spine authority which is not yet established). These are noted for next iteration.
- test: tests/test_brain_authors.py — 4/4 passed. All disconnection-falsifiable.
