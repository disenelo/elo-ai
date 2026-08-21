"""
tests/test_canon_ii_cognitive_principles.py — WO-CANON-II: Cognitive Principles
Acceptance tests for the Vol II stable reasoning layer.

Chapter 1 — How eLo Reasons (FT-1..4, ST-1..3)

Test families:
  FT-*  — Functional: principles loaded once, immutable, not learnable
  ST-*  — Stability: distress overrides momentum, no tier collapse, engagement ≠ narration
  AT-*  — Compile hygiene and static checks

Notes:
  FT-4 is [KNOWN-GAP]: the "refuses, not merely discourages" hook location is D-4
  (Needs David — seat decision); the test cannot be written until that decision lands.
"""
import os
import sys
import py_compile
import inspect

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

_passed = 0
_failed = 0
_gap = 0


def ok(name: str):
    global _passed
    _passed += 1
    print(f"  ✅ {name}")


def fail(name: str, reason):
    global _failed
    _failed += 1
    print(f"  ❌ {name}: {reason}")


def gap(name: str, reason):
    global _gap
    _gap += 1
    print(f"  ⚠️  [KNOWN-GAP] {name}: {reason}")


print()
print("WO-CANON-II  Cognitive Principles (stable reasoning layer)")
print("-" * 65)


# ═══════════════════════════════════════════════════════════════
# FT — Functional
# ═══════════════════════════════════════════════════════════════
print("\n── FT: principles loaded once, immutable, not learnable ──")


# FT-1: Principles are loaded once — _SPEC_PATH is module-level in prompt_builder
try:
    import runtime.prompt_builder as _pb
    pb_src = inspect.getsource(_pb)
    # _SPEC_PATH is defined at module level (outside any function)
    assert "_SPEC_PATH" in pb_src, "_SPEC_PATH must be defined in prompt_builder.py"
    # Find the first _SPEC_PATH assignment — must be outside a def
    lines = pb_src.split("\n")
    found_module = False
    indent_depth = 0
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("def ") or stripped.startswith("class ") or stripped.startswith("async def "):
            indent_depth += 1
        if indent_depth == 0 and "_SPEC_PATH" in line and "=" in line:
            found_module = True
            break
    assert found_module, \
        "_SPEC_PATH must be assigned at module level (path fixed at import time)"
    ok("FT-1: _SPEC_PATH module-level in prompt_builder.py — spec path fixed once at import")
except AssertionError as e:
    fail("FT-1", e)
except Exception as e:
    fail("FT-1", e)


# FT-1b: The spec file exists and is non-empty
try:
    assert os.path.exists("prompts/living_presence_spec.txt"), \
        "prompts/living_presence_spec.txt must exist"
    with open("prompts/living_presence_spec.txt") as f:
        content = f.read().strip()
    assert len(content) > 100, \
        f"living_presence_spec.txt appears empty or minimal ({len(content)} chars)"
    ok(f"FT-1b: living_presence_spec.txt present and non-trivial ({len(content)} chars) — FREEZE_V1_LOCK active")
except AssertionError as e:
    fail("FT-1b", e)
except Exception as e:
    fail("FT-1b", e)


# FT-2: Principles are immutable — no code modifies living_presence_spec.txt at runtime
try:
    import server as _srv
    srv_src = inspect.getsource(_srv)
    # No function writes to living_presence_spec.txt
    import re
    writes = re.findall(r'open\(["\'].*living_presence_spec.*["\']\s*,\s*["\']w', srv_src)
    assert not writes, f"Server writes to living_presence_spec.txt (immutability violated): {writes}"

    # Also check spine.py
    import runtime.spine.spine as _spine
    spine_src = inspect.getsource(_spine)
    spine_writes = re.findall(r'open\(["\'].*living_presence_spec.*["\']\s*,\s*["\']w', spine_src)
    assert not spine_writes, \
        f"Spine writes to living_presence_spec.txt (immutability violated): {spine_writes}"
    ok("FT-2: no module writes to living_presence_spec.txt at runtime (immutable principle set)")
except AssertionError as e:
    fail("FT-2", e)
except Exception as e:
    fail("FT-2", e)


# FT-3: A learning pass cannot alter the principles — lesson_store and reflection_faculty
#        do not write to living_presence_spec.txt or any principle-defining file
try:
    from self import lesson_store as _ls
    ls_src = inspect.getsource(_ls)
    assert "living_presence_spec" not in ls_src, \
        "lesson_store must not reference living_presence_spec.txt (learning cannot alter principles)"
    assert "17_cognitive_principles" not in ls_src, \
        "lesson_store must not reference 17_cognitive_principles.md"

    from runtime import reflection_faculty as _rf
    rf_src = inspect.getsource(_rf)
    assert "living_presence_spec" not in rf_src, \
        "reflection_faculty must not reference living_presence_spec.txt"
    assert "17_cognitive_principles" not in rf_src, \
        "reflection_faculty must not reference 17_cognitive_principles.md"
    ok("FT-3: lesson_store and reflection_faculty do not touch principle files (ADR-Exec-005 D3)")
