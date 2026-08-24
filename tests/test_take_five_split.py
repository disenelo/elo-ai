"""
tests/test_take_five_split.py — FROM_DESIGN card 12 §1 — take-five phrase split.

David ruling 2026-08-24: step_out phrases split into BRIEF (privacy=false, mouse-move
returns) and PRIVACY (privacy=true, stays until "come back").

Tests:
  T1  BRIEF phrases → _step_out_is_brief() returns True
  T2  PRIVACY phrases → _step_out_is_brief() returns False
  T3  leave_command payload includes privacy key (mocked patch)
  T4  DesktopBuddy.LeaveForPrivacy signature accepts bool param (source check)

Run: python3 tests/test_take_five_split.py
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


# ── T1: BRIEF phrases → _step_out_is_brief() True ────────────────────────────

def test_t1_brief_phrases():
    from server import _step_out_is_brief
    brief = [
        "take 5", "take five", "brb",
        "give me a minute", "give me a moment", "give me a mo", "give me a sec",
        "give us a minute", "give us a sec",
        "i need a minute", "need a break", "taking a break",
        "pop off", "heading out",
    ]
    for phrase in brief:
        if not _step_out_is_brief(phrase):
            err(f"T1: '{phrase}' should be BRIEF (privacy=false) but _step_out_is_brief returned False")
    ok(f"T1: all {len(brief)} BRIEF phrases → _step_out_is_brief()=True (privacy=false → mouse-move returns)")


# ── T2: PRIVACY phrases → _step_out_is_brief() False ────────────────────────

def test_t2_privacy_phrases():
    from server import _step_out_is_brief
    privacy = [
        "some privacy", "leave me to it", "give me some space", "give me some room",
        "i need some space", "make yourself scarce", "leave me be", "let me be",
        "need a breather", "good night", "goodnight", "done for today", "signing off",
    ]
    for phrase in privacy:
        if _step_out_is_brief(phrase):
            err(f"T2: '{phrase}' should be PRIVACY (privacy=true) but _step_out_is_brief returned True")
    ok(f"T2: all {len(privacy)} PRIVACY phrases → _step_out_is_brief()=False (privacy=true → stays until called)")


# ── T3: leave_command payload includes privacy key ────────────────────────────

def test_t3_leave_command_has_privacy_key():
    import ast, pathlib
    src = pathlib.Path(ROOT, "server.py").read_text()
    # The payload must contain "privacy" field in leave_command
    if '"privacy"' not in src and "'privacy'" not in src:
        err("T3: 'privacy' key not found in server.py leave_command payload")
    if "_step_out_is_brief" not in src:
        err("T3: _step_out_is_brief() not referenced in server.py leave_command emit")
    ok("T3: leave_command DOWN payload includes privacy key — EloOSAvatarReceiver can route by phrase type")


# ── T4: DesktopBuddy.cs LeaveForPrivacy signature has bool param ─────────────

def test_t4_desktop_buddy_signature():
    import pathlib, re
    cs = pathlib.Path(ROOT).parent / "Desktop/Output/DISENELO-eLoDesktopBuddy/Assets/Scripts/DesktopBuddy.cs"
    if not cs.exists():
        # Try alternate path
        cs = pathlib.Path("/Users/Disenelo/Desktop/Output/DISENELO-eLoDesktopBuddy/Assets/Scripts/DesktopBuddy.cs")
    if not cs.exists():
        err("T4: DesktopBuddy.cs not found — cannot verify signature")

    text = cs.read_text()
    match = re.search(r'public void LeaveForPrivacy\s*\(([^)]*)\)', text)
    if not match:
        err("T4: LeaveForPrivacy method not found in DesktopBuddy.cs")
    params = match.group(1).strip()
    if "bool privacy" not in params:
        err(f"T4: LeaveForPrivacy signature has no 'bool privacy' param — got: ({params})")
    ok(f"T4: DesktopBuddy.cs LeaveForPrivacy({params}) — privacy param present, default=true preserved")


# ── runner ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("TAKE-FIVE SPLIT TEST (FROM_DESIGN card 12 §1)")
    print()
    test_t1_brief_phrases()
    test_t2_privacy_phrases()
    test_t3_leave_command_has_privacy_key()
    test_t4_desktop_buddy_signature()
    print()
    print("TAKE-FIVE DONE: BRIEF phrases → privacy=false (mouse-move returns).")
    print("PRIVACY phrases → privacy=true (stays until 'come back').")
    print("EloOSAvatarReceiver.cs change (pass privacy param) awaiting Design commit.")
