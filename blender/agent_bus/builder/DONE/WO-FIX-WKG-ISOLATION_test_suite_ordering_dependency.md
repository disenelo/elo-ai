# WO-FIX-WKG-ISOLATION — Fix WKG test ordering dependency (P3)

**Full WO:** `engineering/work_orders/WO-FIX-WKG-ISOLATION_test_suite_ordering_dependency.md`
**Source:** MT defect report 2026-08-29 (66 failures = 1 ordering artefact, not behaviour)

Three WKG files (test_wkg_phase2, test_bwkg02_elo_corpus, test_wkg001_context_items) pass in isolation but fail in full suite — earlier test leaves shared state. Implementation files: NOT TOUCHED. Test isolation fix only.

3 ATs. Return: `DONE/FROM_BUILDER_WO-FIX-WKG-ISOLATION_result.md`

*Board · 2026-08-29*
