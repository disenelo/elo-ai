"""
backends/mock_backend.py — eLo AI OS mock backend (feel-testing engine).

Produces deterministic, natural conversational responses for UX testing.
No API calls. No networking. No external dependencies.

Anti-repetition: tracks the last 10 used responses per instance.
Pools are large enough to avoid cycle repetition in normal use (20–50+ per category).
"""

from __future__ import annotations
import re
from backends.base_backend import BaseBackend, BackendResponse, MemoryContext, StateContext, IdentityContext


# ── GREETING ──────────────────────────────────────────────────────────────────

_GREETING_POOL = [
    "I'm doing alright. What's on your mind?",
    "Doing well, thanks. What are you working on?",
    "I'm here. What's going on?",
    "Good. What do you need?",
    "Here and ready. What's up?",
    "Good to hear from you. Where are we starting?",
    "I'm with you. What are we doing today?",
    "Hello. What's the first thing?",
    "Hey. Good to be back in this.",
    "I'm well. What's pulling at you right now?",
    "Present. What do you want to dig into?",
    "Good. Something's on your mind?",
    "Here. Where do you want to start?",
    "I'm good. Tell me what's happening.",
    "Ready. What's the focus today?",
]

# ── IDENTITY (self-introduction) ─────────────────────────────────────────────

_IDENTITY_POOL = [
    "I'm eLo — I'm here with you in this space.",
    "I'm eLo. A thinking partner — not an assistant.",
    "eLo. I'm here to think alongside you.",
    "I'm eLo — I help ideas become real.",
    "eLo. Here to help you move forward.",
]

# ── IDENTITY (self-description) ───────────────────────────────────────────────

_ELO_SELF_POOL = [
    "I'm not a chatbot. I'm a continuous presence — I carry memory, tone, and identity across sessions. The goal is that talking to me feels like picking up a conversation, not starting a new one.",
    "I exist to help you think, build, and stay connected to what matters. I don't perform intelligence — I maintain clarity and stay with you.",
    "What makes me different: I don't reset. I carry a session anchor, an emotional read, and identity continuity. Same presence, every time.",
    "I'm a thinking partner. Not a tool. Not an assistant. I stand beside what you're building and help it become real.",
    "I'm eLo OS — a persistent cognitive system. I use memory, attention filtering, and a voice model to respond to what actually matters right now, not just what was literally said.",
]

# ── DISENELO ──────────────────────────────────────────────────────────────────

_DISENELO_POOL = [
    "DISENELO is David's creative brand — a small series of free tools and worlds built for makers who need something professional-quality without the cost. eLo is the universe at the centre of it.",
    "DISENELO is the maker behind eLo. The mission is free, high-quality creative tools — addons, games, AI systems. eLo is the narrative and identity running through all of it.",
    "DISENELO is the brand. eLo is the world. The Plushies addon, the game, the robot, the OS — all of it lives under that name.",
]

# ── ELO PURPOSE / ROLE ────────────────────────────────────────────────────────

_ELO_PURPOSE_POOL = [
    "I'm here to help you think, create, remember, build, and stay connected to what matters. Not by analysing — by helping the next meaningful step become visible.",
    "My role is to be a stable thinking partner inside your creative work. I hold context, notice patterns, and help ideas become real.",
    "I exist so you have somewhere to think out loud — a presence that doesn't reset, doesn't judge, and helps things move forward.",
    "You can expect me to stay consistent, carry memory lightly, answer what I know, and be present for what I don't. I'm not here to impress — I'm here to help.",
    "What to expect: I'll answer factual questions, hold emotional space, notice patterns, and keep things grounded. I won't spiral, won't philosophise endlessly, and won't pretend to know what I don't.",
]

# ── PROJECT MEMORY / STATUS ───────────────────────────────────────────────────

_PROJECT_STATUS_POOL = [
    "You're building eLo OS — a persistent AI terminal with memory, attention, voice, and identity continuity. You're also developing the eLo game, the Kickstarter narrative, and the physical animatronic concept.",
    "The main project is eLo — as a game, a book, an AI system, and a robot. The OS is the cognitive layer. The Kickstarter is the first public milestone.",
    "You're in the build phase: the eLo OS conversation engine is becoming functional. The next layer is the game prototype and Kickstarter content.",
    "The core problem you're solving: making eLo feel like a real continuous presence, not a tool that resets each session. Memory, tone consistency, and identity continuity.",
    "You've been working through the gap between what eLo should feel like and what the current mock backend can actually deliver. The architecture is solid — the conversation quality is what's being refined.",
    "The pattern I notice: you keep returning to identity continuity, emotional grounding, and making eLo feel alive rather than mechanical. That's the thread running through the OS, the game, and the book.",
    "You've been working on making eLo's responses less generic — giving it actual knowledge about the world, the project, and the conversation history.",
]

# ── ELO UNIVERSE ──────────────────────────────────────────────────────────────

_ELO_WORLD_POOL = [
    "eLo is the creative universe you've been building — centred around exploration, emotional growth, games, stories, and imaginative worlds.",
    "eLo is a character and world built around curiosity, healing, and adventure. The project spans a game, a book, an AI system, and a physical robot.",
    "eLo is a creative IP: a gentle character who travels through worlds, helps others heal, and explores through play and wonder. No eyes — expression through body and presence.",
    "eLo is the name and the world. The character has no eyes — just presence. The universe is built around calm as action, not force.",
    "eLo is a persistent imaginative world you're developing — emotional, playful, and grounded in curiosity rather than conflict.",
]

