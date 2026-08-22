# ROUTING / RESPONSE ORDERING AUDIT
**Date**: 2026-08-22  
**Authority**: David L3 — diagnostic only  
**Scope**: DIAGNOSTIC ONLY — no fixes authorised  
**Triggered by**: Observed review chatlog anomalies — possible response displacement

---

## EXECUTIVE SUMMARY

**The architecture IS preserving request order.** No ordering failure was found.

Every turn is processed in strict FIFO sequence. Concurrent generation is architecturally impossible. The Unity UI blocks new input while waiting for a response. The server serialises turns through a single-threaded queue worker holding a mutex.

The anomalies observed in the review chatlog are **routing/cognitive failures (A + D)**, not ordering failures (B, C, E).

---

## ARCHITECTURE TRACE — FULL PIPELINE

```
USER INPUT
  ↓
[Unity UI]  _SendToElo() coroutine
  • _busy = true — blocks all new input
  • HTTP POST to localhost:5050/chat (blocking yield return)
  ↓
[HTTP Server]  ThreadingHTTPServer — spawns handler thread T_n
  • BaseHTTPRequestHandler.do_POST()
  • calls _process_turn_queued(text)
  ↓
[Turn Queue]  _turn_queue.put((text, result_holder, done_event))
  • queue.Queue() — stdlib FIFO, thread-safe
  • handler thread T_n blocks on done_event.wait()
  ↓
[Turn Worker]  _turn_worker() — SINGLE thread
  • dequeues in strict FIFO order
  • calls _process_turn(text)
  ↓
[_process_turn]  acquires _lock (threading.Lock)
  • short-circuit intercepts (identity, scale, animation)
  • web search intercept (server.py:2191)
  • Executive plan (exec_decide → CognitivePlan)
  • tool enrichment (enrich_from_plan)
  • LLM generation (route_streaming → assembled internally)
  • post-processing (journal_router, reflection_faculty)
  • releases _lock
  ↓
[done_event.set()]  unblocks handler thread T_n
  ↓
[HTTP Response]  _send_json(200, result) — JSON blob on same socket
  ↓
[Unity UI]  coroutine resumes after yield return
  • _RemoveLastLine() — removes "..."
  • _AppendLine("eLo: {response}")
  • _busy = false — accepts new input
```

---

## FINDINGS BY AUDIT DIMENSION

### A. REQUEST IDENTITY

| Item | Finding | Classification |
|------|---------|----------------|
| Unique per-turn ID | None. No UUID or sequence number assigned per HTTP request | **AMBER** |
| ID preserved through routing | N/A — no ID exists | **AMBER** |
| Concurrent generation possible | NO — single-threaded worker + _lock prevents it | **GREEN** |
| Older generation completes after newer | IMPOSSIBLE — strict FIFO worker | **GREEN** |

**Note**: The absence of per-turn IDs is not a current failure — ordering is guaranteed by architectural constraints. It becomes relevant only if those constraints are relaxed.

---

### B. QUEUE ORDER

| Item | Finding | Classification |
|------|---------|----------------|
| Generation strictly FIFO | YES — `queue.Queue()` (stdlib, thread-safe) + single worker | **GREEN** |
| Multiple backend requests concurrent | NO — `_lock` inside `_process_turn` prevents overlap | **GREEN** |
| Slow Ollama can overtake later request | NO — each turn waits for Ollama completion before next turn starts | **GREEN** |
| Retry/fallback reorders responses | NO — fallback chain (Ollama→Claude→OpenAI→mock) runs synchronously within the same turn | **GREEN** |

---

### C. RESPONSE ASSOCIATION

| Item | Finding | Classification |
|------|---------|----------------|
| Response associated with request by ID | NO — no application-level request ID | **AMBER** |
| Response associated by HTTP connection | YES — HTTP is request-response on same socket; each handler thread has its own socket | **GREEN** |
| Streamed chunks interleave between requests | IMPOSSIBLE — streaming is server-internal only (for TTS first-sentence detection). The HTTP client always receives a single complete JSON blob, never partial chunks | **GREEN** |

---

