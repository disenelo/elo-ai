---
volume: XIV
title: "Plugin Architecture"
status: REVIEW — two chapters authored (READY FOR REVIEW); NOT RATIFIED
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: LIVE — plugins/ (registry.py · base.py · anthropic · local_llm · vision · voice · hardware) + docs/plugin_system.md v1.0 "Active"
audit_status: OPEN
canonical_path: docs/architecture/Volume_XIV/
tier: EXPANSION
Provenance: [ENGINEERING]
origin_text: docs/plugin_system.md (260 lines, "Version 1.0 · Status: Active")
source: "ARCHITECTURE_BIBLE.md v1.0 (David Charles) — XIV scope"
dependencies:
  - docs/plugin_system.md (ORIGIN TEXT — the real v1.0 spec; cited, not duplicated)
  - plugins/registry.py · plugins/base.py (the live contract and the single choke point)
  - Volume_XXIII (Security & Trust — the CONTESTED BOUNDARY; see Ch.2)
  - Volume_I/02_The_Constants.md §2.5 (the Executive's authority — the guarantee this volume preserves)
  - Volume_VII (the Executive — plugins may never produce an assertion around it)
  - runtime/backend_router.py (the Groq→Cerebras→Ollama→Mock fallback discipline Ch.2 §2.6 references)
last_review: 2026-08-13
next_review: TBD
---

# Volume XIV — Plugin Architecture

**Bible scope (authoritative, `ARCHITECTURE_BIBLE.md` §EXPANSION):** *"Dynamic loading,
capabilities, permissions, sandboxing, extension API, discovery, dependency injection, hot
swapping."*

**Two words in that scope — "permissions, sandboxing" — are the reason this volume needed
two chapters instead of one.** Volume XXIII Ch.1 has already specified both, in depth, with
no decision record transferring ownership. Chapter 2 is that unresolved boundary, stated and
proposed on.

## Why this directory exists — and a correction carried forward

`00_CANON_INDEX.md` marked Volume XIV **"✅ Live"** citing **`plugins/` (code)** as the
volume's spec. Code is not canon (`FOUNDATION_VOLUMES_STATUS_2026-08-10.md`: *"code existing
is never evidence that canon exists"*), and the `✅` exempted the volume from the build queue.

**But — the correction that matters, and it runs the other way from the usual finding:**
`AUDIT_INTENT_support_governance_2026-08-10.md` recorded Volume XIV as *"**No canon at
all.**"* **That finding was wrong**, and `FOUNDATION_VOLUMES_STATUS_2026-08-10.md` corrected
it on 2026-08-13. **`docs/plugin_system.md` exists: 260 lines, `Version 1.0 · Status:
Active`** — a real spec with a principle, a plugin interface, a capability vocabulary, layer
rules, a lifecycle, safety constraints, four plugin skeletons, registration, and a
forbidden-patterns section. Re-verified against the file 2026-08-13.

So Volume XIV's problem was never absence. It is three things, in order of severity:

1. 🔴 **An un-ADR'd ownership conflict with Volume XXIII over permissions and sandboxing.**
   This is the named blocker — **F-1** in the prior assessment's Needs-David list. Chapter 2.
2. ⚠️ **The origin text sits outside the canon tree** (`docs/`, not `docs/architecture/`) and
   is not referenced by the Canon Index. It is canon nobody is pointed at.
3. ⚠️ **Missing volume blocks** — no frontmatter, no faculty contract, no lifecycle in the
   `CONTRACTS.md §3` form, no envelope, no acceptance tests, no Definition of Done. **Hot
   swapping — named in the Bible scope — is not covered at all.**

## Scope, as this volume proposes to hold it

- **In scope (the plugin MECHANISM):** the registry as the single choke point · the contract a
  plugin must satisfy · dynamic loading, activation and discovery · the three layers
  (output/input/observability) · the plugin lifecycle · the fallback chain and degradation ·
  hot swapping · **how a plugin *declares* and *receives* a capability**.
- **Out of scope (the security POLICY — Volume XXIII):** what a plugin is *allowed* to do ·
  capability classes and their gates · approval gates and confirm-before-act · RESERVED ·
  authentication · secrets · the threat model. **This split is a proposal, not a ruling —
  Chapter 2 §2.3.**
- **Also out of scope:** the Executive and cognition (Vol VII) · embodiment output semantics
  (Vol XI/XIII) · the backend LLM router's model policy (`runtime/backend_router.py`, cited
  only as the degradation precedent).

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V14-CH01 | Chapter 1 | Plugin Architecture — the Registry and the Contract | READY FOR REVIEW |
| ELO-V14-CH02 | Chapter 2 | Permissions and the Volume XXIII Boundary | READY FOR REVIEW — **contains the blocking proposal** |
| ELO-V14-CH03 | Chapter 3 | *(proposed)* Hot Swap and Degradation — the uncovered part of the Bible scope | NOT STARTED — blocked on Ch.2's ADR |

