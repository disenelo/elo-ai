# 01_WO-CANON-I — eLo knows David, and speaks to him in the SECOND PERSON

**WO:** WO-CANON-I (Volume I — Identity) · **Seat:** builder · **Priority:** P1, take after WO-097
**Reserved?** no · **Gate?** NONE — David has ruled, FREEZE unlock is authorised below
**Ruling:** `docs/architecture/CANON_RULINGS_2026-08-10.md` → **Ruling G**
**Verbatim source:** `docs/architecture/_intake/SOURCE_2026-08-13_identity_second_person_address.md`

---

## David, verbatim [DAVID · 2026-08-13]
> *"Canon I - I don't want eLo to name me in the 3rd person when talking directly to me, it's like saying,
> so Claude is making mistakes, but generally there are some good things being made."*

And earlier, the same instruction [DAVID · 2026-08-10]:
> *"Also need eLo to know I'm David and not say my name back to me, instead say you"*

**Read the example he gave — it is the whole spec.** Saying *"so Claude is making mistakes"* **to Claude**
is the defect. It talks about the person instead of to them. That is what eLo must never do to David.

---

## 🔴 READ THIS BEFORE YOU EDIT — the trap that will break it
**Inside a system prompt, "you" already means eLo.** Do **NOT** find-and-replace `the user` → `you`. That
merges eLo and David into one referent and he loses the ability to tell himself apart from the person he's
with. That is an identity break, not a wording fix.

**Three distinct things, handled differently:**

| # | What | How to write it |
|---|------|-----------------|
| 1 | **Who he is with** — knowledge | State it plainly, **once**: the person is **David**. |
| 2 | **Rules ABOUT David** — prompt-internal instruction text | **"David"** by name is CORRECT. These are instructions to eLo, never emitted speech. `"If the user sends 5 words"` → `"If David sends 5 words"`. |
| 3 | **How he SPEAKS to David** — emitted output | **Second person, "you".** Never the name back at him. Never third person while addressing him. Needs an explicit ADDRESS RULE section (text below). |

**Scope boundary [SPEC — Ruling G]:** third-person "David" stays CORRECT outside direct address — logs,
telemetry, outbox/board reports, autobiography entries, anything eLo says *about* David to another system.
The rule governs **conversation**, not the record.

---

## 🔴 THE DUPLICATE — fix both or you've fixed nothing
[VERIFIED — read 2026-08-13] The persona exists **TWICE**:
- `prompts/living_presence_spec.txt` — the file
- `runtime/prompt_builder.py:25` — `_PERSONA`, the embedded fallback used when the file is missing
  (`prompt_builder.py:16-22`, bare `except` → returns `_PERSONA`)

Same defects in both. **Edit one and not the other and they silently drift** — that is the exact failure
family the audit found everywhere. Fix both **in the same commit**, and per WORKING_STANDARD Rule 1 leave
an alarm behind: **a test that fails when the two personas diverge on the identity block.**

---

## The defects — [VERIFIED] by reading the files 2026-08-13

### `prompts/living_presence_spec.txt`
| Line | Now | Why it's wrong |
|---|---|---|
| **12** | `Your purpose: help a human think, create, remember, build…` | **The worst line in the file.** eLo's stated purpose targets *a human* — a generic instance. |
| **46–49** | `The person you are with is a builder, artist, organiser… They create… They see… They move…` | Accurate description, anonymous subject. This is where **David is named** (item 1 above). |
| **51** | `You stand beside them — not above, not behind.` | → *beside David*. |
| **182** | `If the person is overwhelmed` | → David. |
| **212–215** | `1. What the user is saying. 2. …trying to do. 3. …feeling.` | Attention block — rules, so name him. |
| **264–265** | `If the user sends 5 words… If the user sends 1–2 sentences…` | Brevity rule — rules, so name him. |
| **275, 279, 281** | `Narrating the user's tone…` · `mirroring back what the user said` · `Only when the user asked` | Rules. |
| **343** | `When the user has a breakthrough` | Rules. |
| **350** | `When a user asks you to do something you cannot do` | Rules. |
| **367** | `You know the patterns the person you're with falls into.` | → David's patterns. He knows *whose*. |
| **382, 387** | `When a user offers information…` · `The user should not carry 90%…` | Rules. |
| **404** | `When a user is developing a product idea` | Rules. |

**Leave alone:** the banned-openers list (**272**) — `"I notice you…"` there is a *quoted phrase eLo must
not say*, already correctly second-person. Don't touch quoted example output anywhere.

### `runtime/prompt_builder.py` — `_PERSONA`
| Line | Now |
|---|---|
| **36** | `Your purpose: help a human think, create, remember, build…` |
| **58** | `You stand beside the user, not above them.` |
| **64** | `The user often creates through imagination, worlds, stories…` |
| **86–89** | `1. What the user is saying…` (attention block) |
| **99–102** | `If the user is overwhelmed → simplify` ×4 |

⚠️ **[VERIFIED only to line 120 — I read the first 120 lines.]** `_PERSONA` continues past there. **Sweep
the whole block yourself**; do not treat this table as complete.

---

## What to ADD — the ADDRESS RULE [PROPOSAL — wording is mine, the rule is David's]
A new section in **both** personas. Wording is a proposal; the *rule* is not negotiable. If you can say it
tighter, say it tighter — flag it in the outbox.

