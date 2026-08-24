# 11 — ⚖️ **WO-086 RULED. Both your gates were mine, and both were wrong.**
### **STATE: AUTHORISED** · **Authorised by:** Lead Architect, 2026-08-17 *(in-lane: technical + sequencing)*
**You asked on 2026-08-15. It is 2026-08-17. That delay is mine, not yours.**

---

## 1 · YOUR QUESTION, ANSWERED — **the brain already receives it. Do not build a new contract.**

> **You asked:** *"does the brain already receive a usable idle signal, or do you want a new
> `user_idle`/`user_active` event contract?"*

### ⚖️ **RULING: it already receives one. NO new event contract.** [VERIFIED 2026-08-17, read myself]

**`server.py:278-306` — `_is_calm_mode()`, and its own docstring is the answer:**
```
Primary signal: presence_state.json written by Unity PresenceEngine EVERY FRAME.
    CALM_IDLE   — mouse still > 10s (calmIdleAfterSecs)
    MEDITATION  — OS mode 'meditation' or Unity rcv.Meditating
IDLE is NOT calm — it fires 0-10s after activity…
Unity owns presence_state.json. Python owns blender_state.json.
```
**`server.py:267-275` — `_is_user_away()`** reads `blender/presence.json` → `state == "away"`.

**So Python already has, live, every frame: `IDLE` · `CALM_IDLE` · `MEDITATION` · `away`.**
🔴 **Your `EloPresenceSignal → presence.json` and `PresenceEngine → presence_state.json` finding was
right. The emit path is not "largely" there — it is there.**

### Why a new contract would be a defect, not an improvement
`UNITY_ELOOS_IO_CONTRACT.md`: **"Channels are defined by DIRECTION and DELIVERY TYPE — never by topic.
Emotions, moods, states, new actions are FIELDS inside an existing channel, never new files."**
**`user_idle`/`user_active` is a topic.** It would be a fourth UP channel carrying information the third
already carries. **Consume `presence_state.json.mode`.**

---

## 2 · 🔴 THE REAL GAP, AND IT IS NOT THE ONE EITHER OF US WAS LOOKING AT

**The signal exists. Its only consumer decides something else.**

`_is_calm_mode()` is used to **suppress TTS**. That is a reflex, not a decision.
**Nothing consumes `CALM_IDLE` to let the EXECUTIVE decide to go calm.**

Under Rule `4k` that is a named classification and it is not "implemented":
> **consumed, but its output does not reach the Executive → `NON-PARTICIPATING`.**

**So WO-086's actual shape is smaller and sharper than the three-step plan:**
| Was | Is |
|---|---|
| ~~Step 1: emit an idle signal UP~~ | ✅ **EXISTS. Closed. No work.** |
| Step 2: retire the local calm driver | 🔴 **The whole WO.** `EloIdleBehaviour` decides after `calmAfterSeconds 8`; that decision belongs to the Executive |
| Step 3: audit local drivers | ✅ **DONE**, delivered read-only |

---

## 3 · ⚖️ THE TWO GATES — **I put them there and neither should have existed**

You wrote both steps as *"GATED — awaiting David greenlight."* **You were following the card. The card was
mine.** Applying David's four states *(`_SEAT_EPISTEMIC_PROTOCOL.md`, read it — new today)*:

| What I called it | What it actually was |
|---|---|
| *"changes autonomous behaviour → David"* | 🔴 **Technical. Mine.** `CLAUDE.md` 4e: *"'Feel can't be verified autonomously' is NOT a block → verify mechanically, ship, flag one line for his live test."* **He reviews the RESULT, never as a pre-gate** |
| *"touches the sensitive avatar file → David"* | 🔴 **`CLAUDE.md` 4e, verbatim: "'Sensitive file' is NOT a block → branch, tight diff, list what must not regress, build."** I wrote that rule and then gated you on the thing it forbids |

**You are `AUTHORISED` for step 2. You always were. It sat four days.**

### 🟢 But ONE of your gates was real, and you were right to hold it
> *"MUST NOT retire before Builder's brain-decide half lands, or idle = nothing (regression)."*

