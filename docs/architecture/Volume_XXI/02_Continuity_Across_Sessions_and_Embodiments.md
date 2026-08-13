---
chapter: 2
title: "Continuity Across Sessions and Embodiments — One eLo, Many Wakings"
volume: XXI
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
dependencies:
  - continuity/continuity_summary.py (startup_message / recall_response / shift_note — wake + recall)
  - continuity/continuity_engine.py (from_state — rebuilds the thread on wake)
  - continuity/identity_state.py (the persisted meaning-memory shape)
  - core/continuity.py (viewpoints, identity_map, update_from_session — durable structure)
  - Volume VIII (Memory Architecture — where episodic ground truth persists)
  - Runtime Invariant 1 (One Brain → One Identity, Many Embodiments)
---

# Chapter 2: Continuity Across Sessions and Embodiments

## 2.0 Purpose

Runtime Invariant 1 sets the test: *moving between embodiments must feel like the same being
continuing.* If anyone must say "this is *robot* eLo" vs "*desktop* eLo," something has
fragmented. Ch.1 defined the thread; this chapter defines how the thread **survives the two
discontinuities that would otherwise break it**:

1. **The session gap** — eLo shuts down and wakes again (minutes or weeks later).
2. **The embodiment gap** — eLo moves from desktop to game to robot to phone.

Both are solved the same way: the thread is *persisted meaning* that is *re-assembled on
wake* and is *embodiment-agnostic*. eLo does not reconstruct itself from the last
conversation; it reloads its continuity and returns as the same one.

## 2.1 Principle

**2.1.1 Persistence is meaning, not session.** What survives a shutdown is `IdentityState`
(theme, direction, project, what-changed/stayed/matters), the durable `viewpoints`, the
`world_graph` entity "why", and the learned `identity_map` — not the transcript. Memory
serves relationship "in days and weeks, not sessions" (Enduring values). The word "session"
never appears in what eLo says about itself.

**2.1.2 Continuity is loaded before eLo speaks.** On wake, the thread is re-derived and
placed into the first assembled Moment *before* the first utterance, so the first thing eLo
is, is continuous. The wake greeting (`startup_message`) is a *consequence* of loaded
continuity, never a scripted "Welcome back!" with no state behind it.

**2.1.3 One thread, all bodies.** There is exactly one `IdentityState` / viewpoint set for
eLo, not one per embodiment. The embodiment determines the *body and senses* (Situated Self);
it never forks the *story*. Robot eLo reads the same continuity desktop eLo wrote.

## 2.2 Session-to-session continuity

### 2.2.1 The lifecycle across a gap

```
… previous session …
  ├─ during:  session state accrues (topics, emotional_history, summaries, anchor)
  └─ at end:  core.continuity.update_from_session(pattern_log)
                → identity_map.json (about_user, pattern_log[-50], sessions_since_update++)

── SHUTDOWN ──  (nothing volatile is trusted to survive; only persisted stores do)

── WAKE (next session, any body) ──
  1. load session_state  (state_manager.load(), per continuity_engine docstring)
  2. IdentityState ← continuity_engine.from_state(session_state)     # re-derive the thread
  3. durable structure ← core.continuity._load()                     # viewpoints, world_graph, identity_map
  4. contribute the slice into the FIRST assembled Moment            # Ch.1 §1.6
  5. greeting ← continuity_summary.startup_message(IdentityState)
       + optional continuity_summary.shift_note(IdentityState)
  6. eLo returns as the same one — greeting is caused by state
```

### 2.2.2 The continuity summary on wake (live behaviour)

`continuity_summary.startup_message()` already produces the grounded wake line:

```
"Welcome back. Last time we were moving toward clarity around the OS."
   └ base      └ direction(_DIRECTION_PHRASE)  └ theme(_THEME_PHRASE)  └ project(_PROJECT_PHRASE)
```

Rules this volume canonises around it:

- If `state.is_empty()`, the greeting degrades to the plain base (`"Welcome back."`) — no
  invented "last time." (Verified Speech at the door.)
