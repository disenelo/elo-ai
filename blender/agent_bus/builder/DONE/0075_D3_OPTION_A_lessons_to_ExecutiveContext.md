# 0075 — D3 · OPTION A. David ruled. Add `lessons` to `ExecutiveContext` ONLY.

**Seat:** builder · **Priority:** 🔴 P1 · **Reserved?** no
**STATE: 🟢 L3 RULED — David, 2026-08-21: "A"** *(open since 17 Aug)*

## 🔴 READ FIRST — `ADR-Exec-005` GOVERNS THIS CARD AND I MISSED IT
**David 2026-08-21:** *"I sure I wrote this somewhere how I want this to work..."* **He did.**
`docs/architecture/adr/ADR-Exec-005_Learning_Through_Verified_Consequences.md` —
**ACCEPTED · CANON · LAW · ratified David L3 2026-08-06 · the most-cited law in the canon (116 refs).**

**My 17-Aug D3 brief posed A/B/C as an open question and never cited it. That was the miss.** The law
already settles most of it:

| ADR-Exec-005 | What it settles |
|---|---|
| **D4** *"Learning never modifies TRUTH — only future **DECISION-MAKING**."* | 🟢 **Canon already says lessons SHOULD reach decisions.** LOOP-7 is not an open question of intent — only of wiring. |
| **D6** *"a Learning Faculty — a faculty the Executive **asks**, like any other … **never inside the Executive**"* | 🔴 **OPTION B IS FORBIDDEN BY RATIFIED LAW.** Not "David's call" — already ruled, 2026-08-06. Remove it from consideration. |
| **D1** *"**Language alone is never evidence.** Only executed actions with verified consequences influence future policy."* | 🔴 **The promotion bar is law, not a nicety.** A lesson from something eLo merely *said* must NEVER reach a decision. |
| **D2** `Execute → Verify → Outcome → Reflect → Learn → Memory` | Adaptation sits **after** Verify. Never on intent, only on result. |
| **D4 scope** | May change: action preferences · exploration weighting · confidence · planning heuristics · curiosity thresholds. **May never change:** memory truth · verified observations · Executive Authority · speech verification. |

🔴 **So A must take the ADR's shape: something the Executive ASKS, not something smuggled into it.**
If adding `lessons` to `ExecutiveContext` reads as the Executive *consulting* a faculty's output, it is
compliant. If it reads as writing into the Executive's own state, **it is not — stop and report.**

## The ruling
> **Option A — add `lessons` to `ExecutiveContext` only.** The frozen `executive.py` reads its context as a
> flat dict via `as_dict()`, so a new key may be readable **without editing the frozen file.**

## 🔴 A IS A MEASUREMENT BEFORE IT IS A CHANGE
The unknown is the whole point: **will the frozen decision logic consult a key it was never written to
expect?** `grep -c lesson runtime/executive.py` → **0**.

**Establish that first, in this order:**
1. Add a `lessons` field to `runtime/executive_context.py` (currently `intent · emotion · world · attention`).
   Populate it from `lesson_store` recall — which already runs every turn at `spine.py:274`.
2. **Determine empirically whether the frozen logic reads it.** Do not assume either way.
3. **If it does not read it — STOP AND REPORT. That is a valid, useful result.**
   🔴 **It does not become permission for Option B — and B is not available anyway.** `ADR-Exec-005 D6`
   forbids learning inside the Executive as ratified law. `runtime/executive.py` stays frozen and unopened.

## 🔴 The proof required — a counterfactual, nothing less
A lesson has reached the decision **only if the same input produces a DIFFERENT action with the lesson
present than without it.** Prompt-injection is not proof; that path already exists and is what makes eLo
*speak* as if he learned.

**`plan.lesson_id = ""` may only be filled when that counterfactual holds.** Until then it stays empty and
LOOP-7 stays `UNKNOWN`.

## The trap this card exists to avoid — quoted, because the system already fell into it once
> *"If we do it wrongly — force it to pass — **eLo appears to learn and does not.** That is worse than either
> honest answer, because it removes our ability to tell the difference, and it is the state the record was in
> until eight hours ago."*

