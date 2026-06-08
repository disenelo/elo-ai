# eLo AI OS — Safe Update Rules

**Status**: Active from v1.0.0-stable
**Authority**: This document supersedes informal guidance. Consult before any change.

---

## What can be changed safely (no version bump required)

These changes are safe without a version increment or regression run:

| Change | Examples |
|---|---|
| Documentation | Updating TRACKER.md, VISION.md, identity/*.md, docs/ |
| Test additions | Adding new test cases that don't require system changes |
| Dashboard UI | HTML, CSS, terminal colour, layout |
| Config files | system_prompt.txt content, personality.json values |
| World graph | world/world_state.py spatial positions, node labels |
| New plugin | Adding a plugin to plugins/ that passes validate() |
| TTS/STT wiring | plugins/voice/ additions that don't touch core/ |
| Logging | Adding log statements that don't alter execution flow |

---

## What requires a PATCH version bump (x.x.N)

Run: `python tests/test_basic_loop.py` — must pass before merge.

| Change | Examples |
|---|---|
| Bug fix in adapter | Fixing a network error in ClaudeAPIAdapter |
| Dashboard server fix | Fixing an SSE disconnect bug |
| Unity bridge fix | Correcting a signal mapping error |
| Session persistence fix | Fixing a JSON parse error in restore_session() |
| Dependency update | Updating anthropic SDK version |

**Not allowed in a patch:**
- Routing changes
- New classification signals
- New cognitive rules

---

## What requires a MINOR version bump (x.N.0)

Run: all 4 test suites (91 tests) — must pass before merge.

```bash
python tests/test_basic_loop.py
python tests/cognitive_test_suite.py
python tests/engine_isolation_tests.py
python tests/loop_resilience_tests.py
```

| Change | Examples |
|---|---|
| New plugin | Adding a new VisionPlugin that passes validate() |
| New adapter | Adding an OpenAI adapter |
| New dashboard feature | Adding a new /metrics endpoint |
| New world graph feature | Adding bridge weights or 3D positions |
| New Unity signal field | Adding a new `facial_blend` field to EloSignalData |
| New public API in core/ | Adding a method that doesn't change existing behaviour |
| New test suite | Adding a new tests/ file |

**Not allowed in a minor:**
- Routing mode vocabulary changes
- New classification input types
- Loop detection rule changes
- Any change to StateBus fields
- Anything that causes existing tests to fail

---

## What requires a MAJOR version bump (N.0.0) + full audit

All 91 tests must pass AND manual review required.

| Change | Why major |
|---|---|
| Routing logic | Changes what mode is selected for any input |
| New routing mode | Expands the mode vocabulary |
| Classification signal changes | Changes what type is detected for any input |
| Loop detection rule changes | Changes when DIRECT override fires |
| StateBus field changes | Breaks immutability contract |
| Engine role expansion | State/emotion/identity gaining routing influence |
| EloSignalData schema breaking | Breaks Unity receivers |
| `decide_response()` signature | Breaks all callers |

**Required for MAJOR:**
1. Full test suite pass (91+ tests)
2. Update `RELEASE.md` with new frozen state
3. Entry in `CHANGELOG.md` with explicit "Breaking changes" section
4. Update `docs/final_system_report.md`
5. Update `VERSION` file

---

## Strictly forbidden (kernel audit required)

These changes are **never allowed without a formal audit** and MAJOR version increment:

```
FORBIDDEN WITHOUT AUDIT:
    ✗ Any edit to core/kernel.py
    ✗ Any edit to core/behavior_engine.py routing/generation logic
    ✗ Any edit to the route() function priority order
    ✗ Any change to _LOOP_TRIGGER or loop detection patterns
    ✗ Any change that modifies StateBus immutability
    ✗ Any plugin with KERNEL_SAFE=False
    ✗ Monkey-patching core/ module globals
    ✗ Any change that causes engine_isolation_tests.py to fail
```

A "kernel audit" means:
1. Full written rationale for why the change is necessary
2. Analysis of every test that could be affected
3. Before/after comparison of routing decisions for 20+ test inputs
4. MAJOR version bump regardless of scope

---

## Update checklist

Before any merge, verify:

```
□  Does the change fit into one of the allowed categories above?
□  Was the correct version segment incremented?
□  Did all required test suites pass?
□  Were no forbidden patterns introduced?
□  Is the CHANGELOG.md entry written?
□  Is the VERSION file updated (if applicable)?
```

---

## Rollback procedure

### Scenario: patch/minor rollback

```bash
git log --oneline -10          # find the last good commit
git revert <commit-hash>       # revert — do NOT reset
python tests/test_basic_loop.py  # verify clean
```

Never use `git reset --hard` on shared history.

### Scenario: major rollback

```bash
git log --oneline -20
git revert <commit-range>      # revert all commits since last major
# update VERSION, RELEASE.md, CHANGELOG.md
python tests/test_basic_loop.py
python tests/cognitive_test_suite.py
python tests/engine_isolation_tests.py
python tests/loop_resilience_tests.py
```

---

## Failure detection rules

A change has failed if any of the following are true after the change:

| Failure | Detection |
|---|---|
| Any test fails | `test_basic_loop.py` exit code non-zero |
| Route changed for known input | Cognitive suite FAIL |
| Engine isolation broken | Isolation suite FAIL |
| Loop detection altered | Resilience suite FAIL |
| Response contaminated | `"COGNITIVE DEBUG"` appears in response string |
| Backend fallback broken | `generate_response()` raises instead of falling back |
| StateBus mutated | `AttributeError` on bus field assignment |
| Plugin accepted unsafe | `KERNEL_SAFE=False` plugin appears in registry |

**Automated detection:**

```bash
# run all — any failure = change is unsafe
python tests/test_basic_loop.py           || echo "FAIL: basic"
python tests/cognitive_test_suite.py      || echo "FAIL: cognitive"
python tests/engine_isolation_tests.py    || echo "FAIL: isolation"
python tests/loop_resilience_tests.py     || echo "FAIL: resilience"
```

All four must exit 0. If any fail, rollback immediately.

---

*This document is the safe update authority for eLo AI OS.*
*Consult it before any change to the v1.0.0-stable codebase.*
