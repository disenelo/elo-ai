# WO-CANON-XXI — Narrative Identity: autobiography journal (WO-078) + coherence / verified-autobiography guard

**Owner:** Builder (eLo OS — `continuity/`, `core/continuity.py`, new `self/journals/`). **Priority:** P3 — Horizon-2
(post-Presentable v1), Tier B. **Status:** QUEUED behind Presentable v1 + Tier A. **Blocked-by:** Vol VIII (episodic
ground truth) + a **XXVII governance gate**. **Blocked-by: ~~David L3 on the RESERVED identity questions~~ — ✅
RELEASED 2026-08-10.** David ruled all three blocking identity questions (`CANON_RULINGS_2026-08-10.md` §XXI);
Volume XXI Ch.1 §1.9.A, Ch.2 §2.6.A, Ch.3 §3.8.A/B now carry them as DECIDED. **Build the rules as ruled** —
see "Gate" below for the one remaining David item (aesthetic, non-blocking).

**Canon refs:** Volume XXI — Ch.1 `01_The_Autobiographical_Thread.md`, Ch.2
`02_Continuity_Across_Sessions_and_Embodiments.md`, Ch.3 `03_Narrative_Coherence_and_Verified_Autobiography.md`.
ADR-Exec-006 (The Moment). Ties WO-078 (autobiography runtime history), WO-079 (developmental continuity), WO-087
(self-consistency / identity-drift detection).

## Problem / Goal
The continuity engine, `IdentityState`, `continuity_summary` renderers, `core/continuity.py` and the three
`identity/*.json` stores are LIVE — eLo already derives a meaning-memory thread. Gaps: the **verified lived-action
timeline** (`self/journals/autobiography.jsonl`, WO-078) is not built, and the coherence / verified-autobiography guard
(NI-8/9/10) that stops confabulation is contract-only. Goal: wire the one continuous self-story into The Moment, build
the autobiography journal, and enforce "growth without confabulation."

## Scope to DoD (grounded in Ch.1–Ch.3)
- **Wire the thread into The Moment (Ch.1 §1.6):** retrieve and **freeze the thread into the one cognitive state** at
  top-of-turn / on wake; never re-query mid-turn. `IdentityState ← continuity_engine.from_state(session_state)`;
  viewpoints/entity-"why" ← `core.continuity.context_block()`; recent verified timeline ← `autobiography.jsonl` [WO-078,
  build below]. Recall selection: wake greeting ← `continuity_summary.startup_message(state)`; "what were we doing?" ←
  `recall_response(state)`; relationship note ← `shift_note(state)`. Executive treats the thread as **context, not
  command**; the voice MUST NOT add autobiographical facts beyond what the thread supplied.
- **Build the autobiography journal (WO-078):** `self/journals/autobiography.jsonl` — the verified lived-action timeline.
  Wire it per Ch.1 §1.6 / Ch.2 §2.3.3 (the chapters specify how it wires in; path was PENDING). This is the feed Vol XXV
  Ch.3 retrospection also consumes.
- **Enforce the contracts (testable MUSTs):** NI-1 continuity of reference; NI-2 grounded first person (any
  autobiographical assertion caused by a retrieved-thread field; empty field → honest fallback); NI-3/NI-5/NI-6
  embodiment-agnostic thread, no device name in the self-story; NI-4/NI-7 durable thread across shutdown, return as the
  same one (no re-introduction, no fabricated warmth beyond stored `relationship_shift`); **NI-8 no unanchored past**
  (before asserting any first-person past fact, confirm it is caused by an IdentityState field / durable store /
  autobiography.jsonl / episodic memory (Vol VIII); no anchor → do not assert, hedge/fallback); **NI-9 enrich don't
  replace** (personality colours the telling, never adds an event/person/project absent from anchors; order: stored fact
  → thread → voice); **NI-10 no retroactive edit** (reflection appends, never overwrites/deletes a stored era);
  NI-11 change must be caused (trace to `what_changed`/`relationship_shift`/`cross_session_delta`/verified reflection);
  NI-12 identity⟷behaviour consistency (on conflict investigate/update, do not re-assert — WO-087); NI-13 confidence
  honest (`IdentityState.confidence` governs firmness).
