---
volume: XXIII
title: "Security & Trust Architecture"
status: REVIEW — three deep chapters authored (READY FOR REVIEW); scope ratified (ADR-0003)
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "ARCHITECTURE_BIBLE.md v1.0 (David Charles)"
audit_status: OPEN
canonical_path: docs/architecture/Volume_XXIII/
tier: GOVERNANCE
Provenance: [ENGINEERING][CREATIVE]
last_review: 2026-08-10
---

# Volume XXIII — Security & Trust Architecture

## Scope (authoritative, from the Bible)
Authentication · permissions · tool sandboxing · secret management · memory protection ·
trust boundaries · human approval gates · safety policies · threat model.

## Anchors in the live system (for the deep build)
- Confirm-before-act gate: `runtime/router/execution_gate.py` (human approval).
- Opt-in dangerous capability: `ELO_COMPUTER_CONTROL=1` (computer control agent).
- Secrets: `.env` GITIGNORED; never committed (Engineering security rules).
- Memory protection: Memory Faculty is sole permanent writer (D-F).

## Chapter Build Queue

| # | Chapter | File | Status | Anchors grounded |
|---|---|---|---|---|
| 01 | Authentication, Permissions & Sandboxing | `01_Authentication_Permissions_Sandboxing.md` | READY FOR REVIEW | `runtime/capabilities/registry.py` · `capability.py` · `tools/computer_control_agent.py` (`ELO_COMPUTER_CONTROL`) · `server.py:1564` |
| 02 | Approval Gates & Trust Boundaries | `02_Approval_Gates_and_Trust_Boundaries.md` | READY FOR REVIEW | `runtime/router/execution_gate.py` · `runtime/router/pipeline.py` (Stage 06) · Vision Spine LAW-017 / L3 / LG-2 |
| 03 | Secrets, Memory Protection & the Threat Model | `03_Secrets_Memory_Protection_Threat_Model.md` | READY FOR REVIEW | `.env` (gitignored) · `runtime/backend_router.py` · Vol VIII D-F (sole permanent writer) · `17_memory_update.md` |

Original scaffold plan (superseded by the queue above; content redistributed):
~~01 Trust boundaries & the threat model · 02 Permissions, sandboxing & approval gates ·
03 Secret management & memory protection~~ → all three delivered across the chapters above.

## Open decisions flagged (for CA / David)
- Ch.1: single `ELO_COMPUTER_CONTROL` flag vs per-capability opt-ins (David L3); authority
  scope as an explicit `Capability` field (CA).
- Ch.2: `_IMMEDIATE_SAFE` scope — is `folder_organise` reversible enough to run unasked?
  (David L3); LG-2 composition — who is the second reviewer? (David L3).
- Ch.3: threat-model P0 sequencing for Presentable v1 (David L3); Memory Candidate
  provenance as a required typed field (CA / Memory owner); host-OS/network/supply-chain
  in scope or out?

**Status: REVIEW** — three deep chapters authored and READY FOR REVIEW, grounded in the
live anchors. Not RATIFIED/COMPLETE: promotion needs CA acceptance + David L3. David's
threat-model priorities (OQ-3.6.1) still wanted to sequence T-1…T-11.