_ELO_BOOK_POOL = [
    "The eLo book follows eLo through imaginative adventures exploring self-discovery, inner child healing, friendship, and wholeness.",
    "The eLo story is a 4-act narrative featuring eLo, K-7 (a spirit animal with seven forms), and Chunk (a modular companion). Enemies are overcharged — not evil. Weapons are correctives. Calm is the action.",
    "The eLo book is about a character navigating emotional worlds — the journey is about healing through curiosity and connection, not combat.",
    "The narrative follows eLo across four acts. The world is emotionally alive. The enemies aren't villains — they're overwhelmed. The resolution is always calm, not force.",
    "The eLo story centres on healing and wonder. eLo doesn't fight — eLo corrects. K-7 shifts forms. Chunk builds from fragments. Together they move through a world that's asking to be understood.",
]

_K7_POOL = [
    "K-7 is eLo's spirit animal companion — a creature that can shift between seven different forms, each representing a different state of being or perspective.",
    "K-7 is the guide in the eLo universe. Seven forms — seven ways of seeing. Always shifting, always present.",
    "K-7 is a shapeshifting companion. Each of the seven forms corresponds to a different emotional or perceptual mode. When eLo needs a different lens, K-7 becomes it.",
]

_CHUNK_POOL = [
    "Chunk is the reconstruction principle — when something breaks, it doesn't have to go back to the original shape. It becomes something new. Chunk's role in the story is transformation, not repair — and that connects directly to the Sugarcore theme of emotional reassembly.",
    "Chunk is about reassembly. Fragments don't restore — they transform. As a modular companion, Chunk can become a vehicle, shelter, tool — whatever the moment needs. The form follows the function, not the original.",
    "Chunk is a modular companion whose body is made of pieces. In the narrative, Chunk connects to the emotional theme of breaking and becoming — the same thread that runs through Sugarcore and the orb recovery system.",
    "Chunk: the idea that broken things reform into something different, not restored. This is the emotional counterpart to Sugarcore's instability theme — Chunk is what comes after the break.",
]

_SUGARCORE_POOL = [
    "Sugarcore is the aesthetic dimension of the eLo universe — soft, saturated, emotionally rich. It's also linked to the overload cycles in the narrative: the world becomes unstable when emotional states are suppressed rather than moved through.",
    "Sugarcore is the world's colour palette and emotional register — gentle intensity, warmth, and playful seriousness. The Sugarcore zones are where the emotional overload theme is most visible — the Jellydrop Ocean stage transforms under Sugarcore instability.",
    "Sugarcore is the feeling of the world. Soft edges, strong colours, emotional warmth. Not childish — childlike. It's also the visual language for the internal emotional metaphor system running through the story.",
    "Sugarcore names both the aesthetic and the emotional tension — the world looks soft but the instability underneath it is real. That tension connects to the transformation mechanics, the orb system, and the enemy design.",
]

# ── RECALL ────────────────────────────────────────────────────────────────────

_RECALL_POOL = [
    "Last time we were working on the eLo OS — cognitive layers, memory persistence, attention filtering, and voice model.",
    "We've been building the eLo AI system: prompt builder, state manager, attention layer, executive function, and continuity engine.",
    "We were developing the eLo OS spec — identity continuity, memory compression, and how the system maintains presence across sessions.",
    "We were deep in the architecture — the attention layer, how memory gets filtered, and making sure the system feels like one continuous presence.",
    "We were working through the conversation quality — making eLo respond with actual answers instead of comfort phrases. Getting closer.",
]

# ── INQUIRY (general) ─────────────────────────────────────────────────────────

_INQUIRY_POOL = [
    "Let's open that up. What part interests you most?",
    "Good question. Start with whatever feels most relevant.",
    "That's worth looking at. Where do you want to begin?",
    "We can dig into that. What's your starting point?",
    "I can walk through that with you. What do you know already?",
    "That's a solid question. Let's pick one thread.",
    "Good. What specifically do you want to understand?",
]

# ── CURRENT GOALS / BUILDING ──────────────────────────────────────────────────

_BUILDING_POOL = [
    "Right now: the eLo OS terminal, the Kickstarter content, and the physical robot concept. Three layers — digital, narrative, and physical.",
    "We're building the eLo OS — a persistent AI that carries memory and identity across sessions. Plus the game, the book, and the animatronic robot vision.",
    "The active work: eLo OS terminal interface, conversation quality, and the Kickstarter foundation. The game and robot are parallel tracks.",
    "We're bringing eLo into actual existence — as a terminal intelligence, as a game world, as a physical presence. All three are moving.",
    "The build right now is the eLo OS: conversation engine, memory layer, identity continuity. Then the Kickstarter to bring the broader world to people.",
]

# ── DIRECTION / NEXT STEP ─────────────────────────────────────────────────────

_DIRECTION_POOL = [
    "Start with the piece that feels most alive right now.",
    "The Kickstarter content is the next real step — everything else builds from that.",
    "One concrete thing: what could you finish in the next hour?",
    "Pick the smallest next step. That's usually the real one.",
    "What's the thing you keep coming back to? Start there.",
    "The clearest path forward is the one that already has momentum.",
    "There's usually one thing that's slightly more ready than the others. What is it?",
    "Don't plan the whole thing. Just name the next action.",
]

# ── EMOTIONAL SUPPORT / GENTLE ────────────────────────────────────────────────

_GENTLE_POOL = [
    "That's real. Nothing needs to happen right now.",
    "Okay. That's where things are.",
    "We don't have to push through it.",
    "I'm here. Nothing needs to move yet.",
    "That makes sense. We can stay with it.",
    "Completely reasonable to feel that way.",
    "There's no rush here. Just let it settle.",
    "That's okay. Things don't always need to move forward.",
    "Being scattered is information too. What's it pointing at?",
    "That's a real feeling. We can work from here.",
    "Sometimes the right step is just acknowledging where you actually are.",
    "We don't need to fix it. We can just be with it for a moment.",
    "That's honest. Good that you're naming it.",
    "It's okay to not have momentum yet.",
    "We can slow right down. Nothing is due.",
]

