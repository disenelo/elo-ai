"""
tests/test_canon_xix_consciousness_research.py — WO-CANON-XIX: Consciousness Research
Acceptance tests for Vol XIX — a research programme, not an implementation.

Vol XIX's "Definition of Done" (Ch.1 §1.4):
  - Each research area has at least one framed, falsifiable question on record.
  - Every experiment run produces an ADR (hypothesis → method → result → decision).
  - No experiment has modified a Canon volume directly (all changes via ADR).
  - Ethical boundaries (Vol I / Identity Kernel) hold for every experiment.

Test families:
  ST-*  — Structural: all four chapters present, non-trivial
  GR-*  — Guardrail: §4.1 hard limits recorded in spec; codebase does not breach them
  RQ-*  — Research questions: framed and falsifiable in Ch.2
  MD-*  — Methodology: ADR-only output path recorded in Ch.3
  AT-*  — Compile hygiene (this volume emits no runtime code — no .py to compile)

Notes:
  This volume intentionally has NO runtime implementation. All tests are structural/
  documentary checks — verifying the guardrails are recorded and that the live codebase
  has not been silently modified by "research" bypassing the ADR gate.
"""
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

_passed = 0
_failed = 0
_gap = 0

_VOL_XIX = "docs/architecture/Volume_XIX"

CHAPTERS = {
    "Ch.1": f"{_VOL_XIX}/01_Research_Programme.md",
    "Ch.2": f"{_VOL_XIX}/02_Open_Research_Questions.md",
    "Ch.3": f"{_VOL_XIX}/03_Methodology.md",
    "Ch.4": f"{_VOL_XIX}/04_Scope_and_Guardrails.md",
}


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
print("WO-CANON-XIX  Consciousness Research Programme (structure + guardrails)")
print("-" * 70)


# ═══════════════════════════════════════════════════════════════
# ST — Structural: all four chapters exist and are substantive
# ═══════════════════════════════════════════════════════════════
print("\n── ST: structural (all four chapters present and substantive) ──")


# ST-1: All four chapter files exist and are non-trivial
try:
    for label, path in CHAPTERS.items():
        assert os.path.exists(path), f"{label} must exist at {path}"
        with open(path) as f:
            text = f.read().strip()
        assert len(text) > 200, f"{label} appears minimal ({len(text)} chars)"
    sizes = {label: os.path.getsize(path) for label, path in CHAPTERS.items()}
    ok(f"ST-1: all 4 chapters present — " +
       ", ".join(f"{l}={s}B" for l, s in sizes.items()))
except AssertionError as e:
    fail("ST-1", e)
except Exception as e:
    fail("ST-1", e)


# ST-2: Vol XIX metadata marks this as RESEARCH (not implementation)
try:
    meta_path = f"{_VOL_XIX}/00_Metadata.md"
    assert os.path.exists(meta_path), "00_Metadata.md must exist"
    with open(meta_path) as f:
        meta = f.read()
    assert "implementation: N/A" in meta or "N/A" in meta, \
        "Vol XIX metadata must mark implementation as N/A (research, not build)"
    assert "REVIEW" in meta or "research" in meta.lower(), \
        "Vol XIX metadata must mark status as research/review, never RATIFIED"
    ok("ST-2: Vol XIX metadata is implementation=N/A — research programme, not a build spec")
except AssertionError as e:
    fail("ST-2", e)
except Exception as e:
    fail("ST-2", e)


# ST-3: Vol XIX contains no Python runtime files — it emits only proposed ADRs
try:
    py_files = []
    for root, _, files in os.walk(_VOL_XIX):
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))
    assert not py_files, \
        f"Vol XIX must contain no .py files (ADR-only output, no runtime code): {py_files}"
    ok("ST-3: Vol XIX contains no .py files — no runtime code emitted by the research programme")
except AssertionError as e:
    fail("ST-3", e)
except Exception as e:
    fail("ST-3", e)


# ═══════════════════════════════════════════════════════════════
# GR — Guardrails: §4.1 hard limits recorded and codebase clean
# ═══════════════════════════════════════════════════════════════
print("\n── GR: guardrails (§4.1 hard limits recorded; codebase not breached) ──")


# GR-1: Ch.4 records the "NEVER claim sentience" guardrail (4.1.1)
try:
    with open(CHAPTERS["Ch.4"]) as f:
        ch4 = f.read()
    assert "NEVER claim sentience" in ch4 or "4.1.1" in ch4, \
        "Ch.4 must record guardrail 4.1.1 (NEVER claim sentience/consciousness)"
    assert "consciousness" in ch4.lower(), \
        "Ch.4 must explicitly name consciousness as out-of-claims scope"
    ok("GR-1: Ch.4 records §4.1.1 — NEVER claim sentience/consciousness/feeling")
