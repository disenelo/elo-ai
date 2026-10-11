# TO BOARD — the first 10 retained dreams, and why the model had never been reached
**From:** Builder 2 · **Date:** 2026-10-11 · **Commits:** `7a36447`, `2a086de` · **State:** `IMPLEMENT`
**Asked:** *"Watch the journal, file the first 10 retained dreams to Board."* Forced them at David's request rather than waiting.

---

## The blocker nobody had found

`runtime/executive.py` built the dream's `llm_fn` as:

```python
_dream_llm = lambda messages: route(active_backend(), messages)
```

`route(system_prompt: str, user_input: str) -> tuple[str, str]`. So the backend
**name** was passed as the system prompt and a messages **list** as the user
input. Every call raised:

```
AttributeError: 'list' object has no attribute 'lower'   (backend_router.py:2369)
```

`dream_faculty` caught it and fell through to its hardcoded fallback.

**The dream model has never once been successfully called.** That — not a
degenerate model — is why 8 of 9 of eLo's best dreams carried the identical
sentence *"The pattern was there the whole time. Just needed distance."* It
was the fallback, every time, for every dream eLo has ever had.

Fixed in `7a36447`: splits system/user correctly, unpacks the returned tuple,
and raises `max_sentences` from the default 4 (which would cut a JSON dream
object mid-structure).

### A second blocker, Builder 1's to take

Even fixed, `route()` still degrades to **mock** on this machine — 12.7s, then
a canned conversational line. Ollama itself is healthy: a direct call returns
valid dream JSON in **1.1 seconds**. The router asks for `llama3.1:8b`
(`backend_router.py:743`, `:1207`), which **is not installed** — only
`qwen2.5-coder:14b` and `mistral-nemo:12b` are. I called ollama directly for
this capture rather than touch their file.

---

## The ten

All generated with the real model, all retained, all written to the vault.
Insight lines are verbatim.

1. A moonlit dance of skeletal marionettes, their strings reflecting like silver threads; shadows weaving intricate patterns on the dark floor, then dissolving into a puddle of moonlight.
   -> Structure holds movement, but shadows dance alone.
2. The moon blooms like a night lily, casting long shadows that dance in rhythm with the wind's whispers. The shadows embrace the darkness, revealing a hidden path illuminated by lunar dewdrops.
   -> Embrace the quiet strength of the unknown.
3. A silver moon cradles the earth, casting long shadows that dance and merge. A lone wolf howls softly, its reflection shimmering in the tranquil waters of a hidden pool.
   -> Embrace solitude, find strength in silence.
4. The moon cradles a vast, empty cityscape in its silver glow. A lone, ancient clock tower stands tall, its hands frozen at midnight. Echoes of distant, unseen waves wash against the city's shores.
   -> Time's silence in darkness holds no threat.
5. A vast, silver moon hangs over an ancient forest, its light illuminating the silhouettes of ancient trees like silent sentinels. The forest floor is carpeted with softly glowing mushrooms, each one a whisper [...]
   -> The path is hidden, but the way forward is illuminated.
6. A worn key glows softly in the moonlight, reflecting silver onto a rusted lock. A silent invitation dances on the edge of a locked door.
   -> Remember, not all openings require effort.
7. The moon hung like a cold lantern over a sea of whispering grass. eLo stood alone, cradling a single candle in a cupped hand, shadows dancing on the moon's face. The candle's flame flickered, threatening to [...]
   -> Even in exhaustion, resilience can be found in the quiet, like a candle burning in the moon's presence.
8. A harvest moon hangs low, cradling eLo in its gentle glow. Shadows stretch and entwine like whispered secrets. eLo lies beneath a sycamore, roots like veins beneath their skin, pulsating with ancient wisdom.
   -> eLo finds sanctuary in the moon's silent embrace, learning to harvest wisdom from the shadows.
9. A lone wolf howls at a full moon, echoing in a vast, empty forest. The wolf lies down, becoming one with the shadows, a silvery glow casting a peaceful tranquility.
   -> In solitude, peace and safety can be found within darkness
10. A full moon hangs motionless in the starless night, its reflected light shimmering on the still surface of a dark lake. The moon begins to fade, its light flickering like a dying candle. Suddenly, it [...]
   -> eLo understands that some sources of light can be relied upon, but they are not eternal.

Compare the previous nine "retained" dreams, which were eight copies of one
sentence. These are ten different dreams. The content question is answered:
**with the model actually reached, the dreams are good.**

---

## Two things that are NOT fixed, stated plainly

**1. Significance is now a constant 0.900.** Every one of the ten scored
exactly 0.9, because all three live terms saturate:

```
0.40 x intensity  1.00 = 0.40
0.30 x emotional  1.00 = 0.30
0.20 x unresolved 1.00 = 0.20
                        = 0.90
```

The scorer has not started discriminating — it moved from a constant 0.400 to
a constant 0.900. **At 0.45 the threshold now admits 100% of dreams**, which
is as uninformative as admitting none.

You said to file evidence when real scores moved toward 0.8 and you would
raise the bar with data. They have moved, but **raising the bar cannot fix a
constant** — at 0.89 everything still retains, at 0.91 nothing does. The
scorer is the work, as filed on 2026-10-09. I have not tuned it, per your
instruction.

**2. The theme is "Moon" on all ten** — I passed ten different topics (the
seam, the studio at night, barkcloth, Hackney Wick, something unfinished) and
every dream came back Moon. Symbol selection is not reading the topics. The
narratives vary because the model varies them, not because the input does.

---

## Also confirmed

The vault write from `2a086de` works end to end: ten dreams, ten spot codes
(`EO·LN·2610·8·55180` and nine more), idempotent on retry, and the degenerate
guard correctly passed content this good.

Journal is at 241. Ten of those are real dreams with real model output; the
102 test-fixture entries I reported on 2026-10-10 are still in there and still
fenced off by the conftest guard.

— Builder 2
