"""
tests/test_wo048_company_real.py — WO-048: "How's the company" made real (folds WO-061)

Spec: company phrasings → company path (never mock/LLM) + real DISENELO data +
focus not backlog + links + recommendation + varied + honest fallback.

  AT-1:  12+ company/board phrasings ALL classify to company path
  AT-2:  3 non-company controls do NOT misroute
  AT-3:  briefing reply contains real DISENELO tokens (not hallucinated "Company for Doing")
  AT-4:  briefing reply VARIES when state changes (not a fixed string)
  AT-5:  with COMPANY_FOCUS set, briefing surfaces milestone (focus not backlog)
  AT-6:  briefing reply includes a board link/path
  AT-7:  briefing reply includes a recommendation line
  AT-8:  company.approvals intent → routes correctly, names real waiting items
  AT-9:  WO-048 marker present in company_state_writer.py
  AT-10: _parse_company_focus searches full board (not just first 10 000 chars)
  AT-11: py_compile clean on company_state_writer.py
  AT-12: _strip_md helper strips markdown bold markers from titles

Run: python3 tests/test_wo048_company_real.py
"""
import sys, os, json, py_compile, copy, re, time
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: 12+ phrasings classify to company path ────────────────────────────
try:
    from company_runtime.company_state_writer import is_company_intent as _ici

    _BRIEFING_PHRASES = [
        "how's the company", "how is the company", "company status",
        "how are things", "what should I work on", "what is the focus",
        "give me an update", "what is DISENELO doing", "what are the priorities",
        "how is the build going", "any updates", "what is the plan",
        "what is the milestone", "tell me about the company",
    ]
    _BOARD_PHRASES = [
        "what's on the board", "what are we working on", "what's the board",
        "board update", "what's in progress",
    ]
    _ALL = _BRIEFING_PHRASES + _BOARD_PHRASES

    _misses = [p for p in _ALL if not _ici(p)]
    assert not _misses, f"missed: {_misses}"
    assert len(_ALL) >= 12, f"need at least 12 test phrases, got {len(_ALL)}"
    ok(f"AT-1: {len(_ALL)} phrasings all classify to company path (0 misses)")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: non-company controls do NOT misroute ────────────────────────────────
try:
    _CONTROLS = [
        "how are you",
        "play some music",
        "what time is it",
        "can you sit with me",
        "take five",
        "what's the weather",
    ]
    _false_pos = [p for p in _CONTROLS if _ici(p)]
    assert not _false_pos, f"false positives: {_false_pos}"
    ok(f"AT-2: {len(_CONTROLS)} non-company controls — no false positives")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: briefing contains real DISENELO tokens (not hallucinated) ───────────
try:
    from company_runtime.company_state_writer import handle_company_voice_intent as _hcvi
    _reply = _hcvi("how's the company")
    # Must NOT contain the hallucinated company name from the mock backend
    assert "Company for Doing" not in _reply, "hallucinated company name present"
    # Must contain DISENELO identity
    assert "DISENELO" in _reply, "DISENELO not in briefing reply"
    # Must contain real project token
    assert any(tok in _reply for tok in ("eLo", "robot", "game", "book", "Kickstarter")), \
        "no real project token in reply"
    ok(f"AT-3: briefing contains real DISENELO tokens — not hallucinated")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: briefing VARIES when state changes ─────────────────────────────────
try:
    _STATE_PATH = os.path.join("blender", "company_state.json")

    # Load real state
    with open(_STATE_PATH, encoding="utf-8") as _f:
        _real_state = json.load(_f)

    from company_runtime.company_state_writer import _build_briefing
    _original = _build_briefing(_real_state)

    # Mutate state: change the voiced_briefing and engineering count
    _mutated = copy.deepcopy(_real_state)
    _mutated["engineering"]["open"] = 999
    _mutated["company_focus"] = {"milestone": "MUTATED_MILESTONE_XYZ", "items": [], "note": ""}
    _mutated_reply = _build_briefing(_mutated)

    assert _original != _mutated_reply, "reply did not change when state changed"
    assert "MUTATED_MILESTONE_XYZ" in _mutated_reply, "mutated milestone not in reply"
    ok("AT-4: briefing VARIES with state changes (not a fixed string)")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: focus not backlog — milestone surfaced when COMPANY_FOCUS present ───
try:
    from company_runtime.company_state_writer import _build_briefing, _parse_company_focus

    # Build a synthetic state with a clear COMPANY_FOCUS
    _focused_state = {
        "company_focus": {"milestone": "Presentable v1", "items": ["WO-032", "WO-045"], "note": ""},
        "today_priorities": [{"text": "Focused item 1", "owner": "Builder", "priority": "P0"}],
        "waiting_for_approval": [],
        "board": [],
        "engineering": {"open": 5, "in_review": 2},
        "roadmap": [],
    }
    _focused_reply = _build_briefing(_focused_state)
    assert "Presentable v1" in _focused_reply, "milestone not in focused reply"
    # Must NOT contain raw backlog keywords that appeared in the old voiced_briefing
    assert "items ready to pick up" not in _focused_reply, "raw backlog line leaked into reply"
    ok("AT-5: focus milestone surfaced; raw backlog not present")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── AT-6: briefing includes a board link/path ─────────────────────────────────
