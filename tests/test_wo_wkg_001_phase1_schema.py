"""
WO-WKG-001 Phase 1 Schema — Acceptance Tests AT-1 through AT-10.
Disconnection-falsifiable: patching _WKG_DIR to a temp dir isolates from live store.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
import uuid

# Ensure runtime/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import runtime.wkg_faculty as wkg


class WKGPhase1Tests(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._orig_dir = wkg._WKG_DIR
        wkg._WKG_DIR = self._tmp
        # seed relationship_types into temp store (mirrors live file)
        src = os.path.join(os.path.dirname(__file__), "..", "memory", "wkg", "relationship_types.json")
        shutil.copy(src, os.path.join(self._tmp, "relationship_types.json"))
        # seed sources
        src_s = os.path.join(os.path.dirname(__file__), "..", "memory", "wkg", "sources.json")
        shutil.copy(src_s, os.path.join(self._tmp, "sources.json"))

    def tearDown(self):
        wkg._WKG_DIR = self._orig_dir
        shutil.rmtree(self._tmp, ignore_errors=True)

    # AT-1: Entity creation
    def test_at1_entity_creation(self):
        e = wkg.create_entity("CONCEPT", "Sun", aliases=["Sol"], description="Star at centre")
        self.assertIn("entity_id", e)
        uuid.UUID(e["entity_id"])          # stable UUID
        self.assertEqual(e["label"], "Sun")
        self.assertEqual(e["entity_type"], "CONCEPT")
        self.assertIn("Sol", e["aliases"])
        self.assertIn("created_at", e)

    # AT-2: Epistemic class enforcement
    def test_at2_epistemic_class_enforcement(self):
        # Missing epistemic_class raises
        e1 = wkg.create_entity("CONCEPT", "X")
        e2 = wkg.create_entity("CONCEPT", "Y")
        with self.assertRaises(ValueError):
            wkg.record_claim(e1["entity_id"], "IS", e2["entity_id"],
                             epistemic_class="MADE_UP", source_id="SOURCE-001")
        # VERIFIED and SOURCE_ATTRIBUTED are distinct classes — no implicit promotion
        c_verified = wkg.record_claim(e1["entity_id"], "IS", e2["entity_id"],
                                      epistemic_class="VERIFIED", source_id="SOURCE-001")
        c_attributed = wkg.record_claim(e1["entity_id"], "SUPPORTS", e2["entity_id"],
                                        epistemic_class="SOURCE_ATTRIBUTED", source_id="SOURCE-001")
        self.assertEqual(c_verified["epistemic_class"], "VERIFIED")
        self.assertEqual(c_attributed["epistemic_class"], "SOURCE_ATTRIBUTED")
        self.assertNotEqual(c_verified["epistemic_class"], c_attributed["epistemic_class"])

    # AT-3: Claim triple (Sun SYMBOLISES consciousness SOURCE_ATTRIBUTED SOURCE-001)
    def test_at3_claim_triple(self):
        sun = wkg.create_entity("ASTRONOMICAL", "Sun")
        consciousness = wkg.create_entity("CONCEPT", "consciousness")
        claim = wkg.record_claim(
            sun["entity_id"], "SYMBOLISES", consciousness["entity_id"],
            epistemic_class="SOURCE_ATTRIBUTED", source_id="SOURCE-001",
        )
        self.assertEqual(claim["relationship_type"], "SYMBOLISES")
        self.assertEqual(claim["epistemic_class"], "SOURCE_ATTRIBUTED")
        self.assertIn("SOURCE-001", claim["source_ids"])
        self.assertIn("claim_id", claim)
        self.assertIn("confidence", claim)
        self.assertIn("created_at", claim)

    # AT-4: Contradicted claim
    def test_at4_contradicted_claim(self):
        e1 = wkg.create_entity("CONCEPT", "A")
        e2 = wkg.create_entity("CONCEPT", "B")
        c1 = wkg.record_claim(e1["entity_id"], "CAUSES", e2["entity_id"],
                               epistemic_class="HYPOTHESIS", source_id="SOURCE-002")
        c2 = wkg.record_claim(e2["entity_id"], "CAUSES", e1["entity_id"],
                               epistemic_class="HYPOTHESIS", source_id="SOURCE-002")
        wkg.mark_contradicted(c1["claim_id"], c2["claim_id"])
        updated = wkg.get_claims_about(e1["entity_id"])
        c1_updated = next(c for c in updated if c["claim_id"] == c1["claim_id"])
        self.assertIn(c2["claim_id"], c1_updated["contradicted_by"])

    # AT-5: Query get_entity
    def test_at5_get_entity(self):
        created = wkg.create_entity("PERSON", "Harry", description="Author")
        fetched = wkg.get_entity(created["entity_id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["label"], "Harry")
        self.assertIsNone(wkg.get_entity(str(uuid.uuid4())))

    # AT-6: Query get_claims_about
    def test_at6_get_claims_about(self):
        e1 = wkg.create_entity("CONCEPT", "Moon")
        e2 = wkg.create_entity("CONCEPT", "Tide")
        e3 = wkg.create_entity("CONCEPT", "Unrelated")
        wkg.record_claim(e1["entity_id"], "INFLUENCES", e2["entity_id"],
                         epistemic_class="VERIFIED", source_id="SOURCE-001")
        claims = wkg.get_claims_about(e1["entity_id"])
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["subject_entity_id"], e1["entity_id"])
        # Unrelated entity has no claims
        self.assertEqual(wkg.get_claims_about(e3["entity_id"]), [])

    # AT-7: Query search_entities
    def test_at7_search_entities(self):
        wkg.create_entity("CONCEPT", "Mercury", aliases=["Hermes"])
        results = wkg.search_entities("mercury")
        self.assertTrue(len(results) >= 1)
        self.assertTrue(any(r["label"] == "Mercury" for r in results))
        # Alias search
        results_alias = wkg.search_entities("Hermes")
        self.assertTrue(any(r["label"] == "Mercury" for r in results_alias))

    # AT-8: MemoryFaculty write stub
    def test_at8_memory_faculty_write_stub(self):
        exp_id = str(uuid.uuid4())
        e1 = wkg.create_entity("CONCEPT", "Wisdom")
        e2 = wkg.create_entity("CONCEPT", "Knowledge")
        claim = wkg.record_claim(
            e1["entity_id"], "DERIVED_FROM", e2["entity_id"],
            epistemic_class="SYMBOLIC", source_id="SOURCE-002",
            experience_id=exp_id,
        )
        self.assertEqual(claim["experience_id"], exp_id)
        # Claim appears in store
        stored = wkg.get_claims_about(e1["entity_id"])
        self.assertTrue(any(c["claim_id"] == claim["claim_id"] for c in stored))

    # AT-9: Source registry seeded correctly
    def test_at9_source_registry(self):
        s1 = wkg.get_source("SOURCE-001")
        s2 = wkg.get_source("SOURCE-002")
        self.assertIsNotNone(s1)
        self.assertIsNotNone(s2)
        self.assertEqual(s1["source_type"], "BOOK")
        self.assertEqual(s2["source_type"], "EXPERIENCE")

    # AT-10: Experience chain terminus — MemoryFaculty call produces WKG record
    def test_at10_experience_chain_terminus(self):
        """
        Simulates MemoryFaculty.submit() call after processing a spine turn.
        Verifies that a processed experience_id produces a WKG claim in the store.
        """
        experience_id = str(uuid.uuid4())
        subject = wkg.create_entity("CONCEPT", "Stability")
        obj = wkg.create_entity("CONCEPT", "Complexity")
        # MemoryFaculty would call record_claim after distilling the experience
        claim = wkg.record_claim(
            subject["entity_id"], "INFLUENCES", obj["entity_id"],
            epistemic_class="HYPOTHESIS",
            source_id="SOURCE-002",
            experience_id=experience_id,
        )
        # Claim exists in store with correct experience_id linkage
        claims_raw_path = os.path.join(self._tmp, "claims.json")
        with open(claims_raw_path) as f:
            raw = json.load(f)
        matching = [c for c in raw if c["experience_id"] == experience_id]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["claim_id"], claim["claim_id"])


if __name__ == "__main__":
    unittest.main()