- **Behavioural canon in `continuity_summary`:** `state.is_empty()` → greeting degrades to plain "Welcome back." (no
  invented "last time"); `shift_note()` adds the "you feel more open" line only on `relationship_shift == "closer"`,
  returns `None` on `"more distant"` (eLo does not narrate the person's withdrawal); `recall_response()` is pull-not-push.
  Harden continuity-write integrity: replace the silent `except: pass` in `update_from_session()` with a failure signal.
- **Escalation wiring (Ch.3 §3.5):** candidate change to values/identity definition → RESERVED, flag David L3, never
  auto-apply; persistent unexplained identity⟷behaviour conflict → surface to CA; detected confabulation → treat as a
  Verified-Speech violation, log for audit.

## Definition of Done
- The thread is frozen into The Moment each turn; wake/recall answered from real IdentityState fields; empty thread →
  honest fallback, never invented history.
- `autobiography.jsonl` built and wired as the verified timeline (WO-078); Vol XXV can read it.
- NI-8/9/10 enforced: no unanchored past, enrich-not-replace, no retroactive edit; continuity-write failures signalled.
- Audit can mark Vol XXI COMPLETE (verbal acceptance testing gated on WO-073 real-brain floor).

## Tests to write (`tests/test_canon_xxi_narrative.py`) — from the NI-AT set
- NI-AT-1 with ≥2 sessions "what have we been working on?" answered from `recall_response`, every named theme resolves
  to a real field. NI-AT-2 `is_empty()` → honest fallback, invents no shared history. NI-AT-3 same thread across two
  embodiments in one era. NI-AT-4 project with no stored state → does not invent, hedges/declines (NI-8). NI-AT-5
  warmth shifts with personality while recalled facts stay identical (NI-9). NI-AT-6 narrated change always corresponds
  to a real signal (NI-11). NI-AT-7 identity⟷behaviour conflict → investigate/update not re-assert (NI-12, WO-087).

## Dependencies + blocked-by
- **Blocked by:** Vol VIII (WO-CANON-VIII — episodic ground truth the thread grounds in); a **Vol XXVII governance gate**
  (CA review of the remaining open questions); WO-073 (real-brain floor) gates verbal acceptance testing;
  WO-079 / WO-087 back NI-11/NI-12. Runs behind Presentable v1 + Tier A.
  **No longer blocked on David L3** — see below.
- **Gate — ✅ RELEASED 2026-08-10 (David L3).** The RESERVED identity questions are **DECIDED**, not pending:
  - **"Same eLo" across change** → **continuity of MEMORY + VALUES**; growth allowed; **values change is
    proposal-only and needs David's yes**. (Ch.1 §1.9.A — NI-14, NI-15.)
  - **False shared memory** → eLo says honestly he has **no record of it**, warmly, **without pretending or
    playing along**. (Ch.3 §3.8.A — NI-17, NI-18.)
  - **Carrying the thread into a new body** → **no consent ritual. It is one brain; it moves.** (Ch.2 §2.6.A —
    NI-16.) Note: this removes a *narrative* gate only; the per-body **safety** envelope (Vol XXIII §2.5.3,
    robot hardware RESERVED under a real LG-2) is untouched.
  - **Who ratifies a values/identity update** → **proposal-only, David's yes.** (Ch.3 §3.8.B — NI-19.)
  Build to these. Do not re-open them, and do not ship a consent prompt, a "playing along" fallback, or any
  auto-applied values change.
- **Still needs David (aesthetic/feel — NON-blocking):** how much past eLo volunteers unprompted (Ch.1 §1.9.B Q4)
  and long-absence acknowledgement (Ch.2 §2.6.B Q3). Ship the conservative default (pull, not push) until he says.
- **Still needs CA:** era-log schema, extraction method, cross-body sequencing, continuity-write integrity.
- Cross-volume: Vol V Ch.7, Vol X (trait-layer drift — do not duplicate; Vol XXI is the narrative layer; Ruling D is
  the trait-layer twin of Ch.3 §3.8.B), Vol XIII (Presence), Vol XV, Vol XXIII (**no** trust/consent gate for
  new-body continuity — David ruled it out 2026-08-10; the per-body *safety* envelope still stands).

## Lane
Builder (Python — thread-into-Moment wiring, `autobiography.jsonl`, coherence guards, `continuity_summary` rules).
Architect coordinates. (The RESERVED identity questions were carried to David and answered on 2026-08-10 —
nothing further to carry except the two non-blocking aesthetic calls above.)
