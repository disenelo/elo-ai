---
id: WO-021
title: "Enable + verify Computer Control end-to-end (reminders / app control)"
owner_seat: SEAT-ENG-001 (Builder)
occupant: Builder (Python)
priority: P2
reason: "David wants eLo to do things that need computer control (reminders, reaching into apps). Live test: eLo said 'Computer control is off — add ELO_COMPUTER_CONTROL=1 to .env'. Capability exists + is gated off; needs enabling + a routing verify."
review_required: L1 → L3 (touches David's machine — safety)
risk: med (computer control acts on David's computer — off by default for safety)
status: READY
created: 2026-07-31
---

# WO-021 — Enable + verify Computer Control

eLo already has the capability — it's just gated off. From the live transcript: David asked eLo to do
things, eLo replied *"Computer control is off — add ELO_COMPUTER_CONTROL=1 to .env to enable it"* and
confirmed it *wants* control *"to help with things like reminders… reach into those apps."* Good, direct
answers — the capability is wired, just disabled.

## What's already there (verified in code)
- `tools/computer_control_agent.py` — computer control via macOS Quartz/Accessibility; **opt-in**, gated
  `ELO_COMPUTER_CONTROL=1` (default off for safety) — `is_enabled()` @ line 40-41.
- `runtime/capabilities/registry.py:199` — `computer_control` capability registered
  (`agent_module=tools.computer_control_agent`, `response_style=confirm`).

## Steps
1. **David (config):** set `ELO_COMPUTER_CONTROL=1` in `.env` + grant macOS Accessibility permission to the
   host app. (Quick win — enables it immediately for testing.)
2. **Builder (verify end-to-end):** with the flag on, confirm a real request routes correctly:
   - *"remind me to X"* / *"open <app>"* → capability registry resolves `computer_control` → the agent
     **executes** and confirms (per `response_style=confirm`), not a cryptic reply or the wrong target.
   - This is the **counterpart to WO-020 Seam B** (mis-routing / stale-entity latch): with control ON, the
     "opening the wrong thing" failure must not recur — a new imperative re-parses its own target.
3. **Safety:** keep the confirm step (eLo asks before acting); document what it can/can't touch. Anything
   destructive stays behind an explicit confirm. Flag to David if scope widens.

## Acceptance
- [ ] Flag on + Accessibility granted → *"remind me…"* and *"open <app>"* actually execute + confirm.
- [ ] No mis-route (does not open the wrong/last entity); each request re-parses its target (ties WO-020).
- [ ] Confirm-before-act preserved; safety documented.

## Handback
Trace of a real computer-control request (intent → capability → action → confirm) → COMPLETION_LOG → David L3.
Relates to WO-019 (voice), WO-020 (routing).
