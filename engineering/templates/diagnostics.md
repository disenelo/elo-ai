# Diagnostics — [Work Package Name]

**Work Package:** WP_[X] — [Name]
**Engineer Role:** Diagnostics Engineer
**Date:**
**Status:** DRAFT / COMPLETE

---

## 1. Purpose

What is being diagnosed? What symptom or uncertainty prompted this diagnostic?

---

## 2. Diagnostic Environment

| Item | Value |
|---|---|
| Server version | |
| Backend(s) active | |
| eLo OS started via | Terminal / DISENELO Presence |
| Session duration | |
| Date / time | |

---

## 3. Runtime Health Check

Run these checks before any diagnostic session begins.

### 3.1 Server Running

```bash
curl -s http://localhost:5050/chat -H "Content-Type: application/json" \
  -d '{"text": "yo"}' | python3 -m json.tool
```

Expected: `{"response": "...", "mode": "...", "backend": "..."}`. Any other output = server issue.

### 3.2 Backend Active

```bash
# Check which backend responded
# Look at "backend" field in response above
```

### 3.3 Vision Loop

```bash
grep "vision" ~/elo-ai/blender/blender_state.json 2>/dev/null | head -5
```

Expected: `"vision": {"active": ..., "attention": ..., "app": ..., "description": ...}`

### 3.4 Screen Recording Permission

```bash
~/miniconda3/bin/python -c "from Quartz import CGPreflightScreenCaptureAccess; print(bool(CGPreflightScreenCaptureAccess()))"
```

Expected: `True`

---

## 4. Conversation Diagnostics

Record actual exchanges here. Include exact input, exact output, backend, and any anomaly.

| Turn | Input | Output | Backend | Anomaly |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |

---

## 5. Log Analysis

```bash
# Tail server log for errors
tail -100 ~/elo-ai/server.log | grep -i "error\|failed\|exception\|warn"
```

Paste relevant output:

```
[paste here]
```

---

## 6. blender_state.json Snapshot

```bash
cat ~/elo-ai/blender/blender_state.json | python3 -m json.tool
```

Paste:

```json
[paste here]
```

---

## 7. Identified Issues

| Issue | Severity | Root Cause | Affected File(s) |
|---|---|---|---|
| | | | |

---

## 8. Fixes Applied

| Issue | Fix | File Modified | Lines Changed |
|---|---|---|---|
| | | | |

---

## 9. Post-Fix Validation

Re-run health checks above. Confirm all pass.

| Check | Before | After |
|---|---|---|
| Server health | | |
| Backend active | | |
| Vision loop | | |
| Screen permission | | |

---

## 10. Outstanding Issues

Issues identified but not fixed in this session (with reason for deferral):

| Issue | Reason Deferred | Priority |
|---|---|---|
| | | |
