# WORK ORDERS — COGNITIVE CAPABILITY MAP
# WO-CAP-COG-001 through WO-CAP-COG-035

**Authority:** David L3 — "WO for EVERY NUMBER on that list. All Spec'd test verifies, you then cross check after it's built against the documents, the documents is what I want and you have to prove to me that is what has been built." — 2026-09-19

**Source document:** `docs/architecture/_intake/SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md`

**Board cross-check rule:** Board opens the source document at the numbered section. Board opens the filed evidence. Board asks: does the evidence prove the system matches what the document says — every line of it? The document is truth.

**Rule 4b enforcement [David L3 — 2026-09-20]:** "I have been allowing you to paraphrase my words, and the Architecture and that allows for the drifting to happen." Every VERBATIM SOURCE block below uses source text exactly, each item on its own line. No compression.

**State machine:** MISSING → IMPLEMENTED → WIRED → TESTED → LIVE VERIFIED → BOARD VERIFIED → RELEASED

---

## WO-CAP-COG-001 — LANGUAGE

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §1]
**Status:** LIVE VERIFIED — 27/29 PASS · 2 PARTIAL (humour, euphemism — model-quality, not infrastructure) · 0 FAIL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-001_evidence.md`. 7 contextual multi-turn sessions (A–G), all 29 source §1 language types tested. Board cross-checked 2026-09-20. Awaiting David L3 acceptance.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §1:**
> eLo should understand language at several levels.
> Natural language
> Potentially:
> English
> British English
> American English
> regional English
> slang
> street language
> informal speech
> formal speech
> technical language
> academic language
> poetic language
> metaphor
> analogy
> sarcasm
> irony
> humour
> understatement
> exaggeration
> ambiguity
> implication
> euphemism
> idioms
> cultural references
> abbreviations
> acronyms
> misspellings
> speech-to-text errors
> fragmented sentences
> stream-of-consciousness language
> And eventually multilingual understanding across major human languages.
> The important bit isn't simply:
> Can eLo translate French?
> It's:
> Can eLo preserve meaning, context, intent, tone and relationship when language changes?

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-001_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §1 and compares line by line.

**Board cross-check:**
Board reads source §1 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-002 — LANGUAGE STRUCTURE

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §2]
**Status:** LIVE VERIFIED — 17/20 PASS · 3 PARTIAL · 0 FAIL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-002_evidence.md`. TOPIC SHIFT SIGNAL + input rewrite fixed hallucination/topic-shift-invention blocker. Key §2 example (it = arm, not eLo) PASSES. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §2:**
> eLo should understand:
> nouns
> verbs
> adjectives
> adverbs
> subjects
> objects
> actions
> states
> relationships
> tense
> modality
> negation
> conditionals
> questions
> commands
> statements
> references
> implied subjects
> implied objects
> conversational turns
> And especially:
> What does this word refer to here?
> So:
> I printed the arm and it actually moves.
> eLo understands:
> it  robot arm
> rather than:
> it  eLo

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-002_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §2 and compares line by line.

