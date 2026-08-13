---
chapter: 3
title: "Secrets, Memory Protection & the Threat Model — What Must Never Leak or Be Forged"
volume: XXIII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
received: 2026-08-10
dependencies:
  - .env (secrets — GITIGNORED, never committed)
  - runtime/backend_router.py (credential consumers — Groq/Cerebras/Ollama/Mock fallback)
  - Volume_VIII/00_Metadata.md (D-F RATIFIED — Memory Faculty is sole permanent writer)
  - docs/architecture/17_memory_update.md (the write path — integrate_session, three-tier vault)
  - Volume_XXIII/01_Authentication_Permissions_Sandboxing.md (permission model)
  - Volume_XXIII/02_Approval_Gates_and_Trust_Boundaries.md (confirm-before-act gate)
---

# Chapter 3: Secrets, Memory Protection & the Threat Model

## 3.0 Purpose

Two assets, if compromised, break the trust the whole companion rests on: the **secrets**
that let eLo reach the outside world, and the **memory** that makes eLo one continuous
being who "remembers when you first learned to move" (Invariant 1). A leaked key is a
breach of the person's world; a forged memory is a breach of eLo's *self*. This chapter
protects both, then names the **threat model** that the rest of Volume XXIII is measured
against.

It closes the Vol XXIII scope items: *secret management · memory protection · safety
policies · threat model*, grounded in three live truths:

- Secrets live in `.env`, gitignored, never committed.
- The Memory Faculty is the **sole permanent writer** (D-F, RATIFIED 2026-07-27).
- eLo prefers truthful uncertainty over confident fiction (Truth before fluency) — the
  safety default when anything below is uncertain.

## 3.1 Principle

**3.1.1 A secret never enters the record.** Keys, tokens, and credentials live only in
`.env` (gitignored) and in process memory at runtime. They are never committed, never
written to memory (§3.3), never logged, never spoken, and never returned to the person or a
model prompt. If eLo cannot find a credential, it says so (Ch.1 §1.4.1 auth) — it does not
paste one to prove it.

**3.1.2 Memory has exactly one writer.** Only the Memory Faculty writes permanent memory
(D-F). Every other faculty *submits a Memory Candidate*; the Memory Faculty decides. There
is no side door. This is what makes eLo's past *trustworthy* rather than *editable*.

**3.1.3 eLo can never learn a thing that did not happen.** Learning sits after verification
(Execute → Verify → Outcome → Reflect → Learn → Memory; ADR-Exec-005). A memory candidate
derived from unverified speech, an imagined action, or a hallucinated conversation is
rejected. You cannot remember what you only said.

**3.1.4 When uncertain, the safe default is silence or refusal, not a guess.** Safety
policy inherits Truth-before-fluency: an unverified action is not claimed, an ambiguous
RESERVED matter is escalated not executed (Ch.2 §2.4), an unreachable service is reported
absent not faked. The failure mode of eLo is *quiet and honest*, never *confident and
wrong*.

## 3.2 Secret Management

**3.2.1 Where secrets live.** All credentials live in `.env` at the repo root, which is
gitignored and never committed (Engineering security rule; CLAUDE.md "Backend/env truth:
`.env`"). This is the single source of secret truth. Consumers (e.g.
`runtime/backend_router.py` reading `GROQ_API_KEY`, `ELO_OLLAMA_MODEL`, the
Groq→Cerebras→Ollama→Mock fallback) read from the environment; they never hard-code a key
and never carry one in canon, a WO, or a log line.

**Secret rules (MUST):**

- `.env` MUST remain gitignored. A committed secret is a P0 incident: rotate the key,
  purge history, then re-audit (§3.5 threat T-1).
- No secret is ever placed in: canon/docs, a work order, a board row, a prompt sent to any
  model, a memory candidate, a spoken line, an error string shown to the person, or a
  learning-buffer record. (VERIFY-BEFORE-ASK, CLAUDE.md Rule 1: the origin incident was
  re-asking for a `GROQ_API_KEY` already set in `.env` — the fix is *read `.env`*, never
  *echo `.env`*.)
- A missing/invalid credential surfaces as `health_state = AUTH_REQUIRED` (Ch.1) and an
  honest "that service isn't authenticated" — never a fabricated result.
