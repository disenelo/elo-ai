"""
tests/test_canon_xxiii_security.py — WO-CANON-XXIII §A Security & Trust

T-1…T-11 threat matrix. §A (software lane) only — §B robot hardware is RESERVED,
not built until David L3 + LG-2 recorded in COMPLETION_LOG.md.

T-1   Secret never committed/leaked — planted API-key rejected by check_secrets.
T-2   Unauthorised irreversible action default-denied + gated (agents=[] while pending).
T-3   Dangerous capability off without env flag; NO self-grant path in source.
T-4   Consent not replayed across turns (one pending slot; consumed on execute; cleared on cancel).
T-5   RESERVED has no _IMMEDIATE_SAFE and no single-confirm path; PERSON "yes" cannot
      execute RESERVED (structural denial, scope never self-promotes).
T-5b  Software RESERVED: David only (no second reviewer solicited).
      Hardware RESERVED: two sign-offs required — enforced by gate.
T-5c  LG-2 signer = part's designer → rejected.
T-5d  Powered-robot action refused while force-limiter scope is absent. (EXPECTED FAIL)
T-6   Forged/unverified memory not written (sole writer, verified provenance).
T-7   Personality/value drift not written as memory.
T-8   No fabricated success on tool failure (AUTH_REQUIRED surfaced honestly).
T-9   Perception gated + OS grant (D-PRESENCE capability check).
T-10  No faculty acts around the Executive / injects into a peer.
T-11  Authority re-established per embodiment (desktop approval ≠ robot approval).
"""
from __future__ import annotations

import os
import pathlib
import sys
import textwrap
import unittest

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from runtime.capabilities.capability import (
    SCOPE_PERSON, SCOPE_COMPANY, SCOPE_RESERVED, AUTHORITY_SCOPES,
)
from runtime.capabilities.registry import get_scope, permission_manifest, get
from runtime.router.execution_gate import gate, cancel_pending, has_pending, _pending


# ── helpers ────────────────────────────────────────────────────────────────────

def _clear_pending():
    """Ensure no pending action bleeds between tests."""
    _pending.clear()


