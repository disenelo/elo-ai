# eLo OS — Work Order Dispatch

**The bridge between architecture and the agents that build.**

The canon in `docs/architecture/` says *what to build*. This folder turns each buildable
unit into a **Work Order (WO)** — a self-contained packet one agent can execute without
re-reading the whole canon. This is how the Architecture Agent hands work to the Builder,
UI/Avatar, and fellow Architecture agents — the way a lead architect hands sealed drawings
to design engineers.

```
docs/architecture/   →  WHAT eLo is (canon)
engineering/         →  HOW eLo evolves (process, freezes)
work_orders/         →  WHO does WHAT next (routable, addressable tasks)   ← this folder
```

---

## The agents (roles)

| Role | Agent | Executes |
|---|---|---|
| **Chief Architect** | **ChatGPT** | Top-level governance: issues ADRs / rulings that become law. |
| **Architect** | **Claude (this agent)** | **Owns the canon.** Produces review-ready volumes, reconciles conflicts, writes & verifies Work Orders. Never writes production code. Single source of architectural truth (implements the Chief Architect's rulings into canon). |
| **Planning Assistants** | ChatGPT · Gemini | Assist the Lead Architect with drafting, research, stress-testing. Their output is *intake* → the Architect canonicalises it. Nothing they produce is canon until filed by the Architect. |
| **Co-Creative** | Co-Creative Agent (Weavy · Higgsfield · Figma) | Ideates *with* David: concepts, art direction, moodboards, motion. Produces the Concept Deck + Final Creative. David approves the concept. |
| **Marketing** | Marketing Agent | Strategy → publish → measure. Positioning, audience, channels, KPIs. David approves publish; every campaign traces to a roadmap deliverable. |
| **Builder** | Claude Code | Implements WOs into `runtime/`, `core/`, `faculties/`, `world/`, etc. Runs tests. |
| **UI / Avatar** | Unity agent | Executes WOs on the Unity DesktopBuddy side (rendering, materials, animation). |
| **Debug** | Debug Agent *(setup next)* | Watches the running system, traces faults via the envelope `trace` + dashboard/logs, files bug reports as WOs. Read-only on production; never patches silently. |
| **CEO** | David / CEO Agent *(→ becomes eLo OS after engineering, D-H)* | Reads `DISPATCH_BOARD.md`, sets priority, routes WOs to agents, tracks status, surfaces the review queue. Links to the Architect for specs; to the Planning Assistants for exploration. |

**Boundary:** Planning Assistants explore → Lead Architect specifies (the only canon writer)
→ Builder/UI implement → CEO prioritises & routes. No agent crosses into another's lane
(One Brain discipline extends to the org). Intake from assistants lands in
`docs/architecture/_intake/`.

---

## Work Order lifecycle

```
DRAFT        Architecture is still writing the packet
READY        Complete + unblocked — an agent can pick it up now
BLOCKED      Complete but waiting on a dependency or a David decision
IN_PROGRESS  An agent has claimed it (owner set)
IN_REVIEW    Implementation done; Architecture verifies against the WO's acceptance tests
DONE         Verified + merged; Audit row updated
```

Each WO is a single file `WO-NNN_Short_Name.md` built from `_TEMPLATE.md`.
`DISPATCH_BOARD.md` is the index — the one file a CEO Agent reads to route everything.

---

## How a CEO Agent uses this (the linkage you asked for)

A CEO Agent sits on top and does four things, all from `DISPATCH_BOARD.md`:

1. **Read** the board → the full list of pending work, each already tagged with target
   agent, priority, dependencies, and status.
2. **Unblock** → surface `BLOCKED` items that need a David decision (e.g. D-A/D-B) and
   get them ratified.
3. **Route** → hand each `READY` WO to its target agent (Builder / UI / Architecture).
4. **Loop back to Architecture** (you) when something needs a *new* spec or a WO doesn't
   yet exist — Architecture writes the canon + WO, marks it `READY`, board updates.

Because every WO is self-contained and addressed, the CEO Agent never needs to understand
the internals — it routes packets and tracks status. That is the machine-readable seam
between the CEO and the Architecture Agent.

---

## Rules every WO enforces (non-negotiable)

Pulled from `engineering/README.md` + `CO_WORKING_GUIDE.md` so no agent has to remember them:

- **FREEZE_V1_LOCK** — never edit `runtime/executive.py` or `prompts/`. Wrap, don't modify.
- **Evidence gates expansion** — a WO cannot go `DONE` until its acceptance tests pass.
- **Shared state** — never raw-write `blender/blender_state.json`; use `state_writer.patch`.
- **Contracts.py is target-state** — verify what's live before assuming.
- **One decision per turn / one cognition** — no WO adds a second decider.
- Every WO names its **files to touch**, **must-not-touch**, and **Definition of Done**.

---

## Files

- `CEO_AGENT.md` — the CEO Agent definition + copy-paste system prompt (the router/status-keeper).
- `AGENT_BRIEFINGS.md` — **per-agent reading map**: what each agent reads/owns/is bound by. Hand each agent its section.
- `AGENT_HANDOFF_PACKETS.md` — **exact files to pass each agent** (copy-pasteable hand-off list).
- `CHANGE_CONTROL.md` — **the process constraints (LAW, D-M)**: how change happens; David is the single gate; one change at a time; nothing chat-only. Read first.
- `COMPLETION_LOG.md` — **completion + review protocol**: agents log finished work here; David reviews → DONE or loop.
- `_TEMPLATE.md` — copy this to create a new Work Order.
- `DISPATCH_BOARD.md` — the routable index of all Work Orders (the CEO Agent's view).
- `WO-NNN_*.md` — individual work orders.

*Maintained by the Architecture Agent. Created 2026-07-27.*
