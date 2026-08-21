---
volume: XXV
title: "Temporal Cognition"
status: REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "ARCHITECTURE_BIBLE.md v1.0 (David Charles)"
audit_status: OPEN
canonical_path: docs/architecture/Volume_XXV/
tier: GOVERNANCE
Provenance: [ENGINEERING][CREATIVE]
last_review: 2026-08-10
next_review: TBD
---

# Volume XXV — Temporal Cognition

**One Brain → One Identity.** Temporal Cognition is a **faculty**, not a parallel clock-driver.
It is *asked* by the Executive during assembly of The Moment (ADR-Exec-006) exactly like every
other faculty; it reads the one live clock from World State (Vol XV §2.10) rather than running
a timer of its own. There is one autonomous heartbeat in the runtime — the Agency Engine's
`InternalTick` (Vol V Ch.10) — and this volume never competes with it. Time perception *feeds*
The Moment; it does not drive it.

## Scope (authoritative, from the Bible)
Time perception · scheduling · planning horizons · memory ageing · deadlines · circadian
cycles · temporal reasoning · future simulation · retrospection.

## Whose time this is (scope amendment, 2026-08-10)
**One person: David Charles.** eLo is David's personal companion; the product/sharing track is
PARKED (`DISPATCH_BOARD.md` — *"PERSONAL tool — for David's own use, NOT for sharing"*). This
volume therefore has **no user segmentation** — no "daily user vs monthly user", no
"user-configurable" settings surface. **David's rhythm IS the rhythm.** The circadian model,
planning horizons, and natural-time framing are unchanged as architecture; what changes is that
they are calibrated against one known life, not parameterised for an audience.

Two consequences, both binding on the chapters:
1. **Stated outranks learned.** Where a chapter says "learned cadence", read: *tracked from
   David's actual days, and overridden the moment David states otherwise* — never inferred from
   silence (`CANON_RULINGS_2026-08-10.md`, XXVI). Amendments applied at Ch.1 §1.8/§1.12 and
   Ch.3 §3.3/§3.11.
2. **Open questions go to David, not to a review board.** Software RESERVED collapsed to David
   as both L3 and LG-2 on 2026-08-10; the chapters' "for CA / David" headings are read as
   "for David" for everything in this volume (nothing here is robot-hardware scope).

## Anchors in the live system
- Time domain of World State (Vol XV Ch.2 §2.10: `now_ts`/`part_of_day`/`weekday`; the one
  live, never-stale domain and cold-start anchor). **Read, never re-sensed.**
- Dream/idle circadian cycles (Vol IX §1.3: `DREAM_IDLE_THRESHOLD`=600s,
  `DREAM_COOLDOWN`=3600s, `NREM_MIN_IDLE`=600s; sleep signal). Circadian **context** feeds
  `should_dream()`; this volume never fires the dream.
- Ambient idle cadence (`ambient/ambient_engine.py`: idle utterances 8–20 min, idle animation
  wander 3–8 min). Temporal Cognition **advises** appropriateness; the cadence stays ambient's.
- Memory ageing / forgetting curve (Vol VIII §1.4 — **owned there**). This volume reads
  `strength`/`emotional_weight`; it never decays or writes memory (Memory Ownership invariant).
- Planning horizons + goal tiers (Vol V Ch.10 §7 Agency goals: immediate/short_term/long_term/
  identity). Horizons are a *lens* over those tiers, not a new taxonomy.
- Autobiographical thread (Vol XXI `IdentityState`); verified lived-action timeline
  `self/journals/autobiography.jsonl` (WO-078) is **not yet live** — retrospection wires to it
  when built (spec'd PENDING in Ch.3).

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V25-CH01 | Chapter 1 | Time Perception & Circadian Scheduling | READY FOR REVIEW |
| ELO-V25-CH02 | Chapter 2 | Planning Horizons, Deadlines & Future Simulation | READY FOR REVIEW |
| ELO-V25-CH03 | Chapter 3 | Memory Ageing & Retrospection | READY FOR REVIEW |

## Invariants this volume must never break
1. **Temporal Cognition is a faculty, not a clock loop.** Asked by the Executive; no autonomous
   timer of its own (the only heartbeat is Agency `InternalTick`, Vol V Ch.10).
2. **One clock, read once.** The authoritative "now" is `LiveWorldState.time` (Vol XV §2.10);
   never re-queried mid-turn. All subjective time is a derivation, not a second sensor.
3. **Verified Speech extends to time and autobiography.** Deadlines and remembered pasts are
   spoken only with a verifying anchor; anticipation is private cognition, never asserted as fact.
4. **Memory Ownership.** This volume reads memory strength/timestamps and frames them in natural
   time; it never writes memory or runs the decay curve (Vol VIII owns that).
5. **Presence over engagement.** Circadian/quiet-hours judgement suppresses unbidden chatter, but
   never suppresses a directly-wanted turn.

## Definition of Done
- [x] Three deep chapters authored (time perception + circadian; horizons + deadlines + future
      simulation; memory ageing + retrospection)
- [x] Each: contract + lifecycle + envelope + acceptance tests + open questions
- [x] Grounded in named live anchors (Vol XV §2.10, Vol IX constants, Vol VIII §1.4, Vol V Ch.10)
- [x] Faculty-not-clock-driver invariant enforced throughout
- [ ] David's answers to the flagged open questions (Ch.1 ×4, Ch.2 ×4, Ch.3 ×4) — *amended
      2026-08-10: was "Chief Architect review"; software canon is David's single gate. The CA
      may still advise; it is not a required pass.*
- [ ] David L3 on the proactive-reminder question (Ch.2 OQ-1) — his own rhythm, his own call
- [ ] Audit can mark COMPLETE (blocked on the above + WO-078 for Ch.3 §3.5 timeline path)

**Status: REVIEW** — scope locked; three deep chapters READY FOR REVIEW.