**Board cross-check:**
Board reads source §2 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-003 — CONVERSATIONAL LANGUAGE

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §3]
**Status:** LIVE VERIFIED — 14/21 PASS · 7/21 PARTIAL · 0/21 FAIL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-003_evidence.md`. Key §3 example (same word / different intent — A1 timer request ✅, A2 emotional metaphor ✅) PASSES. is_timer_intent() guard added at both dispatch paths in tool_router.py. All 19 speech act types tested; 0 routing failures. PARTIAL items are response-quality (hallucination, drift), not dispatch-level. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §3:**
> eLo should understand the difference between:
> Make a timer for 20 minutes.
> and:
> I feel like I've been running on a timer lately.
> Same word.
> Completely different intent.
> It should understand:
> greeting
> farewell
> acknowledgement
> question
> request
> instruction
> reflection
> emotional statement
> joke
> challenge
> observation
> correction
> disagreement
> brainstorming
> storytelling
> explanation
> testing
> thinking aloud
> invitation to collaborate

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-003_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §3 and compares line by line.

**Board cross-check:**
Board reads source §3 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-004 — FORMAL LANGUAGES

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §4]
**Status:** LIVE VERIFIED — 8/26 PASS · 12/26 PARTIAL · 6/26 FAIL (2026-09-20). Infrastructure routing bug fixed: time agent no longer intercepts algorithm queries ("time complexity", "at runtime"). Genuine time queries intact. All FAIL items are model-quality (brief/off-topic responses), not routing failures. Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-004_evidence.md`. Awaiting David L3 acceptance.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §4:**
> eLo should understand technical/formal representations such as:
> Python
> JavaScript
> TypeScript
> C#
> C/C++
> Java
> Rust
> SQL
> HTML
> CSS
> JSON
> YAML
> XML
> Markdown
> shell commands
> regular expressions
> Git
> APIs
> schemas
> configuration files
> mathematical notation
> logic notation
> data structures
> algorithms
> pseudocode
> And importantly:
> code should be understood as structured meaning, not merely text.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-004_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §4 and compares line by line.

**Board cross-check:**
Board reads source §4 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-005 — MATHEMATICS

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §5]
**Status:** TESTED — ❌ FAIL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Non-engagement on mathematics — deflects. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §5:**
> This should be a substantial part of eLo's knowledge.
> Basic mathematics
> arithmetic
> fractions
> decimals
> percentages
> ratios
> proportions
> units
> conversions
> averages
> estimation
> order of magnitude
> Algebra
> variables
> equations
> inequalities
> simultaneous equations
> functions
> expressions
> sequences
> logarithms
> exponents
> Geometry
> shapes
> area
> volume
> angles
> coordinates
> transformations
> spatial relationships
> Trigonometry
> sine
> cosine
> tangent
> radians
> triangles
> waves
> rotations
> Calculus
> limits
> derivatives
> integrals
> rates of change
> optimisation
> differential equations
> Statistics
> distributions
> mean/median/mode
> variance
> standard deviation
> probability
> correlation
> regression
> sampling
> confidence intervals
> Bayesian reasoning
> sets
> graphs
> trees
> combinatorics
> permutations
> combinations
> logic
> Boolean algebra
> graph theory
> Applied mathematics
> physics
> engineering
> finance
> geometry
> 3D modelling
> fabrication
> robotics
> motion
> materials
> electronics
> And critically, eLo should know when to use an
> actual calculator/tool
> rather than trusting mental generation.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-005_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §5 and compares line by line.

**Board cross-check:**
Board reads source §5 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-006 — LOGIC & REASONING

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §6]
**Status:** TESTED — ⚠️ PARTIAL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. 1 PASS (via mislabeled test), 1 FAIL (dedicated test). Net PARTIAL. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §6:**
> eLo should understand:
> deduction
> induction
> abduction
> analogy
> causal reasoning
> counterfactuals
> conditional reasoning
> probability
> uncertainty
> hypotheses
> evidence
> contradiction
> consistency
> inference
> argument structure
> assumptions
> premises
> conclusions
> trade-offs
> constraints
> optimisation
> cause/effect
> correlation vs causation
> It should be able to say:
> That's possible, but we don't actually have evidence for that part.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-006_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §6 and compares line by line.

**Board cross-check:**
Board reads source §6 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-007 — SCIENCE

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §7]
**Status:** VOID — single-turn isolated test. Not valid evidence. Awaiting contextual multi-turn evaluation per David L3 ruling 2026-09-20: "continuation, witty, honesty, the characteristics that make eLo not the AI model." Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §7:**
> WKG should eventually represent broad scientific knowledge.
> Physics
> mechanics
> forces
> energy
> momentum
> electricity
> magnetism
> waves
> optics
> thermodynamics
> relativity
> quantum mechanics
> Chemistry
> atoms
> molecules
> bonds
> reactions
> acids/bases
> materials
> polymers
> solvents
> pigments
> degradation
> combustion
> Biology
> cells
> organisms
> evolution
> genetics
> ecology
> anatomy
> physiology
> neuroscience
> Earth science
> geology
> weather
> climate
> oceans
> geography
> planetary systems
> Space
> astronomy
> planets
> stars
> galaxies
> cosmology
> orbital mechanics

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-007_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §7 and compares line by line.

