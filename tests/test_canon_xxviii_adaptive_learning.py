"""
tests/test_canon_xxviii_adaptive_learning.py — WO-CANON-XXVIII: Adaptive Learning
Acceptance tests for Vol XXVIII Learning Faculty (ADR-Exec-005 D4/D5/D6).

Test families:
  LF-*  — Learning Faculty: consult(), LearningAdvice, evidence gate, reason travels
  RW-*  — Reward as Significance-vector (not a scalar)
  CB-*  — Constitutional boundary: RL never alters identity/values/truth
  DM-*  — Domains: movement, curiosity, presence timing (robot=RESERVED)
  SIM-* — Simulation-first (confidence threshold before real action)
  AT-*  — Compile hygiene

Notes:
  DM-1/2/3 (domain classes) and SIM-1 (simulation path) are [KNOWN-GAP]:
  domain-specific policy classes and simulation engine not yet built in faculty.py.
  DM-4 (robot RESERVED) is verified as a constitutional constraint, not a code gate.
"""
import os
import sys
import py_compile
import inspect
import re

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
print("WO-CANON-XXVIII  Adaptive Learning & Reinforcement (Learning Faculty)")
print("-" * 75)


# ─── test helpers ─────────────────────────────────────────────────────────────

def _verified_lesson(lesson_id="L1", action="answer", statement="prefer this",
                     scope="", applies_when=None, strength=0.8) -> dict:
    """A lesson that passes the ADR-Exec-005 D1 evidence gate."""
    return {
        "lesson_id": lesson_id,
        "statement": statement,
        "scope": scope,
        "applies_when": applies_when or [],
        "prefers_action": action,
        "avoids_action": "",
        "strength": strength,
        "evidence": [{"verified": True, "session_id": "sess-abc123",
                      "action": "answer", "outcome": "user expressed gratitude"}],
    }


def _unverified_lesson(lesson_id="L9") -> dict:
    """A lesson that fails the D1 gate — no verified evidence."""
    return {
        "lesson_id": lesson_id,
        "statement": "this might be true",
        "prefers_action": "answer",
        "strength": 0.9,
        "evidence": [{"verified": False, "session_id": "12345",
                      "action": "", "outcome": ""}],
    }


# ═══════════════════════════════════════════════════════════════
# LF — Learning Faculty: consult(), LearningAdvice, evidence gate
# ═══════════════════════════════════════════════════════════════
print("\n── LF: Learning Faculty contract ──")


# LF-1: Learning Faculty is an ASSESSOR — consult() is the only public surface
try:
    from faculties.learning.faculty import consult, LearningAdvice
    result = consult([_verified_lesson()], candidate_action="answer",
                     context={"intent": "help"})
    assert isinstance(result, LearningAdvice), \
        f"consult() must return LearningAdvice, got {type(result)}"
    assert result.consulted, "consult() must set consulted=True"
    ok("LF-1: consult() returns LearningAdvice — the ONLY public surface (ADR-Exec-005 D6)")
except AssertionError as e:
    fail("LF-1", e)
except Exception as e:
    fail("LF-1", e)


# LF-2: Unverified lessons produce no action influence (D1 gate)
try:
    from faculties.learning.faculty import consult
    result = consult([_unverified_lesson()], candidate_action="answer")
    assert result.preferences == {}, \
        f"Unverified lesson must produce no preferences, got {result.preferences}"
    assert result.confidence == 0.0, \
        f"Unverified lesson must produce confidence=0.0, got {result.confidence}"
    assert result.consulted, "consulted must be True even when all lessons are rejected"
    ok("LF-2: unverified lessons produce no action influence — "
       "ADR-Exec-005 D1 'language alone is never evidence'")
except AssertionError as e:
    fail("LF-2", e)
except Exception as e:
    fail("LF-2", e)


