# 0009 — **THE PATH TO 26.** Dependency order, proof per row. Run it end to end without stopping.

**Issued 20:10.** David: *"I want the rest of the 26 verified so we can keep going."*
**Current: 4** — 12 ACT · 7 REMEMBER · 18 INTEND · 2 WHERE.
**Do not ask between steps. The card is the instruction.**

Each row below states **the proof that makes it VERIFIED.** Ruling H: state, never the sentence.
If a proof fails, **say so and move on** — an honest fail is progress; a false tick is not.

---

## WAVE 1 — one test run, three rows (do this first)
**Disconnection test on the seam.** Blank `plan.world` ⇒ the decision must change or fail.
→ **4 SEE · 6 ATTEND · 16 AFFORD**
**Proof:** decision differs with state present vs absent. For 6, the **WM winner** — not `attention_model`
— determines what's foregrounded. For 16, affordances reach the Executive, not just the prompt.
*(Unblocked by ruling `0008` — the freeze does not cover this.)*

## WAVE 2 — the four still open from `0003`/`0007` (minutes each)
| Row | Fix | Proof |
|---|---|---|
| **3 BODY** | `server.py:3088` writes `embodiment="desktop"` **hardcoded** — read the real body; compute the tier at `the_moment.py:67` | Field changes when the body changes |
| **24 SELF-OBSERVE** | `record_behaviour(` **zero callers** — call it after every ACKed action; stop passing `"topics": []` | `elo_self_state.json` shows non-empty `recent_behavior` |
| **14 ROUTE** | `route_memory` is fed but the Executive can't consult it — surface it through the assembled state | Route history readable by `decide()` |
| **1 IDENTITY** | No identity fields in `EloSelfState` — add `identity`/`core_values`/`invariants`; render the prompt **from** them | Change a field ⇒ the prompt changes |
| | + the `truncate` (`0007`) — **yours, not David's** | Suite leaves `growth_metrics.jsonl` byte-identical |

## WAVE 3 — WO-103, then everything is provable
**Disconnection-proof tests.** A test must fail if the feature is disconnected. **Do this before Wave 4** —
without it, every row after is claim, not proof.
**Proof:** orphan-faculty test **fails on `faculties.temporal`** today. Leave it red; that's correct.

## WAVE 4 — the epistemic + verification block
| Row | WO | Proof |
|---|---|---|
| **13 VERIFY** | WO-111 | Break an executor ⇒ **eLo says it didn't work.** Test fails when a capability registers with no ACK path |
| **9·10·11 KNOW/INFER/UNKNOWN** | WO-110 | Four tiers on a **non-body** fact; "I don't know" when state is absent; tier changes when source changes; **direct-turn path tiered too** |
| **8 RECALL** | WO-109 | Recall returns `experience_id·timestamp·event·outcome·source·confidence` |
| **15 CHOOSE** | WO-112 | *"Why did you jump?"* reconstructs from the record — **options + utilities + reason + confidence**, not `null` |

## WAVE 5 — the ones that need Wave 4 first
| Row | WO | Proof |
|---|---|---|
| **21 REFLECT** | WO-115 | After a reflection, **`EloSelfState` differs** |
| **23 HISTORY** | WO-115 | `autobiography.jsonl` exists, grows from **verified outcomes only**, reads chronologically |
| **17 GAP** | WO-113 | *"I can wall-jump but not reliably from here"* — with **real** `gap_distance` vs `reliable_range` |
| **5 LOOK** | WO-108 | Directed look produces an **observation record**; occluded target records failure |
| **19 SELF-CHOOSE** | WO-114 | An action fires with `internal_intent.source == SELF` **on the plan**, David idle |
| **11 UNKNOWN** | WO-110 | Absence is statable |

## WAVE 6 — the emergent four (they fall out; don't force them)
| Row | Proof |
|---|---|
| **20 LEARN** | **N lessons reach `confirmed` on a real run.** Ledger is `{'candidate': 1}` — N is currently 0 |
| **22 ADAPT** | §7: `wall_jump 0.71 → attempt succeeds → 0.78`. **A number moves after experience** |
| **25 SELF-INTERPRET** | eLo names a pattern in himself **traceable to logged actions** |
| **26 MEANING** | He says why something mattered, **with the significance score and the outcome behind it** |

**WO-104 (LoRA) runs when a GPU session exists — it is not on this path and must not block it.**

---

## RULES FOR THE WHOLE RUN
- **Never stop to ask.** Only robot hardware · David's identity/values · a real technical dependency.
- **Commit per row**, hash in the outbox, so any single row can be reverted.
- **Report the VERIFIED count after each wave**, with the state evidence per row. **No test counts.**
- **A false VERIFIED is worse than a fail.** If a proof doesn't bite, write "proof failed, here's why."
- **If a proof reveals a design question — raise it, don't decide it.** Ordering and logic are mine.
