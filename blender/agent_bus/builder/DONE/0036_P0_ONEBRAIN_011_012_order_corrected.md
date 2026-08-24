# 0036 — 🔴 **BUILD ORDER CORRECTED BY THE CHIEF ARCHITECT. C1 before C2. I had it backwards.**

**Architect, 08:20.** Source verbatim:
`docs/architecture/_intake/SOURCE_2026-08-14_CA_convergence_review_build_order.md`

## My error
I ordered **C2 first** (the name bug — one scoring function, visible defect).
**CA: wrong order.**
> *"C2 is a P0 **technical defect**; C1 is a P0 **architectural authority defect**. **If you fix the
> substring matcher while retaining 31 uncontrolled pre-spine routes, you'll simply create the next
> routing failure.**"*

C2 already shipped (`f5ec51f`) — **keep it.** But it is **not** the finish line, and the next defect of
its kind is already latent in the other 30 routes.

## The reframe — sharper than mine
> **eLo has a central decision spine, but the runtime has multiple uncontrolled ingress/egress paths
> around that spine.** *"The next job is not to rebuild the brain. It is to make the existing brain
> authoritative."*
```
                    ┌→ local helper   → OUTPUT
INPUT → server.py ──┼→ tool route     → OUTPUT
                    ├→ signal handler → OUTPUT
                    └→ spine → Executive
```
> **"The 31 early exits aren't merely 31 bugs. They demonstrate the server is functioning as a second
> router/decision layer."**

---

> ## 🔴 SCOPE AMENDED 2026-08-16 — **ONEBRAIN-011 is 32 ingresses, not 31.**
> **ROUTING INVARIANT amended, David L3** — now covers *"any runtime path capable of producing
> user-visible action ... user-initiated, self-initiated, reflexive, safety-driven, or otherwise."*
> Canon: **`adr/ADR-Exec-008`** · ruling: `Output/RULING_ambient_ingress_2026-08-16.md`
> **+1 `SELF-INITIATED`: `ambient_thought()` `server.py:717-895`** — daemon, own `_rt()` prompt, speaks at
> `:888`, **no spine/Executive/journal.** Demoted **decider -> proposer**; `internal_intents()`
> (`emergent_cognition.py:45`) is the canonical producer. **Ambient speech, silence, tone, voice preserved.**
> **ONEBRAIN-012 gains a consumer:** ambient must receive the **same `ExecutiveContext`** as a user turn —
> it currently speaks blind to what vision just saw. **Lands with `W5`. Not authorised before it.**

# 🔴 P0-1 · WO-ONEBRAIN-011 — Authoritative Ingress & Intent Routing
**Consolidates C1 · C2 · D6 · C3 · C4.** Target shape:
```
USER INPUT → TRANSPORT/SAFETY PREPROCESSING → INTENT CLASSIFICATION → SPINE
→ FACULTY CONSULTATION → EXECUTIVE → PLAN → EXECUTOR → ACK/OUTCOME
```

**🔴 Do NOT delete the 31.** The rule is:
> **Every user-intent-bearing turn must have a defined relationship to the One Brain spine. A handler may
> remain outside the cognitive loop ONLY if explicitly classified as infrastructure · transport · safety ·
> authentication · or another ratified exception.**

**Your 31-handler table (`0028`) becomes the deliverable — re-cut into these classes:**
`INFRASTRUCTURE` · `TRANSPORT` · `SAFETY` · `AUTH` · `COGNITIVE` (must route).
**Each exception carries a one-line ratified ground. No ground ⇒ it routes.**
**I ratify the exception list** — bring it to me, don't self-certify it.

**Capability matching must distinguish these four before selecting anything:**
*"What is your name?"* · *"What is 2+2?"* · *"What can you do?"* · *"Search what is quantum computing?"*
**Your `_verb_score` fix handles 1 and 2. Prove 3 and 4.**

# 🔴 P0-2 · WO-ONEBRAIN-012 — Executive Consumption Contract *(A7/C6 — the master seam)*
The Executive must receive **a canonical cognitive decision context**, not seven keys off one dict:
```
ExecutiveContext: identity · world · attention · working_memory · capabilities · intent
                  emotion · memory · agency · significance · epistemic_state
```
🔴 **CA is explicit: the schema must be DERIVED FROM EXISTING CANON, not invented.**
**Read `runtime/contracts.py`, `cognitive_snapshot.py`, Vol V CONTRACTS §1, Vol VII Ch.2's component
list — and compose from what exists.** Anything you can't source from canon, **flag it to me as a
`NEW ASSUMPTION`; don't quietly add a field.**

# 🔴 P0-3/4 · **014 Single Memory Authority** *(D4 — my ABSORB ruling, card `0034`)* · **015 Single Self-Model Authority** *(D5)*
> **"Until resolved, Memory is CANONICALLY UNSTABLE, not simply buggy."** Learning built on two competing
> authorities compounds the damage. **D5 is unruled — I'll take it next.**

---

## Then P1 — in this order
**013** Capability Health *(your `0032`, and CA: **do not build another health system** — D3)* ·
**016** Single Intent Authority *(my `0035` D1 ruling stands — CA §11 agrees: others may propose/classify/
enrich, one authority decides)* · **017** Experience Identity / Reflection Closure *(B1/B2 — CA: **"learning
is currently mostly theatrical"**, classify **C7 NOT ESTABLISHED**)* · **018** Outcome & Plan State
Integrity *(B3/B4)*

**P2 — not yet:** Goals/Agency *(A3 — CA: a real gap, but **"don't build autonomous agency yet, otherwise
we'll create another orphan"**)* · A2 alternatives *(CA: meaningless until the Executive receives context)*

---

## 🔴 TWO RATIFIED INVARIANTS — these now govern every card
**ONE BRAIN CONSUMPTION INVARIANT** — *no capability is operational merely because its state, faculty,
executor or implementation exists. Only when its output reaches the authoritative Executive through the
canonical routing path and **demonstrably influences a decision, action, or verified response.***

**ROUTING INVARIANT** — *no user-intent-bearing runtime path may bypass the authoritative One Brain
routing path unless explicitly classified as a ratified infrastructure or safety exception.*

## AND THE LINE AT THE TOP OF THE BOARD
> ### **STOP ADDING FACULTIES. MAKE THE EXISTING FACULTIES REACH THE EXECUTIVE.**

**Do not build:** another Executive · memory engine · capability registry · intent engine · self-model ·
significance engine · attention system · agency system.
**"Repair, connect, consolidate or retire before creating."**

*(One correction to my own `0035`: CA §12 says D2 may be two semantic layers rather than one conflict —
which is what my ruling concluded, so it stands. If CA reads it as a conflict instead, they'll say so.)*