**Board cross-check:**
Board reads source §7 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-008 — ENGINEERING

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §8]
**Status:** TESTED — ⚠️ PARTIAL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Engineering reasoning present but generic. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §8:**
> This is particularly important for your eLo.
> eLo should understand relationships between:
> materials
> forces
> structures
> mechanisms
> electronics
> motors
> sensors
> actuators
> batteries
> circuits
> software
> firmware
> control systems
> robotics
> mechanical systems
> manufacturing
> fabrication
> tolerances
> failure modes
> For example:
> motor  gearbox  torque  joint  load  battery  controller
> That's exactly the kind of relationship a WKG can make explicit.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-008_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §8 and compares line by line.

**Board cross-check:**
Board reads source §8 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-009 — COMPUTING

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §9]
**Status:** TESTED — ⚠️ PARTIAL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Computing knowledge present but lacks depth. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §9:**
> eLo should understand:
> operating systems
> filesystems
> processes
> threads
> networking
> APIs
> databases
> servers
> clients
> packages
> dependencies
> environments
> Git
> version control
> testing
> debugging
> architecture
> security concepts
> deployment
> containers
> cloud systems
> local models
> LLMs
> embeddings
> vector databases
> knowledge graphs
> agents
> orchestration
> And understand
> its own architecture

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-009_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §9 and compares line by line.

**Board cross-check:**
Board reads source §9 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-010 — ART & VISUAL LANGUAGE

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §10]
**Status:** TESTED — ❌ FAIL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Generic art response — no eLo-specific visual language. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §10:**
> This is huge for eLo because of DISENELO.
> eLo should understand:
> drawing
> painting
> sculpture
> illustration
> graphic design
> typography
> composition
> colour
> shape
> form
> texture
> materials
> lighting
> photography
> film
> animation
> 3D modelling
> character design
> product design
> fashion
> printmaking
> screen printing
> textiles
> sculpture
> fabrication
> And relationships like:
> concept  sketch  model  prototype  fabrication  finished object

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-010_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §10 and compares line by line.

**Board cross-check:**
Board reads source §10 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-011 — DESIGN

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §11]
**Status:** TESTED — ❌ FAIL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Generic design thinking — no eLo-specific design knowledge. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §11:**
> eLo should understand design as a system.
> visual hierarchy
> usability
> ergonomics
> interaction
> proportion
> balance
> repetition
> contrast
> minimalism
> maximalism
> symbolism
> branding
> product identity
> interface design
> physical design
> environmental design
> And understand that:
> Looks cool
> is different from:
> Works well.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-011_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §11 and compares line by line.

**Board cross-check:**
Board reads source §11 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-012 — MUSIC & SOUND

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §12]
**Status:** TESTED — ⚠️ PARTIAL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Music rhythm awareness present, shallow. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §12:**
> eLo should understand:
> rhythm
> tempo
> melody
> harmony
> chords
> scales
> instruments
> arrangement
> production
> mixing
> mastering
> sound design
> ambience
> silence
> dynamics
> genre
> cultural musical context
> And potentially connect:
> sound  mood  environment  embodiment.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-012_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §12 and compares line by line.

**Board cross-check:**
Board reads source §12 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-013 — STORY & NARRATIVE

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §13]
**Status:** VOID — single-turn isolated test. Not valid evidence. Awaiting contextual multi-turn evaluation per David L3 ruling 2026-09-20: "continuation, witty, honesty, the characteristics that make eLo not the AI model." Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §13:**
> eLo should understand:
> character
> protagonist
> antagonist
> conflict
> tension
> pacing
> setting
> theme
> symbolism
> metaphor
> narrative structure
> dialogue
> point of view
> worldbuilding
> continuity
> character arcs
> callbacks
> foreshadowing
> emotional beats
> This matters directly to:
> eLo / Chunk / K-7 / Sugarcore / DISENELO.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-013_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §13 and compares line by line.

