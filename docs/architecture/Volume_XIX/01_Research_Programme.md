---
chapter: 1
title: "Research Programme, Areas & Policy"
volume: XIX
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "David Charles Bible content 2026-07-27"
dependencies: [DECISION_LOG.md, Volume I]
---

# Chapter 1: Research Programme, Areas & Policy

## 1.0 Mission
Study how an artificial system may exhibit **coherent, continuous cognition while
remaining transparent, controllable, and aligned** with its design principles. This
volume is a research programme, not a build spec.

## 1.1 Research Areas (open questions)
- **Continuous Identity** — what creates continuity over months?
- **Presence** — what makes an AI feel present without pretending to be human?
- **Reflection** — how does reflection improve intelligence?
- **Dreams** — can symbolic recombination increase creativity?
- **Memory** — what should persist? what should fade?
- **Attention** — how does limited attention improve reasoning?
- **Curiosity** — how should curiosity emerge?
- **Emotion** — how can emotional significance guide learning without simulating human feelings?
- **Embodiment** — how does having a body alter cognition?
- **Social Learning** — can long-term relationships improve reasoning?
- **World Models** — how should internal reality differ from external reality?
- **Self-Improvement** — how can the system evolve without losing identity?

## 1.2 Research Policy (MUST)
- Research **never modifies architecture directly.**
- **Every experiment becomes an Architecture Decision Record** (`DECISION_LOG.md`) —
  hypothesis, method, result, decision.
- Experiments respect the ethical boundaries of Volume I and the Identity Kernel
  (`18_identity_kernel.md`): no experiment may compromise identity, safety, or honesty.

## 1.3 How this volume interacts with the Canon
Each research area maps to a live volume it probes (Identity→I/X, Memory→VIII, Dreams→IX,
Attention→VI, Emotion→V Ch.4, Embodiment→XI–XIII, World Models→XV). Findings feed those
volumes **only through ratified ADRs**, never by direct edit.

## 1.4 Acceptance (research "Definition of Done")
```
- [ ] Each research area has at least one framed, falsifiable question on record.
- [ ] Every experiment run produces an ADR (hypothesis → method → result → decision).
- [ ] No experiment has modified a Canon volume directly (all changes via ADR).
- [ ] Ethical boundaries (Vol I / Identity Kernel) hold for every experiment.
```

## 1.5 References
`ARCHITECTURE_BIBLE.md` (Vol XIX), `18_identity_kernel.md`, `DECISION_LOG.md`, Volume I (ethics).

---
**Status: READY FOR REVIEW** — mission, research areas, and the ADR-only research policy. Canonicalised from David's Bible content.