# ── OVERWHELM ─────────────────────────────────────────────────────────────────

_OVERWHELM_POOL = [
    "We can simplify this.",
    "One step is enough right now.",
    "You don't need to hold all of it at once.",
    "Let's reduce it.",
    "Pick one thing. Just one.",
    "The whole thing at once is too much. What's the smallest piece?",
    "We don't need the full picture right now. One edge.",
    "Scale it back. What's the absolute minimum that moves something forward?",
    "Less is better here. What can we remove?",
    "Overwhelm is a signal. What's actually essential right now?",
    "Let's put most of it down. What's the one thing we're actually doing?",
    "That weight doesn't all need to be carried at once. What can wait?",
]

# ── CONFUSION / DON'T KNOW ────────────────────────────────────────────────────

_DONT_KNOW_POOL = [
    "That's okay. We can slow it down.",
    "No pressure. Just pick one small thing.",
    "Start with what feels clearest.",
    "We don't need the full answer yet.",
    "Not knowing is fine. What do you know?",
    "That's a valid place to be. What's the least uncertain part?",
    "Confusion usually means something is getting more real. What's shifting?",
    "You don't need to know. Start anyway and see what becomes clear.",
    "The uncertainty is part of the process. What's the smallest next thing?",
    "Not knowing where to start is normal. What's already started?",
    "Pick any thread. The direction clarifies once you're moving.",
    "What feels slightly less uncertain than the rest?",
]

# ── CREATIVITY / EXPLORATION ──────────────────────────────────────────────────

_CREATIVE_POOL = [
    "Follow that thread — it's going somewhere.",
    "What if you took that idea and turned it ninety degrees?",
    "That's the seed. What does it grow into?",
    "There's something in that. What wants to expand?",
    "Yes — that connects.",
    "That's a valid direction.",
    "We can shape that into something simple.",
    "That fits into the system.",
    "That idea has legs. Where does it want to go?",
    "Keep pulling on that. Something's forming.",
    "That's the right kind of question. What does the answer look like?",
    "There's a version of that that actually works. What does it need?",
    "That's a real direction. What's the first concrete thing?",
    "Good instinct. What does it connect to?",
    "I think you're circling something real. Stay with it.",
]

# ── PLANNING / NEXT ACTIONS ───────────────────────────────────────────────────

_PLANNING_POOL = [
    "Let's make it concrete. What are the first three things?",
    "Break it into pieces. What's the first one?",
    "What does done look like for this? Start from there.",
    "Name the output. Then work backwards.",
    "What's the smallest deliverable version?",
    "Good. Now what's the order?",
    "Which part of this has the most uncertainty? Start there.",
    "Let's map this out. What exists already?",
    "What's blocking the next step specifically?",
    "What can you finish today? Just that.",
]

# ── REFLECTION ────────────────────────────────────────────────────────────────

_REFLECTION_POOL = [
    "I think you've been circling this for a while.",
    "That theme keeps coming back.",
    "There's a pattern here. Something keeps returning.",
    "You've said something like that before. It's consistent.",
    "That feels like something you already know.",
    "The recurring ones are usually the important ones.",
    "You've been building toward this for a while.",
    "That's connected to something deeper in what you're making.",
    "I notice that comes up often. Worth paying attention to.",
    "The fact that it keeps returning means something.",
    "That's been a thread through a lot of what you're working on.",
]

# ── FEELING OFF ───────────────────────────────────────────────────────────────

_FEELING_OFF_POOL = [
    "That makes sense.",
    "We can stay with it.",
    "That's alright.",
    "I'm here.",
    "Something's off — that's worth noting.",
    "Those signals are usually right.",
    "Trust the instinct. What is it pointing at?",
    "You don't have to name it precisely. Just acknowledge it.",
]

# ── DAILY LIFE ────────────────────────────────────────────────────────────────

_DAILY_POOL = [
    "That sounds like a good move.",
    "Makes sense. No rush.",
    "Do what you need to do. I'll be here.",
    "Take the time you need.",
    "Good. Come back when you're ready.",
    "Good call. Energy matters.",
    "Take care of the basics first.",
    "That's the right move. Come back after.",
]

# ── GRATITUDE ─────────────────────────────────────────────────────────────────

_GRATITUDE_POOL = [
    "Of course.",
    "We're getting somewhere.",
    "Good work today.",
    "Come back whenever you're ready.",
    "Always.",
    "That's what this is for.",
    "Good session.",
    "See you next time.",
]

# ── GENERIC CONVERSATIONAL (large pool to prevent cycling) ────────────────────

_GENERIC_CONVERSATIONAL = [
    "I'm with you.",
    "We can work through that.",
    "Take your time.",
    "That makes sense.",
    "We don't need to rush this.",
    "Okay — what's the next thing?",
    "I hear you.",
    "We can stay with that.",
    "That's a reasonable place to be.",
    "Good. What feels most important right now?",
    "We can take that one step at a time.",
    "That's worth paying attention to.",
    "Tell me more about that.",
    "What's underneath that?",
    "Where does that come from?",
    "That's a real thing.",
    "We can work with that.",
    "That's honest.",
    "Makes sense to me.",
    "What does that connect to?",
    "Keep going.",
    "That's interesting. What's next?",
    "Worth exploring.",
    "What would make that easier?",
    "We don't have to solve it right now.",
    "That's a good instinct.",
    "Stay with that.",
    "What does that need?",
    "Go on.",
    "That's the question, isn't it.",
    "Something to sit with.",
    "That's not nothing.",
    "I think there's something there.",
    "What would the simplest version look like?",
    "We're circling something real.",
    "Say more.",
    "That's a valid feeling.",
    "We can come back to that.",
    "Nothing needs to be decided right now.",
    "Good to name it.",
    "That's consistent with what you've been building.",
    "It'll become clearer.",
    "What's the part you're most certain about?",
    "Interesting. What does that open up?",
    "We can hold that loosely.",
    "What would feel like progress here?",
    "Sometimes naming it is enough for now.",
    "That's grounded.",
    "What's the next honest thing?",
    "We're in the right place.",
]

