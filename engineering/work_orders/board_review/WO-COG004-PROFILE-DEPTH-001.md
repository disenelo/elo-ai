# WO-COG004-PROFILE-DEPTH-001 — David Profile Depth Enrichment (COG-004 Root Fix)

**Priority:** P1
**Assigned:** Builder 1
**Status:** OPEN

## Lane
- `memory/facts.json`
- `memory/user_profile.json`
- `wkg/` (David entity)

## Gap
COG-004 at ~17/26 (spot check). Root cause: David's profile is too sparse. `facts.json` has 1 fact (location — now corrected). `user_profile.json` has 7 fields. WKG entity for David has 3 fields. eLo cannot answer personal questions correctly because the data is not there.

**Evidence:** CLAUDE.md §99 — "Profile is insufficient for eLo's WKG to answer personal questions." `memory/facts.json` — 1 entry. `memory/user_profile.json` — 7 fields only.

## Fix
Builder 1 enriches David's profile from existing source files in `docs/architecture/_intake/`. Source files to read:
- `SOURCE_2026-09-27_DAVID_location_correction.md` — born Fulham, raised Brixton
- Any other biographical SOURCE files for David

Populate:
- `facts.json`: born Fulham, grew up Brixton, founder DISENELO, etc.
- `user_profile.json`: extend to 15+ meaningful fields
- WKG entity: name, location, company, role, relationship to eLo

Add honest-absence signal for any field not yet known.

**Correct values (David L3 confirmed):** Born Fulham. Grew up Brixton. Not Camberwell (that was a mistaken recollection — now corrected). Address as "David" in conversation.

## Acceptance
COG-004 reaches 22/26 or above. "Where are you from?" answered correctly with "Brixton" / "London." "What do you do?" answered with DISENELO / founder context.
