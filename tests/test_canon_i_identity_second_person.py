"""
tests/test_canon_i_identity_second_person.py — WO-CANON-I identity / second-person address.

AT-CI-1a: living_presence_spec.txt names David
AT-CI-1b: _PERSONA fallback names David
AT-CI-2a: spec contains WHO YOU ARE WITH section
AT-CI-2b: _PERSONA contains WHO YOU ARE WITH section
AT-CI-3:  DIVERGENCE GUARD — spec and _PERSONA agree; fails if they drift apart
AT-CI-4a: ADDRESS RULE in spec says not to use David's name back at him
AT-CI-4b: ADDRESS RULE in _PERSONA says not to use David's name back at him
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

_SPEC_PATH   = os.path.join(ROOT, "prompts", "living_presence_spec.txt")
_BUILDER_PATH = os.path.join(ROOT, "runtime", "prompt_builder.py")

_ADDRESS_ANCHOR = "WHO YOU ARE WITH"
_DAVID_ANCHOR   = "The person you are with is David"
_NO_NAME_RULE   = "You do not say it back to him"


def _spec() -> str:
    with open(_SPEC_PATH, encoding="utf-8") as f:
        return f.read()


def _persona() -> str:
    with open(_BUILDER_PATH, encoding="utf-8") as f:
        src = f.read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "_PERSONA":
                    if isinstance(node.value, ast.Constant):
                        return node.value.value
    raise AssertionError("_PERSONA constant not found in runtime/prompt_builder.py")


# ── AT-CI-1: Both personas name David ────────────────────────────────────────

def test_spec_names_david():
    s = _spec()
    assert "help David think" in s or _DAVID_ANCHOR in s, \
        "living_presence_spec.txt must name David in purpose or identity block"


def test_persona_names_david():
    p = _persona()
    assert "help David think" in p or _DAVID_ANCHOR in p, \
        "_PERSONA must name David in purpose or identity block"


# ── AT-CI-2: Both contain ADDRESS RULE ───────────────────────────────────────

def test_spec_has_address_rule():
    s = _spec()
    assert _ADDRESS_ANCHOR in s, \
        f"living_presence_spec.txt must contain '# {_ADDRESS_ANCHOR}' section"
    assert _DAVID_ANCHOR in s, \
        f"living_presence_spec.txt must contain '{_DAVID_ANCHOR}'"


def test_persona_has_address_rule():
    p = _persona()
    assert _ADDRESS_ANCHOR in p, \
        f"_PERSONA must contain '# {_ADDRESS_ANCHOR}' section"
    assert _DAVID_ANCHOR in p, \
        f"_PERSONA must contain '{_DAVID_ANCHOR}'"


# ── AT-CI-3: DIVERGENCE GUARD ─────────────────────────────────────────────────

def test_personas_agree_on_address_rule():
    """
    FREEZE ALARM: fails when spec and _PERSONA diverge on the ADDRESS RULE.
    Edit both in the same commit — never one without the other.
    """
    s = _spec()
    p = _persona()
    spec_ok    = _ADDRESS_ANCHOR in s and _DAVID_ANCHOR in s and _NO_NAME_RULE in s
    persona_ok = _ADDRESS_ANCHOR in p and _DAVID_ANCHOR in p and _NO_NAME_RULE in p
    assert spec_ok == persona_ok, (
        "DIVERGENCE: living_presence_spec.txt and _PERSONA disagree on the ADDRESS RULE. "
        f"spec={'present' if spec_ok else 'MISSING'}, "
        f"_PERSONA={'present' if persona_ok else 'MISSING'}. "
        "Both files must be updated together."
    )


# ── AT-CI-4: ADDRESS RULE says speak TO David, not ABOUT him ─────────────────

def test_address_rule_content_in_spec():
    s = _spec()
    assert _NO_NAME_RULE in s, \
        "ADDRESS RULE in spec must instruct eLo not to say David's name back at him"


def test_address_rule_content_in_persona():
    p = _persona()
    assert _NO_NAME_RULE in p, \
        "ADDRESS RULE in _PERSONA must instruct eLo not to say David's name back at him"


# ── Self-runner ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _tests = [
        ("AT-CI-1a", test_spec_names_david),
        ("AT-CI-1b", test_persona_names_david),
        ("AT-CI-2a", test_spec_has_address_rule),
        ("AT-CI-2b", test_persona_has_address_rule),
        ("AT-CI-3",  test_personas_agree_on_address_rule),
        ("AT-CI-4a", test_address_rule_content_in_spec),
        ("AT-CI-4b", test_address_rule_content_in_persona),
    ]
    _passed = 0
    _failed = 0
    for label, fn in _tests:
        try:
            fn()
            print(f"  ✅ {label}: {fn.__name__}")
            _passed += 1
        except Exception as _e:
            print(f"  ❌ {label}: {fn.__name__} — {_e}")
            _failed += 1
    print()
    print("=" * 62)
    print(f"WO-CANON-I identity/address   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
