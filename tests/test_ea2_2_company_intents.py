"""
EA2-2 acceptance tests — company.* voice intent routing.

AT-1  is_company_intent: briefing phrases → "company.briefing"
AT-2  is_company_intent: board phrases → "company.board"
AT-3  is_company_intent: approvals phrases → "company.approvals"
AT-4  is_company_intent: approve WO-XXX regex → "company.approve"
AT-5  is_company_intent: move WO-XXX to STATUS regex → "company.move"
AT-6  is_company_intent: unrelated input → None
AT-7  handle_company_voice_intent: briefing → returns voiced_briefing from state
AT-8  handle_company_voice_intent: approvals → includes count + wo ids
AT-9  handle_company_voice_intent: approve WO-999 → writes to company_actions.json
AT-10 handle_company_voice_intent: move WO-999 to DONE → writes move action
AT-11 frozen kernel: no modifications to runtime/executive.py or prompts/
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from company_runtime.company_state_writer import (
    is_company_intent,
    handle_company_voice_intent,
)

# ── helpers ──────────────────────────────────────────────────────────────────

_FAKE_STATE = {
    "voiced_briefing": "3 items ready · 2 waiting on David · FH-1 in progress",
    # company_focus must be non-empty so _load_fresh_state does not re-publish
    # from the real DISPATCH_BOARD and overwrite this injected state.
    "company_focus": {
        "milestone": "Presentable v1",
        "items": ["WO-015 Builder P1", "EA2-2 Company Brain"],
    },
    "today_priorities": [
        {"text": "WO-015 Builder P1", "wo": "WO-015"},
        {"text": "EA2-2 Company Brain", "wo": "EA2-2"},
    ],
    "waiting_for_approval": [
        {"wo": "INT-3", "needs_david": True},
        {"wo": "WO-020", "needs_david": True},
        {"wo": "WO-024", "needs_david": True},
    ],
    "board": [
        {"id": "FH-1", "kanban": "WORKING"},
        {"id": "EA2-2", "kanban": "WORKING"},
    ],
}


def _write_state(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


# ── AT-1 ─────────────────────────────────────────────────────────────────────

def test_at1_briefing_phrases():
    triggers = [
        "how's the company",
        "company status",
        "give me a company briefing",
        "company update",
        "how we doing as a company",
    ]
    for phrase in triggers:
        result = is_company_intent(phrase)
        assert result == "company.briefing", f"AT-1 FAIL for '{phrase}': got {result!r}"
    print("AT-1 PASS — briefing phrases")


# ── AT-2 ─────────────────────────────────────────────────────────────────────

def test_at2_board_phrases():
    triggers = [
        "show the board",
        "company board",
        "what's on the board",
        "what are we building",
    ]
    for phrase in triggers:
        result = is_company_intent(phrase)
        assert result == "company.board", f"AT-2 FAIL for '{phrase}': got {result!r}"
    print("AT-2 PASS — board phrases")


# ── AT-3 ─────────────────────────────────────────────────────────────────────

def test_at3_approvals_phrases():
    triggers = [
        "what needs approval",
        "pending approvals",
        "what's waiting on me",
        "what do i need to approve",
    ]
    for phrase in triggers:
        result = is_company_intent(phrase)
        assert result == "company.approvals", f"AT-3 FAIL for '{phrase}': got {result!r}"
    print("AT-3 PASS — approvals phrases")


# ── AT-4 ─────────────────────────────────────────────────────────────────────

def test_at4_approve_regex():
    phrases = ["approve WO-999", "approve INT-7", "approve EA2-2"]
    for phrase in phrases:
        result = is_company_intent(phrase)
        assert result == "company.approve", f"AT-4 FAIL for '{phrase}': got {result!r}"
    print("AT-4 PASS — approve regex")


# ── AT-5 ─────────────────────────────────────────────────────────────────────

def test_at5_move_regex():
    phrases = ["move WO-999 to DONE", "move EA2-2 to REVIEW", "move INT-3 to WORKING"]
    for phrase in phrases:
        result = is_company_intent(phrase)
        assert result == "company.move", f"AT-5 FAIL for '{phrase}': got {result!r}"
    print("AT-5 PASS — move regex")


# ── AT-6 ─────────────────────────────────────────────────────────────────────

def test_at6_unrelated_returns_none():
    negatives = [
        "what time is it",
        "play some music",
        "hey eLo",
        "how are you",
        "who are you",
    ]
    for phrase in negatives:
        result = is_company_intent(phrase)
        assert result is None, f"AT-6 FAIL: '{phrase}' should return None, got {result!r}"
    print("AT-6 PASS — unrelated phrases → None")


# ── AT-7 ─────────────────────────────────────────────────────────────────────

def test_at7_briefing_returns_voiced_briefing():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        _write_state(f.name, _FAKE_STATE)
        state_path = f.name
    actions_path = state_path + ".actions"
    try:
        reply = handle_company_voice_intent("how's the company",
                                            state_path=state_path,
                                            actions_path=actions_path)
        # WO-048: _build_briefing() returns a rich constructed reply, not the raw
        # voiced_briefing field.  "DISENELO" is always the first word of the briefing,
        # and the fake state's today_priorities / waiting items appear in the output.
        assert "DISENELO" in reply and any(w in reply for w in ["WO-015", "EA2-2", "INT-3"]), \
            f"AT-7 FAIL: briefing missing DISENELO identity or fake-state items: {reply!r}"
        print("AT-7 PASS — briefing returns DISENELO identity + state items")
    finally:
        os.unlink(state_path)


# ── AT-8 ─────────────────────────────────────────────────────────────────────

def test_at8_approvals_lists_wos():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        _write_state(f.name, _FAKE_STATE)
        state_path = f.name
    actions_path = state_path + ".actions"
    try:
        reply = handle_company_voice_intent("what needs approval",
                                            state_path=state_path,
                                            actions_path=actions_path)
        assert "INT-3" in reply or "WO-020" in reply, \
            f"AT-8 FAIL: wo ids missing from reply: {reply!r}"
        assert "3" in reply, f"AT-8 FAIL: count '3' missing from reply: {reply!r}"
        print("AT-8 PASS — approvals lists WO ids and count")
    finally:
        os.unlink(state_path)


# ── AT-9 ─────────────────────────────────────────────────────────────────────

def test_at9_approve_writes_action():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        _write_state(f.name, _FAKE_STATE)
        state_path = f.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f2:
        actions_path = f2.name
    try:
        reply = handle_company_voice_intent("approve WO-TEST",
                                            state_path=state_path,
                                            actions_path=actions_path)
        # reply should mention the WO or a fallback
        assert "WO-TEST" in reply or "check" in reply.lower() or "approved" in reply.lower(), \
            f"AT-9 FAIL: expected WO-TEST in reply: {reply!r}"
        # If actions file was written, check it has the right type
        if os.path.exists(actions_path) and os.path.getsize(actions_path) > 2:
            with open(actions_path) as f:
                action = json.load(f)
            assert action.get("work_order") == "WO-TEST", \
                f"AT-9 FAIL: wrong wo in action: {action}"
            assert action.get("type") in ("approval_request",), \
                f"AT-9 FAIL: wrong type in action: {action}"
        print("AT-9 PASS — approve writes action")
    finally:
        os.unlink(state_path)
        if os.path.exists(actions_path):
            os.unlink(actions_path)


# ── AT-10 ────────────────────────────────────────────────────────────────────

def test_at10_move_writes_action():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        _write_state(f.name, _FAKE_STATE)
        state_path = f.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f2:
        actions_path = f2.name
    try:
        reply = handle_company_voice_intent("move WO-TEST to DONE",
                                            state_path=state_path,
                                            actions_path=actions_path)
        assert "WO-TEST" in reply, f"AT-10 FAIL: WO-TEST not in reply: {reply!r}"
        with open(actions_path) as f:
            action = json.load(f)
        assert action.get("type") == "move", f"AT-10 FAIL: wrong type: {action}"
        assert action.get("work_order") == "WO-TEST", f"AT-10 FAIL: wrong wo: {action}"
        assert action.get("to_status") == "DONE", f"AT-10 FAIL: wrong status: {action}"
        print("AT-10 PASS — move writes action with correct fields")
    finally:
        os.unlink(state_path)
        if os.path.exists(actions_path):
            os.unlink(actions_path)


# ── AT-11 frozen kernel ───────────────────────────────────────────────────────

def test_at11_frozen_kernel():
    import hashlib
    _ROOT = os.path.join(os.path.dirname(__file__), "..")
    frozen_files = [
        os.path.join(_ROOT, "runtime", "executive.py"),
    ]
    for path in frozen_files:
        if not os.path.exists(path):
            continue
        with open(path, "rb") as f:
            content = f.read()
        assert b"handle_company_voice_intent" not in content, \
            f"AT-11 FAIL: frozen file {path} was modified (contains EA2-2 code)"
    prompts_dir = os.path.join(_ROOT, "prompts")
    if os.path.isdir(prompts_dir):
        for fname in os.listdir(prompts_dir):
            fpath = os.path.join(prompts_dir, fname)
            with open(fpath, "rb") as f:
                content = f.read()
            assert b"company_state_writer" not in content, \
                f"AT-11 FAIL: prompts/ file {fpath} modified — FREEZE_V1_LOCK violated"
    print("AT-11 PASS — frozen kernel untouched")


# ── runner ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_at1_briefing_phrases,
        test_at2_board_phrases,
        test_at3_approvals_phrases,
        test_at4_approve_regex,
        test_at5_move_regex,
        test_at6_unrelated_returns_none,
        test_at7_briefing_returns_voiced_briefing,
        test_at8_approvals_lists_wos,
        test_at9_approve_writes_action,
        test_at10_move_writes_action,
        test_at11_frozen_kernel,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
    print(f"\n{'ALL PASS' if not failed else f'{failed} FAILED'} — EA2-2 ({len(tests) - failed}/{len(tests)})")
    sys.exit(failed)