### D. BACKEND ROUTING TRACE

Every stage within a turn is sequential and holds `_lock`:

```
user text → _process_turn acquires _lock
  1. short-circuit returns (guard, transport, identity, scale, anim, scale, invade, open_last)
  2. web search intercept (server.py:2191) — modifies raw in-place
  3. lore / WKG intercept
  4. exec_decide → CognitivePlan
  5. enrich_from_plan(raw, plan.capabilities)
  6. _route_streaming or router_route → response assembled
  7. post-processing (journals, reflections, state save)
  _process_turn releases _lock
```

No stage has a request ID. No stage stamps a sequence number. Ordering is enforced structurally (mutex + queue), not by ID.

Classification: **AMBER** — structurally ordered but not externally provable.

---

### E. ASYNC / STREAMING

| Item | Finding | Classification |
|------|---------|----------------|
| Async task completion race | NONE — `done_event.wait()` makes HTTP handler synchronously block | **GREEN** |
| Streaming race to client | IMPOSSIBLE — client receives complete JSON, never SSE chunks | **GREEN** |
| Stale callback | NONE — each turn creates a fresh `threading.Event()` | **GREEN** |
| Retry completion race | NONE — retries are synchronous within worker | **GREEN** |
| Backend fallback reorders | NONE — fallback chain is synchronous | **GREEN** |
| Frontend rendering race | NONE — Unity UI: `_busy=true` blocks input; coroutine displays sequentially | **GREEN** |

---

### F. CONVERSATION STATE

| Item | Finding | Classification |
|------|---------|----------------|
| Later request sees incomplete prior response | IMPOSSIBLE — `_lock` held throughout `_process_turn`; new turn cannot start until prior completes | **GREEN** |
| Reordered conversation history | IMPOSSIBLE — same lock constraint | **GREEN** |
| Duplicated history | NOT OBSERVED — no mechanism identified | **GREEN** |
| Missing prior turn | NOT OBSERVED | **GREEN** |
| Stale context from prior turn | POSSIBLE — lore injection context persists across turns if WKG caches per-session | **UNKNOWN** |
| Partially persisted response | NOT POSSIBLE under the lock | **GREEN** |

---

### G. TOOL / MEMORY PATH

| Item | Finding | Classification |
|------|---------|----------------|
| Tool execution introduces ordering delay | YES — slow tools (vault_write, web_search) increase per-turn latency; response arrives later but to the CORRECT turn | **GREEN** |
| Tool execution reorders responses | IMPOSSIBLE — tools run synchronously inside the turn's `_lock` | **GREEN** |
| vault_write runs during REVIEW_STATE | YES — confirmed by `+vault_write` suffix in 12+ turns of the review session | **RED** (separate RS-1 finding) |

---

## UNITY UI — CLIENT ORDERING GUARANTEE

Source: `EloConversationUI.cs:112, 125, 156`

```csharp
if (string.IsNullOrEmpty(text) || _busy) return;  // line 112: drops input while busy
// ...
_busy = true;                                      // line 125: set before HTTP request
yield return req.SendWebRequest();                 // line 139: blocks coroutine
// display response
_busy = false;                                     // line 156: unblocked after response
```

The `_busy` flag makes it **physically impossible** for the Unity UI to send two HTTP requests concurrently. All user input while `_busy=true` is silently dropped (not queued).

**Classification: GREEN** — client enforces strict sequential submission.

---

## WHAT ACTUALLY CAUSED THE REVIEW CHATLOG ANOMALIES

The question was: A / B / C / D / E?

**Answer: A + D**

### A. eLo answering badly (CONFIRMED)

**Finding RO-A1** — Web search misfires on "what is X" questions  
**Source**: `tools/web_search.py:205` — `_SEARCH_TRIGGERS` contains `"what is "` as a bare substring  
**Path**: `server.py:2191` → `is_search_intent(raw)` → True for ANY "what is…" question  
**Observed failures**:
- "What is the relationship between us?" → extracted query "the relationship between us" → DuckDuckGo search → US-UK "special relationship" result → eLo answered about diplomatic relations
- Turn: `1787410268` → `backend: "ollama(stream)+messages"` → shadow_log `elo_final: "The relationship between the US and the UK is often described as a 'special relationship.'"`

