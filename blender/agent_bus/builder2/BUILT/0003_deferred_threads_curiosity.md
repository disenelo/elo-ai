**WO:** DEFERRED-THREADS · **Seat:** builder2 · **Priority:** P2
**Reserved?** no

## Goal
eLo can return to something he was curious about from a prior session.

## Scope
Create `faculties/inner_thought/deferred_threads.json` if it doesn't exist:
```json
[]
```

Each thread:
```json
{"thread_id":"DT-001","sparked_by":"David mentioned plotters","status":"OPEN","created":"2026-10-06T14:00:00Z","last_checked":null,"resolved":null}
```

On session start: load file, find OPEN threads. If any are relevant to current context, surface as an inner thought ("I'm still wondering about plotters — haven't looked into that yet."). When resolved: update status to RESOLVED.

Add or update entry when eLo encounters something genuinely unresolved.

## Files
`faculties/inner_thought/deferred_threads.json` (create) · `faculties/inner_thought/inner_thought_first.py` (session-start check)

## Test
Create a JSON with one OPEN thread → on "session start" mock → inner thought mentions the thread topic.

## Done when
implemented + test green + committed.

## Result
- commit:
- test:
- notes:
