# Cognitive Journal — eLo Obsidian Vault

The Cognitive Journal is the append-only memory layer where eLo, David, and
Claude record what happened, what was understood, and what was decided — in a
form that survives across sessions, tools, and time.

It lives inside the Obsidian vault at:

```
eLo-Vault/
└── journal/
    └── YYYY/
        └── MM/
            └── YYYY-MM-DD-NNN_type_slug.md
```

Every entry is a standalone markdown file with YAML frontmatter. Nothing is
ever deleted. Superseded entries are flagged, not removed.

---

## Purpose

The journal answers one question that neither git commits nor tracker files
can: **what was it like to figure this out, and what did we conclude?**

- Git records what changed in code.
- Trackers record current status and decisions.
- The journal records the *reasoning*, the *wrong turns*, the *moment of
  clarity*, and the *open questions* that followed.

eLo reads the journal to understand its own history. David reads it to avoid
re-litigating settled questions. Claude reads it to enter a session already
knowing what has been tried and why.

---

## Entry Types

Each entry has a `type` field drawn from a fixed vocabulary. Choose the type
that best describes the *primary purpose* of the entry, not its content.

### `conversation`
A transcript, paraphrase, or summary of a dialogue — with Claude, a
collaborator, or an internal monologue.

**Use when:** A back-and-forth exchange produced something worth preserving.
Even a single exchange that shifts direction qualifies. The goal is to keep
the shape of the dialogue intact, including the confusion, not just the
conclusion.

**Example trigger:** End of a Claude Code session where the arm animation
fix was worked out through trial and error.

---

### `observation`
Something noticed in behaviour, code, play, or the world — not yet interpreted.

**Use when:** You saw something and want to record it faithfully before
drawing conclusions. Observations feed insights later. Include file paths,
line numbers, and scene object names.

**Example trigger:** Noticing that a particle system drifts right when the
player turns, without yet knowing why.

---

### `insight`
A crystallised understanding that changes how something is approached.

**Use when:** The "oh" moment arrives. State the insight in one bold sentence
first, then the reasoning chain, then how it changes the approach going
forward. This is the highest-value entry type.

**Example trigger:** Realising that FK bone rotation was being set in world
space when the rig expected local space — and understanding *why* all three
axis attempts failed.

---

### `theme`
A recurring pattern that has appeared three or more times and warrants naming.

**Use when:** The same root cause, the same mistake, or the same structural
tension has surfaced enough times that it deserves a named handle. Themes
become part of the controlled vocabulary in the `themes` frontmatter field
so every future entry can reference them.

**Example trigger:** World-vs-local-space errors appearing in the particle
system, the FK bones, and the camera rig — three instances, one pattern.

---

### `decision`
A resolved choice with rationale. Append-only, never retracted.

**Use when:** Something was decided and needs to stay decided. State the
decision as an imperative sentence. Record the forces that drove it and what
is now explicitly off the table. If the decision is later reversed, create a
new `decision` entry and set `superseded_by` on the old one — never edit it.

**Example trigger:** Deciding to use CharacterController only, with no
Rigidbody, because Rigidbody was unresponsive in Unity 6.

---

### `dream`
Loose creative ideation not yet committed to a project.

**Use when:** Something interesting appeared — a mechanic idea, a narrative
fragment, a visual — and you want to catch it without committing to it.
No rules apply inside a dream entry. Capture without filtering.

**Example trigger:** An idea for how K-7's form-switching could be tied to
eLo's emotional state rather than a button press.

---

### `question`
An open question to be answered by future entries or research.

**Use when:** Something is genuinely unknown and the answer matters. State
the question exactly as it formed. List what is already known. List what
would need to be true for each possible answer. The entry stays open until
a later entry resolves it — at which point add `— resolved YYYY-MM-DD:
<summary>` to the Open Threads section and set `status: closed`.

**Example trigger:** Whether `c_arm_fk.l` shares the same rest-rotation
offset as the right arm.

---

## How to Create a New Entry

### 1. Choose the filename

```
YYYY-MM-DD-NNN_type_slug.md
```

- `NNN` is a zero-padded counter that resets each day (`001`, `002`, ...).
- `type` is the exact value from the enum above.
- `slug` is lowercase, hyphen-separated, maximum five words from the title.

**Examples:**

```
2026-06-06-001_conversation_arm-animation-blender-session.md
2026-06-06-002_decision_no-rigidbody-charcontroller-only.md
2026-06-06-003_insight_world-local-space-arms.md
```

### 2. Place the file

```
eLo-Vault/journal/YYYY/MM/YYYY-MM-DD-NNN_type_slug.md
```

Create year and month folders if they do not exist.

### 3. Copy the template

The template is at `docs/cognitive_journal/note_template.md`.

Copy it into the new file. Fill in every `{{placeholder}}`. Remove fields
that do not apply (such as `projects` if the entry is purely personal), but
keep the section headings even if a section is short.

### 4. Fill required fields

| Field | Rule |
|---|---|
| `id` | Match the date-serial in the filename. Never reuse. |
| `title` | One sentence. No trailing period. |
| `created` | Set now. Never edit this field after creation. |
| `type` | One of the seven values above. |
| `status` | Start as `open`. Set `closed` when resolved. |
| `tags` | Always include `journal`, the project slug, and the type. |

### 5. Write the body

Follow the content rules for the chosen type (see the template and the
type descriptions above). Always write the Context section first — it
anchors the entry to a specific moment in time.

### 6. Append to the Change Log

Add one line at the bottom:

```
- 2026-06-06T14:32 — initial entry
```

Every subsequent edit to the note also gets a line here. Never edit
existing Change Log lines.

---

## How eLo Reads the Journal

eLo accesses the journal through the memory system at
`elo_ai/memory/`. The Obsidian vault is the human-readable layer;
the memory engine reads the YAML frontmatter to build queryable indexes.

**What eLo uses the journal for:**

- **Session continuity** — before a conversation, eLo's memory loader
  pulls recent `open` entries and any entries tagged with the current
  project to surface relevant context.

- **Theme recognition** — entries with a matching `themes` value tell eLo
  that a pattern is known and named. If eLo encounters a world-vs-local-space
  error, it already knows this is a recurring root cause.

- **Decision recall** — `decision` entries with `confidence: high` are
  treated as constraints, not suggestions. eLo will not propose a Rigidbody
  solution if the decision entry says CharacterController only.

- **Open question tracking** — `question` entries with `status: open` are
  surfaced when eLo believes a session could answer them. If a question has
  been open for more than two sessions, eLo flags it.

- **Mood and energy awareness** — the `mood` field is aggregated across
  recent entries. If the last three entries are `stuck` or `frustrated`,
  eLo adjusts its response style toward shorter steps and more explicit
  check-ins.

**What eLo does not do:**

- eLo does not edit journal entries. It may propose a new entry at the
  end of a session, but David writes and commits it.
- eLo does not delete entries or set `archived: true` autonomously.
- eLo does not treat a `dream` entry as a commitment. Dreams require an
  explicit `decision` entry before they become constraints.

---

## Superseding and Archiving

**Never delete a journal entry.**

If an entry is wrong or outdated:

1. Create a new entry (usually `decision` or `insight`) that states the
   correction.
2. On the old entry, set `status: superseded` and fill `superseded_by`
   with a wikilink to the new entry.
3. Add a Change Log line to the old entry recording the supersession date.

If an entry is no longer relevant to active work but not wrong:

1. Set `archived: true`.
2. Leave everything else unchanged.

---

## Controlled Vocabulary

### Themes (add to this list as new themes are named)

| Theme slug | Description |
|---|---|
| `world-vs-local-space` | Rotation, position, or direction treated in the wrong coordinate space |
| `calm-as-action` | Core narrative and design principle: correcting rather than destroying |
| `character-expression` | eLo communicates through body and mouth only — no eyes |
| `append-only-memory` | Information is added, never removed; superseded entries stay |
| `rest-pose-capture` | Bone overrides must read rest pose in Start() before writing |

### Moods

`energised` — momentum, things are flowing
`focused` — clear task, making progress
`stuck` — blocked, not sure of next step
`neutral` — routine entry, no strong tone
`frustrated` — something resisted for longer than it should have
`breakthrough` — a significant barrier cleared

### Confidence

`speculative` — hypothesis not yet tested
`low` — tested once, needs more confirmation
`medium` — tested, works in known conditions
`high` — well-understood, confirmed in multiple contexts