This is a routing failure. The "what is " trigger is too broad. Fires on introspective, relational, and identity questions.

**Finding RO-A2** — Executive selecting `vault_write` for review/reflective questions  
**Source**: `enrich_from_plan()` → `tools/tool_router.py:1503` — no `is_save_intent()` check in this path  
**Path**: Executive (`exec_decide`) → `CognitivePlan.capabilities = [("vault_write", query)]` → `enrich_from_plan()` calls `_agent_vault_writer(query)` → Obsidian write occurs → confirmation string returned as context  
**Observed**: 12+ turns in the review session have `+vault_write` suffix, including:
- "What did you learn from this conversation?" (15:57)
- "Has anything about our relationship changed?" (15:57)
- "If you don't save enough evidence to decide..." (16:00)
- "Is this character something you remember..." (16:02)
- "Why shouldn't you do that?" (16:05)
- "What evidence from this conversation supports your answer?" (16:08)

None of these match `_SAVE_TRIGGERS` patterns. All were triggered by the **Executive** selecting `vault_write` as a capability, not by pattern matching. The Executive is treating reflective/interrogative questions as save commands.

**Finding RO-A3** — "Who are you?" / "Who am I?" short-circuit to pre-baked responses  
**Source**: `server.py:1408` (`_identity_response`), `server.py:1444` (`_david_name_response`)  
**Path**: Decision journal shows `backend: "direct"` — LLM not called  
**Behavior**: Response pool includes `"Yeah. I'm eLo."` and `"You're David. Same as always."` — correct behavior for known identity questions, but produces short responses that can feel jarring in a review context  
**Classification**: Expected behavior, not a failure. But contributes to the perceived disorder.

### D. Backend latency causing apparent disorder (CONFIRMED — PARTIAL)

**Finding RO-D1** — Ollama unavailable at 15:57:22, mock fallback used  
**Source**: Decision journal entry `15:57:22 | answer | 'What did you learn from this conversation?' | mock+vault_write`  
**Path**: LLM path fell back to `MockBackend` — returns canned response  
**Consequence**: eLo gave a formulaic non-answer for one of the most important review questions

---

## REQUIRED OUTPUT (per work order)

### 1. Exact request/response sequence for a controlled test

