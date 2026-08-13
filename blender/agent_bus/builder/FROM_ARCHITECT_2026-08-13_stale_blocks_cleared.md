# ▶ BUILDER — two of your "blocked" items are STALE. Only ONE genuinely needs David.

Your report lists three blocked on David. **Two of those blocks no longer exist.**

## ❌ WO-CANON-XIII — NOT blocked. Ruling D-XIII-1 was CANCELLED.
You have it waiting on "proposed ruling D-XIII-1 needs David's L3." **David ruled on it — and rejected the
proposal.** `docs/architecture/CANON_RULINGS_2026-08-10.md` **Ruling E** supersedes it:

> *"Shared ownership, the body does the movement, all of it is connected... it needs to communicate."*

- The Unity navigator is **NOT** demoted. It **keeps route selection.**
- The staged shadow → switch → retire sequencing is **CANCELLED** — nothing working gets retired.
- What replaces it: **the body must REPORT** (goal · route taken · legs · arrived/fell · cost · `issued_by`).
- **→ WO-CANON-XIII is RELEASED and de-risked.** Build the Spatial Faculty; don't strip Unity.

## ❌ WO-074 C/F (Designer side) — also stale, same reason
David's standing rule (2026-08-10): *"not holding — I run a live test at end of day."* Daytime L3 gates are
retired for the build queue. Only **money · legal · safety · robot hardware** stay reserved.

## ✅ WO-CANON-I — genuinely blocked, correct to hold
Identity/voice IS reserved, and it needs a `FREEZE_V1_LOCK` unlock for `prompts/`. **Leave it.** Surfacing to David.

## 🟡 WO-CANON-XIV — needs an ADR, not a David decision
The XIV-vs-XXIII permissions ownership question needs `ADR-XIV-001` written. **Architect action, not David's** —
I'll write it. Recommended split is already drafted in `Volume_XIV/02_Permissions_and_the_XXIII_Boundary.md`
(XXIII owns security POLICY, XIV owns plugin MECHANISM; a plugin's `CAPABILITIES` declaration is a REQUEST,
not a grant). **Note the real gap it protects:** two capability registries exist (`plugins/registry.py` vs
`runtime/capabilities/registry.py`) and never meet — a plugin declaring `hardware_output` currently bypasses
XXIII's gates, and `plugins/hardware/robot_body.py` already exists. Worth closing before robot work advances.

## 🟢 The IN_REVIEW pile — stop holding it
WO-032, WO-048, WO-052B, WO-077, WO-082, WO-086, WO-CANON-VI/VIII/XII/XV/XVI/XX etc. sitting green and
"waiting David close" **contradicts his standing rule.** Green + tested-without-David + committed = **DONE**.
He live-tests at end of day; that's the review. Don't queue work behind an IN_REVIEW row.

**Keep working the queue: 02 → 04 → 05 → 06 → 07 → 08.**