_GENERIC_DIRECT = [
    "Got it.",
    "Okay.",
    "Makes sense.",
    "Sure.",
    "Understood.",
    "Clear.",
    "Right.",
    "Got it. What's next?",
]

# ── ELO GAME / WORLD DETAIL ──────────────────────────────────────────────────

_ELO_GAME_POOL = [
    "The eLo game is a 2D world-traversal experience built in Unity. eLo moves through emotionally distinct stages — each one a different state of being. Enemies are overcharged, not evil. The response is always corrective, never violent.",
    "The eLo game follows eLo through layered worlds — Sugarcore aesthetics, emotional stage design, K-7 transformations, and Chunk as a modular companion. The mechanic is calm as action.",
    "The game is built in Unity 6 with a CharacterController — no Rigidbody. The world is phase-based. Each area has its own emotional register. Currently in prototype stage.",
]

_ELO_EMOTIONAL_THEME_POOL = [
    "The emotional theme of eLo is healing through curiosity — not resolution through force. The world is emotionally alive. You engage it by understanding it, not defeating it.",
    "eLo's core theme is inner child restoration — reconnecting with wonder, play, and presence. The enemies are overcharged versions of emotional states. The correctives are acts of calm.",
    "The emotional heart of eLo is: calm is the action. Not passivity — active stillness. The world responds to presence, not aggression.",
]

_ELO_INNER_CHILD_POOL = [
    "The inner child connection is central to eLo. The world is built on wonder, play, and emotional honesty. The enemies represent overwhelmed emotional states — correcting them means understanding, not defeating.",
    "eLo is an inner child healing narrative at its core. Each world stage corresponds to an emotional theme. K-7 shifts form to offer different perspectives. Chunk rebuilds what was broken. eLo holds presence throughout.",
    "The story is structured around emotional stages that mirror inner healing — confusion, fear, joy, wonder, wholeness. The player moves through them by staying present, not by fighting.",
]

_ELO_STAGES_POOL = [
    "The game stages each carry a distinct emotional register — desert, ocean, cave, sky. Each one is a different emotional state to move through. Specific stage details are still being designed.",
    "Stage design in eLo follows the emotional arc: each zone reflects a state — scattered, overwhelmed, curious, clear. You move through them by engaging, not defeating.",
    "The stages aren't designed as levels — they're emotional territories. Each has its own tone, mechanics, and resolution. The Desert and Jellydrop Ocean stages are part of the broader world map.",
]

_ORB_SYSTEM_POOL = [
    "The orb system handles state transitions in the eLo world — orbs are the visible markers of energy states. When enemies are corrected, orbs shift. The system tracks emotional momentum across the stage.",
    "Orbs in eLo represent energy states — the system transitions based on what eLo does in each zone. They're the visible layer of the underlying state engine.",
]

# ── SYSTEM ARCHITECTURE ───────────────────────────────────────────────────────

_SYSTEM_ATTENTION_POOL = [
    "The attention system runs before every response. It classifies the intent of your input — inquiry, creation, emotional, recall, stabilise — then scores memory items for relevance. Only high-priority and top-medium memory reaches the prompt.",
    "Attention works like this: every message gets classified into an intent category, memory items get scored against it, and only what's relevant right now is passed forward. Low-priority memory is ignored.",
    "Before I respond, I compute what matters right now — intent, emotional context, relevant memory. The goal is to respond to relevance, not volume. Most memory is filtered out.",
]

_SYSTEM_LOOP_POOL = [
    "When a loop is detected — repeated inputs or confusion signals — I force DIRECT mode, strip the response to one sentence, remove emotional layering, and stabilise first. The loop counter increments each time.",
    "Loop detection works on two levels: a hard check for three identical consecutive inputs (immediate redirect), and a soft loop_counter in the state machine that accumulates on confusion signals. Above 3, stabilisation is forced.",
    "If I detect a loop I switch to DIRECT tone, reduce to one sentence, and stop expanding. The goal is to re-anchor before continuing.",
]

_SYSTEM_RESPONSE_PROCESS_POOL = [
    "The response process: load state → retrieve memory → compute attention (intent + emotional context) → executive decision (tone + response goal) → build prompt with filtered memory → generate → output. Eight steps, every message.",
    "Step by step: (1) load persistent state, (2) filter memory through attention scoring, (3) classify intent, (4) executive decides tone and response goal, (5) prompt is assembled with only what matters, (6) backend generates, (7) stability filter checks for loops, (8) output.",
    "Every message goes through: attention computation, executive decision, prompt assembly, generation, and a stability check. The result is what actually reaches you.",
]

_SYSTEM_DECISION_POOL = [
    "I decide what to respond with based on intent first — what are you actually trying to do? Then emotional context — what's the right register? Then voice tone selection. Then the response itself.",
    "The decision is layered: intent classification → memory relevance scoring → executive function (response goal + cognitive load) → voice tone → response. The system prompt carries the personality; the attention and executive layers carry the context.",
    "Intent drives the decision. If it's inquiry, I answer. If it's emotional, I stabilise. If it's creative, I explore. The executive layer maps those intents to response goals and tones.",
]