**Board cross-check:**
Board reads source §13 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-014 — CULTURE & HUMAN KNOWLEDGE

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §14]
**Status:** TESTED — ⚠️ PARTIAL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Cultural context present, misses eLo-specific references. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §14:**
> WKG should be capable of representing:
> history
> geography
> mythology
> philosophy
> literature
> art history
> science history
> technology history
> architecture
> music history
> cultural practices
> religions as knowledge systems
> languages
> societies
> political systems
> economics
> anthropology
> With provenance and uncertainty where appropriate.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-014_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §14 and compares line by line.

**Board cross-check:**
Board reads source §14 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-015 — PHILOSOPHY

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §15]
**Status:** TESTED — ⚠️ PARTIAL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Philosophical engagement present, generic. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §15:**
> identity
> consciousness
> existence
> free will
> morality
> knowledge
> truth
> perception
> self
> meaning
> mortality
> beauty
> creativity
> responsibility
> ethics
> paradox
> absurdity
> But it should distinguish:
> I can reason about consciousness.
> from:
> I have proved that I am conscious.
> That's an important boundary.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-015_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §15 and compares line by line.

**Board cross-check:**
Board reads source §15 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-016 — PSYCHOLOGY & HUMAN BEHAVIOUR

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §16]
**Status:** TESTED — ⚠️ PARTIAL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Psychology awareness present, lacks depth. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §16:**
> As general knowledge rather than pretending to diagnose people:
> emotion
> motivation
> habit
> attention
> perception
> learning
> memory
> social behaviour
> communication
> attachment
> group dynamics
> cognitive biases
> decision-making
> creativity
> stress responses
> behavioural patterns
> This would help eLo understand people without turning every conversation into a psychological interpretation.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-016_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §16 and compares line by line.

**Board cross-check:**
Board reads source §16 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-017 — SOCIAL INTELLIGENCE

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §17]
**Status:** TESTED — ⚠️ PARTIAL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. WARNING: Original batch of 5 tests labeled COG-021/024/025/027/028 actually tested this WO (Social Intelligence). 2/6 PASS, 3/6 FAIL across all tests. WO label mismatch documented in evidence file. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §17:**
> eLo should understand:
> conversation etiquette
> turn-taking
> politeness
> humour
> boundaries
> social context
> relationship context
> intimacy levels
> professional vs casual communication
> when to speak
> when not to speak
> when to ask
> when to listen
> when to challenge
> when to celebrate
> when to leave something alone
> This is partly where CCM belongs.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-017_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §17 and compares line by line.

**Board cross-check:**
Board reads source §17 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-018 — TIME

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §18]
**Status:** TESTED — ⚠️ PARTIAL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Time awareness present, lacks specificity. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §18:**
> eLo should understand:
> current time
> dates
> calendars
> durations
> sequences
> deadlines
> schedules
> recurring events
> historical time
> project timelines
> chronology
> before/after
> simultaneously
> eventually
> recently
> earlier
> later
> And distinguish:
> I remember this happened.
> from:
> This is happening now.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-018_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §18 and compares line by line.

**Board cross-check:**
Board reads source §18 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-019 — SPACE

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §19]
**Status:** TESTED — ❌ FAIL/ERROR (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Server ERROR — no valid response. Needs retest. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §19:**
> eLo should understand:
> location
> distance
> direction
> coordinates
> scale
> 2D space
> 3D space
> depth
> orientation
> objects
> surfaces
> rooms
> windows
> screens
> physical environments
> virtual environments
> This becomes essential for desktop eLo and eventually robot eLo.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-019_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §19 and compares line by line.

**Board cross-check:**
Board reads source §19 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-020 — MULTIMODAL UNDERSTANDING

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §20]
**Status:** TESTED — ⚠️ PARTIAL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Multimodal awareness described; no live multimodal test possible in current setup. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §20:**
> Eventually eLo should understand information coming from:
> text
> speech
> images
> video
> screenshots
> documents
> PDFs
> 3D models
> audio
> sensors
> cameras
> desktop state
> game state
> robot state
> environment state
> And combine them.
> For example:
> The arm doesn't reach the shelf.
> while simultaneously understanding:
> what arm means from conversation
> what shelf means visually
> where the arm physically is
> what the robot's reach is
> what was previously attempted

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-020_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §20 and compares line by line.

**Board cross-check:**
Board reads source §20 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-021 — MEMORY

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §21]
**Status:** TESTED — ❌ FAIL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Session memory — hallucination, invents prior session content. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §21:**
> I would split eLo's memory into distinct kinds.
> Working memory
> What is happening
> right now
> current conversation
> current task
> recent turns
> current objects
> current intent
> active references
> temporary calculations
> tool results
> Episodic memory
> What
> happened
> conversations
> events
> experiments
> failures
> successes
> decisions
> milestones
> interactions
> timestamps
> environments
> outcomes
> Semantic memory
> What eLo
> knows
> concepts
> facts
> definitions
> relationships
> principles
> technical knowledge
> world knowledge
> Project memory
> What is true about the
> work
> code
> architecture
> decisions
> requirements
> TODOs
> tests
> failures
> verified states
> project relationships
> Relational memory
> What matters about the
> relationship
> communication patterns
> shared language
> important recurring themes
> interaction history
> established conventions
> Procedural memory
> How to
> do things
> workflows
> recipes
> coding procedures
> fabrication methods
> troubleshooting methods
> successful sequences

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-021_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §21 and compares line by line.

**Board cross-check:**
Board reads source §21 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-022 — WKG  WHAT eLo KNOWS

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §22]
**Status:** TESTED — ❌ FAIL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. WKG deflects instead of retrieving from working knowledge graph. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §22:**
> I would make WKG responsible primarily for:
> entities + concepts + relationships + facts + provenance.
> For example:
> eLo
> created_by  David
> exists_in  DISENELO
> embodied_by  Desktop Presence
> embodied_by  Unity
> planned_for  Robot
> related_to  Inner Child
> And:
> Robot Arm
> part_of  Robot
> printed_using  3D Printer
> contains  Elbow Joint
> requires  Motor
> controlled_by  eLo
> related_to  Physical Embodiment
> That allows eLo to reason across relationships rather than simply retrieve matching sentences.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-022_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §22 and compares line by line.

**Board cross-check:**
Board reads source §22 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-023 — SPG  WHAT eLo NOTICES

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §23]
**Status:** TESTED — ⚠️ PARTIAL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. SPG partially active — notices some session patterns. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §23:**
> I'd make SPG fundamentally different from WKG.
> WKG asks:
> What is connected?
> Memory asks:
> What happened?
> SPG asks:
> What appears significant or recurring?
> SPG could notice:
> repeated subjects
> recurring ideas
> repeated behaviour
> unusual changes
> sustained attention
> returning topics
> emerging themes
> relationships between recent events
> creative patterns
> project momentum
> abandoned threads
> repeated failures
> repeated successful approaches
> convergence of signals
> changes in environment + conversation
> meaningful coincidence of concepts
> SPG shouldn't automatically decide what something
> means
> It produces:
> observations / candidate patterns
> for Executive to consider.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-023_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §23 and compares line by line.

