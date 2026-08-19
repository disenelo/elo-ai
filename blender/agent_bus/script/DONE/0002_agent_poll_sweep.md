---
id: OPS-002
seat: script
transport: python
state: READY
priority: P1
worker: "python3 -m company_runtime.agent_poll"
acceptance: "poll_report.json regenerated with current timestamp"
output_to: "blender/agent_bus/poll_report.json"
---
# OPS-002 — Agent poll sweep
`poll_report.json` last written 2026-08-15. Deterministic sweep, no AI.
