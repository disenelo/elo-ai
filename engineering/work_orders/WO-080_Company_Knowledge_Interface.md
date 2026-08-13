# WO-080 — Company Knowledge Interface (eLo reads his OWN work, safely)

**Owner:** Builder (eLo OS) · Architect coordinates. **Priority:** P2 — converged-system foundation, POST-Presentable
(tracks alongside, doesn't gate the finish line). **Status:** OPEN — spec'd 2026-08-08 (Chief Architect,
David relay). **Canon home:** reconciles onto the EXISTING `company_state` / EA2-2 Company Brain — **NOT a new
Volume XXX** (Check-Before-Build). May warrant an ADR-Corp note at David L3.

## The mandate (safety-first)
eLo is FORBIDDEN from scanning the host filesystem/codebase to guess project status. He reads company state
from a structured, **permissioned READ-ONLY** file (`self/state/company_state.json`) — his admin dashboard.
This is the safe, clean version of "eLo tracks his own engineering": he reasons over a curated representation,
never rummages your private files.

## Schema (`self/state/company_state.json`) — a system tracker keeps it fresh
- **Context layer:** company/version · current sprint + milestone · active WOs (id·title·status·priority·
  dependencies·acceptance_criteria).
- **eLo role context:** title · `permitted_actions` (e.g. assemble_review_pack · trigger_local_test_suite ·
  flag_regression) · `verification_authority: L3_Gated` (real actions need David).
- **Recent logs:** last completed WO · active regressions (module·severity·description).
(Full sample schema in the CA relay; the Builder finalises field names against the real board/`company_state`.)

## Behaviour
"What are we working on?" → eLo reads the exact active-WO array from the file, no guessing/fabricated
deadlines. "What should I do next?" → reasons over status + regressions + dependencies. He can PREPARE a
review pack (a summary manifest to the workspace) — but PREPARE only; anything real is L3-gated.

## Guardrails (Check-Before-Build)
1. **Read-only + permissioned:** no raw filesystem/codebase scan; only the sandbox JSON.
2. **`permitted_actions` gate in `core/executive.py`:** an action outside the array is dropped before execution.
3. **L3 for anything real:** prepare/flag freely; commit/send/spend needs David.
4. Reuse the existing `company_state` writer + EA2-2 company intents (WO-048) — extend, don't duplicate.
(The CA's `core/company_agent.py` sketch is a REFERENCE — the Builder writes the actual code; Architect lane = spec only.)

## Definition of Done
1. "What tasks are we on?" → exact WOs from `company_state.json`, zero hallucinated features/deadlines.
2. An action outside `permitted_actions` is auto-dropped by the executive.
3. On sprint close, eLo can export a structured review-pack summary to the workspace (prepare-only).

## Sequencing
POST-Presentable. Gated on WO-073 (verbal) + the Situated Self invariant (WO-079) for the "why am I running"
self-context. This is where the eLo-OS and the company system converge — safely.
