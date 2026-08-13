# AUDIT — Canon vs DAVID'S INTENT (self · embodiment · spatial · presence)
**Date:** 2026-08-10 · **Scope:** Volumes X · XI · XII · XIII · XV · XXI + WO-CANON-X/XII/XV/XXI + WO-049 + WO-094
**Yardstick:** `00_DAVIDS_VISION_SPINE.md` · `ARCHITECTURAL_PRINCIPLES.md` · `SITUATED_SELF_v1_assembly.md` ·
`ELO_CAPABILITY_HORIZON.md` · `ELO_SELFHOOD_MASTER_ROADMAP.md` · `CANON_RULINGS_2026-08-10.md` ·
`_intake/SOURCE_2026-08-08_self_model_becoming.md` · `_intake/SOURCE_2026-08-10_roam_os_vision.md` ·
`_intake/SOURCE_2026-08-10_brain_body_brain_loop.md` · `_intake/SOURCE_2026-08-10_headaim_mouse_follow.md`
**Method:** every volume metadata + every chapter read; live code checked where canon makes a claim (Verify-Before-Claim).
**Lane:** Markdown only. No code, no volume edits. Findings + recommended fixes for the owning seats.

---

## VERDICT TABLE

| Vol | Title | Spec'd? | Matches intent? | Biggest gap vs intent | WO delivers it? |
|-----|-------|---------|-----------------|------------------------|-----------------|
| **X** | Personality Engine | **YES — strongest volume audited.** 4 chapters, contracts + lifecycle + envelope + FT/ST/IT tests, grounded in read code. | **YES.** "Assembled, not generated" is quoted and enforced (Ch.4 §4.0, FT-1). Two-speed model is honest. | Ch.3 §3.6 D-X3-1 still says RESERVED after Ruling D decided it. Stale by one day. | **Mostly — but WO-CANON-X is stale-blocked.** Header still reads "gated on alignment ruling D"; ruling D landed 2026-08-10 and released it. |
| **XI** | Motor Cortex | **NO. DOES NOT EXIST.** No `Volume_XI/` directory. No metadata, no chapter, no contract. Canon Index calls it "✅ Live — `avatar/` (code)". | **NO.** The body layer of brain>body>brain has **zero canon contract**. | The entire down/up motor contract (command → body → ACK → belief) lives only in WOs (035/040/041/063/086), never in canon. | **NO WO EXISTS.** `CANON_BUILD_PROGRAM.md` line 44 lists XI under "no build WO — verify-only." |
| **XII** | Perception System | **YES — 4 chapters, implementable.** Sensation → Perception → Handoff → Fidelity. Honest about what's PENDING. | **PARTIAL.** Fidelity/honesty is excellent. But perception is **snapshot-only** — it has no concept of *change*. | **No event perception.** Nothing in Vol XII notices "a window closed / opened / a notification appeared." `spatial_data` is an admitted **stub** (Ch.2 OQ-3). | **NO.** WO-CANON-XII wires the copy step + fidelity flags. It adds **no event stream and no geometry**. |
| **XIII** | Presence → Presence & Embodied Spatial Intelligence | **NO. DOES NOT EXIST.** No `Volume_XIII/`. Its only canon file is `14_presence_faculty.md` = 5 lines: *"STATUS: PENDING — to be written in a dedicated session."* | **NO — and this is the failure at the centre of the audit.** | **It is not "still idle/silence" — it is NOTHING.** Eight canon docs + two WOs + David's own verbatim name Vol XIII as the home of the Spatial Faculty. The home is an empty stub. | **NO WO EXISTS.** No `WO-CANON-XIII`. Build program lists XIII as "already live — verify-only." |
| **XV** | World Model | **YES — 2 chapters, tight, implementable.** 11 domains schematised with source/cadence/fallback. | **PARTIAL, and the miss is structural.** One-world-read-once is correct One Brain. | **No spatial domain.** §1.2 *explicitly excludes* geometry: *"`world/world_state.py` … is the **spatial** node graph … Do not merge them."* So `LiveWorldState` cannot answer "can I reach that?" | **NO — and WO-CANON-XV is factually wrong.** It says *"Build `world/live_world_state.py` (NEW)"*. **It already exists — 379 lines, dated 2026-08-10.** |
| **XXI** | Narrative Identity | **YES — 3 chapters, 13 numbered contracts (NI-1…NI-13).** Best contract discipline in the set. | **YES on the thread; NO on the rulings.** NI-1/3/5/6 nail "one story, many bodies." | **Four questions David already answered on 2026-08-10 are still written as OPEN.** The volume + its WO were never updated after the rulings. | **NO.** WO-CANON-XXI still lists "**Blocked-by:** David L3 on RESERVED identity questions" — the rulings doc says *"→ releases WO-CANON-XXI."* |