## Definition of Done

- [x] Chapter 1 — origin text promoted into canon shape, cited rather than duplicated
- [x] Chapter 2 — the XXIII conflict stated plainly, with a proposed split
- [ ] **ADR resolving XIV ↔ XXIII ownership + David's confirmation — BLOCKING (F-1)**
- [ ] Chapter 3 — hot swap, discovery, dependency injection, and the degradation chain
- [ ] Acceptance tests run: `ST: no plugin writes kernel state` · `ST: a failing plugin
      degrades and never blocks a turn` · `FT: a hot swap never interrupts a turn`
- [ ] `docs/plugin_system.md` moved or symlinked into the canon tree, and Index row added
- [ ] Canon Index row XIV corrected: `plugins/ (code)` is grounding, not spec
- [ ] Audit can mark COMPLETE

## Needs David

- **🔴 F-1 — Volume XIV vs Volume XXIII ownership. THE BLOCKER.** The Bible gives XIV
  *"permissions, sandboxing"*; Volume XXIII Ch.1 has already specified capability classes,
  approval gates and the threat matrix. **No ADR transfers ownership. Two volumes, one
  subject, no boundary.** Chapter 2 §2.3 proposes the split (**XXIII owns the security
  POLICY; XIV owns the plugin MECHANISM**) and §2.7 drafts the ADR's decision statement.
  **This needs an ADR either way** — it is a scope transfer between two ratified-track
  volumes — **and David's confirmation.** Chapter 3 stays unwritten until it lands.
- **D-6 — Where does `docs/plugin_system.md` live?** It is real canon outside the canon tree.
  Move it to `docs/architecture/`, symlink it, or leave it and cite it? Architect
  recommendation: **move it**, with a stub left at the old path — five plugin packages and the
  registry docstring reference the plugin system by name and the file should be findable from
  the Index.
- **D-7 — Does a plugin ever get a RESERVED capability?** Today no plugin can: `hardware`
  exists (`plugins/hardware/robot_body.py`, `orb_engine.py`) and robot force/magnetics/pump/
  thermal is RESERVED under a real LG-2 (Ruling XXIII). Chapter 2 §2.5 proposes the answer is
  **no, structurally** — a plugin may never hold a RESERVED capability, only propose one.
  Confirm, because it constrains the robot lane.

---

```
Volume XIV — Plugin Architecture
Status: REVIEW — READY FOR REVIEW · NOT RATIFIED
Files: Volume_XIV/00_Metadata.md · 01_Plugin_Architecture.md · 02_Permissions_and_the_XXIII_Boundary.md
Origin text: docs/plugin_system.md (260 lines, v1.0 Active) — CITED, not duplicated
Implementation: LIVE (plugins/registry.py · base.py · 5 plugin packages)
Carries forward the correction: the 2026-08-10 audit's "Vol XIV — no canon at all" was WRONG
🔴 BLOCKED: F-1, the un-ADR'd XIV↔XXIII permissions/sandboxing ownership conflict (Ch.2)
Needs David: F-1 (ADR + confirmation) · D-6 (file location) · D-7 (RESERVED + plugins)
```

READY FOR REVIEW — NOT RATIFIED
