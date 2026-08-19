---
id: OPS-001
seat: script
transport: python
state: READY
priority: P0
reserved: false
depends_on: []
objective: "Regenerate the live company state used by the Company Brain"
worker: "python3 -m company_runtime.company_state_writer"
acceptance: "blender/company_state.json regenerated; timestamp current; board rows parsed > 0"
output_to: "blender/company_state.json"
---
## DAVID VERBATIM
```
DAVID, 2026-08-19: "Use the real Company State producer... This is not a test fixture.
The output must be the LIVE company state used by the Company Brain."
"Run it now. Then run it again. Do not stop at 'the mechanism exists'."
```
# OPS-001 — Company State Producer
`company_state.json` was **88.3 hours stale**, which is why the Company Brain had nothing current
and eLo answered "how's the company" from 4-day-old data. The producer exists and was never scheduled.


## result
```yaml
state: DONE
run: 2
output: [blender/company_state.json]
evidence: "updated 2026-08-19T03:19:00.871327Z · board rows:           139 total"
duration_s: 0.08
blocked_by: null
david_required_reason: null
next_executable_action: "schedule this producer"
```


---
## 🔴 SUPERSEDED 2026-08-19
**Builder authored `001_company_state_refresh.md` for the SAME work with a better schema (`work_id`/`SEAT-OPS-001`/`module`+`entry`).** Builder's is canonical. This card's two runs stand as evidence (03:18, 03:19) but the ID `OPS-001` now belongs to Builder's card. **Two schemas for one work item is the 'second state system' David forbade — converged, not left to drift.**
