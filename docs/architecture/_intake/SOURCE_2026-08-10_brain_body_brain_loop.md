# VERBATIM — primary source, do not summarise

**Origin:** David, 2026-08-10, relayed via Design (SEAT-ENG-004) outbox `new_board_item_for_architect`.
**Captured by:** Lead Architect autonomous loop, 2026-08-10 09:45 (Rule 4b — capture David's in-depth material verbatim; WOs reference this, never replace it).
**Carried by:** WO-086 (Mouse-Idle Through Brain) — the first application of this pattern. No separate WO-083 authoring (the proposed WO-083 number is already used by Identity_And_Meaning_Convergence; the mouse-idle proposal folded into greenlit WO-086).

---

## The loop model (David's words, verbatim)

> brain > body > brain. A CLOSED LOOP: the brain decides + drives the body (DOWN), the body only SENSES and ACTS and reports its state back UP, and the brain reads that back and decides again. The body NEVER decides on its own. Mouse-idle is just one PERCEPTION feeding this loop — not a special case. The generalisable rule the Architect should check: every body perception (mouse-idle, occlusion/behind-window, perch/surface, user-active, file-drop) relays UP so the brain closes the loop; no local script may choose a behaviour.

## The principle (David's words, verbatim)

> The brain feeds ALL autonomous behaviour: brain > body > brain. Even a mouse-idle trigger must relay UP to the brain and be read back DOWN — no local driver deciding what eLo does. (one brain / no parallel drivers)

## What the Architect is asked to check (verbatim, from Design's flag)

> Evaluate this as the LOOP PATTERN (brain>body>brain), with mouse-idle as the first application. Then audit for OTHER local drivers that skip the loop (EloIdleBehaviour's mouse-idle calm is the known one; check for others that decide behaviour without relaying up). Confirm it composes with WO-041 (verify/ACK) + WO-035 (commanded state owns the body).

---

*Downstream: WO-086 spec is the authored/greenlit application. Any broader "close every local driver into the loop" work references THIS source; it does not paraphrase it.*