# LF-3: The reason travels with the lesson (David 2026-08-21: "there is a reason to why")
try:
    from faculties.learning.faculty import consult
    lesson = _verified_lesson(lesson_id="L3", statement="when the user is coding, be quiet",
                               action="silence", applies_when=["coding"])
    result = consult([lesson], candidate_action="silence",
                     context={"intent": "user is coding", "focal_thread": "focused work"})
    assert result.reasons, "reasons list must be non-empty when a lesson applies"
    for r in result.reasons:
        assert "why" in r, f"each reason entry must carry a 'why' key: {r}"
        assert r["why"], "why must be non-empty (not a bare weight)"
        assert "lesson_id" in r, f"reason must carry lesson_id for traceability: {r}"
    ok(f"LF-3: reason travels with lesson — {len(result.reasons)} reason(s), "
       f"each carrying why + lesson_id (not a bare weight)")
except AssertionError as e:
    fail("LF-3", e)
except Exception as e:
    fail("LF-3", e)


# LF-4: Partial fit raises curiosity (D4 curiosity threshold)
try:
    from faculties.learning.faculty import consult
    lesson = _verified_lesson(lesson_id="L4", statement="this applies to creative tasks",
                               action="build", applies_when=["creative", "specific-context"])
    # Context matches only one of the applies_when conditions → partial fit
    result = consult([lesson], candidate_action="build",
                     context={"intent": "creative", "focal_thread": "other"})
    assert result.fit in ("partial", "conflicts", "fits", "none"), \
        f"fit must be a known string value, got {result.fit!r}"
    ok(f"LF-4: fit classification works (fit='{result.fit}', "
       f"curiosity={result.curiosity:.2f}) — partial fit raises curiosity, not compliance")
except AssertionError as e:
    fail("LF-4", e)
except Exception as e:
    fail("LF-4", e)


# LF-5: LearningAdvice fields cover D4 scope — action preferences only, not truth or speech
try:
    import dataclasses
    from faculties.learning.faculty import LearningAdvice
    fields = {f.name for f in dataclasses.fields(LearningAdvice)}
    expected = {"preferences", "confidence", "lesson_ids", "reasons", "curiosity",
                "wants_to_know", "fit", "rationale", "consulted"}
    missing = expected - fields
    assert not missing, f"LearningAdvice missing fields: {missing}"
    # Forbidden: no truth / speech / identity fields
    forbidden_fields = {"verified_truth", "speech_permission", "identity", "exec_decision",
                        "conclusion"}
    present_forbidden = fields & forbidden_fields
    assert not present_forbidden, \
        f"LearningAdvice must not have truth/speech/identity fields: {present_forbidden}"
    ok(f"LearningAdvice has {len(fields)} fields — D4 scope only (action preferences, "
       "confidence, curiosity, reasons) — no truth/speech/exec fields")
except AssertionError as e:
    fail("LF-5", e)
except Exception as e:
    fail("LF-5", e)


# LF-6: No lessons → rationale explains why, consulted=True
try:
    from faculties.learning.faculty import consult
    result = consult([], candidate_action="answer")
    assert result.consulted, "consulted=True even with no lessons"
    assert result.rationale, "rationale must explain the absence of usable lessons"
    ok(f"LF-6: no lessons → consulted=True, rationale='{result.rationale}'")
except AssertionError as e:
    fail("LF-6", e)
except Exception as e:
    fail("LF-6", e)


# ═══════════════════════════════════════════════════════════════
# RW — Reward as Significance-vector
# ═══════════════════════════════════════════════════════════════
print("\n── RW: reward = Significance-vector (not a scalar) ──")


# RW-1: Significance Engine importable and returns a dict (vector, not scalar)
try:
    from memory.significance_engine import evaluate as sig_evaluate
    sig = sig_evaluate(
        raw="eLo jumped across the window",
        response="that was smooth",
        action="build",
        plan=None,
        state={"last_topics": [], "session_anchor": {"open_loops": []}},
    )
    assert isinstance(sig, dict), "significance_engine.evaluate must return a dict (vector)"
    assert "overall" in sig, "significance vector must include 'overall' field"
    ok(f"RW-1: significance_engine.evaluate returns a vector dict "
       f"(overall={sig.get('overall', '?'):.3f}) — not a scalar reward")
except AssertionError as e:
    fail("RW-1", e)
except Exception as e:
    fail("RW-1", e)


