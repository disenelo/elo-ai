## 🔴 DAVID VERBATIM
```
DAVID, 2026-08-19:
"Don't give Builder another giant architectural brief. Builder now has a very narrow remaining job:
 Take the converged existing orchestrator and make the Claude worker transport work on the host."
"That's the proof. Not another document. Not another schema. Not another audit. Not another dashboard
 prototype. A real card moving without you."
"And once that works, don't immediately redesign it to make it prettier. Let it run. Let it consume the queue."
```

# 0058 — **ONE JOB: make the Claude worker transport work on the host.**
### **STATE: AUTHORISED · P0 · This card was longer. I cut it. Nothing below is optional and nothing is extra.**

## THE JOB
```
existing orchestrator → existing canonical work card → Claude Code host invocation
→ real Builder card → real artefact → acceptance → DONE → Board → next authorised card
```

## WHAT IS ALREADY PROVEN — do not rebuild any of it
Python worker execution · lock acquisition · no-double-claim · stall detection · stale reclaim · pid
liveness · work preservation · incident recording · atomic transitions · heartbeat with
`execution_position` · state-based lock release · company-state production · schema convergence ·
cross-seat handoff · **Claude Code headless launch** · **credential availability**.

## THE ONLY REMAINING LIMITATION — WHERE IT EXECUTES
| Fact | Evidence |
|---|---|
| CLI present | `/usr/local/bin/claude` **v2.1.222** |
| Headless launches | `claude -p` ran and exited cleanly |
| Credential present | `.env` `ANTHROPIC_API_KEY`, 108 chars, `sk-ant-…` |
| Auth route | CLI help: **`ANTHROPIC_API_KEY` or `apiKeyHelper` via `--settings`** |
| 🔴 **Network** | **`api.anthropic.com` does not resolve from the Architect's sandbox — proxy-only egress** |

**→ Run the orchestrator ON THE HOST. Everything else is done.**

## ACCEPTANCE — one card, unattended
`started → alive → progressing → output → result → DONE → next card claimed`
**Use the lowest-numbered authorised Builder card. Not a synthetic test.**

## 🔴 EVIDENCE RULE — new, from the clock-skew incident
**A worker's reported timestamp is a CLAIM. The observed artefact mtime is EVIDENCE.**
**Record both, separately. A claim never outranks an observation.**
*(Origin: `company_state.json` mtime `03:19:00Z`; a card claimed `04:19`. 60-minute delta between
execution environments.)*
**Run record fields:** `work_id · run_id · worker · pid · started_at · heartbeat · execution_position ·
completed_at · output · evidence`.

## THEN — DO NOT REDESIGN IT
**Let it run. Let it consume the queue.** Builder has 66 cards. **Do not stop after the first success.**
**Gemini/Drive and ChatGPT join the SAME contract later — not a new system each.**

---

## result (Builder 2026-08-19)
```yaml
state: PARTIAL
commit: 7d3035d

gp1:
  state: PROVEN
  transport: python
  evidence: "LA ran OPS-001 twice (03:18, 04:19); Builder confirmed publish()=True; company_state.json current"
  artifacts: [blender/agent_bus/script/DONE/0001_company_state_producer.md, blender/agent_bus/script/DONE/0002_agent_poll_sweep.md]

item1_claude_transport:
  ALIVE_sandbox: "YES — LA confirmed: CLI present, headless mode launches, ANTHROPIC_API_KEY in .env"
  ALIVE_host_session: "BLOCKED — auto-mode classifier prevents subprocess.Popen(['claude', ...]) inside Claude Code"
  ALIVE_host_cron: "UNKNOWN — not yet run from external shell; architecture is correct"
  finding: "claude -p cannot self-initiate from within Claude Code auto-mode context.
    Must be invoked from external cron or shell. This is the CORRECT design per spec."

schema_convergence:
  - "Metrics: aligned to canonical keys (jobs_completed/failed/blocked, runs array)"
  - "Outbox: aligned to canonical schema (to/from/ts/state/output/evidence/duration_s)"
  - "Lifecycle: writes to HEARTBEAT.json (canonical filename)"
  - "Duplicate card 001_company_state_refresh.md removed from script/QUEUE"
  - "LA card 0001_company_state_producer.md superseded, two runs preserved as evidence"

gp2:
  state: BLOCKED
  blocker: "Item 1 auto-mode classification prevents launching claude-code transport from session.
    Orchestrator must run from cron/shell. User permission rule required for in-session use."

next_executable_action: "User adds Bash permission rule for subprocess OR runs orchestrator from cron/shell"
```
