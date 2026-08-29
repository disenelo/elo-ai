# WO-MOBILE-001 — Mobile Embodiment Wiring (Spine Side)
**Seat:** Builder (spine side only — see MT dispatch amendment for mobile end)  
**Date issued:** 2026-08-27  
**Authority:** David L3 (MT relay — "relay to board, with my authority for it to be done") + CA ruling 2026-08-27 D1/D2/D3  
**Source:** `docs/architecture/_intake/SOURCE_2026-08-27_CA_RULING_BRIEF1_BRIEF2.md` Item B  
**Depends on:** None (independent of WO-GUARD-001 and navigation wave)  
**Non-scope:** New capability system. New state model. Parallel cognitive registry. Desktop capability replication. `executive.py`. Frozen kernel (LAW-017 / FREEZE_V1_LOCK).

---

## Intent

David L3: eLo on the phone must know it is on the phone. `current_embodiment` is permanently `"desktop"` during a phone session. One Brain reasons about the wrong body; `embodiment_scope` filters to the desktop capability set for a device that has none of them.

CA ruling (G9 — smallest authorised change):
- Builder: self-model + spine side — receive the mobile foreground event, call `apply_embodiment("phone")`, ensure `embodiment_scope` and `embodiment_history` update accordingly.
- MT: mobile end only — fire the foreground event through the window process (authenticated, G4).

---

## Governed Design Decisions (CA-ruled 2026-08-27)

**D1 — Vocabulary string:** Keep `"phone"`. Existing string in `elo_self_model.py:149`. No rename. CA notes conceptual class = `mobile`, concrete = `phone` — Board records for future vocabulary freeze. No code migration.

**D2 — Background behaviour:** Embodiment and lifecycle are separate dimensions. When the phone backgrounds, `current_embodiment` remains `"phone"`. Backgrounding is a visibility/lifecycle event — not an embodiment change. The world-state should reflect `phone + background/unavailable-for-interaction` as a composite state, not revert to `"desktop"` and not use `"dormant"` as a replacement for the embodiment identity.

**D3 — `nearby_surfaces` on mobile switch:** Explicitly clear/invalidate desktop-context `nearby_surfaces` on embodiment transition to `"phone"`. Old desktop surface state must not leak into mobile. Mobile subsequently populates its own valid surface context if applicable. Clearing is the safe default; it is reversible.

---

## What to build (Builder — spine side)

### D-SPINE-1 — Receive mobile foreground event

Wire a handler in `server.py` (or the appropriate event receiver) for the mobile foreground notification. When the phone app comes to foreground and the notification is received:
- Call `apply_embodiment("phone")` on `EloSelfState` / `elo_self_model.py`
- Confirm `current_embodiment` updates to `"phone"` in `world_dict`
- Confirm `embodiment_scope` updates to the mobile-appropriate capability set
- Confirm `embodiment_history` records the transition with a timestamp

### D-SPINE-2 — Background state handling

When a phone background notification is received:
- Do NOT change `current_embodiment` — it remains `"phone"`
- Update a lifecycle/availability field to indicate the mobile context is backgrounded/unavailable
- The world-state should carry both dimensions: embodiment identity (`phone`) + interaction availability (`background`)

### D-SPINE-3 — `nearby_surfaces` clear on mobile switch

On transition to `"phone"` embodiment:
- Explicitly clear `nearby_surfaces` in `LiveWorldState` (set to empty list / empty dict per existing schema)
- Do not preserve desktop surface state across the embodiment boundary
- Log the clear — this is a recoverable state change, not a permanent wipe

---

## Guardrails (CA-validated G1–G11 — apply throughout)

- **G2:** Do not assert an embodiment that is not anchored to a verified event. Only transition on a received foreground notification.
- **G4:** Mobile foreground event must come through the authenticated window process only — not from any unauthenticated source.
- **G5:** Surface stays empty on mobile; do not carry desktop `win_id` semantics into mobile (D3 above).
- **G9:** Smallest authorised change. No new capability system, no parallel registry, no desktop replication.

---

## Acceptance Tests (5)

**AT-1:** On receipt of a mobile foreground event, `current_embodiment` in `world_dict` is `"phone"`.

**AT-2:** `embodiment_scope` after transition reflects the mobile-appropriate set (not desktop).

**AT-3:** `embodiment_history` contains a transition record with timestamp on mobile foreground.

**AT-4:** On phone background notification, `current_embodiment` remains `"phone"` (does not revert to `"desktop"`). Lifecycle/availability field reflects backgrounded state.

**AT-5:** On mobile switch, `nearby_surfaces` is explicitly cleared (empty). Desktop surface state does not persist.

---

## MT dispatch amendment

MT mobile end: fire the authenticated foreground notification through the window process and confirm AT-1 through AT-5 against live spine behaviour. MT does NOT touch the spine — Builder owns D-SPINE-1/2/3.

---

## Verification (Board/LA)

Board/LA confirms: `current_embodiment` = `"phone"` in world_dict after foreground event. `nearby_surfaces` cleared. `executive.py` diff empty. Frozen kernel untouched.

**Do not self-close. Board/LA closes.**

---

*Board / Lead Architect · 2026-08-27 · Authority: David L3 + CA ruling 2026-08-27*