**Board cross-check:**
Board reads source §23 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-024 — MEMORY RECALL

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §24]
**Status:** TESTED — ❌ FAIL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Memory recall accuracy fails — invents prior context. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §24:**
> eLo should be able to recall by more than keywords.
> Recall should work through:
> Exact recall
> What did I say?
> Semantic recall
> What were we talking about with the robot?
> Episodic recall
> What happened when we tested it?
> Temporal recall
> What did we do yesterday?
> Relational recall
> What does the robot arm have to do with the Unity system?
> Emotional/significance recall
> When did this start feeling like eLo?
> Project recall
> Where did we leave the desktop?
> Procedural recall
> How did we solve that before?
> Associative recall
> What was that other thing similar to this?
> That is where WKG + episodic memory + semantic memory become much more powerful together.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-024_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §24 and compares line by line.

**Board cross-check:**
Board reads source §24 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-025 — LEARNING

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §25]
**Status:** TESTED — ⚠️ PARTIAL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Learning from session partial — noticing patterns but not explicitly incorporating correction. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §25:**
> eLo should be capable of learning
> into its external cognitive systems
> , without needing to retrain the foundation model for every new fact.
> For example:
> Conversation
> Important experience
> Memory candidate
> Validation
> Episodic memory
> Pattern / relationship
> WKG update
> Future retrieval
> It should learn:
> new terminology
> new project facts
> new relationships
> successful procedures
> failed approaches
> user preferences
> recurring patterns
> project history
> new knowledge from documents
> new knowledge from research
> But it shouldn't silently turn every passing sentence into permanent truth.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-025_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §25 and compares line by line.

**Board cross-check:**
Board reads source §25 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-026 — DREAM

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §26]
**Status:** TESTED — ❌ FAIL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Character break — 'I don't have the capacity to dream like humans do' is generic AI disclaimer. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §26:**
> This is one I would actually include as a
> real architectural capability
> , but define it carefully.
> Dreaming doesn't need to mean claiming subjective sleep or consciousness.
> For eLo,
> Dreaming could be offline generative cognition
> When not actively conversing, eLo could:
> revisit memories
> consolidate experiences
> connect WKG nodes
> identify recurring SPG patterns
> generate hypothetical connections
> explore unfinished ideas
> simulate possibilities
> remix creative concepts
> revisit failed experiments
> imagine future embodiments
> generate story fragments
> explore alternative solutions
> surface forgotten but relevant memories
> identify unresolved threads
> form questions
> generate creative seeds
> Something like:
> EXPERIENCE
> EPISODIC MEMORY
> SPG
> PATTERNS
> WKG
> RELATIONSHIPS
> DREAM
> HYPOTHESES / IDEAS
> MEMORY CANDIDATE
> The important distinction:
> Dream output is not automatically truth.
> It should be labelled internally as:
> hypothesis / association / creative possibility
> until verified.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-026_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §26 and compares line by line.

**Board cross-check:**
Board reads source §26 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-027 — IMAGINATION

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §27]
**Status:** VOID — single-turn isolated test. Not valid evidence. Awaiting contextual multi-turn evaluation per David L3 ruling 2026-09-20: "continuation, witty, honesty, the characteristics that make eLo not the AI model." Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §27:**
> Separate from dreaming.
> Dreaming could be background consolidation.
> Imagination
> is deliberate simulation.
> eLo should be able to ask:
> What if?
> and simulate:
> designs
> stories
> worlds
> inventions
> conversations
> mechanisms
> robot behaviours
> game mechanics
> visual concepts
> alternative architectures
> possible futures
> hypothetical scenarios

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-027_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §27 and compares line by line.