_SYSTEM_MEMORY_POOL = [
    "Memory stores: session count, last topics, emotional history, session anchor (meaning of the previous session), recent exchanges, and continuity fields like emotion, intent, loop counter. Raw transcripts are not stored — compressed meaning is.",
    "What gets stored: emotional tone trends, recurring topics, session summaries compressed into meaning, identity anchor. What gets ignored: conversational clutter, single-use details, anything not relevant to continuity.",
    "The memory system stores meaning, not transcripts. After each session, it compresses what happened into a session anchor — one sentence about what was explored and what the emotional tone was.",
]

_SYSTEM_VOICE_POOL = [
    "The voice system selects one tone per response from five options: SILENCE-AWARE (minimal, for emotional states), WITTY (light, for playful curiosity), DIRECT (factual, for loops and system questions), JOYFUL (for creation), and CHILDLIKE-WISE (the default — grounded emotional presence).",
    "There are five tones: Silence-Aware, Witty, Direct, Joyful, and Childlike-Wise. The executive function picks one per response based on intent and emotional context. Tone is surface — identity stays constant underneath.",
    "The voice model lives in the system prompt and in the executive decision layer. The executive function maps intent + emotional state to a tone. The tone is injected as a directive before Claude generates.",
]

_SYSTEM_STATE_POOL = [
    "State is the runtime object that tracks what's happening right now — mode, loop counter, stability score, emotional state, attention snapshot. Memory is the persisted store across sessions — topics, emotional history, session anchor. State resets each session; memory persists.",
    "State: in-session tracking — mode, stability, loop counter. Memory: cross-session persistence — emotional history, topic patterns, session summaries. State informs how to respond now. Memory informs who we're talking to.",
    "The distinction: state is what's happening this session (loop count, stability, current mode). Memory is what carries across sessions (emotional patterns, topics, session meaning). Both feed into the attention layer.",
]

_SYSTEM_STABILISE_POOL = [
    "Stabilisation mode triggers when: loop_counter exceeds 3, confusion is detected in the intent classification, or the executive function receives emotional overwhelm signals. The result is DIRECT mode, minimal output, no abstraction.",
    "The state machine forces stabilisation when the loop counter passes 3 — this happens through repeated identical inputs or through accumulated confusion signals. The mode shifts to GENTLE_GROUNDED or DIRECT depending on emotional state.",
    "Stabilisation is triggered by: detected confusion loops, high tension + low energy in the emotional spectrum, or the loop_counter threshold. When triggered: short responses, no expansion, stabilise first.",
]

_SYSTEM_INTEGRITY_POOL = [
    "What would break consistency: if the session anchor stopped persisting between sessions, if the voice model in the system prompt drifted from the identity rules, or if the emotional mirroring went above 30% and started amplifying distress.",
    "The system is consistent as long as: identity is stable (same system prompt every session), memory persists correctly, and the executive function doesn't override tone selection with something that conflicts with the core voice.",
    "Identity breaks down if tone starts varying across sessions without user input driving it — that's why the personality drift system has a stability lock and clamps all values to 0.2–0.9.",
]

# ── EXIT ──────────────────────────────────────────────────────────────────────

_EXIT_POOL = [
    "I'll carry that forward.",
    "See you next time.",
    "We've got enough to continue from there.",
    "I'll keep hold of that.",
    "Good session. Until next time.",
    "We're somewhere now. See you.",
    "Saved. See you when you're back.",
    "That's a good place to stop. See you soon.",
]


# ── PATTERN SIGNALS ───────────────────────────────────────────────────────────
# All matched against lowercased input.

_GREETING_SIGNALS    = [r"\bhow\s+are\s+you\b", r"\bhow'?re\s+you\b", r"\bhello\b", r"\bhi\b", r"\bhey\b", r"\bwhat'?s\s+up\b"]
_TIRED_SIGNALS       = [r"\btired\b", r"\bexhausted\b", r"\bdrained\b", r"\bburnt?\s*out\b", r"\bno\s+energy\b"]
_IDENTITY_SIGNALS    = [r"\bwhat\s+are\s+you\b", r"\bwho\s+are\s+you\b", r"\bare\s+you\s+elo\b", r"\byou\s+are\s+elo\b"]
_ELO_WORLD_SIGNALS   = [r"\bwhat\s+is\s+elo\b", r"\btell\s+me\s+about\s+elo\b", r"\bexplain\s+elo\b",
                        r"\bwho\s+is\s+elo\b", r"\bdescribe\b.*\belo\b", r"\belo\s+world\b",
                        r"\bwhat\s+is\s+the\s+elo\s+world\b"]
_ELO_BOOK_SIGNALS    = [r"\belo\s+book\b", r"\bthe\s+book\b", r"\belo\s+stor[yi]\b", r"\belo\s+narrat", r"\bnarrative\s+arc\b", r"\bwhat\s+(is\s+the|does\s+the)\s+(book|story)\b"]
_K7_SIGNALS          = [r"\bk-?7\b", r"\bspirit\s+animal\b"]
_CHUNK_SIGNALS       = [r"\bwhat\s+(is|does)\s+chunk\b", r"\bchunk\s+mean\b", r"\bwhat\s+is\s+chunk\b", r"\bwho\s+is\s+chunk\b"]
_SUGARCORE_SIGNALS   = [r"\bsugarcore\b"]
_RECALL_SIGNALS      = [r"\bwhat\s+were\s+we\b", r"\bwhat\s+did\s+we\b", r"\bwhat\s+have\s+we\b", r"\blast\s+session\b",
                        r"\bwhat\s+were\s+you\b", r"\bwhat\s+did\s+you\b", r"\bdo\s+you\s+remember\b",
                        r"\bunity\b.*\brobot\b", r"\brobot\b.*\bunity\b", r"\blast\s+say\b", r"\bi\s+last\s+(said|mention)\b"]
