# WO-CONV-001 — WKG + SPG + Memory → One Brain Convergence
**Priority:** P2 (after WO-RS-001..004 + WO-WKG-001..002 + WO-SPG-001..002)
**Authority:** `_intake/SOURCE_2026-08-22_CA_recovery_delivery_plan.md`
**Date:** 2026-08-22

---

## Objective

Verify the thing we've actually been building. Wire the full signal path and run it as an integration test.

## The signal path to verify

```
INPUT
  ↓
CLASSIFY
  ↓
┌──────────────┬──────────────┐
↓              ↓              ↓
WKG            SPG         MEMORY
world          self-model   episodic/
knowledge                   semantic
↓              ↓              ↓
└──────────────┴──────────────┘
                ↓
          CURRENT STATE
                ↓
          CAPABILITIES
                ↓
           EXECUTIVE
                ↓
           RESPONSE
                ↓
    learning/evolution (where appropriate)
```

## What to test

For each layer: confirm the signal arrives structured, labelled, and with provenance intact.

1. Input classifies correctly
2. WKG claim reaches Executive as `ContextItem` with `epistemic_class`
3. SPG self-state reaches Executive as structured data
4. Memory retrieval reaches Executive as `ContextItem`
5. REVIEW_STATE blocks all writes end-to-end
6. Response generated without provenance contamination
7. Learning writes only where authorised

## This is the integration test — not another audit

If a layer fails: identify the broken contract/path, fix it within its existing WO scope, re-run. Do not create a new architecture document.

## Hard constraints

Do not extend scope. Do not add new layers. Do not create a new convergence framework.
This WO exists only to verify the wired system.