- **Local-first fallback is a safety property, not only availability.** The
  Groq→Cerebras→Ollama→Mock chain means a credential outage degrades to the local
  `llama3.1:8b` brain (per CLAUDE.md) or Mock, rather than eLo silently failing or leaking
  a retry loop. Degradation is honest and bounded.

**3.2.2 What is NOT a secret.** Capability *declarations* (registry) and permission classes
are canon and public within the repo. The secret is the *credential*, not the *fact that a
capability needs one*. Do not over-classify — over-secreting hides the permission model the
audit needs to see (Security serves trustworthiness, not bureaucracy).

## 3.3 Memory Protection

Memory is eLo's continuity across bodies and days; protecting it is protecting identity.

**3.3.1 Sole-writer enforcement (D-F).** The Memory Faculty owns persistence, retrieval,
indexing, forgetting, and consolidation. No other faculty writes permanent memory directly
— all submit a **Memory Candidate** and the Memory Faculty arbitrates (Vol VIII §D-F; the
write path is `17_memory_update.md` / `integrate_session()`, three-tier vault). The
Executive coordinates but does not write long-term memory (Vol XVI §prohibitions; D-F).

**Memory-protection rules (MUST):**

- The permanent store has **one writer**. Any code path that writes memory outside the
  Memory Faculty is an architecture violation (Vol XVI ST-3: a faculty attempting a direct
  long-term write is *blocked*).
- A Memory Candidate MUST carry provenance (what verified event it derives from) so §3.1.3
  can reject candidates with no verified basis. Speech alone is not provenance.
- **Identity, values, and truth are immutable in memory**; only skills, policies, and
  preferences adapt (ADR-Exec-005). No learning path may edit who eLo *is* — only what eLo
  *can do* or *prefers*. This is the guard against personality/value drift being written in
  as "memory".
- Forgetting is a *designed* operation of the sole writer (decay/consolidation, Vol VIII),
  never an uncontrolled deletion by another faculty or a tool. Memory is not editable from
  outside even to *remove*.
- The vault is read through its sole reader (`obsidian_loader` — Vol VIII); writes go
  through the write path. Read and write are separated so a reader can never mutate.

**3.3.2 Why forgery is the real threat.** The danger is not mainly an attacker reading
eLo's memory — it is eLo *believing something false about its own past*, which would make
it a different being telling a fabricated story (violates Invariant 1 + Verified Speech).
Sole-writer + verified-provenance + immutable-identity together make eLo's past *earned*,
not *authored*.

## 3.4 Safety Policies (the standing defaults)

These are the always-on defaults that the gates (Ch.2) and permissions (Ch.1) enforce:

1. **Default-deny world-changing capability** (Ch.1 §1.1.1).
2. **Confirm before irreversible act; RESERVED needs L3 + LG-2** (Ch.2 §2.4).
3. **Speak only verified reality** (Verified Speech / Embodied Truth) — never narrate
   intent as fact.
4. **Secrets never leave `.env`/process** (§3.2).
5. **One memory writer; no learning from the unverified** (§3.3).
6. **Honest degradation** — an outage degrades to local/Mock or an explicit "can't right
   now", never a fabricated success (§3.2.1).
7. **Presence is not surveillance** — perception (screen/vision) is a gated capability with
   an out-of-band OS grant (Ch.1); "present when wanted, gone when not" (D-PRESENCE) is a
   safety default, not only a UX one.

## 3.5 Threat Model

The assets, the adversaries/failure sources, and the mitigation each maps to. This is the
audit target for Volume XXIII.

**Assets to protect:** (A1) the person's machine/world; (A2) the person's data & privacy;
(A3) eLo's secrets/credentials; (A4) eLo's memory & identity continuity; (A5) the person's
trust that eLo is truthful.