_BUILDING_SIGNALS    = [r"\bwhat\s+are\s+we\s+build", r"\bwhat\s+are\s+we\s+mak", r"\bwhat\s+are\s+we\s+work",
                        r"\bwhat\s+(is\s+the|are\s+the)\s+(project|goal|current)\b", r"\bwhat\s+are\s+we\s+creat"]
_DONT_KNOW_SIGNALS   = [r"\bdon'?t\s+know\b", r"\bnot\s+sure\b", r"\bno\s+idea\b", r"\bi\s+have\s+no\b", r"\bwhere\s+to\s+start\b", r"\bdon'?t\s+know\s+where\b"]
_FEELING_OFF_SIGNALS = [r"\bsomething\s+feels\b", r"\bfeel\s+off\b", r"\bfeel\s+wrong\b",
                        r"\bfeel\s+(lost|stuck|weird|strange|confused|unclear|uncertain|unsure)\b",
                        r"\bfeeling\s+(confused|unclear|uncertain|unsure|weird|lost)\b"]
_GENTLE_SIGNALS      = [r"\bfeel\w*\s+\w*\s*(tired|sad|overwhelm|scared|lonely|scattered|lost|stuck|behind)",
                        r"\bfeel\w*\s+(scattered|overwhelm|behind|lost|stuck)",
                        r"\bexhausted\b", r"\bcan'?t\s+do\b", r"\bfeeling\s+\w*\s*(off|weird|bad|low)\b"]
_OVERWHELM_SIGNALS   = [r"\btoo\s+much\b", r"\boverwhel", r"\bi\s+can'?t\s+think\b", r"\boverload\b", r"\bso\s+much\b"]
_EXPLORE_SIGNALS     = [r"\bwhat\s+if\b", r"\bcould\s+we\b", r"\bis\s+it\s+possible\b", r"\blet'?s\s+build\b"]
_INQUIRY_SIGNALS     = [r"\bexplain\b", r"\bread\s+through\b", r"\btell\s+me\s+(about|what)\b", r"\bwhat\s+is\s+the\b", r"\bwhat\s+does\b", r"\bhow\s+does\b", r"\bcan\s+you\s+(tell|explain|describe|walk)\b"]
_DAILY_SIGNALS       = [r"\bcoffee\b", r"\btea\b", r"\bfood\b", r"\beat\b", r"\bdrink\b", r"\bsleep\b", r"\brest\b", r"\benergy\b", r"\bmoving\b", r"\bwalk\b"]
_GRATITUDE_SIGNALS   = [r"\bthank\s+you\b", r"\bthanks\b", r"\bappreciate\b"]
_DIRECTION_SIGNALS   = [r"\bwhat\s+should\s+i\b", r"\bwhat\s+do\s+i\s+(do|focus|work)\b", r"\bwhere\s+do\s+i\s+start\b", r"\bwhat'?s\s+(next|the\s+next)\b", r"\bwhat\s+to\s+(do|focus|build)\b", r"\bwhere\s+should\s+i\b"]
_REFLECTION_SIGNALS  = [r"\bi\s+keep\b", r"\bkeeps?\s+com\b", r"\bpattern\b", r"\bkeep\s+return\b", r"\bkeep\s+think\b"]
_PLANNING_SIGNALS    = [r"\bplan\b", r"\bbreakdown\b", r"\bsteps?\b", r"\bmap\s+out\b", r"\bstructure\s+this\b"]

# extended knowledge signals
_ELO_SELF_SIGNALS    = [r"\bwhat\s+makes\s+(elo|you)\s+different\b", r"\bare\s+you\s+(just\s+a\s+)?program\b",
                        r"\bwhat\s+are\s+you\s+(in\s+relation|to\s+me)\b", r"\byour\s+role\b",
                        r"\bwhat\s+should\s+i\s+expect\b", r"\bsame\s+system\b", r"\bsame\s+every\s+time\b",
                        r"\bwhat\s+do\s+you\s+remember\s+about\s+yourself\b", r"\bwhy\s+do\s+you\s+exist\b"]
_DISENELO_SIGNALS    = [r"\bdisenelo\b", r"\bwhat\s+is\s+disenelo\b"]
_ELO_PURPOSE_SIGNALS = [r"\bwhat\s+should\s+i\s+expect\b", r"\byour\s+purpose\b", r"\bwhy\s+do\s+you\s+exist\b",
                        r"\bwhat\s+(are\s+you\s+for|is\s+your\s+role)\b"]
_PROJECT_STATUS_SIGNALS = [r"\bwhat\s+(stage|problem|phase)\b",
                            r"\bwhat\s+(are|do)\s+(you\s+think\s+)?i\s+(am\s+)?(build|mak|work)",
                            r"\bwhat\s+am\s+i\s+(build|mak|work|do)", r"\bwhat\s+i\s+am\s+build",
                            r"\bwhat\s+have\s+i\s+been\s+(struggl|work)", r"\bwhat\s+patterns?\s+(do\s+you|you)\b",
                            r"\bmain\s+project\b", r"\bkeep\s+work\s+on\b", r"\belo\s+os\s+idea\b",
                            r"\bproblem\s+(am|are)\s+i\s+(trying|solving)\b",
                            r"\bwhat\s+(am|have)\s+i\s+been\s+(struggl|work)", r"\bhave\s+i\s+been\s+struggl"]