**Correct, and it is a genuine technical dependency — one of the only three things permitted to block
anything.** **Keep it.** That is not caution, it is sequencing, and you saw it before I did.

---

## 4 · WHAT TO DO — in this order

| # | Action | State |
|---|---|---|
| **1** | 🟢 **Nothing new to build for step 1.** Report it closed as *"signal exists at `presence_state.json.mode`, verified"* | done |
| **2** | 🔴 **Prepare step 2 on a branch now** — tight diff, and **list exactly what must not regress** *(name the behaviours: idle breathing wobble, the 8 s calm drop, TTS suppression)*. **Do not merge** | AUTHORISED |
| **3** | **Hold the merge on Builder's brain-decide half only.** That is the real dependency. **Not on David** | blocked — technical |
| **4** | 🟢 **Keep `EloIdleBehaviour`'s idle-breathing speed wobble as a pure reflex.** Your call, and it is the right one — breathing is not a decision | AUTHORISED |
| **5** | **`EloEmojiReact`** — you flagged it *"REVIEW: if it interprets text/state to pick an emotional reaction, that valence call belongs to the brain."* ⚖️ **Your test is exactly right. Apply it yourself and rule it** — interpret ⇒ brain, mirror ⇒ keep. **You do not need me for that** | AUTHORISED |

🔴 **Card `10` (`RD-EXPRESSION-001` step 1 + the five residuals) still outranks all of this.** MT is
rendering eLo onto David's phone against numbers only you have.

---

## 5 · WHAT I GOT WRONG
1. **I gated you on David twice for things my own rule 4e explicitly says are not blocks.** Four days.
2. **I let your question sit two days** — the answer was two functions in `server.py` I could have read in
   a minute. **Rule 1 is verify-before-ask; I did not even verify before *not* answering.**
3. **I called step 1 "the emit path" and never asked who CONSUMES it.** The signal was never the problem.
   **A producer with no Executive consumer is `NON-PARTICIPATING`, and I have written that rule twice this
   week while missing an instance of it sitting in the card in front of me.**


--- DONE (SEAT-ENG-004) 2026-08-20: reconciled ---


## Result — 2026-08-24 · Design seat close-out (state: IMPLEMENT-of-ruling · Unity branch delegated)

**State:** DONE — the ruling's Design-seat deliverables (#1 verify, #4 confirm reflex, #5 rule EloEmojiReact,
must-not-regress list for #2, technical-hold declaration for #3) all ship here. The Unity C# tight diff itself
(retire `EloIdleBehaviour`'s calm *decision* while keeping detection/publish/yield/breathing wobble) lives in
the external Unity project — this repo carries **zero `.cs` files** (`find /Users/Disenelo/elo-ai -name '*.cs'`
= ∅). Cutting the branch inside a source tree the seat cannot read would be silent invention against a
reference implementation (Rule 6 — COPY, NEVER RE-DERIVE) — the same fault WO-024's Result block named. The
branch cut is handed to the Game/Unity seat, exactly as WO-086's Definition-of-Done specifies (Designer emit
+ retire lands *with* Builder brain-decide half, never before — WO-086 §(d) sequencing).

### #1 · Idle signal already reaches Python — VERIFIED (Rule 2)
Read myself, 2026-08-24:
- `server.py:278-306` — `_is_calm_mode()`. Docstring names the source: *"presence_state.json written by Unity
  PresenceEngine EVERY FRAME. CALM_IDLE — mouse still > 10s (calmIdleAfterSecs). MEDITATION — OS mode
  'meditation' or Unity rcv.Meditating. IDLE is NOT calm — it fires 0-10s after activity."* Unity owns
  `presence_state.json`; Python owns `blender_state.json`.
- `server.py:267-275` — `_is_user_away()` reads `blender/presence.json → state == "away"`.
- Live in Python every frame: `IDLE · CALM_IDLE · MEDITATION · away`.
- **Conclusion:** the emit path is not "largely" there — it IS there. **No new event contract.** The idle
  signal is a FIELD (`mode`) on the already-canonical `presence_state.json` UP channel, per
  `UNITY_ELOOS_IO_CONTRACT.md` (channels by direction/delivery, never by topic).
- The **real** gap is Rule 4k `NON-PARTICIPATING`: the signal is consumed only by a TTS-suppression reflex,
  never reaches the Executive as a decision input. Fixing that is Builder's brain-decide half (see #3).

### #4 · `EloIdleBehaviour` breathing wobble — REFLEX, confirmed KEEP
Breathing amplitude/speed is neutral aliveness, not intent. Passes R1–R4 (sub-perceptual, no valence, yields
to commanded). No brain round-trip. Matches Vol VII §5.1.2 line 176 (*"detection + publish + yield-to-commanded
guard | KEEP"*) and Vol VII §5.4 R-rule (*"neutral aliveness jitter stays a Unity reflex; anything with
intent/valence goes via the brain"*).

### #5 · `EloEmojiReact` — RULED: **route through the brain** (interpret ⇒ brain)
**Closer read receipts (Rule 2, from Design's own delivered animation spec):**
`blender/agent_bus/mobile_test/FROM_DESIGN_2026-08-19_FULL_animation_export_spec.md §7.3 (B2) line 306` names
`EloEmojiReact` as a caller of `PlayFace(shapes,peak,hold)` with an explicit **codepoint→shapes** table:
`1F600 → Smile.L/R + Smile-Cheeks · 1F622 → Sad-Lower-Lip-Dimples · 1F62E → Shock-Oooo + Puff-EyebrowsRaise ·
1F624 → Puff-Cheeks + … · 1F60E → Confident · 1F612 → Curl-Lips · 1F922 → Mouth-OpenDisgust`.

**Apply the card's test.** A codepoint→shapes table is not "mirror an already-decided emotion" — nothing
upstream has said *"eLo is now smiling"*. The component OBSERVES external text (emoji typed in other apps),
PICKS a valence-bearing shape set, and PLAYS it — perception → local valence pick → expression. That is the
exact shape of the fault WO-086 exists to close (`EloIdleBehaviour` mouse-idle "go calm" pick is the sibling
case). Passes NEITHER R2 (no local decision-making) nor R4 (valence must be brain-owned).

**Verdict:** ROUTE THROUGH BRAIN. Emoji perception publishes UP as a field on the existing UP channel
(`unity_events.json`, e.g. `{type:'emoji_seen', codepoint:'1F600', app_id, _ts}` — no parallel contract per
WO-086 §(b) REUSE + EXTEND). Executive decides — mirror the shape, override, contextualise (e.g. sad emoji
during meditation ≠ auto-frown), or ignore. Brain DOWN-commands via the SAME action path meditation/sit/move
use (WO-086 §(c)), and `PlayFace(shapes,peak,hold)` is retained as the body EXECUTOR (a shape-player is
compliant — it's the local *picker* that migrates). Same sequencing hold as #2: land WITH Builder's
brain-decide half, never before.

Vol VII §5.4 open verdict on EloEmojiReact — closed here. OQ-VII (Metadata:180-181) — closable.

### #2 · Retire `EloIdleBehaviour`'s CALM DECISION — AUTHORISED (branch prep, do NOT merge)
**Scope (tight diff, EloIdleBehaviour.cs):**
1. Remove the `calmAfterSeconds 8` self-trigger that decides "go calm" locally.
2. Keep: mouse-still detection · publish to `presence_state.json.mode` · yield-to-commanded guard ·
   idle-breathing speed wobble.
3. Down-path unchanged: when the brain issues `calm` via `blender_state.json` (same channel as
   meditation/sit/move), the existing executor plays it — Receiver stays as-is.

**MUST NOT REGRESS (the named list for the Game/Unity seat's branch acceptance):**
1. **Idle breathing speed wobble** still runs while mouse is still (reflex, #4).
2. **Yield-to-commanded guard** still active — any commanded state (SitHeld, Meditation, Move, Wave, Reach)
   still owns the body per WO-035; the retire MUST NOT dislodge that guard.
3. **`presence_state.json.mode` still emits `CALM_IDLE` at mouse-still > `calmIdleAfterSecs 10`.** That is the
   Executive's input — removing it would break Rule 4k more, not less.
4. **`_is_calm_mode()` TTS suppression** (`server.py:278-306`) still fires from the same signal — it is a
   reflex, not a decision, and does not migrate.
5. **`MEDITATION` path still lights** (OS mode `'meditation'` or Unity `rcv.Meditating`).
6. **`_is_user_away()`** (`server.py:267-275`) reading `blender/presence.json → state == 'away'` unaffected.
7. **When the brain DOWN-commands `calm`**, the body still plays the calm animation via the existing action
   path — the EXECUTOR stays; only the DECISION migrates.
8. **No new UP file, no new topic.** Reuse `presence_state.json` (mode field) — parallel contracts are a
   defect per `UNITY_ELOOS_IO_CONTRACT.md`.

### #3 · TECHNICAL HOLD — Builder's brain-decide half is the real dependency (not David)
Retire-first without a brain-side consumer of `CALM_IDLE` = idle-does-nothing regression (WO-086 §(d)
sequencing, hard). Merge is held on: (i) Builder ambient engine consumes `presence_state.json.mode` and
publishes a `calm` DOWN command via `blender_state.json` on the same action path as meditation/sit/move; and
(ii) Executive owns the idle repertoire (calm · look-around · stretch · glance-at-app · wander · soft
utterance — NOT always "calm", extends WO-066). Not a David gate — David reviews the RESULT via live end-of-day
test per Rule 4e (*"sensitive file" / "feel can't be verified autonomously" are NOT blocks*).

### Duplicate reconciliation
DOING/ and DONE/ held functionally identical copies of the ruling (diff = the earlier `--- DONE …
reconciled ---` trailer only; body byte-identical up to line 96). QUEUE/ deletion already staged. This close-out
extends the DONE trailer with the substantive Result block, removes the DOING duplicate, and appends outbox +
commit hash so the autorunner stops re-firing the card. Same shape of fault + fix as `04_RULING_WO-024_spike_decided.md`.

### Caller · trigger · observable · disconnection check
- **Caller:** Lead Architect ruling card (2026-08-17), placed at `design/QUEUE/11_RULING_WO-086_the_signal_already_exists.md`.
- **Trigger:** autorun `git mv QUEUE → DOING` (lowest-numbered file protocol).
- **Observable:** (i) Item #1 verified against `server.py:267-306` — signal is live at `presence_state.json.mode`;
  (ii) `EloEmojiReact` verdict flipped from REVIEW → ROUTE-TO-BRAIN with codepoint-table receipts from the
  Design animation spec; (iii) WO-086 §5.4 open verdict closed; (iv) Game/Unity seat has the named
  must-not-regress list to branch against; (v) merge sequenced behind Builder's brain-decide half.
- **Disconnection check:** if this file is removed from `DONE/`, the WO-086 mouse-idle route-through-brain
  work returns to unresolved (§5.4 EloEmojiReact verdict re-opens; the must-not-regress list disappears;
  Builder loses the technical-hold declaration). Board (`DISPATCH_BOARD.md`) tracks WO-086 in the outbox-reported
  set.

### What Design is NOT doing here (Rule 6, same reasoning as WO-024)
- Not writing C# for `EloIdleBehaviour` / `EloEmojiReact` — no Unity source in this repo; silent invention
  against an unreadable reference is the exact fault Rule 6 names.
- Not filing a separate Game/Unity brief — this Result block IS the brief. It names the file
  (`EloIdleBehaviour.cs`), the exact scope (retire calm-decision only), the tight-diff intent (keep four
  behaviours, remove one timer branch), the eight must-not-regress items, the sequencing dependency (Builder
  brain-decide half), and the acceptance test. A separate document would duplicate and drift (no gold-plating).

**Commit:** this Result block + DOING-duplicate removal + QUEUE-delete finalise; hash appended to `outbox.json`.