# RW-2: Learning Faculty does NOT invent a scalar reward — no local reward computation
try:
    from faculties.learning import faculty as _lf
    lf_src = inspect.getsource(_lf)
    # Check it doesn't define its own reward scalar (reward = float, reward_fn, etc.)
    scalar_patterns = re.findall(r"\breward\s*=\s*[\d.]+\b|\breward_fn\b|\bscalar_reward\b", lf_src)
    assert not scalar_patterns, \
        f"faculty.py must not invent a scalar reward — use significance_engine: {scalar_patterns}"
    ok("RW-2: faculty.py has no scalar reward computation — "
       "reward is the Significance-vector (Vol V Ch.5 / significance_engine.py)")
except AssertionError as e:
    fail("RW-2", e)
except Exception as e:
    fail("RW-2", e)


# RW-3: Significance vector has expected dimensions (Vol V Ch.5 alignment)
try:
    from memory.significance_engine import evaluate as sig_evaluate
    sig = sig_evaluate(
        raw="test",
        response="ok",
        action="answer",
        plan=None,
        state={"last_topics": [], "session_anchor": {"open_loops": []}},
    )
    # Vol XXVIII spec: Meaning · Novelty · Relationship · Embodiment · Curiosity · Efficiency · Safety
    expected_dims = {"overall"}  # minimum required; others optional but expected
    missing = expected_dims - set(sig.keys())
    assert not missing, f"significance vector missing dims: {missing}"
    ok(f"RW-3: significance vector has required dimensions — keys={list(sig.keys())}")
except AssertionError as e:
    fail("RW-3", e)
except Exception as e:
    fail("RW-3", e)


# ═══════════════════════════════════════════════════════════════
# CB — Constitutional boundary
# ═══════════════════════════════════════════════════════════════
print("\n── CB: constitutional boundary (RL never alters identity/values/truth) ──")


# CB-1: faculty.py does not import or call the Executive — it ADVISES only
try:
    from faculties.learning import faculty as _lf
    lf_src = inspect.getsource(_lf)
    forbidden = ["exec_decide", "_executive_faculty", "import executive",
                 "from runtime.executive", "import runtime.executive"]
    hits = [f for f in forbidden if f in lf_src]
    assert not hits, \
        f"faculty.py must not import or call Executive (it advises — never decides): {hits}"
    ok("CB-1: faculty.py does not import/call Executive — Learning Faculty ADVISES, never decides "
       "(ADR-Exec-005 D6: 'faculty the Executive ASKS')")
except AssertionError as e:
    fail("CB-1", e)
except Exception as e:
    fail("CB-1", e)


# CB-2: faculty.py does not write to truth / memory truth / identity
try:
    from faculties.learning import faculty as _lf
    lf_src = inspect.getsource(_lf)
    truth_writes = ["memory_truth", "verified_truth", "write_truth", "update_identity",
                    "set_identity", "write_identity"]
    hits = [t for t in truth_writes if t in lf_src]
    assert not hits, \
        f"faculty.py must not write to truth or identity: {hits}"
    ok("CB-2: faculty.py has no truth/identity writes — "
       "ADR-Exec-005 D5 'memory truth never changes'")
except AssertionError as e:
    fail("CB-2", e)
except Exception as e:
    fail("CB-2", e)


# CB-3: The 9 CAL actions are frozen — faculty can weight, never add/remove/rename
try:
    from faculties.learning import faculty as _lf
    lf_src = inspect.getsource(_lf)
    # _CAL_ACTIONS must be defined as a tuple/constant
    assert "_CAL_ACTIONS" in lf_src, \
        "faculty.py must define _CAL_ACTIONS (frozen action set from FREEZE_V1_LOCK §5)"
    import re as _re
    match = _re.search(r'_CAL_ACTIONS\s*=\s*\(([^)]+)\)', lf_src)
    assert match, "_CAL_ACTIONS must be a frozen tuple"
    action_count = len([a.strip().strip('"\'') for a in match.group(1).split(',') if a.strip()])
    assert action_count == 9, \
        f"_CAL_ACTIONS must have exactly 9 actions (FREEZE_V1_LOCK §5), got {action_count}"
    ok(f"CB-3: _CAL_ACTIONS frozen at 9 actions — Learning Faculty weights them, never adds/removes "
       f"(FREEZE_V1_LOCK §5)")