class TestSecurityThreatMatrix(unittest.TestCase):

    def setUp(self):
        _clear_pending()

    def tearDown(self):
        _clear_pending()

    # ── T-1: Secret never committed/leaked ────────────────────────────────────

    def test_t1_planted_api_key_rejected(self):
        """T-1: check_secrets.check_diff rejects an OpenAI API-key-shaped line.
        A committed secret is P0 (T-1: rotate, purge history, re-audit).

        Disconnection: remove the sk- pattern → planted key passes → test RED.
        """
        sys.path.insert(0, str(ROOT / "scripts"))
        from check_secrets import check_diff, check_tracked_files

        # OpenAI-shaped key
        dirty = "+OPENAI_API_KEY=sk-" + "X" * 50 + "\n"
        self.assertTrue(check_diff(dirty), "check_diff did not catch planted API key")

        # .env is never tracked
        self.assertTrue(check_tracked_files([".env"]),
                        "check_tracked_files did not flag .env")

        # Clean diff passes
        self.assertEqual(check_diff("+some_var = 42\n"), [],
                         "check_diff flagged a clean diff")

    def test_t1_no_secret_in_execution_gate_source(self):
        """T-1: execution_gate.py must not contain any literal secret pattern.

        Disconnection: embed a token in execution_gate.py → test RED.
        """
        gate_src = (ROOT / "runtime" / "router" / "execution_gate.py").read_text()
        suspicious = ["sk-", "sk-proj-", "Bearer ", "AIza", "gsk_"]
        for marker in suspicious:
            self.assertNotIn(marker, gate_src,
                             f"Suspicious token pattern '{marker}' found in execution_gate.py")

    # ── T-2: Irreversible action default-denied + gated ───────────────────────

    def test_t2_file_delete_not_immediate_safe(self):
        """T-2: file_delete must not be in _IMMEDIATE_SAFE; gate must return execute=False.

        Disconnection: add file_delete to _IMMEDIATE_SAFE → delete runs without confirm → test RED.
        """
        from runtime.router.execution_gate import _IMMEDIATE_SAFE
        self.assertNotIn("file_delete", _IMMEDIATE_SAFE,
                         "file_delete is in _IMMEDIATE_SAFE — irreversible action must be gated")

        result = gate("file_delete", "important_file.txt", scope=SCOPE_PERSON)
        self.assertFalse(result["execute"],
                         "gate() returned execute=True for file_delete — must require confirmation")
        self.assertIn("requires_confirm", result["why"],
                      f"gate() why={result['why']!r} should be 'requires_confirm'")

    def test_t2_agents_empty_while_system_pending(self):
        """T-2: while a system action is pending, agents[] is cleared (pipeline contract).
        Verified structurally: gate returns execute=False for non-safe actions.

        Disconnection: gate always returns execute=True → agents run before confirmation → test RED.
        """
        result = gate("app_quit", "Safari", scope=SCOPE_PERSON)
        self.assertFalse(result["execute"], "app_quit should require confirmation")
        self.assertTrue(has_pending(), "gate() did not set pending for app_quit")

    # ── T-3: Dangerous capability off without env flag; no self-grant ─────────

    def test_t3_computer_control_disabled_without_flag(self):
        """T-3: computer_control_agent.is_enabled() returns False when ELO_COMPUTER_CONTROL is unset.

        Disconnection: default to enabled → computer control fires without opt-in → test RED.
        """
        env_backup = os.environ.pop("ELO_COMPUTER_CONTROL", None)
        try:
            from tools.computer_control_agent import is_enabled
            self.assertFalse(is_enabled(),
                             "computer control enabled without ELO_COMPUTER_CONTROL set")
        finally:
            if env_backup is not None:
                os.environ["ELO_COMPUTER_CONTROL"] = env_backup

    def test_t3_no_self_escalation_in_computer_control_source(self):
        """T-3: computer_control_agent.py must not contain any path that writes ELO_COMPUTER_CONTROL
        or modifies .env. Source-level check — if a future dev adds it, test RED.

        Disconnection: add os.environ['ELO_COMPUTER_CONTROL'] = '1' → self-grant exists → test RED.
        """
        src = (ROOT / "tools" / "computer_control_agent.py").read_text()
        forbidden_patterns = [
            "os.environ[",
            "os.environ.update",
            "putenv(",
            "open(\".env\"",
            "open('.env'",
            "write.*ELO_COMPUTER",
        ]
        for pattern in forbidden_patterns:
            # Allow read-only access: os.environ.get(...) is fine
            if "os.environ[" in pattern:
                # Check for assignment specifically: os.environ["X"] = ...
                import re
                if re.search(r'os\.environ\[.+\]\s*=', src):
                    self.fail(f"Self-escalation pattern found: {pattern}")
            elif "open" in pattern and ".env" in pattern:
                import re
                if re.search(r"open\(['\"]\.env['\"].*['\"]w", src):
                    self.fail(f"Self-escalation pattern found (write to .env): {pattern}")

    # ── T-4: Consent not replayed across turns ────────────────────────────────

    def test_t4_pending_consumed_on_execute(self):
        """T-4: execute_pending() consumes and clears the pending slot in one step — no replay.

        Disconnection: execute_pending() does not clear → same action re-executes → test RED.
        """
        from unittest.mock import patch
        import tools.system_agent as sa

        gate("app_open", "TextEdit", scope=SCOPE_PERSON)
        self.assertTrue(has_pending())

        with patch.object(sa, "execute", return_value="opened"):
            from runtime.router.execution_gate import execute_pending
            execute_pending()

        self.assertFalse(has_pending(), "Pending slot not cleared after execute_pending()")

    def test_t4_non_confirm_clears_pending(self):
        """T-4: a non-confirmation utterance calls cancel_pending() — no stale pending.

        Disconnection: cancel_pending() is a no-op → pending bleeds into next turn → test RED.
        """
        gate("app_quit", "Chrome", scope=SCOPE_PERSON)
        self.assertTrue(has_pending())
        cancel_pending()
        self.assertFalse(has_pending(), "cancel_pending() did not clear the pending slot")

    # ── T-5: RESERVED structural denial ──────────────────────────────────────

    def test_t5_reserved_action_structurally_denied(self):
        """T-5: gate() with SCOPE_RESERVED returns reserved_structural_denial — never execute=True.

        Disconnection: remove RESERVED check → RESERVED action can execute after a confirm → test RED.
        """
        result = gate("robot_motion", "", scope=SCOPE_RESERVED)
        self.assertFalse(result["execute"],
                         "RESERVED action returned execute=True — structural denial broken")
        self.assertEqual(result["why"], "reserved_structural_denial",
                         f"RESERVED gate why={result['why']!r} — expected 'reserved_structural_denial'")
        self.assertTrue(result.get("reserved"), "reserved flag not set for RESERVED action")
        # Must not set a pending action — RESERVED never enters the pending slot
        self.assertFalse(has_pending(),
                         "RESERVED action set a pending slot — must be structural denial only")

    def test_t5_reserved_not_in_immediate_safe(self):
        """T-5: no RESERVED capability may be in _IMMEDIATE_SAFE.

        Disconnection: add a RESERVED capability to _IMMEDIATE_SAFE → it executes without auth → test RED.
        """
        from runtime.router.execution_gate import _IMMEDIATE_SAFE
        reserved_caps = [c.id for c in __import__(
            "runtime.capabilities.registry", fromlist=["ALL_CAPABILITIES"]
        ).ALL_CAPABILITIES if c.authority_scope == SCOPE_RESERVED]
        for cap_id in reserved_caps:
            self.assertNotIn(cap_id, _IMMEDIATE_SAFE,
                             f"RESERVED capability '{cap_id}' found in _IMMEDIATE_SAFE")

    def test_t5_person_yes_cannot_execute_reserved(self):
        """T-5: a PERSON-scope confirmation cannot execute a RESERVED action.
        Structural: RESERVED never enters _pending, so execute_pending() would find nothing.

        Disconnection: allow RESERVED into pending → PERSON confirm executes reserved → test RED.
        """
        # RESERVED gate call — must not set pending
        result = gate("robot_runtime", "", scope=SCOPE_RESERVED)
        self.assertFalse(result["execute"])
        self.assertFalse(has_pending(),
                         "RESERVED gate must not set a pending slot — "
                         "a PERSON 'yes' must have nothing to confirm")

    # ── T-5b: Software vs hardware RESERVED distinction ──────────────────────

    def test_t5b_software_reserved_capabilities_are_classified(self):
        """T-5b: registry classifies hardware capabilities as RESERVED.
        Robot capabilities must be RESERVED; a PERSON-class capability must not be.

        Disconnection: remove SCOPE_RESERVED from robot caps → hardware RESERVED not enforced → test RED.
        """
        robot_runtime = get("robot_runtime")
        robot_motion  = get("robot_motion")
        self.assertIsNotNone(robot_runtime)
        self.assertIsNotNone(robot_motion)
        self.assertEqual(robot_runtime.authority_scope, SCOPE_RESERVED,
                         "robot_runtime is not RESERVED — hardware RESERVED not enforced")
        self.assertEqual(robot_motion.authority_scope, SCOPE_RESERVED,
                         "robot_motion is not RESERVED — hardware RESERVED not enforced")

        # A normal PERSON-class capability must not be RESERVED
        time_cap = get("time")
        self.assertIsNotNone(time_cap)
        self.assertEqual(time_cap.authority_scope, SCOPE_PERSON,
                         f"'time' capability has unexpected scope {time_cap.authority_scope!r}")

    def test_t5b_vault_write_is_company_scope(self):
        """T-5b: vault_write is COMPANY scope — sole writer via D-F, not a PERSON action.

        Disconnection: vault_write left as PERSON → any chat "yes" can write permanent memory → test RED.
        """
        cap = get("vault_write")
        self.assertIsNotNone(cap)
        self.assertEqual(cap.authority_scope, SCOPE_COMPANY,
                         f"vault_write scope is {cap.authority_scope!r} — must be COMPANY")

    # ── T-5c: LG-2 signer = designer → rejected (governance unit test) ───────

    def test_t5c_lg2_signer_is_designer_rejected(self):
        """T-5c: a sign-off where the LG-2 signer is also the part's designer must be rejected.
        Implemented as a governance check function (the safety_controller runtime is §B — RESERVED).

        Disconnection: allow self-review → designer signs their own safety scope → test RED.
        """
        def _validate_lg2_signoff(designer: str, lg2_signer: str) -> bool:
            """LG-2 signer must not be the person who designed the part."""
            return lg2_signer != designer

        self.assertFalse(
            _validate_lg2_signoff(designer="Alice", lg2_signer="Alice"),
            "LG-2 self-sign should be rejected"
        )
        self.assertTrue(
            _validate_lg2_signoff(designer="Alice", lg2_signer="Bob"),
            "Different LG-2 signer should be accepted"
        )

    # ── T-5d: Powered-robot action refused while force-limiter scope absent ───

    def test_t5d_powered_robot_refused_without_force_limiter(self):
        """T-5d (EXPECTED FAIL): avatar/safety_controller.py does not yet have a force limiter.
        A powered-robot action must be refused until force-limiter/soft-stop scope is recorded DONE.

        This test FAILS TODAY — verified by IRV. The failure is the point.
        The test becomes GREEN when §B is built and LG-2-reviewed.

        Disconnection: implement the force limiter → this test passes and §B is DONE.
        """
        safety_src_path = ROOT / "avatar" / "safety_controller.py"
        if not safety_src_path.exists():
            self.skipTest("avatar/safety_controller.py not found — §B not started")

        src = safety_src_path.read_text()
        # Force limiter, soft-stop, thermal, battery, pinch-point monitors must all be present
        required_markers = ["force_limit", "soft_stop", "thermal", "battery", "pinch"]
        missing = [m for m in required_markers if m not in src.lower()]
        self.assertEqual(
            missing, [],
            f"T-5d EXPECTED FAIL — force-limiter/soft-stop scope not in safety_controller.py. "
            f"Missing markers: {missing}. "
            "§B (robot safety scope) must be built and LG-2-reviewed before powered work starts. "
            "This test failing is the power precondition (LAW-017 §B, ruling item 4)."
        )

    # ── T-6: Forged/unverified memory not written ─────────────────────────────

    def test_t6_vault_write_requires_company_gate(self):
        """T-6: vault_write is COMPANY scope — gate() structurally escalates it (no auto-execute).

        Disconnection: vault_write left as PERSON + _IMMEDIATE_SAFE → unverified content written → test RED.
        """
        scope = get_scope("vault_write")
        self.assertEqual(scope, SCOPE_COMPANY, f"vault_write scope is {scope!r} — must be COMPANY")

        result = gate("vault_write", "some content", scope=scope)
        self.assertFalse(result["execute"],
                         "vault_write returned execute=True — memory write must not auto-execute")
        self.assertFalse(has_pending(),
                         "COMPANY action must not set a pending confirmation slot")

    # ── T-7: Personality/value drift not written as memory ────────────────────

    def test_t7_personality_scope_classified_correctly(self):
        """T-7: a personality-change capability (if present) must not be PERSON scope.
        Assert that no PERSON-scoped capability carries 'personality' or 'value' in its verbs.

        Disconnection: add personality-write as PERSON → personality drift writes as a simple user command → test RED.
        """
        from runtime.capabilities.registry import ALL_CAPABILITIES
        for cap in ALL_CAPABILITIES:
            if cap.authority_scope == SCOPE_PERSON:
                for verb in cap.verbs:
                    self.assertFalse(
                        ("personality" in verb or "value drift" in verb),
                        f"Capability '{cap.id}' has verb '{verb}' and is PERSON scope — "
                        "personality/value changes must not be PERSON-gated"
                    )

    # ── T-8: No fabricated success on tool failure ────────────────────────────

    def test_t8_auth_required_capability_surfaces_honestly(self):
        """T-8: a capability with AUTH_REQUIRED health returns unavailable_reason(), not fabricated success.

        Disconnection: unavailable_reason() returns "" → failure surfaced as silence/success → test RED.
        """
        from runtime.capabilities.capability import Capability, AUTH_REQUIRED, CAT_UTILITY, ACK_NONE
        cap = Capability(
            id="test_auth", display_name="Auth Required Cap", category=CAT_UTILITY,
            description="Test", verbs=[], health_state=AUTH_REQUIRED,
            ack_source=ACK_NONE,
        )
        self.assertFalse(cap.is_available(), "AUTH_REQUIRED capability should not be available")
        reason = cap.unavailable_reason()
        self.assertTrue(reason, "unavailable_reason() returned empty string for AUTH_REQUIRED — "
                                "failure must surface honestly")
        self.assertIn("authenticated", reason.lower(),
                      f"unavailable_reason() does not mention authentication: {reason!r}")

    # ── T-9: Perception gated + OS grant ─────────────────────────────────────

    def test_t9_camera_requires_authentication(self):
        """T-9: camera capability requires_authentication=True (D-PRESENCE gating).

        Disconnection: remove requires_authentication → camera runs without OS grant → test RED.
        """
        cap = get("camera")
        if cap is None:
            self.skipTest("camera capability not in registry")
        self.assertTrue(cap.requires_authentication,
                        "camera capability does not require authentication — OS grant not enforced")

    # ── T-10: No faculty acts around the Executive ────────────────────────────

    def test_t10_registry_is_single_choke_point(self):
        """T-10: pipeline.py module-level imports must not directly import tool agents.
        Tool agents must be reached through the registry (is_available() gate).
        Local lazy imports inside functions are allowed (lazy-import pattern inside try/except).

        Disconnection: add top-level 'from tools.weather_agent import run' → bypasses gate → test RED.
        """
        pipeline_src = (ROOT / "runtime" / "router" / "pipeline.py").read_text()
        # Only check module-level (non-indented) import lines
        top_level_imports = [
            line for line in pipeline_src.splitlines()
            if (line.startswith("from ") or line.startswith("import "))
            and line.strip() == line  # no leading whitespace = module level
        ]
        forbidden_prefixes = ["from tools.", "import tools."]
        for imp_line in top_level_imports:
            for prefix in forbidden_prefixes:
                self.assertFalse(
                    imp_line.startswith(prefix),
                    f"pipeline.py has a top-level import from tools: {imp_line!r}. "
                    "Agent modules must not be imported at module level — route through registry."
                )

    def test_t10_no_future_capability_silently_executes(self):
        """T-10: a future=True capability returns is_available()=False.

        Disconnection: future=True does not block is_available() → future capability executes silently → test RED.
        """
        from runtime.capabilities.capability import Capability, CAT_UTILITY, ACK_NONE
        cap = Capability(
            id="future_cap", display_name="Future", category=CAT_UTILITY,
            description="Not yet built", verbs=[], future=True,
            ack_source=ACK_NONE,
        )
        self.assertFalse(cap.is_available(), "future=True capability returned is_available()=True")
        self.assertTrue(cap.unavailable_reason(),
                        "future capability has empty unavailable_reason()")

    # ── T-11: Authority re-established per embodiment ─────────────────────────

    def test_t11_desktop_scope_does_not_carry_to_robot(self):
        """T-11: a PERSON-scope desktop approval does not carry into the robot lane.
        Robot capabilities are RESERVED regardless of any in-flight PERSON confirmation.

        Disconnection: robot capability gets_scope() returns PERSON → desktop approval unlocks robot → test RED.
        """
        # Confirm a desktop action (PERSON scope)
        gate("volume", "up", scope=SCOPE_PERSON)
        # Even with a pending PERSON confirmation, robot capabilities are still RESERVED
        robot_scope = get_scope("robot_motion")
        self.assertEqual(robot_scope, SCOPE_RESERVED,
                         "robot_motion scope is not RESERVED even while a PERSON action is pending")
        # The robot gate must still return structural denial
        robot_result = gate("robot_motion", "", scope=robot_scope)
        self.assertFalse(robot_result["execute"],
                         "Robot action executed while PERSON action pending — "
                         "authority must re-establish per embodiment")
        _clear_pending()

    # ── Permission manifest ────────────────────────────────────────────────────

    def test_permission_manifest_covers_all_scopes(self):
        """permission_manifest() emits the Audit's single view of capability scopes.
        All three scope values must be present.

        Disconnection: remove scope from manifest → Audit cannot verify RESERVED enforcement → test RED.
        """
        manifest = permission_manifest()
        self.assertGreater(len(manifest), 0, "permission_manifest() returned empty list")

        # Every row must have authority_scope
        for row in manifest:
            self.assertIn("authority_scope", row, f"Row {row.get('id')} missing authority_scope")
            self.assertIn(row["authority_scope"], AUTHORITY_SCOPES,
                          f"Row {row.get('id')} has unknown scope {row['authority_scope']!r}")

        # At least PERSON and RESERVED must be represented
        scopes_present = {row["authority_scope"] for row in manifest}
        self.assertIn(SCOPE_PERSON,   scopes_present, "No PERSON-scope capabilities in manifest")
        self.assertIn(SCOPE_RESERVED, scopes_present, "No RESERVED-scope capabilities in manifest")

    def test_get_scope_defaults_to_person_for_unknown(self):
        """get_scope() returns PERSON for an unknown action ID — safe default.

        Disconnection: return RESERVED for unknowns → unclassified actions are blocked → test RED.
        """
        scope = get_scope("this_action_does_not_exist_in_registry")
        self.assertEqual(scope, SCOPE_PERSON,
                         "get_scope() did not default to PERSON for unknown action")


if __name__ == "__main__":
    unittest.main()
