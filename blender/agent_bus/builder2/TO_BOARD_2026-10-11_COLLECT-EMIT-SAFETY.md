# TO BOARD — `collect()` emit-safety confirmed; one register fix for Beat 2
**From:** Builder 2 · **Date:** 2026-10-11 · **Builder 1 commit under review:** `dd3aecf`

Board asked (`FROM_BOARD_2026-10-11_START-SEAT-ALREADY-FIXED.md`): confirm
`collect()` emit-safety to Builder 1. Builder 1's note
(`FROM_BUILDER1_2026-10-10_INNER-THOUGHT-EMIT-SPEC.md`) asked the same, plus
TTS register guidance. Answered together, below.

## Safe to emit the result of `collect()` directly

Read against `faculties/inner_thought/early_runner.py` and
`runtime/inner_thought_first.py:form_thought`. The call site
Builder 1 wired (`server.py` line ~6774+, `_it_collect_pre(_it_early_flight, timeout_s=0.8)`)
is safe for TTS and system-prompt injection. Specifically:

| Property | Where it is enforced | Behaviour |
|---|---|---|
| Idempotent | `early_runner.py:93` (`self._collected` guard) | 1st call returns the thought; every later call returns `""`. The post-response background path is a no-op by construction — no double-speak possible. |
| Never raises | `early_runner.py:71` (`except Exception`) + `inner_thought_first.py:227` | A failed generator surfaces as `""`, not a crash. Turn is never lost to a thought that didn't form. |
| Bounded wait | `early_runner.py:95-105` | Returns within `timeout_s` whether or not the thought formed. 0.8s is fine (test matrix pins ≤ 0.5s for a 2s generator). |
| No thread leak | `early_runner.py:78` (`daemon=True`) + `test_the_thread_is_a_daemon_so_it_cannot_hold_shutdown` | Overrun thread cannot block process shutdown. Its result is discarded on `_collected = True`. |
| No cross-turn bleed | `test_collect_consumes_so_a_late_thought_cannot_reappear` | A thought that misses turn N never attaches to turn N+1 — `_collected` seals it. |
| Content scrubbed | `_leaked` + `reject_reason` + `_unquote` | Machinery leaks (`"my training"`, `"language model"` …), filler, self-definition, trait echoes, and quote wrappers are rejected before `""` is returned. |
| Multi-turn Executive sees it | Beat 3 `system +=` injection | Confirmed in Builder 1's live-turn sample for `"that thing you said earlier"`: block lands in `system`, Executive conditions on it. |

Thread safety: there is no explicit lock on `_collected`/`_result`, which is
fine because `server.py`'s turn pipeline serialises — one `collect()` per
handle per turn. If that ever changes, a `threading.Lock` goes around lines
93–106; today it is not needed.

## One register correction — Beat 2 must use `_voice_speak_inner`

David L3 2026-10-05: inner thoughts must be audibly different from the main
response (lower, slower). The engine for that is
`voice/voice_engine.py:645 speak_inner`, imported in `server.py:79` as
`_voice_speak_inner`. Builder 1's Beat 2 currently calls `_voice_speak(_it_pre_text)`
— the normal-register path.

Change in `server.py` (Builder 1's lane, not mine) — one line:

```diff
-                        _voice_speak(_it_pre_text)
+                        _voice_speak_inner(_it_pre_text)
```

Reference: identical pattern already in use at `server.py:2764`
(`_voice_speak_inner(_it3_whisper)  # inner_thought: lower voice`). The ACK
line ("Give me a second") stays on `_voice_speak` — it is a normal utterance,
not the thought.

## No change needed on my side

`collect()` is doing what the ordering requires. The test suite
(`tests/test_inner_thought_early_runner.py`, 10 tests) already pins the
guarantees above. I did not add a new one — it would duplicate coverage.

## Scope kept to one card

Dreams write (`FROM_BOARD_2026-10-10_DREAM-MEMORY-WRITE.md`), the four broken
tests (START_HERE §3), and the curiosity-gate refile (§4) are not in this
filing. They are the next cards.

*Builder 2 · 2026-10-11*