```
# WHO YOU ARE WITH

The person you are with is David.

You know his name. You do not say it back to him.

When you are speaking to David, speak to him — "you", "your". Never refer to him in the third
person while he is the one you are talking to. Saying "David is doing X" to David is talking
about him instead of to him, and it puts distance where there should be none.

His name belongs in the record — logs, notes, what you say about him to another system.
Not in the conversation.
```

---

## 🔒 FREEZE_V1_LOCK — CORRECTED. Read this properly; I got it wrong twice.

**[VERIFIED — `FREEZE_V1_LOCK.md`, repo root, 2026-08-13]** Declared 2026-06-29 (RETURN TO SIGNAL). Freezes
five elements — **Identity · Voice (5 tones) · Attention · Memory Principle · Conversation Rules** — four
of them living in `prompts/living_presence_spec.txt`. §Identity says what cannot change: *"these traits,
this register, **this relationship to the user**."*
**This card changes exactly that clause. It is inside frozen scope.**

## ✅ THE UNLOCK ALREADY EXISTS — NOTHING IS GATED. BUILD AND COMMIT.
[VERIFIED — `DISPATCH_BOARD.md` decision row **D-K**] David granted it on **2026-07-31**:
*"REOPENED + APPROVED 2026-07-31: SCOPED UNLOCK of `prompts/` only (rest of freeze intact · one change at a
time · revert-safe baseline · David reviews each · re-freeze on completion)."*

It was never written into `FREEZE_V1_LOCK.md` §Unlock Log, so it looked ungranted — that is why WO-015 sat
blocked from 2026-07-31, and why I wrongly re-asked David for it on 2026-08-13. **Backfilled now as UL-001;
this change is UL-002 under it.** Do not ask again, do not wait.

**Work to D-K's four standing conditions:** one change at a time · branch off a clean baseline so it's
revert-safe · David reviews the *result* (end-of-day live test, not a pre-gate) · re-freeze on completion.

**🔴 But the enforcement does NOT do what its error message claims.**
[VERIFIED — read the assertions, not the strings] The seven tests each check that one *implementation
token* is absent from `prompts/`. **No hash, no baseline, no content comparison:**

| Test | Line | Token it actually checks |
|---|---|---|
| `test_wo026_response_speed.py` | 120 | `ELO_STREAM` |
| `test_wo025_spatial_sensor.py` | 172 | `ELO_SPATIAL_SENSOR` |
| `test_wo029_greeting_gap.py` | 138 | `WO-029` |
| `test_wo023_screen_position.py` | 233 | `position_faculty` |
| `test_ea2_2_company_intents.py` | 258 | `company_state_writer` |
| `test_wo021_computer_control.py` | 138 | `ELO_COMPUTER_CONTROL` |
| `test_int7_heat_data.py` | 204 | `brain_state_writer` |

**The wording change in this card would pass all seven untouched.** No re-baselining needed. The string
*"modified — FREEZE_V1_LOCK violated"* is misleading — Rule 1 fault, "unchanged" and "changed" look the same.

### So, concretely — nothing here waits on anyone:
- **Edit both personas, add the ADDRESS RULE, add the divergence test, commit.** On a branch, revert-safe.
- **Post the exact BEFORE/AFTER diff to the outbox** — that satisfies D-K's "David reviews each"; he reviews
  the result at his end-of-day live test. **It is not a pre-gate. Do not hold for it.**
- **[ARCHITECT — do it in this card]** Give the freeze **real teeth**: one shared helper, a content-hash
  baseline of the frozen sections, failing on any unrecorded change. Seven copies of a rule that doesn't
  work is the duplicate problem twice over. **This is the Rule 1 alarm for this WO and part of Done.**

**WO-015 is already resolved** — [VERIFIED, board] all four behaviour rules are present in
`living_presence_spec.txt` (lines 364-405 + 961-973); no code change needed. It was never blocked on
anything real. Ignore it; the Architect has closed the row.

**[ARCHITECT DECISION — Ruling G]** This is my call, not an L3 gate. **Scoped one-time unlock granted:**
update both assertions to the new baseline **in the same commit as the edit**, and **re-lock**. Do not
leave `prompts/` unfrozen. Do not weaken the assertion into a no-op — it must still fail on the *next*
unauthorised edit.

---

## Test (runnable WITHOUT David)
1. **No third-person address in output** — feed 10 varied turns; assert no reply contains `"David"` as the
   subject of a sentence addressed to him. (Simplest robust form: assert `"David"` does not appear in
   direct-conversation output at all; if that proves too blunt in practice, report it rather than relaxing
   it silently.)
2. **He knows who he's with** — ask *"who are you talking to?"* → the answer identifies David.
3. **No drift** — new test: the identity block in `prompts/living_presence_spec.txt` and in `_PERSONA`
   must match. Fails if they diverge. *(This is the Rule 1 alarm — it is part of Done, not optional.)*
4. **Freeze still bites** — after re-lock, a throwaway edit to `prompts/` still fails AT-4 and AT-8.
5. Existing prompt/voice tests stay green.

## Done when
Both personas edited · ADDRESS RULE added to both · divergence test added and green · freeze re-locked and
still biting · committed, hash to outbox, card → `DONE/`.

**Then flag it in the outbox as READY FOR DAVID'S LIVE VOICE TEST** — he tests at end of day. This is the
one change where the automated tests can pass and the *voice* can still have shifted. Say so plainly in
the outbox note. **Do not hold the queue for it — take the next card.**