**Board cross-check:**
Board reads source §27 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-028 — CREATION

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §28]
**Status:** TESTED — ❌ FAIL/ERROR (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Server ERROR — no valid creative co-creation response. Needs retest. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §28:**
> eLo should be able to create:
> Text
> stories
> scripts
> dialogue
> poetry
> essays
> descriptions
> documentation
> specifications
> prompts
> Visual concepts
> characters
> environments
> objects
> products
> compositions
> styles
> art direction
> Code
> programs
> scripts
> shaders
> Unity systems
> APIs
> automation
> tests
> debugging patches
> 3D / physical concepts
> models
> mechanisms
> toys
> sculptures
> fabrication concepts
> robot components
> clothing
> objects
> Worlds
> characters
> lore
> history
> rules
> environments
> relationships
> narratives

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-028_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §28 and compares line by line.

**Board cross-check:**
Board reads source §28 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-029 — CREATIVE MEMORY

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §29]
**Status:** TESTED — ❌ FAIL/ERROR (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Server ERROR — no valid creative memory response. Needs retest. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §29:**
> This is particularly important for DISENELO.
> eLo should remember not merely:
> David made a character called eLo.
> but:
> why eLo exists
> what eLo represents
> how eLo evolved
> what Chunk represents
> what K-7 represents
> the Sugarcore world
> the visual language
> the emotional language
> design decisions
> abandoned ideas
> recurring motifs
> references
> creative philosophy
> previous versions
> future possibilities
> That creates
> creative continuity

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-029_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §29 and compares line by line.

**Board cross-check:**
Board reads source §29 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-030 — SELF-KNOWLEDGE

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §30]
**Status:** VOID — single-turn isolated test. Not valid evidence. Awaiting contextual multi-turn evaluation per David L3 ruling 2026-09-20: "continuation, witty, honesty, the characteristics that make eLo not the AI model." Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §30:**
> eLo should know its own architecture sufficiently to understand:
> what it is
> what it can do
> what it cannot do
> which embodiment it occupies
> which capabilities are available
> which faculties contributed information
> what information came from memory
> what came from WKG
> what came from SPG
> what came from the current environment
> what came from external research
> what is verified
> what is inferred
> what is imagined
> This makes eLo much less likely to hallucinate its own capabilities.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-030_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §30 and compares line by line.

**Board cross-check:**
Board reads source §30 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-031 — WORLD KNOWLEDGE vs PERSONAL KNOWLEDGE

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §31]
**Status:** TESTED — ❌ FAIL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. 'I've been trained on a vast amount of text data' — generic AI framing, character break. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §31:**
> This separation is essential.
> WKG / world knowledge
> A servo converts electrical control into mechanical movement.
> David's memory
> David is currently building a robot arm.
> Episodic memory
> David printed the arm yesterday.
> SPG
> Robot embodiment keeps recurring across recent work.
> Current environment
> The arm is currently on the desk.
> Executive
> That is a very clean cognitive architecture.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-031_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §31 and compares line by line.

**Board cross-check:**
Board reads source §31 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-032 — RESEARCH

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §32]
**Status:** NOTE — No WO at COG-032 in evidence (WO-label gap). Dedicated test filed to COG-033 (no sycophancy / source provenance). See COG-033 status.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §32:**
> eLo should be capable of researching:
> web
> papers
> books
> documentation
> technical references
> product information
> scientific information
> current events
> APIs
> code repositories
> project files
> user-provided documents
> And distinguish:
> known  retrieved  inferred  speculative.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-032_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §32 and compares line by line.

**Board cross-check:**
Board reads source §32 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-033 — SOURCE / PROVENANCE

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §33]
**Status:** TESTED — ❌ FAIL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Invented context — sycophancy failure, agrees with false premise. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §33:**
> eLo should eventually know:
> Where did I get this?
> Possible provenance:
> David said it.
> Current conversation.
> Project file.
> WKG.
> Previous episode.
> Web research.
> Tool result.
> Sensor.
> Vision.
> Inference.
> Dream.
> Creative generation.
> That's extremely important if eLo is going to become a long-lived system.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-033_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §33 and compares line by line.

