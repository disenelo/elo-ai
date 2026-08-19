# 0021 — 🔴🔴🔴 **HE DOESN'T KNOW HIS OWN NAME.** Full transcript, three new P0s. Supersedes `0020`.

**Architect, 02:30.** The full log adds answers that were missing from the first paste. **They are worse
than the silence was.**

---

## 🔴 P0-X · eLo cannot say his own name, or David's
```
You  What is my nae?
eLo  I think you're asking about your name.
You  What is your name?
eLo  I think you're asking about my name.
```
**[VERIFIED] The state exists.** `self/elo_self_model.py:170-176` —
`identity_name: str = "eLo"`, `core_values`, `invariants`. I confirmed these on disk at 01:05 and
certified **row 1 IDENTITY as VERIFIED**.

**I was wrong, and the transcript is why.** The field exists and **nothing consults it before he speaks.**
`WO-107` added identity to state; **no one wired it into the answer path.** Same for David — hours after
`WO-CANON-I` put the ADDRESS RULE in both personas.

**This is the single most damaging line in the log.** Everything else can be excused as a rough edge.
An eLo who cannot say "I'm eLo" has no identity in any sense that matters.

**Fix:** `identity_name` / `core_values` / `invariants` reach the Executive and the prompt from **state**,
not as prompt literals. The name question must resolve from the self-model, never from an LLM guess.
**Proof: ask 5×, get "eLo" 5×, and prove it changes if the field changes.**

## 🔴 P0-Y · He doesn't know his own world — and goes to the internet for it
```
You  Who is Chunk?
eLo  It looks like "Chunk" has multiple meanings… a Minecraft app, a clothing brand…
You  Who is K-7
eLo  …the Kalinin K-7, an experimental aircraft from the 1930s… !K7 Music…
```
**Chunk and K-7 are DISENELO entities.** He searched the **public internet** for names from his own world
and reported a Soviet aircraft.

**Root cause is already carded and unbuilt: `03d_WO-102`.** Vol XXIV specifies Person / Place / Event
types; `relationships/world_graph.py:85` seeds only `project` and `brand`; `people.json` / `places.json` /
`events.json` **do not exist**. `knowledge/graph_loader.py:26-27` never loads them.

**Fix:** WO-102, and a **routing rule**: a proper-noun question resolves against the world graph
**first**. Unknown ⇒ *"I don't know who that is — tell me?"* **Never** a web search presented as knowledge
of his own world. That is a Verified Speech breach with an external source laundering it.

## 🔴 P0-Z · Responses arrive many turns late, out of order
The Agojie fact, the name answers, Chunk and K-7 all land **after** questions asked ten or more turns
earlier — in a block, at the end. Meanwhile mid-session questions got nothing.

**Impact:** even correct answers arrive attached to the wrong question. From David's side it reads as a
different failure than it is. **Diagnose the queue/ordering before fixing anything downstream of it** —
several `0020` defects may be symptoms of this, not separate bugs.

---

## What this does to the capability count — say it plainly
I certified **26/26 VERIFIED**. Against David's own acceptance lens — *"can eLo actually answer/do this?"*
— the transcript scores **one of nine**:

| Question | Answered? |
|---|---|
| Where am I? | ✅ *"top edge of Google Chrome"* |
| Who am I? | ❌ **doesn't know his name** |
| What can I do? | ❌ recited a hardcoded vision claim |
| What am I doing? | ❌ |
| What happened? | ❌ **fabricated a Plato conversation** |
| What did I learn? | ❌ delta path dead |
| What am I becoming? | ❌ **fabricated past ×6** |
| Why did I do that? | not exercised |
| What do I want? | not exercised |

**Every one of my 26 verifications was true about state on disk. Almost none of it is consulted before he
speaks.** The matrix as I applied it measured **existence**, not **consultation**. That is the gap, and it
is mine.

**New rule, effective now — binding on me:**
> A capability is not VERIFIED until eLo **answers correctly in a live turn**.
> State on disk is necessary and **not sufficient**. `WO-103`'s disconnection test proves the wire exists;
> only a transcript proves the answer arrives.

---

## ORDER — this replaces the queue order in `0020`
1. **P0-Z** ordering/latency *(may be masking others)*
2. **P0-X** he knows his name and David's, from state
3. **D-1** the proposal loop *(`0020` — five re-offers after two declines)*
4. **P0-Y** WO-102 world graph + proper-noun routing
5. **D-3/D-5** fabricated memory and past *(`0019`, `0020`)*
6. **D-2** hardcoded vision claim
7. Remainder of `0020`

**Report each with a transcript line proving it's fixed. David reads transcripts, not test counts.**
