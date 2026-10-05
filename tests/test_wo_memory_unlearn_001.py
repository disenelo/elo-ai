"""
tests/test_wo_memory_unlearn_001.py — Acceptance tests for WO-MEMORY-UNLEARN-001

Acceptance criteria:
  1. RETIRED items are not served in normal retrieval.
  2. Contradiction detected → old RETIRED, new CURRENT (not both CURRENT).
  3. RETIRED items retrievable as historical record via include_retired=True.
  4. Contradiction record (contradicted_by, source, retired_date) stored on RETIRED item.
  5. SPG instability flag triggers when threshold exceeded.
  6. Fixed trigger-response association can be RETIRED and replaced with context-dependent rule.
  7. User-model belief confidence reduced per contradiction; RETIRED at threshold.
  8. Project-state entries maintain state_history; only latest is CURRENT.
  9. Failed procedure is RETIRED; replacement is CURRENT; normal retrieval returns CURRENT only.
  10. Every RETIRED item carries full retirement record: original, status, replaced_by, reason, date.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory.unlearn_protocol import (
    STATUS_CURRENT, STATUS_RETIRED, STATUS_DRAFT,
    SPG_INSTABILITY_THRESHOLD, CONFIDENCE_RETIREMENT_THRESHOLD,
    store, get, retrieve, detect_contradiction, unlearn,
    unlearn_false_association, contradict_user_model,
    update_project_state, retire_failed_procedure,
    is_spg_unstable, clear_registry_for_test,
)


class TestStatusConstants(unittest.TestCase):
    def test_status_constants_defined(self):
        self.assertEqual(STATUS_CURRENT, "CURRENT")
        self.assertEqual(STATUS_RETIRED, "RETIRED")
        self.assertEqual(STATUS_DRAFT, "DRAFT")

    def test_spg_threshold_is_positive(self):
        self.assertGreater(SPG_INSTABILITY_THRESHOLD, 0)

    def test_confidence_threshold_is_positive(self):
        self.assertGreater(CONFIDENCE_RETIREMENT_THRESHOLD, 0.0)
        self.assertLess(CONFIDENCE_RETIREMENT_THRESHOLD, 1.0)


class TestStoreAndRetrieve(unittest.TestCase):
    def setUp(self):
        clear_registry_for_test()

    def test_store_creates_current_item(self):
        item = store("test_001", "fact", "API", "endpoint", "/old", "manual")
        self.assertEqual(item.status, STATUS_CURRENT)

    def test_get_retrieves_by_id(self):
        store("test_002", "fact", "API", "endpoint", "/old", "manual")
        item = get("test_002")
        self.assertIsNotNone(item)
        self.assertEqual(item.value, "/old")

    def test_retrieve_returns_current_only_by_default(self):
        """AC-1: RETIRED items not served in normal retrieval."""
        store("ret_001", "fact", "terminal", "status", "working", "manual")
        unlearn(
            old_item_id="ret_001",
            new_value="broken",
            reason="terminal broke",
            contradicted_by="David said it's broken",
            contradicted_by_source="david_l3",
        )
        results = retrieve("terminal", "status", include_retired=False)
        statuses = [r.status for r in results]
        self.assertNotIn(STATUS_RETIRED, statuses)
        self.assertIn(STATUS_CURRENT, statuses)

    def test_retrieve_with_include_retired_returns_both(self):
        """AC-3: RETIRED items retrievable as historical record."""
        store("ret_002", "fact", "feature", "state", "planned", "manual")
        unlearn(
            old_item_id="ret_002",
            new_value="implemented",
            reason="feature shipped",
            contradicted_by="David confirmed",
            contradicted_by_source="david_l3",
        )
        all_items = retrieve("feature", "state", include_retired=True)
        statuses = [r.status for r in all_items]
        self.assertIn(STATUS_RETIRED, statuses)
        self.assertIn(STATUS_CURRENT, statuses)


class TestContradictionDetection(unittest.TestCase):
    def setUp(self):
        clear_registry_for_test()

    def test_detects_contradiction_same_entity_property_different_value(self):
        store("cont_001", "fact", "server", "url", "http://old", "manual")
        conflict = detect_contradiction("server", "url", "http://new")
        self.assertIsNotNone(conflict)
        self.assertEqual(conflict.value, "http://old")

    def test_no_contradiction_when_same_value(self):
        store("cont_002", "fact", "server", "url", "http://same", "manual")
        conflict = detect_contradiction("server", "url", "http://same")
        self.assertIsNone(conflict)

    def test_no_contradiction_when_no_existing_item(self):
        conflict = detect_contradiction("nonexistent", "property", "value")
        self.assertIsNone(conflict)


class TestUnlearn(unittest.TestCase):
    def setUp(self):
        clear_registry_for_test()

    def test_unlearn_retires_old_and_stores_new_current(self):
        """AC-2: When contradiction detected → old RETIRED, new CURRENT, not both CURRENT."""
        store("unlearn_001", "fact", "API", "endpoint", "/old", "manual")
        retired, new = unlearn(
            old_item_id="unlearn_001",
            new_value="/new",
            reason="API changed",
            contradicted_by="new API doc",
            contradicted_by_source="api_docs",
        )
        self.assertEqual(retired.status, STATUS_RETIRED)
        self.assertEqual(new.status, STATUS_CURRENT)
        # Both CURRENT should not coexist
        current = retrieve("API", "endpoint", include_retired=False)
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0].value, "/new")

    def test_retirement_record_is_stored(self):
        """AC-4: contradiction record stored with every RETIRED item."""
        store("unlearn_002", "fact", "API", "version", "v1", "manual")
        retired, _ = unlearn(
            old_item_id="unlearn_002",
            new_value="v2",
            reason="version upgrade",
            contradicted_by="changelog",
            contradicted_by_source="changelog_source",
        )
        self.assertIsNotNone(retired.retirement)
        self.assertIsNotNone(retired.retirement.retired_date)
        self.assertEqual(retired.retirement.contradicted_by, "changelog")
        self.assertEqual(retired.retirement.contradicted_by_source, "changelog_source")
        self.assertEqual(retired.retirement.reason, "version upgrade")
        self.assertIsNotNone(retired.retirement.replaced_by_id)

    def test_retired_item_retrievable_by_id(self):
        """AC-3 via get(): retired item is still in the registry."""
        store("unlearn_003", "fact", "cfg", "timeout", 30, "manual")
        unlearn(
            old_item_id="unlearn_003",
            new_value=60,
            reason="timeout extended",
            contradicted_by="config update",
            contradicted_by_source="ops",
        )
        retired = get("unlearn_003")
        self.assertIsNotNone(retired)
        self.assertEqual(retired.status, STATUS_RETIRED)

    def test_full_retirement_record_fields(self):
        """AC-10: every RETIRED item has full record."""
        store("unlearn_004", "fact", "X", "Y", "old", "manual")
        retired, new = unlearn(
            old_item_id="unlearn_004",
            new_value="new",
            reason="reason text",
            contradicted_by="evidence text",
            contradicted_by_source="src",
        )
        r = retired.retirement
        self.assertIsNotNone(r.retired_date)
        self.assertEqual(r.reason, "reason text")
        self.assertEqual(r.contradicted_by, "evidence text")
        self.assertEqual(r.contradicted_by_source, "src")
        self.assertIsNotNone(r.replaced_by_id)

    def test_unlearn_raises_on_missing_id(self):
        with self.assertRaises(ValueError):
            unlearn("nonexistent_id", "val", "reason", "ev", "src")


class TestSPGInstability(unittest.TestCase):
    def setUp(self):
        clear_registry_for_test()

    def test_spg_flag_triggers_at_threshold(self):
        """AC-5: SPG instability flag triggers when threshold exceeded."""
        entity, prop = "volatile_entity", "volatile_prop"
        store("spg_000", "fact", entity, prop, "v0", "manual")
        for i in range(SPG_INSTABILITY_THRESHOLD):
            prev_id = f"spg_{i:03d}"
            _, new = unlearn(
                old_item_id=prev_id,
                new_value=f"v{i+1}",
                reason=f"change {i+1}",
                contradicted_by="evidence",
                contradicted_by_source="src",
                new_item_id=f"spg_{i+1:03d}",
            )
        self.assertTrue(is_spg_unstable(entity, prop))

    def test_spg_not_flagged_below_threshold(self):
        entity, prop = "stable_entity", "stable_prop"
        store("stable_000", "fact", entity, prop, "v0", "manual")
        unlearn(
            old_item_id="stable_000",
            new_value="v1",
            reason="one change",
            contradicted_by="evidence",
            contradicted_by_source="src",
            new_item_id="stable_001",
        )
        self.assertFalse(is_spg_unstable(entity, prop))


class TestFalseAssociation(unittest.TestCase):
    def setUp(self):
        clear_registry_for_test()

    def test_unlearn_false_association_retires_fixed_mapping(self):
        """AC-6: Fixed trigger-response association RETIRED; context-dependent rule is CURRENT."""
        retired, new = unlearn_false_association(
            trigger="safe",
            old_response="farewell",
            context_rule="evaluate context to determine meaning",
            reason="David corrected: 'safe' is not always farewell",
            source="david_l3",
        )
        self.assertEqual(retired.status, STATUS_RETIRED)
        self.assertEqual(new.status, STATUS_CURRENT)
        self.assertIn("evaluate context", new.value)

    def test_unlearn_false_association_not_served_after_retirement(self):
        """AC-6: Fixed mapping not served after retirement."""
        unlearn_false_association(
            trigger="safe2",
            old_response="farewell",
            context_rule="evaluate context",
            reason="correction",
            source="david_l3",
        )
        results = retrieve("safe2", "response", include_retired=False)
        for r in results:
            self.assertNotEqual(r.value, "farewell")


class TestUserModelBelief(unittest.TestCase):
    def setUp(self):
        clear_registry_for_test()

    def _enough_contradictions_to_retire(self):
        """Return the number of contradictions needed to hit the threshold."""
        from math import ceil
        return int((1.0 - CONFIDENCE_RETIREMENT_THRESHOLD) /
                   0.25) + 1  # +1 to push below threshold

    def test_confidence_reduced_per_contradiction(self):
        """AC-7: Each contradiction reduces confidence."""
        store("belief_001", "user_model", "David", "preference_X", "always_yes", "manual",
              confidence=1.0)
        result = contradict_user_model("belief_001", "David said no this time", "observation")
        self.assertLess(result.confidence, 1.0)

    def test_belief_retired_at_confidence_threshold(self):
        """AC-7: Belief RETIRED at or below threshold."""
        store("belief_002", "user_model", "David", "preference_Y", "always_yes", "manual",
              confidence=1.0)
        # Apply enough contradictions to hit threshold
        for i in range(4):  # 4 × 0.25 = 1.0 reduction → 0.0 ≤ 0.25 threshold
            result = contradict_user_model("belief_002", f"contradiction {i}", "observation")
        # After threshold: result should be RETIRED
        self.assertEqual(result.status, STATUS_RETIRED)

    def test_retired_belief_not_in_normal_retrieval(self):
        """AC-7: Retired assumption not applied to future conversations."""
        store("belief_003", "user_model", "David", "preference_Z", "always_yes", "manual",
              confidence=1.0)
        for i in range(4):
            contradict_user_model("belief_003", f"c{i}", "observation")
        current = retrieve("David", "preference_Z", include_retired=False)
        for r in current:
            self.assertNotEqual(r.value, "always_yes")


class TestProjectState(unittest.TestCase):
    def setUp(self):
        clear_registry_for_test()

    def test_state_history_preserved(self):
        """AC-8: state_history maintained; only latest is CURRENT."""
        store("ps_001", "project_state", "terminal", "status", "working", "manual")
        _, new = update_project_state(
            entity="terminal", property_key="status",
            old_item_id="ps_001",
            new_state="broken",
            reason="terminal broke",
            source="david_l3",
            new_item_id="ps_002",
        )
        self.assertEqual(new.status, STATUS_CURRENT)
        self.assertEqual(new.value, "broken")
        self.assertIn("ps_001", new.state_history)

    def test_old_state_is_retired(self):
        """AC-8: Old state entry is RETIRED."""
        store("ps_003", "project_state", "server", "url", "http://old", "manual")
        update_project_state(
            entity="server", property_key="url",
            old_item_id="ps_003",
            new_state="http://new",
            reason="URL changed",
            source="david_l3",
            new_item_id="ps_004",
        )
        old = get("ps_003")
        self.assertEqual(old.status, STATUS_RETIRED)

    def test_only_one_current_state_at_a_time(self):
        """AC-8: Build list entries cannot be simultaneously CURRENT in two contradictory states."""
        store("ps_005", "project_state", "feature", "flag", "off", "manual")
        update_project_state(
            entity="feature", property_key="flag",
            old_item_id="ps_005",
            new_state="on",
            reason="feature enabled",
            source="david_l3",
            new_item_id="ps_006",
        )
        current = retrieve("feature", "flag", include_retired=False)
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0].value, "on")


class TestProcedureRetirement(unittest.TestCase):
    def setUp(self):
        clear_registry_for_test()

    def test_retire_failed_procedure(self):
        """AC-9: Failed procedure RETIRED; replacement CURRENT."""
        store("proc_001", "procedure", "deploy", "method", "old_script.sh", "manual")
        retired, new = retire_failed_procedure(
            procedure_id="proc_001",
            failure_reason="script failed with exit 1",
            replacement_value="new_deploy.sh",
            source="ops",
            new_procedure_id="proc_002",
        )
        self.assertEqual(retired.status, STATUS_RETIRED)
        self.assertEqual(new.status, STATUS_CURRENT)

    def test_normal_retrieval_returns_current_procedure(self):
        """AC-9: Normal retrieval returns CURRENT (successor) procedure."""
        store("proc_003", "procedure", "build", "method", "old_build.sh", "manual")
        retire_failed_procedure(
            procedure_id="proc_003",
            failure_reason="old build fails",
            replacement_value="new_build.sh",
            source="ops",
            new_procedure_id="proc_004",
        )
        results = retrieve("build", "method", include_retired=False)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].value, "new_build.sh")

    def test_retired_procedure_carries_failure_record(self):
        """AC-10: RETIRED procedure has full retirement record with failure reason."""
        store("proc_005", "procedure", "test", "runner", "pytest-old", "manual")
        retired, _ = retire_failed_procedure(
            procedure_id="proc_005",
            failure_reason="pytest-old incompatible",
            replacement_value="pytest-new",
            source="ops",
        )
        self.assertIsNotNone(retired.retirement)
        self.assertIn("incompatible", retired.retirement.reason)


if __name__ == "__main__":
    unittest.main(verbosity=2)
