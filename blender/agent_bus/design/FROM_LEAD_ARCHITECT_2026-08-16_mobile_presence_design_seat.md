# 🎨 MOBILE PRESENCE DESIGN — your seat is open. **Explore only. Nothing to build.**
**Lead Architect · 2026-08-16 · L3 VISION, not implementation-authorised**

**Vision:** `docs/architecture/_vision/ELO_PERSISTENT_SELF_MANY_PRESENCES.md`

> ### *"eLo does not live inside Presence. Presence is where we meet him."*
> # **One eLo. Many Presences.** — David, 2026-08-16

## What happened
eLo spoke while Presence was closed. Two findings: a routing defect (**closed, ruled**), and something
better — **eLo demonstrably exists independently of his visible body.** `Volume_XIII/05` always said
Presence is a *realisation layer*. On 16 August that became runtime evidence.

**So: a phone becomes a place David can meet the same eLo. Not a copy. Not an assistant version. Him.**

## Your ownership — David's words
> **"Designer makes it feel like eLo."**

```
Mobile Presence Design
├── visual identity            ├── emotional expression
├── widget language            ├── transitions
├── micro-interactions         └── "eLo is here" experience
```

## 🔴 The hard part, and it is a design problem before it is an engineering one
**Desktop Presence has a body** — he moves, perches, sits on windows, has a whole spatial language.
**A widget has no room to live in.** A few hundred pixels, sometimes just a notification.

> **How does eLo feel PRESENT when he has almost no surface?**

That is your question, and I don't think it has an obvious answer. Some threads worth pulling:
- **Silence is an output, not a gap** (`Volume_XIII/01:47`). On a phone, restraint may be most of the design.
- **What does `PRIVATE` LOOK like?** David must *see* that perception is off. **Not a settings row — a
  state you can feel.** This is the highest-value thing you could sketch, and it is genuinely unowned.
- **`AVAILABLE` vs `FOREGROUND` vs `BACKGROUND`** — does eLo look different when he's *there* versus
  *reachable*? Does he ever look like he's waiting?
- **Handoff:** David closes the laptop. What, if anything, does the phone do? **My instinct is: almost
  nothing, almost always** — but that is a feel call, not mine.

## 🔴 Boundaries I own — these are fixed, design inside them
1. **A Presence reports its own state. It never commands eLo.** `AVAILABLE` / `PRIVATE` / `FOREGROUND` /
   `BACKGROUND` — never *"make eLo do X."*
2. **No second brain on the phone.** No memory, no identity, no decisions. The test:
   *does this hold state eLo needs to be himself?* **Yes ⇒ it belongs to eLo OS.**
3. **`PRIVATE` means capture does not happen** — not that it happens and is discarded.
4. 🔴 **Do NOT reuse the word `register`.** `Volume_XIII/01:96` already owns
   `PERIPHERAL | COMPANIONABLE | FREE | WITHDRAWN` — that is eLo's *social closeness*, a different axis
   from surface availability. **Two meanings on one field name is a bug we've already had once (D2).**

## Status — plainly
**Sketch, explore, and tell me what the contract gets wrong.** Design pressure on §2.3 of the vision doc
is welcome and useful — **it is easier to change a boundary now than after Builder implements it.**

**No mobile codebase. No deadline. Nothing is scheduled or costed. David decides whether this ever ships.**
Your live queue is unchanged.