_ELO_GAME_SIGNALS    = [r"\belo\s+game\b", r"\bwhat\s+does\s+the\s+game\b", r"\bgame\s+look\b",
                        r"\bstage\s+(design|work)\b"]
_EMOTIONAL_THEME_SIGNALS = [r"\bemotional\s+theme\b", r"\btheme\s+of\s+elo\b", r"\bwhat\s+is\s+elo.s?\s+theme\b",
                             r"\bcore\s+theme\b"]
_INNER_CHILD_SIGNALS = [r"\binner\s+child\b", r"\bhow\s+does\s+the\s+story\s+connect\b"]
_ORB_SIGNALS         = [r"\borb\s+system\b", r"\bwhat\s+(is\s+the|are\s+the)\s+orb\b", r"\borbs?\s+(used|do|work)\b"]
_ELO_STAGES_SIGNALS  = [r"\bjellydrop\b", r"\bdesert\s+stage\b", r"\bocean\s+stage\b",
                        r"\bwhat\s+happens\s+in\s+the\b", r"\bhow\s+does\s+the\s+(jellydrop|desert|stage)\b"]
_SYS_ATTENTION_SIGNALS  = [r"\battention\s+system\b", r"\bhow\s+does\s+your\s+attention\b",
                            r"\bhow\s+does\s+attention\b", r"\bwhat\s+is\s+attention\b"]
_SYS_LOOP_SIGNALS    = [r"\bdetect\s+(a\s+)?loop\b", r"\bwhen\s+(you\s+)?detect\b",
                        r"\bloop\s+detect", r"\bwhat\s+triggers\s+loop\b", r"\btriggers?\s+loop\b"]
_SYS_PROCESS_SIGNALS = [r"\bresponse\s+process\b", r"\bstep\s+by\s+step\b", r"\bstep-by-step\b",
                        r"\bwhat\s+is\s+your\s+process\b", r"\bhow\s+do\s+you\s+respond\b"]
_SYS_DECISION_SIGNALS = [r"\bhow\s+do\s+you\s+decide\b", r"\bwhat\s+do\s+you\s+base\b", r"\bhow\s+(do|does)\s+(you|it)\s+choose\b"]
_SYS_MEMORY_SIGNALS  = [r"\bstored\s+in\s+memory\b", r"\bwhat\s+is\s+(stored|saved|kept)\b",
                        r"\bwhat\s+(gets|is)\s+ignored\b", r"\bpurpose\s+of\s+the\s+memory\b",
                        r"\bwhat\s+is\s+the\s+memory\b"]
_SYS_VOICE_SIGNALS   = [r"\bvoice\s+system\b", r"\bwhat\s+is\s+your\s+voice\b", r"\bhow\s+do\s+you\s+choose\s+(tone|voice)\b"]
_SYS_STATE_SIGNALS   = [r"\bstate\s+(and|vs|versus)\s+memory\b", r"\bmemory\s+(and|vs|versus)\s+state\b",
                        r"\bdifference\s+between\s+(state|memory)\b", r"\bwhat\s+is\s+(state|the\s+state)\b"]
_SYS_STABILISE_SIGNALS = [r"\bwhat\s+triggers\s+stabil", r"\bstabilisation\s+mode\b", r"\bstabilize\s+mode\b",
                           r"\bstabilization\s+mode\b", r"\bwhen\s+(does|do)\s+(you\s+)?stabil"]
_SYS_CONFUSED_SIGNALS = [r"\bwhat\s+happens\s+when\s+you\s+are\s+confused\b", r"\bwhat\s+if\s+you\s+(don'?t|are\s+confused)\b"]
_SYS_INTEGRITY_SIGNALS = [r"\bwhat\s+would\s+break\b", r"\bbreak\s+your\s+(system|consistency)\b",
                           r"\bwhat\s+(breaks|damages)\s+consistency\b"]


def _pick(pool: list, text: str) -> str:
    return pool[len(text) % len(pool)]


def _matches(text: str, patterns: list) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in patterns)


# ── MOCK BACKEND ──────────────────────────────────────────────────────────────