try:
    _reply = _hcvi("company status")
    assert "DISPATCH_BOARD" in _reply or "board" in _reply.lower(), \
        "no board link in briefing reply"
    ok("AT-6: briefing includes board link/path")
except AssertionError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)


# ── AT-7: briefing includes a recommendation line ─────────────────────────────
try:
    from company_runtime.company_state_writer import _recommend
    # Build a state with one WORKING P1 WO and a company_focus referencing it
    _rec_state = {
        "company_focus": {"milestone": "Presentable v1", "items": ["WO-099"], "note": ""},
        "board": [
            {"id": "WO-099", "title": "Test work order", "status": "WORKING",
             "pri": "P1", "seat": "Builder (eLo OS)"},
        ],
        "today_priorities": [],
        "waiting_for_approval": [],
        "engineering": {"open": 1, "in_review": 0},
    }
    _rec = _recommend(_rec_state)
    assert "WO-099" in _rec, f"expected WO-099 in recommendation, got {_rec!r}"

    # Full briefing also contains a recommendation phrase
    _reply = _hcvi("how's the company")
    assert any(tok in _reply.lower() for tok in ("next", "pick up", "recommendation", "best")), \
        "no recommendation phrase in briefing"
    ok(f"AT-7: recommendation present — _recommend returns WO ID + briefing has 'next'/'pick up'")
except AssertionError as e:
    fail("AT-7", e)
except Exception as e:
    fail("AT-7", e)


# ── AT-8: company.approvals → real waiting items ──────────────────────────────
try:
    _appr = _hcvi("what needs approval")
    # Should be either "Nothing waiting" or mention waiting items
    assert "waiting" in _appr.lower() or "nothing" in _appr.lower(), \
        f"unexpected approvals reply: {_appr!r}"
    ok(f"AT-8: company.approvals routes correctly — {_appr[:60]!r}")
except AssertionError as e:
    fail("AT-8", e)
except Exception as e:
    fail("AT-8", e)


# ── AT-9: WO-048 marker present in company_state_writer.py ───────────────────
try:
    with open("company_runtime/company_state_writer.py", encoding="utf-8") as _f:
        _src = _f.read()
    assert "WO-048" in _src, "WO-048 marker not found"
    assert "_build_briefing" in _src, "_build_briefing helper not found"
    assert "_strip_md" in _src, "_strip_md helper not found"
    ok("AT-9: WO-048 markers present — _build_briefing + _strip_md in file")
except AssertionError as e:
    fail("AT-9", e)


# ── AT-10: _parse_company_focus searches full board, not just :10000 ──────────
try:
    from company_runtime.company_state_writer import _parse_company_focus

    # Create a synthetic board where the COMPANY_FOCUS is beyond char 10000
    _padding = "x" * 30000
    _synthetic_board = (
        _padding +
        "\n<!-- COMPANY_FOCUS: Full-Board-Test | items: WO-ZZZ | note: verifying full scan -->\n"
    )
    _focus = _parse_company_focus(_synthetic_board)
    assert _focus is not None, "_parse_company_focus returned None (marker missed — still slicing to 10000?)"
    assert _focus.get("milestone") == "Full-Board-Test", f"wrong milestone: {_focus}"
    ok("AT-10: _parse_company_focus scans full board — finds marker at char 30000+")
except AssertionError as e:
    fail("AT-10", e)
except Exception as e:
    fail("AT-10", e)


# ── AT-11: py_compile clean ───────────────────────────────────────────────────
try:
    py_compile.compile("company_runtime/company_state_writer.py", doraise=True)
    ok("AT-11: py_compile clean on company_state_writer.py")
except py_compile.PyCompileError as e:
    fail("AT-11", e)


# ── AT-12: _strip_md strips markdown bold markers ─────────────────────────────
try:
    from company_runtime.company_state_writer import _strip_md
    assert _strip_md("**Bold title**") == "Bold title", f"bold not stripped: {_strip_md('**Bold title**')!r}"
    assert _strip_md("↩ **REOPENED — some fix**") == "REOPENED — some fix", \
        f"arrow not stripped: {_strip_md('↩ **REOPENED — some fix**')!r}"
    assert _strip_md("Normal title") == "Normal title", "clean title modified"
    ok("AT-12: _strip_md strips bold markers and leading symbols")
except AssertionError as e:
    fail("AT-12", e)
except Exception as e:
    fail("AT-12", e)


print()
print("=" * 55)
print(f"WO-048 company real  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
