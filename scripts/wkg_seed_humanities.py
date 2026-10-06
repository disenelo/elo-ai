#!/usr/bin/env python3
"""
scripts/wkg_seed_humanities.py — WO-WKG-HUMANITIES-001

Seed the WKG with humanities domain knowledge across all 17 David-specified domains:
history, geography, mythology, philosophy, literature, art history, science history,
technology history, architecture, music history, cultural practices, religions
(as knowledge systems), languages, societies, political systems, economics, anthropology.

Provenance tagged per node/claim. Uncertain/contested claims marked HYPOTHESIS or DISPUTED.
Runs idempotently — create_entity() returns rejected=True on duplicate label, so
re-running adds nothing and breaks nothing.

Run from ~/elo-ai/:
    python scripts/wkg_seed_humanities.py
    python scripts/wkg_seed_humanities.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
_log = logging.getLogger("wkg_seed_humanities")

_WKG_DIR   = os.path.join(_ROOT, "memory", "wkg")
_PROV_CONS = "SOURCE-HUM-001"   # academic/encyclopaedic consensus
_PROV_PRIM = "SOURCE-HUM-002"   # primary historical sources
_PROV_ACAD = "SOURCE-HUM-003"   # academic scholarship


# ── source registry additions ─────────────────────────────────────────────────

_NEW_SOURCES = [
    {
        "source_id": _PROV_CONS,
        "source_type": "ENCYCLOPAEDIC",
        "title": "Encyclopaedic consensus — general humanities",
        "author": None,
        "date": None,
        "notes": "Well-established facts from encyclopaedic / academic consensus (Britannica, peer-reviewed overview). WO-WKG-HUMANITIES-001.",
    },
    {
        "source_id": _PROV_PRIM,
        "source_type": "PRIMARY",
        "title": "Primary historical sources",
        "author": None,
        "date": None,
        "notes": "Ancient / early primary sources: Ibn Battuta, Herodotus, Plutarch, etc. Cited per claim.",
    },
    {
        "source_id": _PROV_ACAD,
        "source_type": "ACADEMIC",
        "title": "Academic scholarship — humanities",
        "author": None,
        "date": None,
        "notes": "Peer-reviewed secondary scholarship. Where contested, claims marked DISPUTED or HYPOTHESIS.",
    },
]


# ── entity / claim seed data ──────────────────────────────────────────────────
# Format:  {"label", "type", "aliases", "description", "sources", "domain",
#           "claims": [{"rel", "obj_label", "eclass", "confidence", "src", "note"}]}
#
# obj_label refers to another entity's label (resolved after all entities created).
# eclass: VERIFIED | HISTORICAL | SOURCE_ATTRIBUTED | HYPOTHESIS | DISPUTED | SYMBOLIC
# confidence 1.0=established, 0.85=high confidence, 0.6=estimated/uncertain

_SEED = [

    # ── HISTORY ─────────────────────────────────────────────────────────────
    {
        "label": "Mansa Musa",
        "type": "PERSON",
        "aliases": ["Musa I of Mali", "Musa Keita I"],
        "description": "14th-century emperor of the Mali Empire, reigned c.1312–1337. Undertook Hajj pilgrimage to Mecca in 1324, distributing gold en route; his wealth is among the largest ever documented in human history. His pilgrimage caused gold price inflation across North Africa and the Middle East.",
        "sources": [_PROV_PRIM, _PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "BELONGS_TO", "obj": "Mali Empire", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_PRIM},
            {"rel": "CAUSES",     "obj": "Gold Price Collapse Egypt 1324", "eclass": "HISTORICAL", "conf": 0.85, "src": _PROV_PRIM},
            {"rel": "HAS_PROPERTY", "obj": "Extraordinary Wealth", "eclass": "HYPOTHESIS", "conf": 0.6, "src": _PROV_CONS},
            {"rel": "ASSOCIATED_WITH", "obj": "Hajj Pilgrimage", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_PRIM},
        ],
    },
    {
        "label": "Mali Empire",
        "type": "CULTURAL",
        "aliases": ["Manden Kurufaba", "Empire of Mali"],
        "description": "West African empire that flourished c.1230–1600 CE. At its peak under Mansa Musa one of the wealthiest states in the world, controlling trans-Saharan gold and salt trade routes. Capital: Niani. Major cities: Timbuktu, Djenné.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "BELONGS_TO", "obj": "West Africa", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
            {"rel": "TEMPORALLY_PRECEDES", "obj": "Songhai Empire", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Hajj Pilgrimage",
        "type": "CONCEPT",
        "aliases": ["Hajj", "Muslim pilgrimage to Mecca"],
        "description": "Annual Islamic pilgrimage to Mecca, Saudi Arabia — one of the Five Pillars of Islam. Obligatory for Muslims who are financially and physically able. One of the world's largest annual gatherings.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "BELONGS_TO", "obj": "Islam", "eclass": "VERIFIED", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Gold Price Collapse Egypt 1324",
        "type": "CONCEPT",
        "aliases": ["Mansa Musa gold inflation", "Cairo gold devaluation 1324"],
        "description": "Economic disruption in Cairo, Medina, and Mecca following Mansa Musa's Hajj pilgrimage (1324), during which he distributed so much gold that the metal was devalued in the region for roughly a decade. Documented by Egyptian historian al-Maqrizi.",
        "sources": [_PROV_PRIM, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "CAUSES", "obj": "Devaluation of Gold", "eclass": "HISTORICAL", "conf": 0.85, "src": _PROV_PRIM},
        ],
    },
    {
        "label": "Extraordinary Wealth",
        "type": "CONCEPT",
        "aliases": ["immense wealth", "incalculable fortune"],
        "description": "Abstract concept denoting wealth beyond reliable quantification. Applied to historical figures like Mansa Musa where contemporaneous accounts attest enormous resources but modern monetary estimates are contested.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "West Africa",
        "type": "PLACE",
        "aliases": ["West African region"],
        "description": "Western sub-region of Africa, roughly from Senegal and Mauritania in the west to Nigeria and Niger in the east. Home to major historical empires: Ghana, Mali, Songhai. Rich in gold and salt resources that drove trans-Saharan trade.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "BELONGS_TO", "obj": "African Continent", "eclass": "VERIFIED", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "African Continent",
        "type": "PLACE",
        "aliases": ["Africa"],
        "description": "Earth's second-largest continent. Cradle of modern human origins. Hosts extraordinary cultural, linguistic, and historical diversity across 54 recognised nations and thousands of ethnic groups.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "Songhai Empire",
        "type": "CULTURAL",
        "aliases": ["Songhay Empire"],
        "description": "West African empire (c.1340–1591 CE) that superseded the Mali Empire as the dominant power in the western Sudan. At its peak under Askia the Great, one of the largest empires in African history.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "BELONGS_TO", "obj": "West Africa", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Alexander the Great",
        "type": "PERSON",
        "aliases": ["Alexander III of Macedon", "Alexandros"],
        "description": "Macedonian king (356–323 BCE) who created one of the largest empires of the ancient world, stretching from Greece to northwestern India. Student of Aristotle. His campaigns spread Hellenic culture across the Near East, Egypt, and Persia (Hellenisation).",
        "sources": [_PROV_PRIM, _PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "ASSOCIATED_WITH", "obj": "Hellenism", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
            {"rel": "ASSOCIATED_WITH", "obj": "Aristotle", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_PRIM},
        ],
    },
    {
        "label": "Hellenism",
        "type": "CONCEPT",
        "aliases": ["Hellenisation", "Greek cultural diffusion"],
        "description": "Spread of Greek culture, language, and ideas across the Mediterranean and Near East following Alexander's conquests (c.323–31 BCE). Produced philosophical, artistic, and scientific synthesis between Greek and Eastern traditions.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Roman Empire", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Roman Empire",
        "type": "CULTURAL",
        "aliases": ["Imperium Romanum", "Rome"],
        "description": "Political entity centred on Rome that governed much of Europe, the Mediterranean, and parts of the Middle East from 27 BCE to 476 CE (Western) / 1453 CE (Eastern/Byzantine). Major influence on law, governance, language, engineering, and Western culture.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Western Legal Tradition", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Western Legal Tradition",
        "type": "CONCEPT",
        "aliases": ["Roman law tradition", "civil law"],
        "description": "Legal tradition derived substantially from Roman law, transmitted through medieval canon law and secular codes. Foundation of legal systems across continental Europe, Latin America, and former European colonies.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "Silk Road",
        "type": "CONCEPT",
        "aliases": ["Silk Routes", "ancient Eurasian trade network"],
        "description": "Network of ancient trade routes connecting China, Central Asia, South Asia, the Middle East, East Africa, and Europe (c.2nd century BCE – 15th century CE). Facilitated exchange of silk, spices, ideas, religions, and diseases across Eurasia.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "CONNECTED_TO", "obj": "Trans-Saharan Trade", "eclass": "HISTORICAL", "conf": 0.9, "src": _PROV_ACAD},
            {"rel": "INFLUENCES", "obj": "Buddhism", "eclass": "HISTORICAL", "conf": 0.9, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Trans-Saharan Trade",
        "type": "CONCEPT",
        "aliases": ["trans-Saharan trade routes", "Saharan caravan routes"],
        "description": "Ancient and medieval trade routes crossing the Sahara Desert linking sub-Saharan Africa with North Africa and the Mediterranean. Primarily traded gold, salt, slaves, and ivory. Enabled the wealth of the Mali and Songhai Empires.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Mali Empire", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Devaluation of Gold",
        "type": "CONCEPT",
        "aliases": ["gold inflation", "currency devaluation"],
        "description": "Reduction in the exchange value of gold relative to other goods. In the economics domain, an increase in gold supply without corresponding increase in demand drives devaluation — as occurred in North Africa following Mansa Musa's Hajj.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [],
    },

    # ── GEOGRAPHY ────────────────────────────────────────────────────────────
    {
        "label": "Sahara Desert",
        "type": "PLACE",
        "aliases": ["the Sahara", "Great Desert"],
        "description": "Largest hot desert in the world (~9.2 million km²), covering most of North Africa. Major barrier and connector — trade routes and migrations cross it; its expansion has shaped civilisations across millennia.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "BELONGS_TO", "obj": "African Continent", "eclass": "VERIFIED", "conf": 1.0, "src": _PROV_CONS},
            {"rel": "INFLUENCES", "obj": "Trans-Saharan Trade", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Mesopotamia",
        "type": "PLACE",
        "aliases": ["the Land Between Rivers", "ancient Iraq"],
        "description": "Historical region between the Tigris and Euphrates rivers (modern Iraq and parts of Syria/Turkey). Site of some of humanity's earliest civilisations: Sumeria, Akkad, Babylon, Assyria. Birthplace of writing (cuneiform), the wheel, and complex city-states.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "ASSOCIATED_WITH", "obj": "Cuneiform Writing", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Cuneiform Writing",
        "type": "CONCEPT",
        "aliases": ["cuneiform script", "Sumerian writing"],
        "description": "One of the earliest writing systems, developed in Mesopotamia around 3100 BCE. Impressed onto clay tablets using a reed stylus, producing wedge-shaped marks. Used for administrative, literary, and religious texts.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "TEMPORALLY_PRECEDES", "obj": "Alphabetic Writing", "eclass": "HISTORICAL", "conf": 0.9, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Alphabetic Writing",
        "type": "CONCEPT",
        "aliases": ["alphabet", "phonemic script"],
        "description": "Writing system where symbols represent phonemes (sounds). Developed in the ancient Near East around 1800–1200 BCE. Ancestor of most modern writing systems including Arabic, Latin, Greek, Hebrew, and Cyrillic scripts.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "Amazon River Basin",
        "type": "PLACE",
        "aliases": ["Amazonia", "Amazon rainforest"],
        "description": "World's largest tropical rainforest and river drainage basin (~7 million km²) in South America. Home to extraordinary biodiversity and hundreds of indigenous cultures with distinct languages and knowledge systems.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "ASSOCIATED_WITH", "obj": "Indigenous Knowledge Systems", "eclass": "VERIFIED", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Indigenous Knowledge Systems",
        "type": "CONCEPT",
        "aliases": ["traditional ecological knowledge", "IKS"],
        "description": "Bodies of knowledge, practice, and belief developed by indigenous peoples across generations through direct experience with their environment. Encompasses ecological, medicinal, agricultural, cosmological, and social knowledge.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "CHALLENGES", "obj": "Western Scientific Framework", "eclass": "SOURCE_ATTRIBUTED", "conf": 0.7, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Western Scientific Framework",
        "type": "CONCEPT",
        "aliases": ["scientific method", "Western science"],
        "description": "The epistemological tradition centred on empirical observation, hypothesis testing, peer review, and falsifiability. Developed from Enlightenment Europe. Dominant global knowledge-validation system today, though challenged as a complete framework by postcolonial and indigenous knowledge scholars.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "DERIVED_FROM", "obj": "Enlightenment", "eclass": "HISTORICAL", "conf": 0.95, "src": _PROV_ACAD},
        ],
    },

    # ── MYTHOLOGY ────────────────────────────────────────────────────────────
    {
        "label": "Hero's Journey",
        "type": "CONCEPT",
        "aliases": ["monomyth", "Campbell's monomyth"],
        "description": "Narrative archetype identified by Joseph Campbell (1949, 'The Hero with a Thousand Faces'): a hero ventures from ordinary world → enters special world → faces trials → transforms → returns with boon. Appears across cultures from Gilgamesh to modern film. Cross-cultural structural claim is contested by scholars who note cultural specificity.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "PROPOSED_BY", "obj": "Joseph Campbell", "eclass": "SOURCE_ATTRIBUTED", "conf": 1.0, "src": _PROV_ACAD},
            {"rel": "ANALOGOUS_TO", "obj": "Trickster Archetype", "eclass": "SYMBOLIC", "conf": 0.7, "src": _PROV_ACAD},
            {"rel": "INFLUENCES", "obj": "Narrative Theory", "eclass": "SOURCE_ATTRIBUTED", "conf": 0.9, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Joseph Campbell",
        "type": "PERSON",
        "aliases": ["Campbell"],
        "description": "American mythologist (1904–1987). Synthesised comparative mythology across world cultures in 'The Hero with a Thousand Faces' (1949) and 'The Masks of God' series. Coined the term 'monomyth'. Major influence on George Lucas (Star Wars).",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "ASSOCIATED_WITH", "obj": "Hero's Journey", "eclass": "VERIFIED", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Trickster Archetype",
        "type": "CONCEPT",
        "aliases": ["trickster figure", "trickster deity"],
        "description": "Cross-cultural mythic figure who breaks rules, disrupts order, and enables transformation through transgression. Examples: Anansi (Akan/West African), Loki (Norse), Coyote (various Native American), Hermes (Greek), Br'er Rabbit (African American). Connects to chaos, creativity, and liminal spaces.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "REPRESENTS", "obj": "Chaos and Transformation", "eclass": "SYMBOLIC", "conf": 0.9, "src": _PROV_ACAD},
            {"rel": "ASSOCIATED_WITH", "obj": "Anansi", "eclass": "SYMBOLIC", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Chaos and Transformation",
        "type": "CONCEPT",
        "aliases": ["creative destruction", "disruption as creation"],
        "description": "The duality of chaos as both destructive and generative. In mythological thinking, disorder is often the precondition for new order. Parallels in modern complexity theory (edge of chaos as site of emergence).",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "Anansi",
        "type": "SYMBOLIC",
        "aliases": ["Kwaku Anansi", "Aunt Nancy"],
        "description": "Spider deity and trickster figure in Akan mythology (Ghana/West Africa). Symbol of wisdom, storytelling, and cunning. Stories spread across the African diaspora via the transatlantic slave trade; evolved into Br'er Rabbit in North American tradition.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "BELONGS_TO", "obj": "Akan Culture", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
            {"rel": "REPRESENTS", "obj": "Trickster Archetype", "eclass": "SYMBOLIC", "conf": 1.0, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Akan Culture",
        "type": "CULTURAL",
        "aliases": ["Akan people", "Akan"],
        "description": "Ethnic group and culture of southern Ghana and parts of Ivory Coast. Rich oral literary tradition (including Anansi stories), known for Kente cloth, adinkra symbols, matrilineal social structure, and the Asante Empire.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "BELONGS_TO", "obj": "West Africa", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Prometheus",
        "type": "SYMBOLIC",
        "aliases": ["Prometheus Bound", "the Titan fire-bringer"],
        "description": "Greek Titan who stole fire from the gods and gave it to humanity, enabling civilization, technology, and arts. Punished by Zeus (eternal torment). Symbolic archetype: the rebel creator who suffers for transgression that benefits others. Reappears in Frankenstein, Lucifer myth, modernity narratives.",
        "sources": [_PROV_PRIM, _PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "BELONGS_TO", "obj": "Greek Mythology", "eclass": "SYMBOLIC", "conf": 1.0, "src": _PROV_PRIM},
            {"rel": "REPRESENTS", "obj": "Technology as Transgression", "eclass": "SYMBOLIC", "conf": 0.9, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Greek Mythology",
        "type": "CULTURAL",
        "aliases": ["Hellenic mythology", "ancient Greek religion"],
        "description": "Body of myths originating in ancient Greece, primarily transmitted through Homer's epics and Hesiod's Theogony and Works and Days. Encompasses gods (Olympians), heroes, monsters, and cosmological narratives. Foundational influence on Western literature, art, and culture.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Roman Mythology", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Roman Mythology",
        "type": "CULTURAL",
        "aliases": ["Roman religion", "Latin mythology"],
        "description": "Religious and mythological tradition of ancient Rome, heavily syncretised with Greek mythology (Zeus→Jupiter, Hera→Juno, etc.) while incorporating Italic and Etruscan elements. Transmitted through Virgil's Aeneid, Ovid's Metamorphoses.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "Technology as Transgression",
        "type": "CONCEPT",
        "aliases": ["technological hubris", "fire-theft narrative"],
        "description": "The recurring mythological motif that human technological achievement represents theft or transgression against divine order, often punished. Prometheus, the Tower of Babel, Frankenstein. Reflects cultural ambivalence about technological progress.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [],
    },

    # ── PHILOSOPHY ───────────────────────────────────────────────────────────
    {
        "label": "Socrates",
        "type": "PERSON",
        "aliases": ["Sokrates"],
        "description": "Athenian philosopher (c.470–399 BCE). Developed the Socratic method (elenchus): systematic questioning to expose contradictions and elicit truth. Left no writings; known through Plato's dialogues and Xenophon. Executed by Athens for impiety and corrupting youth.",
        "sources": [_PROV_PRIM, _PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "PROPOSED_BY", "obj": "Socratic Method", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_PRIM},
            {"rel": "ASSOCIATED_WITH", "obj": "Plato", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_PRIM},
        ],
    },
    {
        "label": "Socratic Method",
        "type": "CONCEPT",
        "aliases": ["elenchus", "Socratic dialogue", "method of inquiry"],
        "description": "Philosophical technique of cooperative argumentative dialogue, using questions to stimulate critical thinking and expose contradictions in the interlocutor's beliefs. Still fundamental to philosophical education and legal reasoning.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Epistemology", "eclass": "HISTORICAL", "conf": 0.9, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Plato",
        "type": "PERSON",
        "aliases": ["Platon"],
        "description": "Athenian philosopher (c.428–348 BCE), student of Socrates, teacher of Aristotle. Founded the Academy (first institution of higher learning in the Western world). Developed Theory of Forms: abstract, immaterial Forms are the most real things; the physical world is a shadow. Major works: Republic, Symposium, Phaedo.",
        "sources": [_PROV_CONS, _PROV_PRIM],
        "domain": "Humanities",
        "claims": [
            {"rel": "PROPOSED_BY", "obj": "Theory of Forms", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_PRIM},
            {"rel": "ASSOCIATED_WITH", "obj": "Socrates", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_PRIM},
            {"rel": "ASSOCIATED_WITH", "obj": "Aristotle", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Theory of Forms",
        "type": "CONCEPT",
        "aliases": ["Platonic Forms", "Theory of Ideas"],
        "description": "Plato's metaphysical doctrine that the material world is a shadow of eternal, perfect, abstract Forms (Ideas). The Form of the Good is highest. Knowledge is recollection (anamnesis) of Forms the soul knew before birth. Foundational to idealism and rationalism.",
        "sources": [_PROV_PRIM, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "CONTRADICTS", "obj": "Empiricism", "eclass": "SOURCE_ATTRIBUTED", "conf": 0.85, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Aristotle",
        "type": "PERSON",
        "aliases": ["Aristoteles"],
        "description": "Greek philosopher (384–322 BCE), student of Plato, tutor to Alexander the Great. Founded the Lyceum. Systematised logic (syllogism), biology, physics, ethics, politics, rhetoric, and aesthetics. His work was the foundation of medieval scholasticism via Arabic transmission.",
        "sources": [_PROV_CONS, _PROV_PRIM],
        "domain": "Humanities",
        "claims": [
            {"rel": "PROPOSED_BY", "obj": "Formal Logic", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
            {"rel": "ASSOCIATED_WITH", "obj": "Empiricism", "eclass": "SOURCE_ATTRIBUTED", "conf": 0.7, "src": _PROV_ACAD},
            {"rel": "INFLUENCES", "obj": "Islamic Golden Age", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Formal Logic",
        "type": "CONCEPT",
        "aliases": ["Aristotelian logic", "syllogism", "deductive logic"],
        "description": "System of valid reasoning based on defined rules for drawing conclusions from premises. Aristotle's syllogism (all A are B; all B are C; therefore all A are C) was the dominant logical framework for nearly 2000 years. Foundation of mathematics, computer science, and analytic philosophy.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "TEMPORALLY_PRECEDES", "obj": "Mathematical Logic", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Mathematical Logic",
        "type": "CONCEPT",
        "aliases": ["symbolic logic", "modern logic"],
        "description": "Extension of formal logic using mathematical notation (Frege, Russell, Whitehead, Gödel). Foundation of proof theory, set theory, computability, and the theoretical basis of computer science.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "Epistemology",
        "type": "CONCEPT",
        "aliases": ["theory of knowledge", "gnoseology"],
        "description": "Branch of philosophy concerned with the nature, scope, and limits of knowledge. Central questions: What is knowledge? How is it justified? What can we know? Major positions: rationalism (reason is primary), empiricism (experience is primary), scepticism (knowledge may be impossible).",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "CONNECTED_TO", "obj": "Ethics", "eclass": "SOURCE_ATTRIBUTED", "conf": 0.8, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Empiricism",
        "type": "CONCEPT",
        "aliases": ["empirical tradition", "sensory knowledge"],
        "description": "Philosophical tradition holding that knowledge derives from sensory experience. Major empiricists: Aristotle (proto-empiricist), John Locke, David Hume, George Berkeley. Counterpole to rationalism. Foundation of the scientific method.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "CHALLENGES", "obj": "Theory of Forms", "eclass": "SOURCE_ATTRIBUTED", "conf": 0.85, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Ethics",
        "type": "CONCEPT",
        "aliases": ["moral philosophy", "normative ethics"],
        "description": "Branch of philosophy concerned with moral questions: what is right action? What is good? Major frameworks: virtue ethics (Aristotle — character), deontology (Kant — duty/rules), consequentialism (Mill/Bentham — outcomes), care ethics (Noddings — relationships).",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "ASSOCIATED_WITH", "obj": "Immanuel Kant", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Immanuel Kant",
        "type": "PERSON",
        "aliases": ["Kant"],
        "description": "German philosopher (1724–1804). Central figure of Enlightenment thought. Major works: Critique of Pure Reason (epistemology), Critique of Practical Reason (ethics), Critique of Judgment (aesthetics). Developed the Categorical Imperative as the foundation of morality: act only according to maxims you could will to be universal laws.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "PROPOSED_BY", "obj": "Categorical Imperative", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
            {"rel": "ASSOCIATED_WITH", "obj": "Enlightenment", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Categorical Imperative",
        "type": "CONCEPT",
        "aliases": ["Kant's moral law", "universal law formulation"],
        "description": "Kant's foundational ethical principle: 'Act only according to that maxim whereby you can at the same time will that it should become a universal law.' Deontological — moral duty is independent of consequences. Formulation: treat humanity always as an end, never merely as a means.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "BELONGS_TO", "obj": "Ethics", "eclass": "VERIFIED", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Enlightenment",
        "type": "CONCEPT",
        "aliases": ["Age of Reason", "Aufklärung"],
        "description": "Intellectual movement of 17th–18th century Europe emphasising reason, individualism, and science over tradition and religious authority. Key figures: Locke, Voltaire, Rousseau, Hume, Kant, Newton. Produced modern liberal democracy, human rights discourse, and the scientific method as dominant epistemology.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Western Scientific Framework", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
            {"rel": "INFLUENCES", "obj": "Democracy", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },

    # ── LITERATURE ───────────────────────────────────────────────────────────
    {
        "label": "Homer",
        "type": "PERSON",
        "aliases": ["Homer of Chios", "the poet"],
        "description": "Ancient Greek poet traditionally credited with composing the Iliad and the Odyssey (c.8th century BCE). Whether a single historical person is debated (the 'Homeric question'). The epics are the oldest surviving works of Western literature and foundational to Western cultural tradition.",
        "sources": [_PROV_PRIM, _PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "CREATED_BY", "obj": "Iliad", "eclass": "HISTORICAL", "conf": 0.8, "src": _PROV_PRIM},
            {"rel": "CREATED_BY", "obj": "Odyssey", "eclass": "HISTORICAL", "conf": 0.8, "src": _PROV_PRIM},
        ],
    },
    {
        "label": "Iliad",
        "type": "CONCEPT",
        "aliases": ["the Iliad"],
        "description": "Ancient Greek epic poem (c.8th century BCE) attributed to Homer. Narrates events during the Trojan War — the wrath of Achilles. First major work of Western literature. Explores themes of honour (timé), fate (moira), heroism, grief, and the futility of war.",
        "sources": [_PROV_PRIM, _PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Western Literary Canon", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
            {"rel": "REPRESENTS", "obj": "Hero's Journey", "eclass": "SYMBOLIC", "conf": 0.8, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Odyssey",
        "type": "CONCEPT",
        "aliases": ["the Odyssey", "Odysseus's voyage"],
        "description": "Ancient Greek epic poem (c.8th century BCE) attributed to Homer. Narrates the decade-long journey home of Odysseus (Ulysses) after the fall of Troy. Foundational text for themes of homecoming, identity, temptation, and the journey as transformation.",
        "sources": [_PROV_PRIM, _PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Western Literary Canon", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Western Literary Canon",
        "type": "CONCEPT",
        "aliases": ["literary canon", "canon of world literature"],
        "description": "Body of literature considered foundational or exemplary in Western culture. Contested: originally Eurocentric and male-dominated; increasingly challenged and expanded to include world literatures, women writers, and postcolonial voices.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "CHALLENGES", "obj": "World Literature Diversity", "eclass": "SOURCE_ATTRIBUTED", "conf": 0.8, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "World Literature Diversity",
        "type": "CONCEPT",
        "aliases": ["global literary traditions", "non-Western literature"],
        "description": "Recognition of the richness of literary traditions outside the Western canon — African oral epics (Sundiata, Ozidi Saga), Sanskrit epics (Mahabharata, Ramayana), Chinese classical literature, Arabic maqāma, Japanese mono no aware tradition, Mesoamerican Popol Vuh.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "Magical Realism",
        "type": "CONCEPT",
        "aliases": ["magic realism", "realismo mágico"],
        "description": "Literary mode in which magical elements appear in an otherwise realistic setting as everyday occurrences. Associated with Latin American literature (Borges, García Márquez, Allende) and African literature (Ben Okri). Reflects worldviews in which the spiritual and material interpenetrate.",
        "sources": [_PROV_ACAD, _PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "ASSOCIATED_WITH", "obj": "Gabriel García Márquez", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Gabriel García Márquez",
        "type": "PERSON",
        "aliases": ["García Márquez", "Gabo"],
        "description": "Colombian novelist and journalist (1927–2014). Nobel Prize in Literature (1982). Author of 'One Hundred Years of Solitude' (1967) and 'Love in the Time of Cholera' (1985). Central figure of the Latin American Boom. Master of magical realism.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "CREATED_BY", "obj": "One Hundred Years of Solitude", "eclass": "VERIFIED", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "One Hundred Years of Solitude",
        "type": "CONCEPT",
        "aliases": ["Cien años de soledad", "100 Years of Solitude"],
        "description": "Novel by Gabriel García Márquez (1967). Chronicles seven generations of the Buendía family in the fictional town of Macondo. Defining work of magical realism. Sold over 50 million copies; translated into 46 languages. Considered the defining novel of the Latin American Boom.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "REPRESENTS", "obj": "Magical Realism", "eclass": "VERIFIED", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Oral Tradition",
        "type": "CONCEPT",
        "aliases": ["oral culture", "oral literature", "orature"],
        "description": "Transmission of cultural knowledge, history, law, and artistic expression through spoken word across generations, without written records. Griots (West Africa), Aboriginal Songlines (Australia), Homeric oral composition. Oral traditions carry complex information and are often undervalued in literate-centric epistemologies.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "World Literature Diversity", "eclass": "HISTORICAL", "conf": 0.9, "src": _PROV_ACAD},
        ],
    },

    # ── ART HISTORY ──────────────────────────────────────────────────────────
    {
        "label": "Cave Painting",
        "type": "CONCEPT",
        "aliases": ["prehistoric art", "cave art", "parietal art"],
        "description": "Earliest known visual art by modern humans, created on cave walls and ceilings. Lascaux (France, c.17,000 BCE), Altamira (Spain, c.14,000 BCE), Sulawesi (Indonesia, c.45,500 BCE — among the oldest known figurative art). Motifs: animals, hand stencils, geometric patterns.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "TEMPORALLY_PRECEDES", "obj": "Baroque", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
            {"rel": "REPRESENTS", "obj": "Visual Meaning-Making", "eclass": "SYMBOLIC", "conf": 0.9, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Visual Meaning-Making",
        "type": "CONCEPT",
        "aliases": ["visual communication", "visual culture"],
        "description": "The human capacity to create and interpret meaning through visual forms — images, symbols, gesture, spatial arrangement. Foundational to art, design, architecture, and typography.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "Baroque",
        "type": "CONCEPT",
        "aliases": ["Baroque art", "Baroque period"],
        "description": "European art movement c.1600–1750. Characterized by dramatic use of light and shadow (chiaroscuro), movement, emotional intensity, and grandeur. Emerged partly in response to the Protestant Reformation. Major figures: Caravaggio, Rubens, Rembrandt, Bernini, Bach (in music).",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Romanticism", "eclass": "HISTORICAL", "conf": 0.85, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Romanticism",
        "type": "CONCEPT",
        "aliases": ["Romantic movement", "Romantic era"],
        "description": "19th-century artistic and intellectual movement emphasising emotion, nature, imagination, and individual experience over rationalism and industrialisation. Reaction against Enlightenment and the Industrial Revolution. Literature: Byron, Keats, Shelley. Music: Beethoven, Schubert, Schumann.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "CHALLENGES", "obj": "Enlightenment", "eclass": "HISTORICAL", "conf": 0.9, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Wabi-sabi",
        "type": "CONCEPT",
        "aliases": ["wabi sabi"],
        "description": "Japanese aesthetic philosophy centred on the acceptance of transience and imperfection. Finds beauty in the worn, weathered, asymmetric, and incomplete. Derived from Buddhist notions of impermanence (anicca). Influenced Japanese ceramics (kintsugi), garden design, and tea ceremony.",
        "sources": [_PROV_ACAD, _PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "ASSOCIATED_WITH", "obj": "Buddhism", "eclass": "SOURCE_ATTRIBUTED", "conf": 0.85, "src": _PROV_ACAD},
            {"rel": "BELONGS_TO", "obj": "Japanese Aesthetic Tradition", "eclass": "VERIFIED", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Japanese Aesthetic Tradition",
        "type": "CULTURAL",
        "aliases": ["Japanese aesthetics", "Japanese art tradition"],
        "description": "Set of aesthetic values central to Japanese culture: wabi-sabi (impermanence), ma (negative space/pause), mono no aware (pathos of things), iki (sophisticated understated elegance), and yūgen (profound mystery). Expressed through art, architecture, garden design, and everyday objects.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "Bauhaus",
        "type": "CULTURAL",
        "aliases": ["Bauhaus school", "Staatliches Bauhaus"],
        "description": "German art school (1919–1933) founded by Walter Gropius in Weimar. Sought to unify fine arts and functional design. Foundational to modernist design, typography, and architecture. Closed by the Nazis; faculty emigrated to the US and disseminated its ideas globally.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Modernist Design", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Modernist Design",
        "type": "CONCEPT",
        "aliases": ["modernism in design", "functional design"],
        "description": "Design philosophy emphasising function over ornamentation, industrial materials, and geometric forms. 'Form follows function' (Louis Sullivan). Shaped 20th-century architecture, typography, product design, and graphic design.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [],
    },

    # ── SCIENCE HISTORY ──────────────────────────────────────────────────────
    {
        "label": "Paradigm Shift",
        "type": "CONCEPT",
        "aliases": ["scientific revolution", "Kuhnian shift"],
        "description": "Thomas Kuhn's concept (The Structure of Scientific Revolutions, 1962): science does not progress by linear accumulation of knowledge but through periodic revolutionary changes in framework (paradigm shifts) — Copernican revolution, Darwinian evolution, Einsteinian relativity. Normal science operates within a paradigm until anomalies force a crisis.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "PROPOSED_BY", "obj": "Thomas Kuhn", "eclass": "SOURCE_ATTRIBUTED", "conf": 1.0, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Thomas Kuhn",
        "type": "PERSON",
        "aliases": ["Kuhn"],
        "description": "American philosopher and historian of science (1922–1996). Author of 'The Structure of Scientific Revolutions' (1962), one of the most cited academic books of the 20th century. Developed the concepts of paradigm, normal science, and paradigm shift.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "CHALLENGES", "obj": "Logical Positivism", "eclass": "SOURCE_ATTRIBUTED", "conf": 0.85, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Logical Positivism",
        "type": "CONCEPT",
        "aliases": ["logical empiricism", "Vienna Circle"],
        "description": "Philosophical movement (Vienna Circle, 1920s–30s) holding that meaningful statements must be either empirically verifiable or analytically true (tautologies). Metaphysical claims are meaningless. Major influence on 20th-century philosophy of science. Largely superseded but foundational.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "Isaac Newton",
        "type": "PERSON",
        "aliases": ["Newton", "Sir Isaac Newton"],
        "description": "English mathematician and physicist (1643–1727). Formulated laws of motion and universal gravitation (Principia Mathematica, 1687), co-invented calculus (with Leibniz, contested), discovered spectral decomposition of light. His framework dominated physics for over 200 years until Einstein.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "PROPOSED_BY", "obj": "Newtonian Mechanics", "eclass": "VERIFIED", "conf": 1.0, "src": _PROV_CONS},
            {"rel": "INFLUENCES", "obj": "Enlightenment", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Newtonian Mechanics",
        "type": "CONCEPT",
        "aliases": ["classical mechanics", "Newtonian physics"],
        "description": "Framework of physics based on Newton's three laws of motion and law of universal gravitation. Accurately describes motion at everyday speeds and scales. Superseded at very high speeds by special relativity and at atomic scales by quantum mechanics.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "TEMPORALLY_PRECEDES", "obj": "Relativistic Mechanics", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Relativistic Mechanics",
        "type": "CONCEPT",
        "aliases": ["Einstein's relativity", "special and general relativity"],
        "description": "Einstein's framework of physics: special relativity (1905) — time and space are relative to observer velocity; general relativity (1915) — gravity is curvature of spacetime. Supersedes Newtonian mechanics at high velocities and massive scales.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "Marie Curie",
        "type": "PERSON",
        "aliases": ["Maria Skłodowska-Curie", "Madame Curie"],
        "description": "Polish-French physicist and chemist (1867–1934). First woman to win a Nobel Prize; only person to win Nobel Prizes in two sciences (Physics 1903, Chemistry 1911). Discovered polonium and radium. Pioneered research into radioactivity. Died of aplastic anaemia from radiation exposure.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "ASSOCIATED_WITH", "obj": "Radioactivity Research", "eclass": "VERIFIED", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Radioactivity Research",
        "type": "CONCEPT",
        "aliases": ["radioactivity", "nuclear physics origins"],
        "description": "The scientific study of radioactive decay — the spontaneous emission of particles or energy from unstable atomic nuclei. Curie's discovery of polonium and radium established radioactivity as an atomic property rather than a molecular one, helping overturn prior models of the atom.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [],
    },

    # ── TECHNOLOGY HISTORY ───────────────────────────────────────────────────
    {
        "label": "Johannes Gutenberg",
        "type": "PERSON",
        "aliases": ["Gutenberg", "Johann Gutenberg"],
        "description": "German inventor (c.1400–1468). Developed movable-type printing press in Europe c.1440. The Gutenberg Bible (c.1455) was among the first major books printed with this technology. The press enabled mass literacy, democratised knowledge, accelerated the Reformation and Renaissance.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "CREATED_BY", "obj": "Printing Press", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
            {"rel": "INFLUENCES", "obj": "Protestant Reformation", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Printing Press",
        "type": "CONCEPT",
        "aliases": ["movable type printing", "Gutenberg press"],
        "description": "Mechanical device for mass-reproducing text and images using movable type, developed in Europe by Gutenberg c.1440 (building on earlier Chinese and Korean block-printing). Enabling technology for the Reformation, Scientific Revolution, and Enlightenment by dramatically reducing cost of distributing knowledge.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Enlightenment", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Protestant Reformation",
        "type": "CONCEPT",
        "aliases": ["the Reformation", "Reformation"],
        "description": "16th-century movement to reform the Roman Catholic Church, initiated by Martin Luther's 95 Theses (1517). Resulted in the establishment of Protestant churches. Accelerated by the printing press, which enabled mass distribution of reformist ideas. Transformed European politics, culture, and religion.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Enlightenment", "eclass": "HISTORICAL", "conf": 0.85, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Industrial Revolution",
        "type": "CONCEPT",
        "aliases": ["industrialisation", "First Industrial Revolution"],
        "description": "Transition from agrarian-handicraft economies to manufacturing-factory economies (c.1760–1840, beginning in Britain). Enabled by steam power, mechanised textile production, iron and steel industries. Transformed social structures, urbanisation, labour relations, and environmental conditions.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "CAUSES", "obj": "Urbanisation", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
            {"rel": "CHALLENGES", "obj": "Feudalism", "eclass": "HISTORICAL", "conf": 0.85, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Urbanisation",
        "type": "CONCEPT",
        "aliases": ["urban growth", "city expansion"],
        "description": "Demographic and social process of increasing concentration of population in urban areas. Accelerated by the Industrial Revolution. Associated with social stratification, new labour forms, slums, sanitation challenges, and eventually civil infrastructure.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "Ada Lovelace",
        "type": "PERSON",
        "aliases": ["Ada King, Countess of Lovelace", "Augusta Ada Byron"],
        "description": "English mathematician (1815–1852), daughter of Lord Byron. Collaborated with Charles Babbage on his Analytical Engine. Wrote what is considered the first algorithm intended to be processed by a machine (1843). Widely regarded as the first computer programmer.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "ASSOCIATED_WITH", "obj": "Computation History", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Computation History",
        "type": "CONCEPT",
        "aliases": ["history of computing", "computing origins"],
        "description": "Historical trajectory from mechanical calculation (Babbage Analytical Engine, 1837) through electromechanical systems (Turing, 1936) to electronic computers (ENIAC, 1945) and onwards. Ada Lovelace, Alan Turing, Grace Hopper, Claude Shannon are foundational figures.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [],
    },

    # ── ARCHITECTURE ─────────────────────────────────────────────────────────
    {
        "label": "Gothic Architecture",
        "type": "CONCEPT",
        "aliases": ["Gothic style", "medieval Gothic"],
        "description": "European architectural style (c.1100–1500 CE) characterised by pointed arches, ribbed vaults, flying buttresses, and large stained-glass windows. Developed in France; spread across Europe. Major examples: Notre-Dame de Paris, Chartres Cathedral, Cologne Cathedral. Associated with Christian theology: verticality as aspiration toward the divine.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "TEMPORALLY_PRECEDES", "obj": "Renaissance Architecture", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Renaissance Architecture",
        "type": "CONCEPT",
        "aliases": ["Renaissance style", "Italian Renaissance architecture"],
        "description": "Architectural style c.1400–1600 centred in Italy, reviving Greek and Roman classical forms. Emphasis on symmetry, proportion, geometry, and regularity based on ancient Roman models. Vitruvian principles revived. Key figures: Brunelleschi, Bramante, Michelangelo, Palladio.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Modernist Design", "eclass": "HISTORICAL", "conf": 0.7, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Vitruvian Principles",
        "type": "CONCEPT",
        "aliases": ["Vitruvius", "firmitas utilitas venustas"],
        "description": "Architectural theory from Vitruvius's 'De Architectura' (c.15 BCE): a building must have firmitas (structural strength), utilitas (functional usefulness), and venustas (beauty/aesthetics). The triad remains foundational in architectural education. Rediscovered during the Renaissance.",
        "sources": [_PROV_PRIM, _PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Renaissance Architecture", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Frank Lloyd Wright",
        "type": "PERSON",
        "aliases": ["FLW", "Wright"],
        "description": "American architect (1867–1959). Developed organic architecture — buildings that harmonise with their natural environment. Major works: Fallingwater, Guggenheim Museum (NY), Usonian houses. Pioneered open-plan interiors, horizontal emphasis, and integration of building with landscape.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "ASSOCIATED_WITH", "obj": "Organic Architecture", "eclass": "VERIFIED", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Organic Architecture",
        "type": "CONCEPT",
        "aliases": ["nature-integrated design", "biophilic architecture"],
        "description": "Architectural philosophy in which a building should grow from its natural environment, materials, and cultural context — not be imposed on the landscape. Associated with Frank Lloyd Wright; precursor to contemporary biophilic design and sustainable architecture.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [],
    },

    # ── MUSIC HISTORY ────────────────────────────────────────────────────────
    {
        "label": "Blues",
        "type": "CULTURAL",
        "aliases": ["the blues", "Delta blues"],
        "description": "Music genre originating in the Deep South of the United States in the late 19th century, primarily in African American communities. Developed from spirituals, work songs, field hollers, and African musical traditions. Foundational to rock, jazz, R&B, soul, and hip-hop.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Rock Music", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
            {"rel": "INFLUENCES", "obj": "Jazz", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Rock Music",
        "type": "CULTURAL",
        "aliases": ["rock and roll", "rock 'n' roll"],
        "description": "Genre of popular music that originated in the United States in the late 1940s and early 1950s from blues, rhythm and blues, and country music. Electric guitar, drums, and bass guitar are central. Transformed popular culture globally from the 1950s onward.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "Jazz",
        "type": "CULTURAL",
        "aliases": ["jazz music"],
        "description": "Music genre originating in African American communities of New Orleans in the late 19th–early 20th century. Characterised by syncopation, improvisation, swung rhythm, and polyrhythm. Draws on blues, ragtime, and African and European musical traditions.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Polyrhythm", "eclass": "HISTORICAL", "conf": 0.85, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Polyrhythm",
        "type": "CONCEPT",
        "aliases": ["cross-rhythm", "multiple simultaneous rhythms"],
        "description": "The simultaneous use of two or more conflicting rhythmic patterns. Central to African traditional music (West African percussion ensembles), jazz, and Afro-Cuban music. Not inherently chaotic — the patterns interlock and resolve.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "ASSOCIATED_WITH", "obj": "West African Musical Tradition", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "West African Musical Tradition",
        "type": "CULTURAL",
        "aliases": ["West African music", "Sub-Saharan African musical tradition"],
        "description": "Rich musical traditions of West Africa including polyrhythmic percussion (djembe, talking drum), griot singing and storytelling, kora, balafon, and communal singing. Root tradition for blues, jazz, gospel, R&B, hip-hop, Afrobeats, and other African diaspora musics.",
        "sources": [_PROV_ACAD, _PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Blues", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Johann Sebastian Bach",
        "type": "PERSON",
        "aliases": ["J.S. Bach", "Bach"],
        "description": "German composer and musician (1685–1750). Baroque master. Works include the Well-Tempered Clavier, Mass in B minor, St Matthew Passion, Goldberg Variations, and the Brandenburg Concertos. Foundational to Western classical music; influenced virtually every Western composer after him.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "BELONGS_TO", "obj": "Baroque", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
            {"rel": "INFLUENCES", "obj": "Western Classical Music", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Western Classical Music",
        "type": "CULTURAL",
        "aliases": ["classical music tradition", "art music"],
        "description": "Formal musical tradition of Western Europe, developed c.9th–21st century. Major periods: Medieval, Renaissance, Baroque, Classical, Romantic, Modern. Characterised by written notation, complex harmonic structures, and professional performance context.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "Griots",
        "type": "CULTURAL",
        "aliases": ["griot", "jali", "jeli", "djeli"],
        "description": "West African oral historians, storytellers, praise-singers, and musicians who serve as living repositories of community memory. Griots preserve genealogies, historical narratives, and cultural knowledge across generations through oral performance. Professional caste in Manding cultures (Mandé people).",
        "sources": [_PROV_ACAD, _PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "BELONGS_TO", "obj": "West African Musical Tradition", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
            {"rel": "REPRESENTS", "obj": "Oral Tradition", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_ACAD},
        ],
    },

    # ── CULTURAL PRACTICES ───────────────────────────────────────────────────
    {
        "label": "Rites of Passage",
        "type": "CONCEPT",
        "aliases": ["rites de passage", "initiation rites", "life-cycle rituals"],
        "description": "Rituals that mark transitions between social statuses or life stages: birth, coming-of-age, marriage, death. Term coined by Arnold van Gennep (1909). Three phases: separation (from old status), liminality (threshold, betwixt-and-between), incorporation (into new status).",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "ANALOGOUS_TO", "obj": "Hero's Journey", "eclass": "SYMBOLIC", "conf": 0.8, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Kintsugi",
        "type": "CONCEPT",
        "aliases": ["kintsukuroi", "golden repair"],
        "description": "Japanese art of repairing broken pottery with gold (or silver/platinum) lacquer. Treats breakage as part of the object's history rather than something to hide. Embodies wabi-sabi: the broken and repaired object is more beautiful than the original. Widely used as a metaphor for resilience.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "REPRESENTS", "obj": "Wabi-sabi", "eclass": "SYMBOLIC", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Carnival",
        "type": "CONCEPT",
        "aliases": ["Mardi Gras", "Carnaval", "festival season"],
        "description": "Festive season immediately before Lent in Christian tradition, characterised by public celebrations, masquerade, music, and reversal of social hierarchies. Roots in ancient Roman Saturnalia and agricultural festivals. Major carnivals: Venice, Rio de Janeiro, New Orleans (Mardi Gras), Trinidad.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "ASSOCIATED_WITH", "obj": "Rites of Passage", "eclass": "SOURCE_ATTRIBUTED", "conf": 0.7, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Ancestor Veneration",
        "type": "CONCEPT",
        "aliases": ["ancestor worship", "ancestral reverence"],
        "description": "Cultural and religious practice of honouring deceased relatives as influential presences in the lives of the living. Present across many cultures: Chinese ancestral rites, Yoruba Egungun, Japanese O-Bon, Mexican Día de los Muertos, West African traditions. Treats death as a transition rather than an ending.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "ASSOCIATED_WITH", "obj": "Yoruba Religion", "eclass": "SOURCE_ATTRIBUTED", "conf": 0.9, "src": _PROV_ACAD},
        ],
    },

    # ── RELIGIONS AS KNOWLEDGE SYSTEMS ───────────────────────────────────────
    {
        "label": "Buddhism",
        "type": "CULTURAL",
        "aliases": ["the Dharma", "Buddha Dhamma"],
        "description": "Knowledge system and spiritual tradition founded by Siddhartha Gautama (the Buddha, c.5th–4th century BCE) in ancient India. Core teachings: Four Noble Truths (dukkha — suffering; its origin; its cessation; the path), Eightfold Path, impermanence (anicca), no-self (anatta). Spread across Asia via the Silk Road; now global.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Japanese Aesthetic Tradition", "eclass": "HISTORICAL", "conf": 0.9, "src": _PROV_ACAD},
            {"rel": "INFLUENCES", "obj": "Silk Road", "eclass": "HISTORICAL", "conf": 0.8, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Islam",
        "type": "CULTURAL",
        "aliases": ["Islamic tradition", "Muslim faith"],
        "description": "Monotheistic knowledge system and religion founded in 7th-century Arabia by the Prophet Muhammad. Five Pillars: Shahada (faith declaration), Salat (prayer), Zakat (charity), Sawm (fasting during Ramadan), Hajj (pilgrimage to Mecca). Central text: the Quran. Gave rise to the Islamic Golden Age of science, philosophy, and mathematics.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Islamic Golden Age", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Islamic Golden Age",
        "type": "CONCEPT",
        "aliases": ["Islamic Renaissance", "Golden Age of Islam"],
        "description": "Period of Islamic history (c.8th–13th century) characterised by remarkable advances in science, mathematics, astronomy, philosophy, and medicine. Preserved and extended Greek knowledge (especially Aristotle) and transmitted it to medieval Europe. Key figures: Al-Khwarizmi (algebra), Ibn Sina (Avicenna, medicine), Al-Biruni (anthropology).",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Renaissance Architecture", "eclass": "HISTORICAL", "conf": 0.7, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Yoruba Religion",
        "type": "CULTURAL",
        "aliases": ["Yoruba traditional religion", "Ifá", "Orisha tradition"],
        "description": "West African knowledge system and spiritual tradition of the Yoruba people (Nigeria, Benin, Togo). Structured cosmology: Olodumare (supreme being), Orishas (divine forces/principles), ancestral spirits, divination system (Ifá — a sophisticated knowledge corpus). Spread via the African diaspora as Candomblé, Santería, Vodou.",
        "sources": [_PROV_ACAD, _PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Afro-Diasporic Religions", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_ACAD},
            {"rel": "BELONGS_TO", "obj": "West Africa", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Afro-Diasporic Religions",
        "type": "CULTURAL",
        "aliases": ["African diaspora religions", "Candomblé", "Santería", "Vodou"],
        "description": "Religious traditions developed in the Americas by enslaved Africans and their descendants, blending West African (primarily Yoruba, Fon, Ewe) traditions with Catholicism and indigenous elements. Major examples: Candomblé (Brazil), Santería/Lucumí (Cuba), Vodou (Haiti), Obeah (Caribbean).",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "Animism",
        "type": "CONCEPT",
        "aliases": ["animist worldview", "spirit world belief"],
        "description": "Worldview attributing spiritual essence, agency, or personhood to non-human entities (animals, plants, rivers, mountains, objects). The predominant cosmological framework of hunter-gatherer and many agricultural societies globally. Not a unified 'religion' but a broad relational ontology.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "ASSOCIATED_WITH", "obj": "Indigenous Knowledge Systems", "eclass": "SOURCE_ATTRIBUTED", "conf": 0.85, "src": _PROV_ACAD},
        ],
    },

    # ── LANGUAGES ────────────────────────────────────────────────────────────
    {
        "label": "Proto-Indo-European",
        "type": "CONCEPT",
        "aliases": ["PIE", "Proto-Indo-European language"],
        "description": "Hypothetical ancestor language (not directly attested) reconstructed by historical linguistics, estimated spoken c.4500–2500 BCE. Ancestor of the Indo-European language family (English, Spanish, French, German, Hindi, Persian, Russian, etc.) — the largest language family by number of speakers.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "HYPOTHESISED_AS", "obj": "Common Ancestor of Indo-European", "eclass": "HYPOTHESIS", "conf": 0.85, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Common Ancestor of Indo-European",
        "type": "CONCEPT",
        "aliases": ["Indo-European proto-language"],
        "description": "The inferred single ancestral language from which the Indo-European language family descended, reconstructed through comparative linguistics. Its existence is a scientific consensus; its exact form and homeland are debated (steppe hypothesis vs Anatolia hypothesis).",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "Arabic Language",
        "type": "CULTURAL",
        "aliases": ["Arabic", "al-arabiyya"],
        "description": "Semitic language of the Afro-Asiatic family. Liturgical language of Islam (the Quran is in Classical Arabic). Carrier of the Islamic Golden Age's scientific and philosophical texts into medieval Europe. Today: ~420 million speakers; official language of 26 countries. Rich poetic and literary tradition.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Islamic Golden Age", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Swahili",
        "type": "CULTURAL",
        "aliases": ["Kiswahili"],
        "description": "Bantu language of the Swahili Coast (East Africa). Lingua franca across East, Central, and parts of Southern Africa (~200 million speakers). Developed through centuries of Indian Ocean trade contacts, incorporating Arabic, Persian, Portuguese, and other loanwords. Rich literary tradition in Arabic script before Romanisation.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "BELONGS_TO", "obj": "African Continent", "eclass": "VERIFIED", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Language as Cultural Artefact",
        "type": "CONCEPT",
        "aliases": ["Sapir-Whorf hypothesis", "linguistic relativity"],
        "description": "The view that language shapes thought and perception (Sapir-Whorf hypothesis / linguistic relativity). Strong version (language determines thought) largely rejected; weak version (language influences thought) supported by research. Each language encodes a worldview: different colour terms, tense systems, evidentiality markers.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "ASSOCIATED_WITH", "obj": "Anthropology", "eclass": "SOURCE_ATTRIBUTED", "conf": 0.85, "src": _PROV_ACAD},
        ],
    },

    # ── SOCIETIES ────────────────────────────────────────────────────────────
    {
        "label": "Feudalism",
        "type": "CONCEPT",
        "aliases": ["feudal system", "feudal order"],
        "description": "Medieval European social and political system (roughly 9th–15th century) based on exchange of land (fief) for military service and loyalty. Hierarchical: king → lords → knights → serfs. Eroded by the Black Death, monetisation of economies, and the Renaissance.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "TEMPORALLY_PRECEDES", "obj": "Capitalism", "eclass": "HISTORICAL", "conf": 0.9, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Ubuntu",
        "type": "CONCEPT",
        "aliases": ["ubuntu philosophy", "I am because we are"],
        "description": "African humanist philosophy of personhood and community, most prominent in Nguni Bantu cultures (South Africa, Zimbabwe, etc.). Ubuntu: 'I am because we are' (umuntu ngumuntu ngabantu). Holds that individual identity is constituted through relationships and community. Applied in post-apartheid South Africa's Truth and Reconciliation Commission.",
        "sources": [_PROV_ACAD, _PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "CHALLENGES", "obj": "Western Individualism", "eclass": "SOURCE_ATTRIBUTED", "conf": 0.85, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Western Individualism",
        "type": "CONCEPT",
        "aliases": ["liberal individualism", "individual rights tradition"],
        "description": "Philosophical and cultural tradition emphasising the primacy of the individual person over the collective. Associated with Enlightenment liberalism (Locke, Mill), modern capitalism, and Western legal systems. Contrasts with collectivist traditions in many non-Western societies.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "Social Contract",
        "type": "CONCEPT",
        "aliases": ["social contract theory", "Rousseau's social contract"],
        "description": "Political philosophy concept: individuals consent (explicitly or implicitly) to surrender some freedoms to a political authority in exchange for protection of remaining rights. Theorists: Hobbes (sovereign needed to prevent war of all against all), Locke (protect natural rights), Rousseau (general will). Foundation of modern liberal democracy.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Democracy", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },

    # ── POLITICAL SYSTEMS ────────────────────────────────────────────────────
    {
        "label": "Democracy",
        "type": "CONCEPT",
        "aliases": ["democratic governance", "popular sovereignty"],
        "description": "System of governance in which political authority derives from the consent of the governed. Forms: direct democracy (Athenian), representative democracy (modern), deliberative democracy. Tension between majority rule and protection of minority rights. Ancient Greek origins; modern form developed from 17th-century England and 18th-century revolutions.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "ASSOCIATED_WITH", "obj": "Social Contract", "eclass": "HISTORICAL", "conf": 0.9, "src": _PROV_CONS},
            {"rel": "DERIVED_FROM", "obj": "Enlightenment", "eclass": "HISTORICAL", "conf": 0.95, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Republic",
        "type": "CONCEPT",
        "aliases": ["republican government", "res publica"],
        "description": "Form of government in which the country is considered a public matter (res publica), not private property of rulers. Power exercised via elected representatives. Roman Republic (509–27 BCE) is the classical model. Distinguished from democracy by representative rather than direct participation.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Democracy", "eclass": "HISTORICAL", "conf": 0.85, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Colonialism",
        "type": "CONCEPT",
        "aliases": ["colonial system", "imperialism"],
        "description": "Practice of dominant powers establishing control over other peoples and territories. European colonial period (c.1500–1960s) reshaped global economies, cultures, and political systems. Left legacies: extraction economies, language displacement, cultural trauma, artificial borders. Distinct from (but related to) cultural imperialism.",
        "sources": [_PROV_ACAD, _PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "CAUSES", "obj": "Afro-Diasporic Religions", "eclass": "HISTORICAL", "conf": 0.9, "src": _PROV_ACAD},
        ],
    },

    # ── ECONOMICS ────────────────────────────────────────────────────────────
    {
        "label": "Mercantilism",
        "type": "CONCEPT",
        "aliases": ["mercantilist theory", "bullionism"],
        "description": "Dominant economic theory of 16th–18th century European states: national wealth maximised by exporting more than importing, accumulating gold/silver (bullion), and controlling colonial trade. Led to protectionist policies. Challenged by Adam Smith (The Wealth of Nations, 1776) and the rise of classical liberalism.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "TEMPORALLY_PRECEDES", "obj": "Capitalism", "eclass": "HISTORICAL", "conf": 0.9, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Capitalism",
        "type": "CONCEPT",
        "aliases": ["market capitalism", "market economy"],
        "description": "Economic system in which private individuals own the means of production, goods are produced for profit, and markets coordinate production/distribution. Emerged in England from the 17th–18th century. Produces vast wealth and innovation; also produces inequality, class stratification, and environmental costs.",
        "sources": [_PROV_CONS, _PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "CHALLENGES", "obj": "Gift Economy", "eclass": "SOURCE_ATTRIBUTED", "conf": 0.7, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Gift Economy",
        "type": "CONCEPT",
        "aliases": ["gift exchange", "gift culture", "potlatch"],
        "description": "Economic system in which goods and services are given without explicit agreement for immediate or future reward. Creates social bonds, status, and obligation (Marcel Mauss, The Gift, 1925). Examples: potlatch ceremonies (Pacific Northwest indigenous peoples), Kula ring (Trobriand Islands), open-source software culture.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "Division of Labour",
        "type": "CONCEPT",
        "aliases": ["specialisation of labour", "economic specialisation"],
        "description": "Organisation of production in which workers specialise in particular tasks or roles rather than each producing everything they need. Adam Smith's key insight (The Wealth of Nations, 1776): specialisation dramatically increases productivity (pin factory example). Foundation of industrial and modern economies.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "INFLUENCES", "obj": "Industrial Revolution", "eclass": "HISTORICAL", "conf": 0.9, "src": _PROV_CONS},
        ],
    },

    # ── ANTHROPOLOGY ─────────────────────────────────────────────────────────
    {
        "label": "Anthropology",
        "type": "CONCEPT",
        "aliases": ["human anthropology", "cultural anthropology"],
        "description": "The comparative and holistic study of humanity: biological, cultural, linguistic, and archaeological. Four sub-fields: biological/physical anthropology, cultural/social anthropology, linguistic anthropology, archaeology. Developed largely in the 19th–20th century; now includes critical and decolonial approaches.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "ASSOCIATED_WITH", "obj": "Cultural Relativism", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Cultural Relativism",
        "type": "CONCEPT",
        "aliases": ["cultural relativism principle"],
        "description": "Anthropological principle that a culture's values and practices should be understood on their own terms and within their own context, not judged by the standards of another culture. Franz Boas and his students developed this as a scientific and ethical stance against ethnocentrism. Distinct from moral relativism.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "CHALLENGES", "obj": "Ethnocentrism", "eclass": "SOURCE_ATTRIBUTED", "conf": 1.0, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Ethnocentrism",
        "type": "CONCEPT",
        "aliases": ["cultural bias", "cultural chauvinism"],
        "description": "Tendency to evaluate other cultures according to the standards of one's own culture, and to view one's own culture as superior. A cognitive bias embedded in colonial and nationalist ideologies. Cultural relativism developed as its antidote in anthropology.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [],
    },
    {
        "label": "Structuralism",
        "type": "CONCEPT",
        "aliases": ["structural anthropology", "structural linguistics"],
        "description": "Intellectual method analysing culture, language, and mind as systems of relationships between elements rather than isolated elements. In anthropology (Lévi-Strauss): myths, kinship, and rituals are structured like language — binary oppositions (raw/cooked, nature/culture) organise cultural thought.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "PROPOSED_BY", "obj": "Claude Lévi-Strauss", "eclass": "SOURCE_ATTRIBUTED", "conf": 1.0, "src": _PROV_ACAD},
        ],
    },
    {
        "label": "Claude Lévi-Strauss",
        "type": "PERSON",
        "aliases": ["Lévi-Strauss"],
        "description": "French anthropologist (1908–2009). Father of structural anthropology. Major works: Tristes Tropiques (1955), Mythologiques (4 vols, 1964–1971). Applied structuralist method (from Saussurean linguistics) to the study of myths, kinship systems, and totemism. Argued that apparently different cultural practices share deep universal structures.",
        "sources": [_PROV_CONS],
        "domain": "Humanities",
        "claims": [
            {"rel": "PROPOSED_BY", "obj": "Structuralism", "eclass": "HISTORICAL", "conf": 1.0, "src": _PROV_CONS},
        ],
    },
    {
        "label": "Narrative Theory",
        "type": "CONCEPT",
        "aliases": ["narratology", "narrative studies"],
        "description": "Study of the structure, function, and cultural significance of narrative. Developed across literary theory (Propp, Barthes), linguistics (Labov), psychology (Bruner), and anthropology. A narrative is not just a story — it is a primary cognitive tool for organising experience and transmitting culture.",
        "sources": [_PROV_ACAD],
        "domain": "Humanities",
        "claims": [
            {"rel": "ASSOCIATED_WITH", "obj": "Hero's Journey", "eclass": "SOURCE_ATTRIBUTED", "conf": 0.85, "src": _PROV_ACAD},
        ],
    },

    # ── remaining cross-domain entities ─────────────────────────────────────
    {
        "label": "Narrative Theory",  # duplicate guard — handled by create_entity
        "type": "CONCEPT",
        "aliases": [],
        "description": "",
        "sources": [],
        "domain": "Humanities",
        "claims": [],
    },
]

# ── script logic ──────────────────────────────────────────────────────────────

def _ensure_sources(dry_run: bool) -> None:
    """Add new source records if not already present."""
    sources_path = os.path.join(_WKG_DIR, "sources.json")
    with open(sources_path, "r", encoding="utf-8") as f:
        sources = json.load(f)
    existing_ids = {s["source_id"] for s in sources}
    added = 0
    for src in _NEW_SOURCES:
        if src["source_id"] not in existing_ids:
            sources.append(src)
            added += 1
            _log.info("  + source %s", src["source_id"])
    if added and not dry_run:
        tmp = sources_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(sources, f, indent=2)
        os.replace(tmp, sources_path)
    _log.info("Sources: %d added, %d pre-existing", added, len(existing_ids))


def run(dry_run: bool = False) -> None:
    from runtime.wkg_faculty import create_entity, record_claim

    _ensure_sources(dry_run)

    label_to_id: dict[str, str] = {}
    n_created  = 0
    n_skipped  = 0
    n_claims   = 0
    n_claims_skip = 0

    # ── pass 1: create all entities ──────────────────────────────────────────
    seen_labels: set[str] = set()
    for item in _SEED:
        lbl = item["label"]
        if lbl in seen_labels:
            continue
        seen_labels.add(lbl)

        if dry_run:
            _log.info("  [DRY-RUN] would create entity: %s (%s)", lbl, item["type"])
            label_to_id[lbl] = f"DRY-RUN-{lbl}"
            n_created += 1
            continue

        result = create_entity(
            entity_type=item["type"],
            label=lbl,
            aliases=item.get("aliases") or [],
            description=item.get("description") or "",
            source_ids=item.get("sources") or [],
        )
        if result.get("rejected"):
            _log.info("  SKIP entity (already exists): %s", lbl)
            # still resolve its id for claim edges
            from runtime.wkg_faculty import search_entities as _se
            hits = _se(lbl)
            if hits:
                label_to_id[lbl] = hits[0]["entity_id"]
            n_skipped += 1
        else:
            label_to_id[lbl] = result["entity_id"]
            _log.info("  + entity: %s [%s]", lbl, result["entity_id"])
            n_created += 1

    _log.info("Entities: %d created, %d skipped/pre-existing", n_created, n_skipped)

    # ── pass 2: record claims ────────────────────────────────────────────────
    for item in _SEED:
        subj_lbl = item["label"]
        subj_id  = label_to_id.get(subj_lbl)
        if not subj_id:
            continue
        for claim in item.get("claims") or []:
            obj_lbl = claim["obj"]
            obj_id  = label_to_id.get(obj_lbl)
            if not obj_id:
                _log.warning("  SKIP claim %s→%s: object entity not resolved", subj_lbl, obj_lbl)
                n_claims_skip += 1
                continue

            if dry_run:
                _log.info("  [DRY-RUN] claim: %s -[%s]-> %s", subj_lbl, claim["rel"], obj_lbl)
                n_claims += 1
                continue

            try:
                record_claim(
                    subject_entity_id=subj_id,
                    relationship_type=claim["rel"],
                    object_entity_id=obj_id,
                    epistemic_class=claim["eclass"],
                    source_id=claim["src"],
                    confidence=claim.get("conf"),
                    memory_type="semantic",
                )
                n_claims += 1
                _log.info("  + claim: %s -[%s]-> %s (conf=%.2f)", subj_lbl, claim["rel"], obj_lbl, claim.get("conf", 0.5))
            except Exception as exc:
                _log.warning("  FAIL claim %s→%s: %s", subj_lbl, obj_lbl, exc)
                n_claims_skip += 1

    _log.info("Claims: %d recorded, %d skipped", n_claims, n_claims_skip)
    _log.info("WO-WKG-HUMANITIES-001 seed %scomplete.", "[DRY-RUN] " if dry_run else "")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed WKG humanities knowledge (WO-WKG-HUMANITIES-001)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be created without writing")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