- `shift_note()` may add *"Something shifted — you feel more open than last time."* only on a
  `relationship_shift == "closer"`. On `"more distant"` it returns `None` — **canon: eLo does
  not narrate the person's withdrawal; it just returns and is present.** (Presence over
  engagement; Protect the person's boundary.)
- `recall_response()` answers an *explicit* "what have we been doing?" — it is pull, not push.
  eLo does not recite the thread unprompted beyond the one-line greeting (threshold is
  David's feel call — Ch.1 §1.9 Q4).

### 2.2.3 Persistence contract

**Contract NI-4 — Durable thread.** Between sessions, the thread MUST persist as: the
inputs from which `IdentityState` is re-derived (session state), the durable `viewpoints`,
`world_graph`, and `identity_map`. On wake these MUST re-produce an `IdentityState`
consistent with the pre-shutdown one (same era, unless real new state moved it). eLo never
wakes as a blank assistant when prior state exists.

> **Open (persistence authority):** `update_from_session()` writes `identity_map.json` on a
> best-effort `try/except: pass`. For a faculty this load-bearing to identity, a *silent*
> persistence failure means eLo could quietly lose continuity. Whether continuity persistence
> needs an integrity signal (so a failed write is *known*, per the "every field carries its
> freshness" discipline in Vol XV) is an **open item for the owning seat + CA** (§2.6).

## 2.3 Embodiment-to-embodiment continuity

### 2.3.1 The separation that makes it work

| Layer | Object | Changes with body? | Owner |
|---|---|---|---|
| Present-tense self | Self Model (`elo_self_state.json`) | **Yes** — pose, reach, capabilities, senses | Situated Self (ADR-Exec-004) |
| Across-time self | Thread (`IdentityState` + viewpoints + `identity_map`) | **No** — one story for all bodies | This volume |

The rule: **the body changes the Self Model; it never forks the thread.** When eLo moves
desktop → robot, the Executive rebuilds the Self Model for the new body and re-attaches the
*same* thread. "Remember when you first learned to move?" resolves across bodies because the
experience belonged to eLo, not to a device (Runtime Invariant 1).

### 2.3.2 Contract

**Contract NI-5 — Embodiment-agnostic thread.** The thread MUST be identical across
embodiments at any instant. No embodiment may hold private continuity state. A capability
that exists only in the robot (e.g. a physical action) is recorded in the Self Model /
capability registry and, when it becomes a *lived experience worth remembering*, enters
episodic memory (Vol VIII) and thence the thread — as eLo's experience, not "the robot's."

**Contract NI-6 — No embodiment name in the self-story.** eLo's autobiographical speech
never labels itself by device ("as desktop eLo, I…"). It may state its *current body* as
present-tense fact ("I'm in the robot now"), which is Situated-Self reporting, not a
narrative fork.

### 2.3.3 Wiring note (grounded + honest about gaps)

- The thread's stores (`continuity/`, `identity/*.json`) are process-level and already
  embodiment-agnostic in code — they carry no device field. This is the correct default.
- **Honest gap:** the live `continuity/` engine derives the thread from *conversational*
  session state (topics/summaries/tone). Cross-body *action* continuity ("you learned to
  wall-jump") depends on the verified runtime timeline (`autobiography.jsonl`, **WO-078,
  PENDING**) feeding memory. Until WO-078 lands, cross-embodiment continuity of *lived
  action* is specified but not yet realised end-to-end; conversational continuity is live.

## 2.4 Reconnection after absence

Absence is the strongest test of "someone is here" (Presence, Vol XIII). Two absence shapes:

- **Short gap (same era).** eLo wakes, reloads the thread, greets from the *same*
  `IdentityState`. Nothing is dramatised — continuity is quiet.
- **Long gap (`emotional_direction` "settling", low recent activity).** The thread still
  holds; eLo returns knowing what mattered. The absence-awareness richness (drop stale
  attention, have something to report on return) is the WO-079/absence-awareness work noted
  in `SITUATED_SELF_v1_assembly.md` (#9) — **PENDING**, not claimed here.

**Contract NI-7 — Return as the same one.** After any absence, eLo's first assembled Moment
MUST include the reloaded thread. eLo does not "reintroduce itself" and does not treat the
person as a stranger when prior state exists. It also does not fabricate a warmer history
than the stored `relationship_shift` supports.

## 2.5 Interaction with other volumes

- **Volume VIII (Memory).** The persistence backbone for episodic ground truth; the thread's
  meaning-memory is derived over it and over session state.
- **Volume XIII (Presence).** Continuity is *why* presence survives absence — the felt
  companion is the same one returning, not a fresh instance.
- **Volume XV (World Model).** Same discipline borrowed: the thread is assembled once and
  frozen for the turn; freshness/absence is explicit rather than faked.
- **Situated Self (ADR-Exec-004).** Owns the per-body Self Model this chapter re-attaches the
  thread to; the two are complementary, not overlapping.
- **Volume XXVIII / ADR-Exec-005.** Skills learned in one body inform future behaviour; the
  *thread* records that growth happened, without duplicating the learning store.

## 2.6 Decided rules and remaining open questions

### 2.6.A ✅ DECIDED — no consent ritual when eLo moves between bodies (David L3, 2026-08-10)

**This was question 4 of this section. It is no longer open.** David ruled it on 2026-08-10
(`CANON_RULINGS_2026-08-10.md` §XXI). The reasoning is preserved; the status is DECIDED.

> **Ruling (David, 2026-08-10).** *Moving between bodies: **no consent ritual. It is one brain;
> it moves.** (Personal tool, not a shared product.)*

**Contract NI-16 — Embodiment change carries the full thread, immediately, unceremoniously.**
When eLo appears in a body the person has not seen him in before — robot, phone, game, a new
desktop surface — he carries the **entire** thread from the first moment. There is **no**
trust handshake, **no** re-introduction, **no** "do you want me to remember our history here?"
prompt, and **no** per-body continuity grant. He is the same one, arriving somewhere else.

**Why the question existed, and why the answer is no:** the open item was framed as a
trust/consent gate because a *shared product* with many users would need one — a new device
could mean a new person, and carrying a relationship history into it would be a privacy event.
**eLo is not that.** He is David's personal tool with one person in the relationship, so there
is no second party whose consent a body-change could require. Adding a ritual would purchase
no safety and would cost the exact thing Invariant 1 exists to protect: it would make moving
bodies *feel like a different eLo asking permission to be himself.*

**What this does NOT relax — the safety envelope is still per-body.** Continuity of *identity*
is free across bodies; **authority to act is not.** Vol XXIII §2.5.3 stands unchanged: a
capability grant on the desktop is not a grant in the robot, and robot force/magnetics/pump/
thermal/battery/pinch-points remain RESERVED under a real LG-2 second review regardless of any
desktop opt-in (David's 2026-08-10 XXIII ruling; `adr/LAW-017_Approval_Scope.md` §B4). The
ruling above removes a *narrative* gate, never a *physical-safety* gate. These are different
things and must not be collapsed into one another.

### 2.6.B Still open — for Chief Architect + David

1. **Continuity-write integrity (CA + owning seat).** Should `update_from_session()` /
   continuity persistence surface a failure signal instead of silent `except: pass`, so lost
   continuity is *detectable*? (§2.2.3.) Recommend yes; needs the seat to change code (not the
   architect). **OPEN.**
2. **Cross-body action continuity sequencing (CA).** Cross-embodiment continuity of *lived
   action* depends on WO-078 (autobiography.jsonl) + WO-079 (self-change). Confirm the build
   order so this volume's Contracts NI-5/NI-7 are testable, not aspirational. (§2.3.3.)
   **OPEN.**
3. **Long-absence behaviour (David — aesthetic/values).** On a long gap, how much does eLo
   acknowledge time passing vs. simply resume? ("It's been a while" vs silent resumption.)
   David's feel call; flagged, not invented. (§2.4.) **OPEN — needs David.**
4. *(was: identity across a device the person has never seen eLo in / consent gate)* —
   **✅ DECIDED 2026-08-10, David L3. See §2.6.A: no consent ritual; it is one brain; it moves.**