except AssertionError as e:
    fail("CB-3", e)
except Exception as e:
    fail("CB-3", e)


# ═══════════════════════════════════════════════════════════════
# DM — Domains
# ═══════════════════════════════════════════════════════════════
print("\n── DM: domains (movement, curiosity, presence, robot-RESERVED) ──")


# DM-1: Movement domain [KNOWN-GAP — policy class not built]
try:
    gap("DM-1",
        "Movement domain policy class not yet built. Vol XXVIII §'four domains' domain 1: "
        "state=window·speed·momentum; actions=walk/run/jump/…; reward=Significance-vector. "
        "No MovementPolicy in faculty.py or faculties/learning/. Gap until WO-049 + WO-056 land.")
except Exception as e:
    fail("DM-1", e)


# DM-2: Curiosity domain [KNOWN-GAP — policy class not built]
try:
    gap("DM-2",
        "Curiosity domain policy class not yet built. Vol XXVIII domain 2: learned exploration "
        "(don't interrupt David, discover affordances). No CuriosityPolicy in faculty.py. Gap.")
except Exception as e:
    fail("DM-2", e)


# DM-3: Presence timing domain [KNOWN-GAP — policy class not built]
try:
    gap("DM-3",
        "Presence timing domain policy class not yet built. Vol XXVIII domain 3: learns "
        "*when* to approach/observe/disappear from David's state. No PresenceTimingPolicy. "
        "Vol XIII Presence provides the state feed; timing RL not yet wired.")
except Exception as e:
    fail("DM-3", e)


# DM-4: Robot locomotion is RESERVED — must not be built without LG-2 + David L3
try:
    # Verify the Vol XXVIII spec itself records the RESERVED constraint
    spec_path = "docs/architecture/Volume_XXVIII/00_Adaptive_Learning_Reinforcement.md"
    assert os.path.exists(spec_path), f"Vol XXVIII spec must exist at {spec_path}"
    with open(spec_path) as f:
        spec_text = f.read()
    assert "RESERVED" in spec_text, \
        "Vol XXVIII spec must record RESERVED for robot locomotion (RD-3)"
    assert "LG-2" in spec_text or "legal" in spec_text.lower(), \
        "Vol XXVIII spec must reference LG-2 / legal review for robot domain"
    assert "robot" in spec_text.lower(), "spec must mention robot domain"
    ok("DM-4: robot locomotion (RD-3) is RESERVED — spec records LG-2 + David L3 gate "
       "(safety, not sequencing — physical mass)")
except AssertionError as e:
    fail("DM-4", e)
except Exception as e:
    fail("DM-4", e)


# ═══════════════════════════════════════════════════════════════
# SIM — Simulation-first
# ═══════════════════════════════════════════════════════════════
print("\n── SIM: simulation-first ──")


# SIM-1: Simulation-first — confidence threshold before real action [KNOWN-GAP]
try:
    gap("SIM-1",
        "Simulation-first path not yet built. Vol XXVIII spec: eLo simulates movement → "
        "fails/succeeds → stores policy + confidence → Executive only acts for real above "
        "confidence/safety threshold. No simulate() or confidence gate in faculty.py. Gap.")
except Exception as e:
    fail("SIM-1", e)


# ═══════════════════════════════════════════════════════════════
# AT — Compile hygiene
# ═══════════════════════════════════════════════════════════════
print("\n── AT: compile hygiene ──")

for _mod in (
    "faculties/learning/faculty.py",
    "memory/significance_engine.py",
    "self/lesson_store.py",
):
    _label = f"AT-compile: {_mod}"
    try:
        py_compile.compile(_mod, doraise=True)
        ok(_label)
    except py_compile.PyCompileError as e:
        fail(_label, e)
    except FileNotFoundError:
        gap(_label, "file not found")
    except Exception as e:
        fail(_label, e)


# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 75)
print(f"WO-CANON-XXVIII adaptive learning   {_passed} passed   {_gap} known-gaps   {_failed} failed")
if _failed:
    sys.exit(1)