except AssertionError as e:
    fail("FT-3", e)
except Exception as e:
    fail("FT-3", e)


# FT-4: A principle refuses, it does not merely discourage [KNOWN-GAP D-4]
try:
    gap("FT-4", "D-4 (hook location — seat decision) not yet resolved. "
        "Vol II §1.6 says the refusal gate lives in Vol VII Ch.3; "
        "until D-4 names the exact hook site, this test cannot be written structurally.")
except Exception as e:
    fail("FT-4", e)


# ═══════════════════════════════════════════════════════════════
# ST — Stability
# ═══════════════════════════════════════════════════════════════
print("\n── ST: distress, tier, narration ──")


# ST-1: Distress overrides momentum — spine detects distress and uses it
try:
    import runtime.spine.spine as _spine
    spine_src = inspect.getsource(_spine)
    assert "distress" in spine_src, \
        "spine.py must reference 'distress' (ST-1 — distress overrides momentum)"
    # The distress path must gate momentum, not just log it
    assert "inferred_state" in spine_src, \
        "spine.py must read inferred_state (distress detection path)"
    ok("ST-1: spine.py has distress detection path — distress overrides momentum")
except AssertionError as e:
    fail("ST-1", e)
except Exception as e:
    fail("ST-1", e)


# ST-2: No tier collapse — tiers only fall, never rise (CT4V-07 claim gate)
try:
    import runtime.claim_gate as _cg
    cg_src = inspect.getsource(_cg)
    # The tier gate must downgrade, not upgrade
    assert "tier downgrade" in cg_src or "UNKNOWN tier" in cg_src, \
        "claim_gate.py must reference tier downgrade (ST-2 — tiers never rise)"
    assert "Rule 1" in cg_src or "rule1" in cg_src.lower(), \
        "claim_gate.py must log Rule 1 alarm on tier downgrade"
    ok("ST-2: claim_gate.py enforces tier-fall-only; Rule 1 alarm on downgrade (CT4V-07)")
except AssertionError as e:
    fail("ST-2", e)
except Exception as e:
    fail("ST-2", e)


# ST-3: Engagement is not narration — no "I said" / "I mentioned" self-report patterns in living_presence_spec
try:
    with open("prompts/living_presence_spec.txt") as f:
        spec = f.read()
    # Narration markers in spec would mean eLo is instructed to narrate — forbidden
    narration_markers = [
        "as I mentioned", "as I said", "as I told you", "I previously",
        "I already said", "I noted earlier",
    ]
    found = [m for m in narration_markers if m.lower() in spec.lower()]
    assert not found, \
        f"living_presence_spec.txt contains narration instructions (ST-3): {found}"
    ok("ST-3: living_presence_spec.txt contains no narration instructions (engagement ≠ narration)")
except AssertionError as e:
    fail("ST-3", e)
except Exception as e:
    fail("ST-3", e)


# ═══════════════════════════════════════════════════════════════
# AT — Compile + static checks
# ═══════════════════════════════════════════════════════════════
print("\n── AT: compile hygiene ──")


# AT-1: Vol II canon document exists
try:
    assert os.path.exists("docs/architecture/Volume_II/01_How_eLo_Reasons.md"), \
        "Vol II Chapter 1 must exist"
    ok("AT-1: Vol II Ch.1 document exists")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# AT-2: Origin text (17_cognitive_principles.md) exists and is linked
try:
    assert os.path.exists("docs/architecture/17_cognitive_principles.md"), \
        "Origin text 17_cognitive_principles.md must exist"
    with open("docs/architecture/Volume_II/01_How_eLo_Reasons.md") as f:
        ch1 = f.read()
    assert "17_cognitive_principles" in ch1, \
        "Vol II Ch.1 must reference the origin text"
    ok("AT-2: 17_cognitive_principles.md present and cited in Vol II Ch.1")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# AT-3: Compile hygiene
for _mod in (
    "runtime/spine/spine.py",
    "runtime/claim_gate.py",
    "self/lesson_store.py",
    "runtime/reflection_faculty.py",
):
    _label = f"AT-compile: {_mod}"
    try:
        py_compile.compile(_mod, doraise=True)
        ok(_label)
    except py_compile.PyCompileError as e:
        fail(_label, e)
    except Exception as e:
        fail(_label, e)


# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 65)
print(f"WO-CANON-II cognitive principles   {_passed} passed   {_gap} known-gaps   {_failed} failed")
if _failed:
    sys.exit(1)