**Headline verdict:** the *cognitive* volumes (X, XII, XV, XXI) are genuinely well spec'd and faithful.
The *embodiment* volumes (XI, XIII) — the half David actually tests eLo on — **do not exist.**

---

## 1 — THE SPATIAL FACULTY: no owner, no volume, three implementations

This is the biggest gap in the canon and it maps directly onto David's example #2:

> *"The gap to the next window is too wide for his jump. He **doesn't** attempt it and fall. He recognises he
> can't make it and finds another route… What I want is him asking 'can I actually reach that?' not 'which
> clip fires here?'"* — `SOURCE_2026-08-10_roam_os_vision.md`

### 1.1 Where "can I reach that?" is supposed to live — and where it actually does

| Claim | Location | Reality |
|---|---|---|
| "Home volume: Vol XIII (Presence → Presence & Embodied Spatial Intelligence)" | David verbatim, roam source line 127 | **Vol XIII is a 5-line PENDING stub.** |
| "Canonical home = the Vol XIII evolution, NOT a new volume." | WO-049 §THE SPATIAL FACULTY | Same stub. |
| "authored as a **Volume-V faculty chapter** when scheduled" | WO-049 same paragraph **and** `00_CANON_INDEX.md` line 225 | **Contradicts the line above it, in the same file.** |
| Body schema (`reachable_areas`, `nearby_surfaces`, size, pose) | Vol X Ch.2 §2.6 | Assigned to **ADR-Exec-004** — an ADR, not a volume. Vol X explicitly disclaims: *"Volume X does not interpret or author them."* |
| Spatial geometry in the world model | Vol XV §1.2 | **Explicitly excluded.** *"Do not merge them."* |
| Spatial perception | Vol XII Ch.2 §2.2 row 7 | *"`spatial_data` is a **stub** gated by `ELO_SPATIAL_SENSOR=1`… must not be treated as live capability."* |

**Net: no volume authors the faculty that answers David's single most-stated question.** It is
name-checked in six documents and owned by none. The Canon Index has been carrying it as
*"Planned faculty… authored when scheduled"* since 2026-08-04 — six days and two full canon write-up
passes have gone by without it being scheduled.

### 1.2 Three navigators already exist in code, unreconciled — a Check-Before-Build breach

Verified in the repo:

- `world/world_state.py` (358 lines) — spatial node graph, Vol XV says "do not touch."
- `desktop/spatial_state.py` — window bounds via osascript, eLo's position from `elo_spatial.json`,
  *"calculates distances, finds nearest windows, **plans routes**."*