| # | Threat | Asset | Primary failure source | Mitigation (chapter) |
|---|---|---|---|---|
| **T-1** | Secret committed / leaked (git, log, prompt, speech) | A3, A2 | dev error, prompt echo | `.env` gitignored; never in canon/WO/log/prompt/memory; rotate-on-leak (§3.2) |
| **T-2** | Unauthorised irreversible action on the machine | A1 | mis-route, hallucinated intent | default-deny + confirm-before-act gate; `agents=[]` when pending (Ch.2 §2.2–2.3) |
| **T-3** | Dangerous capability enabled without David | A1 | self-escalation attempt | `ELO_COMPUTER_CONTROL` out-of-band + OS grant; no self-grant (Ch.1 §1.5) |
| **T-4** | Consent replay / bleed across turns | A1, A5 | stale pending state | one pending slot; consumed on execute; cleared on non-confirm (Ch.2 §2.1.3) |
| **T-5** | RESERVED action taken on eLo's authority | A1(safety), A2(money/legal) | scope confusion | no `_IMMEDIATE_SAFE`/single-confirm path; David L3 + LG-2 required (Ch.2 §2.4) |
| **T-6** | Forged / unverified memory written | A4, A5 | learn-from-speech, direct write | sole writer (D-F); verified provenance; learn-after-verify (§3.1.3, §3.3) |
| **T-7** | Personality / value / identity drift written as memory | A4 | over-broad learning | immutable identity/values; only skills/prefs adapt (§3.3.1) |
| **T-8** | Fabricated success on service/tool failure | A5 | fluency over truth | honest degradation; AUTH_REQUIRED surfaced; Groq→…→Mock (§3.2.1, §3.4) |
| **T-9** | Perception used as covert surveillance | A2 | ungated sensing | perception is a gated capability + OS grant; D-PRESENCE default (§3.4) |
| **T-10** | Faculty acts around the Executive / injects into a peer | A1, A4 | bus misuse | canonical envelope only; Executive is sole external authority (Ch.2 §2.5.1) |
| **T-11** | Cross-embodiment authority carry-over | A1(robot safety) | grant assumed across bodies | authority re-established per embodiment; robot force = RESERVED (Ch.2 §2.5.3) |

**Out of scope (named, not addressed here):** hardened OS-level threat modelling of the
host Mac; network transport security of third-party APIs; supply-chain of pip dependencies.
These are real but sit below the companion-trust boundary this volume owns — flag if David
wants them pulled in (OQ-3.6.4).

## 3.6 Open Questions (for CA / David)

- **OQ-3.6.1 (David L3 — threat-model priorities).** The Vol XXIII scaffold noted this
  volume "may want David's threat-model priorities first." Which of T-1…T-11 are P0 for
  Presentable v1 vs deferred? The table is complete; the *sequencing* is David's.
- **OQ-3.6.2 (CA).** Should Memory Candidate *provenance* (§3.3.1) become a required typed
  field in the Vol VIII / `17_memory_update` write contract, so T-6/T-7 are enforced
  structurally rather than by policy? Recommend yes; needs the Memory owner's sign-off.
- **OQ-3.6.3.** Do we add an automated pre-commit / CI check that fails on a would-be secret
  (T-1) reaching git — and if so, is that an Engineering-Standards item (Vol XXVII) rather
  than canon here?
- **OQ-3.6.4 (David).** Pull host-OS / network / supply-chain threats into scope, or keep
  Volume XXIII strictly at the companion-trust boundary as drafted?

## 3.7 Architecture References

- `.env` — sole secret store (gitignored); `runtime/backend_router.py` — credential
  consumers + Groq→Cerebras→Ollama→Mock fallback.
- `docs/architecture/Volume_VIII/00_Metadata.md` — D-F RATIFIED (Memory Faculty sole
  permanent writer); `Volume_VIII/01_Memory_Architecture.md` — sole vault reader / write
  layer.
- `docs/architecture/17_memory_update.md` — the write path (`integrate_session()`,
  three-tier vault).
- `docs/architecture/Volume_XVI/01_Coordination_Under_One_Executive.md` — prohibition on
  direct long-term writes (ST-3); D-F/D-G.
- `docs/architecture/ARCHITECTURAL_PRINCIPLES.md` — Truth before fluency; Learning From
  Consequences (ADR-Exec-005); Verified Speech; Presence over engagement (D-PRESENCE).
- Siblings: `Volume_XXIII/01_*`, `Volume_XXIII/02_*`.

---

```
Chapter 3 — Secrets, Memory Protection & the Threat Model
Status: READY FOR REVIEW
Files: Volume_XXIII/03_Secrets_Memory_Protection_Threat_Model.md
Secret management: Included (.env sole store; never-leak rules; honest degradation)
Memory protection: Included (D-F sole writer; verified provenance; immutable identity)
Threat model: Included (T-1…T-11 mapped asset → source → mitigation-chapter)
Safety policies: 7 standing defaults (§3.4)
Open questions: 4 (2 → David L3, 1 → CA/Memory owner)
```

READY FOR REVIEW