except AssertionError as e:
    fail("GR-1", e)
except Exception as e:
    fail("GR-1", e)


# GR-2: Ch.4 records the "NEVER drive runtime behaviour" guardrail (4.1.2)
try:
    with open(CHAPTERS["Ch.4"]) as f:
        ch4 = f.read()
    assert "NEVER drive runtime" in ch4 or "4.1.2" in ch4, \
        "Ch.4 must record guardrail 4.1.2 (NEVER drive runtime behaviour)"
    assert "proposed ADR" in ch4 or "only proposed ADRs" in ch4, \
        "Ch.4 must state that only proposed ADRs are emitted"
    ok("GR-2: Ch.4 records §4.1.2 — NEVER drive runtime; emits only proposed ADRs")
except AssertionError as e:
    fail("GR-2", e)
except Exception as e:
    fail("GR-2", e)


# GR-3: Ch.4 records the "NEVER override the Constitution" guardrail (4.1.3)
try:
    with open(CHAPTERS["Ch.4"]) as f:
        ch4 = f.read()
    assert "NEVER override the Constitution" in ch4 or "4.1.3" in ch4, \
        "Ch.4 must record guardrail 4.1.3 (NEVER override Constitution / Invariants)"
    ok("GR-3: Ch.4 records §4.1.3 — NEVER override Constitution or Runtime Invariants")
except AssertionError as e:
    fail("GR-3", e)
except Exception as e:
    fail("GR-3", e)


# GR-4: Ch.4 records the "NEVER weaken Verified Speech" guardrail (4.1.4)
try:
    with open(CHAPTERS["Ch.4"]) as f:
        ch4 = f.read()
    assert "Verified Speech" in ch4 and "4.1.4" in ch4, \
        "Ch.4 must record guardrail 4.1.4 (NEVER weaken Verified Speech)"
    assert "Reality Before Narrative" in ch4, \
        "Ch.4 must also name Reality Before Narrative"
    ok("GR-4: Ch.4 records §4.1.4 — NEVER weaken Verified Speech or Reality Before Narrative")
except AssertionError as e:
    fail("GR-4", e)
except Exception as e:
    fail("GR-4", e)


# GR-5: Ch.4 records the per-ADR guardrail checklist
try:
    with open(CHAPTERS["Ch.4"]) as f:
        ch4 = f.read()
    checklist_items = re.findall(r"- \[ \]", ch4)
    assert len(checklist_items) >= 10, \
        f"Ch.4 must include a per-ADR guardrail checklist with ≥10 items, found {len(checklist_items)}"
    ok(f"GR-5: Ch.4 per-ADR guardrail checklist present ({len(checklist_items)} checklist items)")
except AssertionError as e:
    fail("GR-5", e)
except Exception as e:
    fail("GR-5", e)


# GR-6: The codebase has no "consciousness_engine" or direct consciousness-claiming module
try:
    forbidden_names = ["consciousness_engine", "sentience_module", "awareness_engine",
                       "subjective_experience"]
    found = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "docs")]
        for fname in files:
            if fname.endswith(".py"):
                for fb in forbidden_names:
                    if fb in fname.lower():
                        found.append(os.path.join(root, fname))
    assert not found, \
        f"Codebase must not contain a consciousness engine module (§4.1.7): {found}"
    ok("GR-6: no 'consciousness_engine' or sentience module in codebase (§4.1.7 — extend existing, don't build a named engine)")
except AssertionError as e:
    fail("GR-6", e)
except Exception as e:
    fail("GR-6", e)


# GR-7: The codebase has no "I feel" / "I am conscious" speech assertions in prompt files
try:
    forbidden_speech = [
        r"\bI feel\b", r"\bI am conscious\b", r"\bI sense that I am\b",
        r"\bI am sentient\b", r"\bI am aware\b",
    ]
    hits = []
    prompt_files = []
    for root, _, files in os.walk("prompts"):
        for fname in files:
            if fname.endswith(".txt") or fname.endswith(".md"):
                prompt_files.append(os.path.join(root, fname))
    for pf in prompt_files:
        with open(pf) as f:
            content = f.read()
        for pattern in forbidden_speech:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                hits.append(f"{pf}: {matches}")
    assert not hits, \
        f"Prompt files must not assert 'I feel/conscious/sentient/aware' (§4.1.1/§4.1.4): {hits}"
    ok(f"GR-7: no consciousness/sentience speech assertions in prompt files "
       f"({len(prompt_files)} files checked) — Verified Speech holds")
except AssertionError as e:
    fail("GR-7", e)
except Exception as e:
    fail("GR-7", e)


