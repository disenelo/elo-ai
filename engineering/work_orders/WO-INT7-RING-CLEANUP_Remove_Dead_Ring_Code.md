---
id: INT7-RING-CLEANUP
title: "One Brain — remove dead sphere-cage ring code (ShellRing / _rings / ringBeads / DrawRings)"
owner_seat: SEAT-ENG-004 (UI/Avatar) — Design lane
occupant: UI/Avatar (Design)
priority: P2
reason: "The sphere-cage `ShellRing` is confirmed DEAD — never rendered, not on screen. Dead code adds noise and confuses viewer diagnostics. Remove cleanly from the approved HR base (5d4427e)."
review_required: L1 → L3 (visual confirm nothing changed)
risk: low (removing unrendered code; visual output must be identical)
status: READY
created: 2026-08-01
base_commit: 5d4427e
---

# INT7-RING-CLEANUP — delete the dead sphere-cage ring code

Confirmed dead (grep on `Assets/Scripts/EloBrainCluster.cs`, never invoked/rendered):

- `49:  class ShellRing { public SpriteRenderer[] beads; ... }`  — great-circle of the sphere cage
- `66:  readonly List<ShellRing> _rings = new List<ShellRing>();`
- `89:  [SerializeField] int ringBeads = 40;`  — beads per great-circle
- `726: void DrawRings(Quaternion tilt, Quaternion face) { ... foreach (var rg in _rings) ... }`

## Task
Remove all four references (class, list field, serialized `ringBeads`, `DrawRings` method) **and any
call sites** of `DrawRings(...)` / `_rings` population if present. Leave nothing referencing the sphere
cage.

## Acceptance
1. `grep -n "ShellRing\|_rings\|ringBeads\|DrawRings" Assets/Scripts/EloBrainCluster.cs` → **no matches**.
2. Project compiles (no unresolved symbols).
3. **Visual output is byte-for-byte identical** to `5d4427e` at rest and active — the ring was never
   drawn, so removing it must change nothing on screen. David eyeballs to confirm.
4. Handback: the diff (deletion-only), commit off `5d4427e`.

## Notes
- Do this **before** re-doing WEB so the web work starts from a truly clean base.
- ONE change / build / wait → then INT7-WEB re-spec.