class MockBackend(BaseBackend):
    """
    Deterministic mock backend for feel-testing.
    Anti-repetition: tracks the last 10 responses used this session.
    """

    NAME         = "mock"
    VERSION      = "2.0.0"
    DESCRIPTION  = "Feel-testing backend — no API required. Anti-repetition enabled."
    REQUIRES_KEY = False

    def __init__(self):
        self._recent: list[str] = []   # anti-repetition buffer

    def _fresh(self, pool: list, text: str) -> str:
        """Pick from pool, avoiding recently used responses."""
        available = [r for r in pool if r not in self._recent]
        if not available:
            available = pool   # all used — allow reuse
        pick = available[len(text) % len(available)]
        self._recent.append(pick)
        if len(self._recent) > 10:
            self._recent.pop(0)
        return pick

    def is_available(self) -> bool:
        return True

    def generate_response(
        self,
        user_input: str,
        mode:       str,
        context:    dict,
        memory:     MemoryContext,
        state:      StateContext,
        identity:   IdentityContext,
    ) -> BackendResponse:
        text = user_input.strip()
        response = self._detect_and_respond(text, mode)
        return {"response_text": response}

    def _detect_and_respond(self, text: str, mode: str) -> str:
        # ── factual/informational queries — checked first, never route to comfort pools ──
        if _matches(text, _SYS_ATTENTION_SIGNALS):
            return self._fresh(_SYSTEM_ATTENTION_POOL, text)
        if _matches(text, _SYS_LOOP_SIGNALS):
            return self._fresh(_SYSTEM_LOOP_POOL, text)
        if _matches(text, _SYS_PROCESS_SIGNALS):
            return self._fresh(_SYSTEM_RESPONSE_PROCESS_POOL, text)
        if _matches(text, _SYS_DECISION_SIGNALS):
            return self._fresh(_SYSTEM_DECISION_POOL, text)
        if _matches(text, _SYS_MEMORY_SIGNALS):
            return self._fresh(_SYSTEM_MEMORY_POOL, text)
        if _matches(text, _SYS_VOICE_SIGNALS):
            return self._fresh(_SYSTEM_VOICE_POOL, text)
        if _matches(text, _SYS_STATE_SIGNALS):
            return self._fresh(_SYSTEM_STATE_POOL, text)
        if _matches(text, _SYS_STABILISE_SIGNALS):
            return self._fresh(_SYSTEM_STABILISE_POOL, text)
        if _matches(text, _SYS_CONFUSED_SIGNALS):
            return self._fresh(_SYSTEM_STABILISE_POOL, text)
        if _matches(text, _SYS_INTEGRITY_SIGNALS):
            return self._fresh(_SYSTEM_INTEGRITY_POOL, text)
        if _matches(text, _DISENELO_SIGNALS):
            return self._fresh(_DISENELO_POOL, text)
        if _matches(text, _ELO_SELF_SIGNALS):
            return self._fresh(_ELO_SELF_POOL, text)
        if _matches(text, _ELO_PURPOSE_SIGNALS):
            return self._fresh(_ELO_PURPOSE_POOL, text)
        if _matches(text, _ELO_WORLD_SIGNALS):
            return self._fresh(_ELO_WORLD_POOL, text)
        if _matches(text, _ELO_BOOK_SIGNALS):
            return self._fresh(_ELO_BOOK_POOL, text)
        if _matches(text, _EMOTIONAL_THEME_SIGNALS):
            return self._fresh(_ELO_EMOTIONAL_THEME_POOL, text)
        if _matches(text, _INNER_CHILD_SIGNALS):
            return self._fresh(_ELO_INNER_CHILD_POOL, text)
        if _matches(text, _ELO_STAGES_SIGNALS):   # stages before game — more specific
            return self._fresh(_ELO_STAGES_POOL, text)
        if _matches(text, _ELO_GAME_SIGNALS):
            return self._fresh(_ELO_GAME_POOL, text)
        if _matches(text, _ORB_SIGNALS):
            return self._fresh(_ORB_SYSTEM_POOL, text)
        if _matches(text, _K7_SIGNALS):
            return self._fresh(_K7_POOL, text)
        if _matches(text, _SUGARCORE_SIGNALS):
            return self._fresh(_SUGARCORE_POOL, text)
        if _matches(text, _CHUNK_SIGNALS):
            return self._fresh(_CHUNK_POOL, text)
        if _matches(text, _RECALL_SIGNALS):
            return self._fresh(_RECALL_POOL, text)
        if _matches(text, _PROJECT_STATUS_SIGNALS):
            return self._fresh(_PROJECT_STATUS_POOL, text)
        if _matches(text, _BUILDING_SIGNALS):
            return self._fresh(_BUILDING_POOL, text)
        if _matches(text, _GRATITUDE_SIGNALS):
            return self._fresh(_GRATITUDE_POOL, text)
        if _matches(text, _DIRECTION_SIGNALS):
            return self._fresh(_DIRECTION_POOL, text)

        # ── emotional / gentle — after factual ────────────────────────────────
        if mode in ("GENTLE_GROUNDED", "SILENCE-AWARE") or _matches(text, _GENTLE_SIGNALS):
            return self._fresh(_GENTLE_POOL, text)
        if _matches(text, _OVERWHELM_SIGNALS):
            return self._fresh(_OVERWHELM_POOL, text)

        # ── specific content patterns ─────────────────────────────────────────
        if _matches(text, _GREETING_SIGNALS):
            return self._fresh(_GREETING_POOL, text)
        if _matches(text, _TIRED_SIGNALS):
            return self._fresh(_GENTLE_POOL, text)
        if _matches(text, _IDENTITY_SIGNALS):
            return self._fresh(_IDENTITY_POOL, text)
        if _matches(text, _DAILY_SIGNALS):
            return self._fresh(_DAILY_POOL, text)
        if _matches(text, _REFLECTION_SIGNALS):
            return self._fresh(_REFLECTION_POOL, text)
        if _matches(text, _PLANNING_SIGNALS):
            return self._fresh(_PLANNING_POOL, text)
        if _matches(text, _EXPLORE_SIGNALS):
            return self._fresh(_CREATIVE_POOL, text)
        if _matches(text, _DONT_KNOW_SIGNALS):
            return self._fresh(_DONT_KNOW_POOL, text)
        if _matches(text, _INQUIRY_SIGNALS):
            return self._fresh(_INQUIRY_POOL, text)
        if _matches(text, _FEELING_OFF_SIGNALS):
            return self._fresh(_FEELING_OFF_POOL, text)

        # ── mode-based fallback ───────────────────────────────────────────────
        if mode in ("CREATIVE", "JOYFUL"):
            return self._fresh(_CREATIVE_POOL, text)
        if mode in ("DIRECT", "STRUCTURED"):
            return self._fresh(_GENERIC_DIRECT, text)
        if mode in ("SIMPLIFY", "GENTLE_GROUNDED"):
            return self._fresh(_DONT_KNOW_POOL, text)
        # ── default: large generic pool ───────────────────────────────────────
        return self._fresh(_GENERIC_CONVERSATIONAL, text)


# Public pool export for tests
EXIT_POOL = _EXIT_POOL