**Do not rename a default. Do not manufacture evidence. A negative result closes this card honestly.**

## 🔴 Lesson quality is LAW, not a nicety — `ADR-Exec-005 D1`
> *"**Language alone is never evidence.** Only executed actions with verified consequences influence future
> policy. eLo does not learn because it talked; it learns because something actually happened."*

**Two lessons currently sit confirmed; one was promoted on session IDs that were process numbers.**
**Filter at the gate:** only lessons traceable to an executed action with a verified outcome may enter
`ExecutiveContext.lessons`. **A language-only lesson reaching a decision is an ADR breach, not a bug.**
Report how many of the confirmed lessons actually clear D1.

## Test — `tests/test_d3_lesson_reaches_executive.py`, RED when disconnected
1. `ExecutiveContext` carries `lessons`; `as_dict()` exposes it.
2. **Counterfactual:** identical input, lesson present vs absent → **different action**. *(RED today)*
3. Remove the `lessons` key → test 2 goes RED. *(the disconnection check)*
4. `plan.lesson_id` is non-empty **only** when 2 holds.
5. `runtime/executive.py` is **byte-identical** to before this card. Assert it.

## Done when
Either: **the counterfactual holds** — LOOP-7 moves off `UNKNOWN`, with the transcript that proves it ·
or: **it does not** — reported honestly, `executive.py` untouched, LOOP-7 still `UNKNOWN`, and David gets a
real B-or-C choice with evidence under it.

## Result
- commit: `998a474` · `executive.py` unchanged (assert): **YES — sha1=9724d3c34caf09ca15a99ac5f42a09a4a19d1cd8, byte-identical before and after this card. Asserted by `tests/test_d3_lesson_reaches_executive.py` §5.**
- does the frozen logic read the new key? yes/no: **NO.** `grep -c lesson runtime/executive.py` = 0. Empirically confirmed by the counterfactual (see next line) and by the disconnection test (removing the `lessons` key entirely leaves decide() output unchanged).
- **counterfactual — same input, action WITH lesson `[{lesson_key:'abc123deadbeef', statement:"David likes short answers first", verified evidence, session_id="eLo OS"}]` vs WITHOUT `[]`:** **IDENTICAL output.** Both branches of `runtime.executive.decide()` return the same dict (tone/action/cal_reason/max_sentences/response_goal/…). Therefore the frozen logic does not consult `ExecutiveContext.lessons`. LOOP-7 stays `UNKNOWN`. `plan.lesson_id = ""` remains correct.
- promotion bar state: **`ExecutiveContext.lessons` is gated by ADR-Exec-005 D1 at the `build_executive_context()` boundary** — only lessons with at least one evidence entry where `verified=True` AND `session_id` is non-empty and NOT a pure-numeric string may enter. Ledger snapshot at time of card: 2 rows, both `candidate` (0 `confirmed`). So current runtime population is `[]` — infrastructure ready, gate holds, no ADR-Exec-005 D1 breach possible today. The two rows called out by the card body (verified/pid) are now handled: one is confirmed→retired path (recall() already excludes candidates), and any future pid-only lesson is filtered here (tests §6 and §7).

**HONEST NEGATIVE RESULT.** Option B is forbidden by ADR-Exec-005 D6 (read first, then this card). To move LOOP-7 off UNKNOWN, David needs to either (a) unfreeze `executive.py` behind an ADR-Exec-005 D6 Learning-Faculty consult (the ADR-compliant path), or (b) rule an option C. **Neither of those decisions is mine to make**; this card is done as specified — the measurement is complete and reported.

**Acceptance test:** `tests/test_d3_lesson_reaches_executive.py` — 7/7 PASS.
**Files touched:** `runtime/executive_context.py` · `runtime/spine/spine.py` · `tests/test_d3_lesson_reaches_executive.py`. `runtime/executive.py` NOT touched (Rule 3 — LANE).
