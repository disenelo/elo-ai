"""
company_runtime/ — the DISENELO Company Runtime (EA-2 / EA-3), ADDITIVE package.

Observes/reuses eLo OS primitives; NEVER modifies the frozen cognitive kernel (LAW-017).
First slice (EA2-1): parse the live dispatch board → emit blender/company_state.json,
the business twin of brain_state.json, which DISENELO Presence renders.
"""
__all__ = ["company_state_writer", "company_graph"]