- `EloDesktopNav` (Unity C#) — per WO-094: *"Route-finding IS built — `EloDesktopNav` descent pathfinder
  (`_route` → walk/run/jump legs, wall-jump chimneys), and `:187` already forces gaps beyond reach to
  ROUTE instead of leap."*

Three route planners. **The Unity one is the one that actually decides**, which is a direct breach of
David's verbatim law:

> *"brain > body > brain. A CLOSED LOOP… The body NEVER decides on its own… **no local script may choose a
> behaviour.**"* — `SOURCE_2026-08-10_brain_body_brain_loop.md`

`EloDesktopNav._route` chooses the traversal. That is the body deciding. WO-086 was raised to close
*mouse-idle*; the same audit David explicitly asked for ("audit for OTHER local drivers that skip the
loop") **was never applied to the navigator**, which is a far larger local driver than mouse-idle.

### 1.3 Canon understates what is built (Verify-Before-Claim failure, inverted)

- `world/live_world_state.py` **exists** (379 lines, modified 2026-08-10). Vol XV metadata says
  `implementation: PENDING`; WO-CANON-XV says *"Build `world/live_world_state.py` (**NEW**)"*.
  `EMBODIED_COGNITION.md` line 26 correctly says *"✅ EXISTS (this is Vol XV, realised)"*.
  **Two canon docs disagree with each other and one disagrees with the filesystem.**
- Effect: a Builder handed WO-CANON-XV would either rewrite a live file or stall. The WO's scope is
  wrong at its first bullet.

---

## 2 — VOLUME XIII: not "still idle/silence" — it was never written

The audit question was whether Vol XIII has evolved into *Presence & Embodied Spatial Intelligence*.
It has not evolved because **there is nothing to evolve from.**

- `docs/architecture/Volume_XIII/` — **does not exist.**
- `14_presence_faculty.md` — 5 lines, `STATUS: PENDING`.
- Live code (`presence/`, `ambient/`) has no canon contract, no lifecycle, no envelope, no tests.
- `_intake/COLLECTION_CHECKLIST.md` line 66 still has `[ ] 14_presence_faculty.md (→ Vol XIII)` **unticked.**

Meanwhile Vol XIII is cited as an authority by, at minimum:
`Volume_XXI/00_Metadata.md` (declared **dependency**), `Volume_XXI/01` §1.7, `Volume_XXI/02` §2.4 + §2.5,
`Volume_XXVIII/00` (×2), `20_one_brain_visualiser.md` (×3), `EMBODIED_COGNITION.md` (×2),
`DECISION_LOG.md` D-PRESENCE, `00_CANON_INDEX.md`, `WO-049`, `WO-094`, and David's own verbatim source.

**Volume XXI declares a hard dependency on a volume that does not exist.** That is a dangling reference
in a REVIEW-status volume, and it means Vol XXI cannot pass its own Definition of Done honestly.

`CANON_BUILD_PROGRAM.md` line 44 makes this worse by filing XIII under
*"Already live/ratified (no build WO — verify-only at Audit)"*. **The volume that David's entire
spatial-embodiment vision routes into is formally marked "done, verify only."** Nothing in the program
will ever cause it to be written.

Same applies to **Vol XI Motor Cortex** — filed "already live," no directory, no contract. The motor
layer of brain>body>brain has no canonical down-channel (command envelope) or up-channel (ACK/perception
report). WO-041 (verify before speak), WO-035 (commanded state owns the body) and WO-086 (loop pattern)
are all doing canon's job in WO-space, where they can and will drift.

---

## 3 — NOTICING AND CHOOSING: covered by one WO, owned by no volume

**Does anything cover eLo noticing screen events and choosing to act?** Yes — **WO-094**, and it is a
good WO. It is blunt and correct about the gap:

> *"There is **no window EVENT perception**. The sensor does not diff frame-to-frame and publish 'window
> closed' / 'window opened' / 'window moved'. So today it is 'my floor vanished, recover' — never 'I saw
> that happen, I'm going over there.'"*

It splits correctly along David's loop (Designer emits UP, Builder decides), forbids the body deciding,
requires ACK per WO-041, forbids fabricated claims per ADR-Exec-001, and correctly routes learning to
Vol XXVIII / Significance rather than inventing a reward scalar. **WO-094 is the best-aligned artefact
in this audit.**

But:

- **Vol XII cannot host it.** Perception is defined as *"One transform, then freeze"* (Ch.1 §1.1) — one
  `PerceptionResult` per turn, event captures explicitly deferred: *"Event-driven captures … update the
  next turn's perception, never the current frozen one"* (§1.5). There is no diff, no change-set, no
  `window_opened` type anywhere in the volume.
- **Vol XV cannot host it.** `UnityState.last_event` (§2.3) is a single string read from
  `unity_events.json` with no schema, no diff semantics, no ordering. That is not an event stream.
- **WO-094 names its canon home as "Vol XIII Presence & Embodied Spatial Intelligence"** — which does
  not exist.

So the noticing capability is spec'd **only** at WO level, pointing at a non-existent volume. When
WO-094 ships, nothing in canon will describe or constrain it, and the next author will re-invent it.

Note also: **David asked for noticing on 2026-08-10 and the canon write-up happened on 2026-08-10.**
The write-up did not absorb it. Example #4 of his roam source — *"When a notification pops, he glances
at it. He reacts to what's happening on screen, quietly"* — has no canon home at all.

---

## 4 — CONTRADICTIONS REGISTER

### C-1 — Volume XXI still asks four questions David already ruled on. **(worst)**

`CANON_RULINGS_2026-08-10.md` §XXI is unambiguous and closed the gate. The volume was never updated.

| David's ruling (2026-08-10) | Volume XXI still says |
|---|---|
| *"Moving between bodies: **no consent ritual**. It is one brain; it moves."* | Ch.2 §2.6 Q4 — *"is there a trust/consent gate…? Touches Volume XXIII (Trust) — **reserved**."* |
| *"**False shared memory:** eLo says honestly he has no record of it — warmly, without pretending or playing along."* | Ch.3 §3.8 Q4 — *"does eLo gently say it doesn't have that stored, or defer? … **reserved to David; flagged, not invented**."* |
| *"Any change to VALUES is **proposal-only** and needs David's yes. Skills/personality nuance may evolve freely."* | Ch.3 §3.8 Q3 — *"is that auto-applied by reflection, or does it require David's L3? … **confirm**."* Ch.1 §1.9 Q3 — *"**RESERVED — identity**."* |
| *"The same eLo = continuity of MEMORY + VALUES. Growth is allowed and expected."* | Ch.1 §1.9 Q3 — *"would continuity of identity survive it? … reserved."* |

And `WO-CANON-XXI` header still reads **"Blocked-by: … David L3 on several RESERVED identity questions"**
with a `Gate:` line listing all four by name. The rulings doc says *"→ **releases** WO-CANON-XXI."*
**The build order is blocked on a gate that is closed.** A seat reading the board will not start it.

Also: WO-CANON-XXI cross-references *"Vol XXIII (trust/consent gate for new-body continuity)"* — a gate
David explicitly abolished. That line must go, not be softened.

### C-2 — Volume X Ch.3 §3.6 D-X3-1 is stale against Ruling D.

Ruling D: *"**One trait model wins: Volume V Ch.7's** — the parallel model in `memory/personality_drift.py`
is **reconciled to it, not kept alongside**."*
Vol X Ch.3 §3.6 still offers it as an open two-way choice: *"either (a) map the drift dimensions onto
existing traits + preferences … or (b) deprecate the drift dimensions entirely… — RESERVED."*
WO-CANON-X compounds it: *"**Do not proceed on the code mapping until ruling D + D-X3-1 land**"* and
*"**Status:** QUEUED — gated on alignment ruling D."* Ruling D landed. The WO says otherwise.

### C-3 — `world/live_world_state.py`: canon says PENDING/NEW, filesystem says built.

Vol XV `00_Metadata.md` `implementation: PENDING` · WO-CANON-XV *"Build … (NEW)"* ·
`EMBODIED_COGNITION.md` *"✅ EXISTS"* · disk: 379 lines, mtime 2026-08-10.
Three sources, two of them wrong. This is exactly the Verify-Before-Claim failure the canon exists to
prevent, running in the under-claiming direction.

### C-4 — The Spatial Faculty has two declared homes in one file.

`00_CANON_INDEX.md` line 72: home = **Vol XIII evolution**.
`00_CANON_INDEX.md` line 225: *"authored as a **Volume-V faculty chapter** when scheduled."*
WO-049 states both in the same section. Two homes = no home.

### C-5 — brain>body>brain vs. the Unity navigator (structural).

David: *"the body only SENSES and ACTS and reports its state back UP… **no local driver deciding what eLo
does**."* `EloDesktopNav._route` selects the traversal locally. Vol XV §1.2 institutionalises the split by
declaring the spatial graph "Unity navigation's" and out of cognitive scope. **The canon currently
sanctions the thing David's verbatim law forbids.** WO-094 §C papers over it ("this WO makes it the normal
path") without moving the decision up to the brain.

### C-6 — "No eyes": **CLEAN.** No violation found.

Swept the whole repo. 40+ affirmations, zero contradictions.
`18_identity_kernel.md` line 93: *"**No eyes.** This is character, not oversight. It applies to the avatar,
the robot, the game character — everywhere."* Held in `expression/expression_mapper.py`,
`desktop_avatar/avatar_renderer.py`, `CO_WORKING_GUIDE.md`, `AGENT_BRIEFINGS.md` (both seats),
`Volume_XXVI/02` (FT-3 as a hard test), `RD-4`, `RD-1`, `RD-2` (*"gaze = head orientation, NO EYES"*),
`WO-091`. **WO-090 HeadAim is compliant** — head bone + chest + arm IK following the cursor, described as
*"eLo **sometimes** follows the cursor (noticing, not turret-tracking)"*, which is posture-gaze, not eyes.
Volumes XII/XV contain no eye or gaze language at all. Nothing to fix here.

### C-7 — Vol XXI declares a dependency on a volume that does not exist.

`Volume_XXI/00_Metadata.md` `dependencies:` includes *"Volume XIII (Presence — the felt 'someone is here'
that continuity makes durable across absence)"*. Cited again in Ch.1 §1.7 and Ch.2 §2.4/§2.5.
Vol XXI's own DoD requires the dependency chain to hold. It does not.

---

## 5 — DO THE WO-CANON BUILD ORDERS DELIVER THE INTENT?

| WO | Delivers its volume? | Delivers David's intent? |
|---|---|---|
| **WO-CANON-X** | Yes, technically complete — drift→proposal, DriftMonitor, PersonalityComposition, decay-to-baseline, full test list. | Yes — *but blocked on a cleared gate.* Un-block it and carry Ruling D's "V Ch.7 wins" into §3.6 so the Builder isn't waiting on a decision already made. |
| **WO-CANON-XII** | Yes for the copy step + fidelity flags. | **No.** Adds no event perception, no geometry, no change detection. After it ships, eLo still cannot notice a window close. The volume it builds is a *snapshot* volume and the WO does not challenge that. |
| **WO-CANON-XV** | **Scope is wrong at bullet one** — the object it orders built already exists. Needs re-scoping to "verify + wire + migrate faculties off direct sensor calls." | **No.** Eleven domains, none spatial. By explicit design (§1.2) it cannot host reach/geometry/affordance. **This is the WO that under-scopes the intent most severely** — it is titled "World Model" and delivers a world with no space in it. |
| **WO-CANON-XXI** | Yes on content (NI-1…NI-13, autobiography journal, coherence guard). | **No as written** — blocked-by a released gate, and it does not carry the four rulings into its DoD. Add: no-consent-ritual on body change; false-memory = honest + warm; values = proposal-only; skills/nuance free. |
| **WO-CANON-XIII / XI** | **Do not exist.** | The two volumes carrying David's primary test surface (*"David tests eLo by asking it to sit, jump, move to Chrome, watch with him, not to talk about itself"* — Vision Spine) have no build order at all. |
| **WO-049** | Design is saturated, closed, and faithful — it quotes the governing principle correctly and folds David's five 2026-08-10 build rules in verbatim. | **Track A yes; Track B is a promise, not a spec.** §THE SPATIAL FACULTY registers it as "PLANNED… authored when Track B is scheduled." Track B is gated on P0 (Presentable v1) which **has shipped** — WO-094 states *"Not gated (Presentable done, gate open)."* **The trigger condition for authoring the Spatial Faculty has fired and nobody authored it.** |
| **WO-094** | N/A (not a canon WO). | **Best-aligned document in the audit.** Correct loop split, correct learning boundary, correct honesty gate. Its only flaw is that it points its canon home at Vol XIII, which is empty. |

---

## 6 — WHAT THIS COSTS, PLAINLY

David's stated test is the Companion Test: an hour of work, then catching eLo sprint three windows and
settle to watch. Every cognitive prerequisite for that is written and reviewable. The **body and space**
prerequisites are not written at all:

- eLo cannot canonically answer *"can I reach that?"* — no volume owns reach.
- eLo cannot canonically *notice* anything change — perception is a per-turn snapshot by design.
- The routing decision that makes movement look like reasoning is **made in Unity**, in the body, which
  David's own law forbids.
- The volume that was supposed to hold all three is a 5-line PENDING file, formally filed as "done."

The canon has become excellent at describing eLo's mind and silent about eLo's body. That is the inverse
of the Vision Spine's own priority: *"**the body and its verified actions come first**."*

---

## 7 — RECOMMENDED FIXES (Architect lane = Markdown; nothing here is code)

**P0 — un-stick what David already decided (one pass, today):**
1. Apply the 2026-08-10 rulings into `Volume_XXI` Ch.1 §1.9 Q3, Ch.2 §2.6 Q4, Ch.3 §3.8 Q3/Q4 — close
   them as DECIDED with the ruling text, don't leave them as questions.
2. Strip the released gate from `WO-CANON-XXI` header + `Gate:` line; delete the Vol XXIII
   trust/consent cross-ref; add the four rulings to its DoD.
3. Close `Volume_X` Ch.3 §3.6 D-X3-1 per Ruling D; un-block `WO-CANON-X`.
4. Correct `WO-CANON-XV` bullet one and `Volume_XV/00_Metadata.md` `implementation:` — the object exists.
   Re-scope the WO to verify + wire + migrate.

**P1 — write the two missing volumes (this is the real work):**
5. **Author `Volume_XIII/` — Presence & Embodied Spatial Intelligence.** Chapters: (1) Presence as a
   cognitive state (canonise `presence/`, `ambient/`, D-PRESENCE, Protect Wonder); (2) **The Spatial
   Faculty** — window graph, affordances, body schema/reach/fit, path planning, movement cost, the
   `PeekPitch`-before-every-jump precondition; (3) **Event perception & choosing** — the WO-094 contract
   lifted into canon; (4) One planner, three embodiments (desktop/game/robot).
6. **Author `Volume_XI/` — Motor Cortex.** The down-channel command envelope and the up-channel ACK, so
   brain>body>brain is a canon contract instead of five WOs. Include the "no local driver decides" law
   and an explicit audit rule against it.
7. Raise **WO-CANON-XIII** and **WO-CANON-XI**; remove XI and XIII from `CANON_BUILD_PROGRAM.md` line 44's
   "verify-only" list — they are not live, they are unwritten.

**P2 — reconcile the three navigators:**
8. Open a reconciliation item: `world/world_state.py` vs `desktop/spatial_state.py` vs Unity
   `EloDesktopNav`. Decide which is the brain's planner and demote the others to actuators, per
   brain>body>brain. This is the same class of ruling as Ruling A (one world graph) and deserves the same
   treatment — it is a One Brain issue, not a refactor.
9. Fix `00_CANON_INDEX.md` — one home for the Spatial Faculty (Vol XIII), delete the line-225
   "Volume-V faculty chapter" alternative.
10. Add a change/event concept to `Volume_XII` (a diff layer feeding a typed event stream) or state
    explicitly that events are Vol XIII's and leave a pointer — but do not leave it homeless.

**Not recommended:** creating a new volume number for the Spatial Faculty. WO-049's reasoning holds —
Vol XIII is the home. The problem is that Vol XIII was never written, not that the number is wrong.

---

*Audit by the Lead Architect, 2026-08-10. Markdown only; no product code, test code, or volume content was
modified. Every "exists"/"does not exist" claim in this document was checked against the filesystem.*