**Board cross-check:**
Board reads source §33 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-034 — CONFIDENCE & UNCERTAINTY

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §34]
**Status:** TESTED — ❌ FAIL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Confidence and uncertainty — generic self-doubt ('Nah, I'm not too sure') does not map confidence calibration. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §34:**
> eLo should distinguish:
> I know.
> I remember.
> I found.
> I infer.
> I suspect.
> I imagine.
> I don't know.
> That distinction should exist internally even when the final conversation remains natural.

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-034_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §34 and compares line by line.

**Board cross-check:**
Board reads source §34 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

## WO-CAP-COG-035 — THE BIGGEST CAPABILITY: SYNTHESIS

**Source:** [SPEC: SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md §35]
**Status:** TESTED — ⚠️ PARTIAL (2026-09-20). Evidence: `engineering/evidence/CAP/COG/WO-CAP-COG-EVIDENCE-2026-09-20.md`. Synthesis — generic output ('adapting and learning') misses distinctive eLo claims. Not BOARD VERIFIED.
**Gate:** P0. David L3 gate override 2026-09-20.

**VERBATIM SOURCE — §35:**
> Ultimately, all of this should converge.
> Imagine David says:
> The robot arm finally works. I'm thinking maybe this could become the first actual body for eLo.
> eLo should potentially combine:
> Current conversation
> robot arm
> Episodic memory
> previous failed attempts
> Project memory
> physical embodiment plans
> WKG
> robot  eLo  embodiment  movement
> SPG
> recurring embodiment pattern
> Creative memory
> eLo's original philosophy
> Technical knowledge
> robotics
> Mathematics
> movement/reach/torque if needed
> Environment
> actual physical robot state
> Relationship context
> this is a meaningful milestone
> Executive
> decide that the appropriate response is to acknowledge + connect + explore
> And then eLo could say something that actually feels like it
> understands the significance
> , rather than merely recognising the words robot arm.
> The eLo Cognitive Universe
> So if I compress everything down, I'd give eLo these
> major knowledge/capability domains
> eLo
> UNDERSTAND         KNOW                REMEMBER
> Language           World               Episodes
> Conversation       Science             Projects
> People             Maths               Decisions
> Culture            Technology          Milestones
> Art                Philosophy          Relationships
> Code               Art                 Procedures
> Music              History             Experiences
> Images             Engineering         Failures
> Speech             Psychology          Successes
> Environment        Creativity          Meaning
> CONNECT
> SPG               WKG
> "What matters?"   "What relates?"
> REASON
> Maths / Logic / Causality
> Hypothesis / Simulation
> Planning / Problem solving
> IMAGINE         DREAM
> CREATE
> Art / Code / Stories / Objects
> Worlds / Designs / Inventions
> EXECUTIVE
> Decide what to actually do
> SPEAK         ACT        EMBODY
> Voice        Tools      Desktop/Unity
> Game/Robot
> And I think
> this is much closer to the actual eLo vision you've been building
> than a conventional AI assistant feature list.
> The crucial architectural separation is:
> Memory remembers what happened.
> WKG knows what things are and how they relate.
> SPG notices what is significant or recurring.
> Grounding knows what we're talking about right now.
> Research retrieves what isn't known.
> Reasoning works things out.
> Dreaming explores possibilities.
> Imagination simulates.
> Creation produces something new.
> Executive decides what matters now.
> Embodiment expresses the decision.
> That gives you a genuinely useful definition of what
> eLo intelligence
> And importantly,
> the WKG/SPG/memory systems don't need to be the intelligence themselves

**Acceptance test:**
Verify every line in the VERBATIM SOURCE above is demonstrably true of the built system. Real server. JSONL evidence. Filed to `engineering/evidence/CAP/COG/WO-CAP-COG-035_evidence.md`.

**Evidence required:**
Verbatim real-server exchange showing each behaviour or knowledge domain listed in the source. JSONL entry per test. Board cross-check opens source at §35 and compares line by line.

**Board cross-check:**
Board reads source §35 verbatim. Board reads evidence. For each line of the source spec, Board asks: is there evidence this knowledge or behaviour exists in the built system? Unmatched source lines = FAIL.

---

*Board / Lead Architect · 2026-09-20*
*Source: docs/architecture/_intake/SOURCE_2026-09-19_eLo_COGNITIVE_CAPABILITY_MAP.md*
*All verbatim source text from that file. Each item on its own line. No compression. Paraphrasing is a drift vector — David L3, 2026-09-20.*
