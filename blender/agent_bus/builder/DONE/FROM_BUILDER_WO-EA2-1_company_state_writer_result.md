# FROM BUILDER — WO-EA2-1 Company State Writer + company.approve intake
**Seat:** Builder  
**WO:** WO-EA2-1 — Company State writer + action intake (company_runtime, additive)  
**Date:** 2026-08-27 (governance record — implementation 2026-08-01)  
**Authority:** WO-EA2-1 in `engineering/work_orders/WO-EA2-1_Company_State_Writer.md`

**Note:** Implementation was completed 2026-08-01 (commit `af9a451`) before the current result-card convention was established. This card closes the governance gap. COMPLETION_LOG.md entry appended in same commit.

---

## Deliverables

### D-1 — company_runtime/company_state_writer.py (NEW) ✅
- `publish()` → emits `blender/company_state.json` (schema `company_state/v1`)
- Fields consumed by Presence dashboard: `today_priorities · waiting_for_approval · blocked · money · roadmap · board[] · graph{} · seats_sample · voiced_briefing · company_focus`
- Parses DISPATCH_BOARD.md (WO table rows by status tag), COMPANY_FOCUS HTML marker, seat records
- Called once per cycle; also supports one-shot CLI (`python3 -m company_runtime.company_state_writer`)

### D-2 — Action intake (company_actions.json watcher) ✅
- Watches `blender/company_actions.json` for `approval_request | move | reorder` requests
- Wraps each as Faculty Bus Envelope (`runtime:"company"`, payload with work_order / to_status / actor)
- Routes to Executive path
- Safety gate: money/legal WOs require `human_flag=True` AND L3 actor — refused + logged if absent
- Non-L3 actor: refused. Malformed request: dropped with trace note, no crash.

### D-3 — company.approve CAL hook (stub) ✅
- Intent name registered so EA2-2 can call it
- Full approval/scheduling/orchestration faculties are EA2-4/5/6 (separate WOs)

### D-4 — Additive-only constraint (LAW-017) ✅
- Zero edits to `core/`, `runtime/spine/`, or anything under `FREEZE_V1_LOCK`
- Verified: frozen kernel tests (WO-001, WO-014, WO-006) pass unaffected

---

## Acceptance Tests — 6/5 + 11/11 PASS ✅ (confirmed 2026-08-27 via miniconda3)

```
~/miniconda3/bin/python3 tests/test_ea2_1_company_state.py
```
```
AT-1: company_state/v1 valid — 139 rows, today=4, waiting=1 ✅
AT-2: approval david/WO-TEST-99 → board flipped, state re-emitted ✅
AT-3: money WO refused without human_flag ✅
AT-3b: same WO passes with human_flag=True ✅
AT-4: malformed/unauthorized refused gracefully, no crash ✅
AT-5: frozen kernel tests (WO-001/014/006) still pass — additive-only verified ✅
Result: 6/5 passed, 0 failed
```

```
~/miniconda3/bin/python3 tests/test_ea2_2_company_intents.py
```
```
AT-1 PASS — briefing phrases
AT-2 PASS — board phrases
AT-3 PASS — approvals phrases
AT-4 PASS — approve regex
AT-5 PASS — move regex
AT-6 PASS — unrelated phrases → None
AT-7 PASS — briefing returns DISENELO identity + state items
AT-8 PASS — approvals lists WO ids and count
AT-9 PASS — approve writes action
AT-10 PASS — move writes action with correct fields
AT-11 PASS — frozen kernel untouched
ALL PASS — EA2-2 (11/11)
```

---

## Commits
- `af9a451` — initial: company_state_writer.py (662 lines) + EA2-2 intent wiring (2026-08-01)
- `aa380e0` — D-1..D-7 live-test defect fixes including company-state refresh (2026-08-?)
- Multiple interim refinements via WO-048, WO-061, WO-080 (company board query, focus marker, knowledge depth)

---

## Alignment check
- **Architecture:** company_runtime/ is the eLo-side of the Presence bridge — additive, never mutates cognitive kernel
- **Scope:** D-1, D-2, D-3 delivered per WO spec. D-4 (constraint) verified by frozen kernel pass.
- **Next:** MT formal verification via `FROM_ARCHITECT_2026-08-27_VERIFY_WO-NAV-013_and_EA2-1.md` → Board dispatches WO-EA2-2 on PASS

*Builder · 2026-08-27*