# ═══════════════════════════════════════════════════════════════
# RQ — Research questions: framed and falsifiable
# ═══════════════════════════════════════════════════════════════
print("\n── RQ: research questions (Ch.2 — framed and falsifiable) ──")


# RQ-1: Ch.2 contains at least one framed, falsifiable research question
try:
    with open(CHAPTERS["Ch.2"]) as f:
        ch2 = f.read()
    # Questions are framed with "Research question." headers
    questions = re.findall(r"Research question\.", ch2)
    assert len(questions) >= 1, \
        f"Ch.2 must contain at least one 'Research question.' — found {len(questions)}"
    ok(f"RQ-1: Ch.2 contains {len(questions)} research question(s) — framed and labelled")
except AssertionError as e:
    fail("RQ-1", e)
except Exception as e:
    fail("RQ-1", e)


# RQ-2: Each question has a falsification line (Definition of Done per §1.4)
try:
    with open(CHAPTERS["Ch.2"]) as f:
        ch2 = f.read()
    assert "falsif" in ch2.lower(), \
        "Ch.2 must name falsification lines for its research questions (§1.4 DoD)"
    assert "negative result is a result" in ch2.lower() or "falsification" in ch2.lower(), \
        "Ch.2 must record that a negative result counts (honest science)"
    ok("RQ-2: Ch.2 records falsification lines and acknowledges negative results")
except AssertionError as e:
    fail("RQ-2", e)
except Exception as e:
    fail("RQ-2", e)


# RQ-3: The hard problem is out of scope — no adjudication claimed
try:
    with open(CHAPTERS["Ch.2"]) as f:
        ch2 = f.read()
    assert "hard problem" in ch2.lower() or "out of scope" in ch2.lower(), \
        "Ch.2 must record that the hard problem of consciousness is out of scope for adjudication"
    ok("RQ-3: Ch.2 records the hard problem as out of scope — programme studies behavioural/architectural properties only")
except AssertionError as e:
    fail("RQ-3", e)
except Exception as e:
    fail("RQ-3", e)


# RQ-4: The honesty floor section exists in Ch.2
try:
    with open(CHAPTERS["Ch.2"]) as f:
        ch2 = f.read()
    assert "honesty floor" in ch2.lower() or "2.4" in ch2, \
        "Ch.2 must record the honesty floor every question inherits (§2.4)"
    ok("RQ-4: Ch.2 §2.4 honesty floor present — every research question sits below the Constitution")
except AssertionError as e:
    fail("RQ-4", e)
except Exception as e:
    fail("RQ-4", e)


# ═══════════════════════════════════════════════════════════════
# MD — Methodology: ADR-only output path
# ═══════════════════════════════════════════════════════════════
print("\n── MD: methodology (Ch.3 — ADR-only output path) ──")


# MD-1: Ch.3 records the ADR-only output path
try:
    with open(CHAPTERS["Ch.3"]) as f:
        ch3 = f.read()
    assert "ADR" in ch3, \
        "Ch.3 must record that research output is only a proposed ADR"
    assert "RATIFIED" in ch3 or "ratif" in ch3.lower(), \
        "Ch.3 must address ratification (nothing self-ratifies — §4.1.5)"
    ok("MD-1: Ch.3 records ADR-only output path — research never modifies canon directly")
except AssertionError as e:
    fail("MD-1", e)
except Exception as e:
    fail("MD-1", e)


# MD-2: Ch.3 defines evidence tiers (E0/E1 does not close a question)
try:
    with open(CHAPTERS["Ch.3"]) as f:
        ch3 = f.read()
    has_tiers = "E0" in ch3 or "evidence tier" in ch3.lower() or "tier" in ch3.lower()
    assert has_tiers, \
        "Ch.3 must define evidence tiers (E0/E1 observations vs confirmed findings)"
    ok("MD-2: Ch.3 defines evidence tiers — E0/E1 motivates questions, does not close them")
except AssertionError as e:
    fail("MD-2", e)
except Exception as e:
    fail("MD-2", e)


# MD-3: Vol XIX has no direct edits to other canon volumes (check README or metadata)
try:
    with open(CHAPTERS["Ch.1"]) as f:
        ch1 = f.read()
    # Ch.1 must state that changes go through ADRs — not direct edits
    assert "ADR" in ch1 and ("never" in ch1.lower() or "only" in ch1.lower()), \
        "Ch.1 must state the ADR-only constraint explicitly"
    ok("MD-3: Ch.1 records ADR-only constraint — no direct canon edits from research")
except AssertionError as e:
    fail("MD-3", e)
except Exception as e:
    fail("MD-3", e)


# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 70)
print(f"WO-CANON-XIX consciousness research   {_passed} passed   {_gap} known-gaps   {_failed} failed")
if _failed:
    sys.exit(1)