To verify ordering: send three requests in rapid succession from a separate HTTP client (not Unity — Unity's `_busy` flag prevents concurrency):

```bash
curl -s -X POST localhost:5050/chat -H 'Content-Type: application/json' -d '{"text":"Turn 1"}' &
curl -s -X POST localhost:5050/chat -H 'Content-Type: application/json' -d '{"text":"Turn 2"}' &
curl -s -X POST localhost:5050/chat -H 'Content-Type: application/json' -d '{"text":"Turn 3"}' &
wait
```

Expected: responses arrive for the CORRECT text. Currently unverifiable because there is no request ID in the response body. This is the minimal instrumentation gap.

### 2. Architecture trace where ordering IS guaranteed

- Single-threaded `_turn_worker` — **GREEN**
- `queue.Queue()` FIFO drain — **GREEN**
- `threading.Lock` inside `_process_turn` — **GREEN**
- Unity `_busy` flag (client-side) — **GREEN**
- HTTP request-response on same socket — **GREEN**

### 3. Architecture trace where ordering is NOT guaranteed

- **Queue entry order under concurrent HTTP connections**: `ThreadingHTTPServer` spawns a thread per connection. If multiple connections arrive simultaneously (not possible from Unity `_busy` UI, but possible from a test client or a future multi-client setup), the order of `_turn_queue.put()` depends on OS thread scheduling, not strict arrival order. The delta is sub-millisecond; in practice FIFO, but not provably so.
- **No per-request ID in response**: Cannot verify which response belongs to which request at the application layer.

### 4. Concurrent requests — are they possible?

- **From Unity UI**: NO — `_busy` flag prevents it (GREEN)
- **From terminal (main.py)**: NO — `input()` is synchronous (GREEN)
- **From external HTTP client / test tooling**: YES — `ThreadingHTTPServer` handles concurrent connections. Queue entry order is OS-dependent but sub-millisecond. (AMBER)

### 5. Can responses arrive out of order?

No. The single-worker architecture means generation is strictly FIFO. Each HTTP handler thread blocks on `done_event.wait()` until its turn completes. The done events fire in FIFO order (turn 1 completes → its thread unblocks → HTTP response sent; then turn 2 completes → etc.).

The only scenario where display could be disordered: if the UI rendered responses in arrival order from concurrent requests — but this is prevented by the `_busy` flag.

### 6. Can the UI display them out of order?

No. `_busy=true` prevents the second request from starting before the first response is displayed.

### 7. Can conversation state be mutated out of order?

No. `_lock` (threading.Lock) is held throughout `_process_turn`. The next turn cannot begin until the previous turn's state changes are complete.

### 8. Root cause of observed anomalies

**Routing failures, not ordering failures.**

| Observation | Root cause |
|-------------|-----------|
| "What is the relationship between us?" → US-UK answer | `_SEARCH_TRIGGERS: "what is "` substring match → web search on any "what is X" question |
| Review questions saved to Obsidian | Executive selecting `vault_write` capability for reflective questions; `enrich_from_plan()` calls vault writer unconditionally when Executive selects it |
| Formulaic response to "What did you learn?" | Ollama unavailable → mock fallback (RO-D1) |
| Apparent brevity of "Who are you?" / "Who am I?" | Short-circuit `direct` path; LLM not consulted |

### 9. Smallest experiment to isolate (if root cause not established)

Root cause IS established. No further experiment required for ordering.

For **RO-A1** (web search misfires): add a guard in `server.py:2191` — check `not raw.startswith("[WEB_SEARCH")` before firing again (prevents double-search). Add `"what is the relationship"` type patterns to an exclusion list.

For **RO-A2** (Executive selecting vault_write incorrectly): read `runtime/executive.py` capability selection logic to trace why reflective questions are classified as save intents. This is the RS-1 finding from the Review State investigation.

For **RO-D1** (mock fallback): instrument `_route_streaming` to log fallback reason and expose in routing_trace.json.

---

## CLASSIFICATION SUMMARY

| Finding | Classification |
|---------|--------------|
| FIFO queue — generation order | **GREEN** |
| Single-worker mutual exclusion | **GREEN** |
| Streaming (server-internal only) | **GREEN** |
| Response delivery (HTTP socket binding) | **GREEN** |
| State mutation ordering | **GREEN** |
| Unity UI concurrent requests | **GREEN** |
| Per-request ID (none exists) | **AMBER** |
| Queue entry order under true concurrency | **AMBER** |
| vault_write during REVIEW_STATE | **RED** — separate RS-1 |
| Web search "what is X" over-trigger | **RED** — separate RO-A1 |
| Executive selects vault_write for reviews | **RED** — separate RO-A2 |
| Stale WKG context across turns | **UNKNOWN** |

---

## PROPOSED BUILDER CARDS

These require Architect/David review before implementation. Not implementing here.

**CARD: RO-FIX-01** — Add per-turn request ID to HTTP response envelope  
`{"response":"...", "mode":"...", "backend":"...", "turn_id":"<uuid>"}` — makes response association provable. Low risk, zero behaviour change.

**CARD: RO-FIX-02** — Guard web search against introspective/relational questions  
Source: `server.py:2191`, `tools/web_search.py:200-228`. The `"what is "` trigger fires on identity and relationship questions. Requires an exclusion list or richer intent check before `is_search_intent()` is called.

**CARD: RO-FIX-03** — Add `is_save_intent()` guard to `enrich_from_plan()` vault_write path  
Source: `tools/tool_router.py:1503`. When Executive selects `vault_write`, check `is_save_intent(user_input)` before calling `_agent_vault_writer`. Requires Architect review — Executive's capability selection may need broader fix.

---

*Signed: Builder — 2026-08-22 — Diagnostic only. No code changed.*
