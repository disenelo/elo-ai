"""
tools/research.py — WO-RESEARCH-001: eLo finds out what he doesn't know.

Source:
  engineering/work_orders/WO-RESEARCH-001_external_knowledge_retrieval.md
  docs/architecture/_intake/SOURCE_2026-09-27_DAVID_research_capability_spec.md
  builder3/START_HERE.md: "David wants eLo to say 'I don't know that — let me
  look it up' and then actually look it up. Right now eLo says 'I don't have
  that recorded' and stops."

Pipeline (WO §"What must be built"):
  1. Internal first   — eLo's world graph + WKG (graph_loader) and vault memory
                        (memory_faculty.retrieve) before anything external.
  2. Gap detection    — a clear factual question whose topic internal knowledge
                        doesn't cover. Personal / contextual / eLo's-own-world
                        questions are never gaps (ID-035, card 0021).
  3. External         — tools.web_search (SerpAPI + Wikipedia).
  4. Epistemic tag    — every finding RETRIEVED with source + date.
  5. Promotion gate   — RETRIEVED → CANDIDATE → VERIFIED → KNOWLEDGE, ledger in
                        data/research/ledger.json. KNOWLEDGE goes to
                        MemoryFaculty.submit() (sole memory writer, which owns
                        the WKG write) — never written to the graph from here.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass, asdict, field

from tools import web_search as ws

_LEDGER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "research", "ledger.json")
_lock = threading.Lock()

# Reference sources: one of these plus an independent second domain = VERIFIED.
_REFERENCE_HOSTS = ("wikipedia.org", "britannica.com", ".gov", ".edu", "nasa.gov", "who.int",
                    "nature.com", "sciencedirect.com", "ncbi.nlm.nih.gov")

STATUSES = ("RETRIEVED", "CANDIDATE", "VERIFIED", "KNOWLEDGE")


@dataclass
class ResearchResult:
    """WO-RESEARCH-001 output record."""
    query: str
    source: str              # url, or "google:knowledge_graph"
    content: str             # the sentence, verbatim from the source
    retrieved_at: float
    verified: bool = False
    epistemic_status: str = "RETRIEVED"
    relevance: float = 1.0
    corroborated_by: list = field(default_factory=list)


# ── 2 · gap detection ─────────────────────────────────────────────────────────

_FACTUAL_RE = re.compile(
    r"^(?:(?:hey|so|ok(?:ay)?|but|and)\s+)?(?:do\s+you\s+know\s+)?"
    r"(?:"
    r"what\s+(?:is|are|was|were)\s+(?P<a>(?:a|an)\s+.+)"
    r"|what'?s\s+(?P<b>(?:a|an)\s+.+)"
    r"|what\s+(?:is|are|was|were|'s)\s+(?P<c>the\s+\S+(?:\s+\S+)+)"       # "the" + ≥2 words
    r"|what\s+(?:is|are|was|were|'s)\s+(?P<d>[A-Z][\w\-']*(?:\s+\S+)*)"   # capitalised subject
    r"|what\s+does\s+(?P<e>.+?)\s+mean"
    r"|define\s+(?P<f>.+)"
    r"|how\s+(?:does|do|did)\s+(?P<g>.+?)\s+work"
    r"|(?:when|where)\s+(?:did|was|were)\s+(?P<h>.+)"
    r"|who\s+(?:invented|wrote|created|founded|discovered|designed|directed|painted|built)\s+(?P<i>.+)"
    r"|who\s+was\s+(?P<j>.+)"
    r"|how\s+(?:many|much|tall|old|far|big|long|deep|fast|heavy)\s+(?P<k>.+)"
    r")$",
)
_PERSONAL_RE = re.compile(r"\b(?:i|me|my|mine|we|us|our|you|your|yours|elo|david|k-7|k7|chunk)\b", re.I)
_VAGUE_TOPIC = frozenset("""
that this it thing things one time point plan problem idea deal matter issue
going on up next difference best way reason
""".split())


# Groups h/i/k ask for a fact about the topic (a date, a person, a number):
# answered from the question itself, not from the topic's encyclopedia lead.
_FACT_GROUPS = {"h", "i", "k"}


def factual_question(text: str) -> tuple[str, str] | None:
    """("define", topic) | ("fact", topic) for a clear factual question, else
    None. Never personal, never about the conversation itself ("what is the
    plan"), never eLo's own world."""
    t = (text or "").strip().rstrip("?!. ")
    # Embedded questions (IS-ELO verdicts 2026-10-06): "can you tell me what a
    # capybara is", "do you know what a Kalman filter is", "could you tell me
    # when the Berlin Wall fell".
    t = re.sub(r"^(?:(?:can|could|would|will)\s+you\s+(?:please\s+)?(?:tell\s+me|explain|say)"
               r"|do\s+you\s+know|i\s+wonder)\s+", "", t, flags=re.I)
    emb = re.match(r"^what\s+(?P<x>(?:a|an|the)\s+.+?|[A-Z][\w\-']*(?:\s+\S+)*?)\s+(?:is|are|was|were|means?)$", t)
    if emb:
        t = f"what is {emb.group('x')}"
    emb = re.match(r"^(?P<w>when|where)\s+(?!did\b|was\b|were\b|is\b)(?P<x>.+)$", t, flags=re.I)
    if emb:
        topic = emb.group("x")
        if not _PERSONAL_RE.search(topic):
            return ("fact", re.sub(r"\s+\w+$", "", topic) if len(topic.split()) > 2 else topic)
        return None
    t = re.sub(r"^(how\s+(?:many|much|tall|old|far|big|long|deep|fast|heavy)\s+.+?)\s+(?:is|are|was|were)$", r"\1", t,
               flags=re.I)
    m = _FACTUAL_RE.match(t) or _FACTUAL_RE.match(t[0].lower() + t[1:] if t else t)
    if not m:
        return None
    group, topic = next(((k, v) for k, v in m.groupdict().items() if v), ("", ""))
    topic = topic.strip(" ,'\"")
    if not topic or _PERSONAL_RE.search(topic):
        return None
    words = re.findall(r"[a-z0-9]+", topic.lower())
    content = [w for w in words if w not in _VAGUE_TOPIC and w not in {"a", "an", "the", "of", "in", "on", "is"}]
    if not content:
        return None
    if group in _FACT_GROUPS:
        return ("fact", re.sub(r"^(?:is|are|was|were)\s+", "", topic))
    return ("define", re.sub(r"^(?:a|an|the)\s+", "", topic, flags=re.I))


def factual_topic(text: str) -> str:
    q = factual_question(text)
    return q[1] if q else ""


# ── 1 · internal first ────────────────────────────────────────────────────────

def internal(topic: str) -> list[dict]:
    """What eLo already holds about the topic: world graph / WKG hits on a whole
    word of the topic, then vault memory whose summary names it."""
    hits: list[dict] = []
    words = ws._content_words(topic)
    if not words:
        return hits
    try:
        from knowledge.graph_loader import retrieve, retrieve_wkg
        for h in (retrieve(topic) or []) + (retrieve_wkg(topic) or []):
            label = str(h.get("label", "")).lower()
            if all(re.search(r"\b" + re.escape(w) + r"\b", label + " " + str(h.get("content", "")).lower())
                   for w in words):
                hits.append({"store": "graph", "label": h.get("label"), "content": h.get("content", "")})
    except Exception:
        pass
    try:
        from memory.memory_faculty import retrieve as mem_retrieve
        for m in mem_retrieve(topic, max_results=3) or []:
            text = f"{m.get('summary', '')} {m.get('deep_text', '')}".lower()
            if all(re.search(r"\b" + re.escape(w) + r"\b", text) for w in words):
                hits.append({"store": "memory", "label": m.get("summary", ""), "content": m.get("summary", "")})
    except Exception:
        pass
    return hits


# ── 5 · ledger + promotion gate ───────────────────────────────────────────────

def _load() -> dict:
    try:
        with open(_LEDGER, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"claims": {}, "topics": {}}


def _save(d: dict) -> None:
    os.makedirs(os.path.dirname(_LEDGER), exist_ok=True)
    tmp = _LEDGER + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1, ensure_ascii=False)
    os.replace(tmp, _LEDGER)


def _host(url: str) -> str:
    if url.startswith("google:"):
        return "google"
    return re.sub(r"^https?://(?:www\.|en\.|m\.)?", "", url).split("/")[0]


def _key_facts(text: str) -> set[str]:
    """Numbers / years and mid-sentence capitalised names — what a second
    source has to repeat for the claim to count as cross-checked."""
    nums = {n.replace(",", "") for n in re.findall(r"\d[\d,]*(?:\.\d+)?", text)}
    names = {w.lower() for w in re.findall(r"(?<=\s)[A-Z][a-z]{2,}", text)}
    return nums | names


def _corroborating(sentence: str, src: str, results: list) -> list[str]:
    """Other domains that repeat this sentence's key facts (≥2, ≥60% of them),
    or share most of its content (≥6 words, ≥50% of the shorter text)."""
    facts = _key_facts(sentence)
    words = set(ws._content_words(sentence))
    out = []
    for r in results:
        if _host(r.url or "") == _host(src) or not ws._usable_source(r.url or ""):
            continue
        text = f"{r.title} {r.snippet}"
        if len(facts) >= 2:
            theirs = _key_facts(text) | set(ws._content_words(text))
            if len(facts & theirs) / len(facts) >= 0.6:
                out.append(r.url)
                continue
        hay = set(ws._content_words(text))
        shared = words & hay
        if len(shared) >= 6 and len(shared) / max(1, min(len(words), len(hay))) >= 0.5:
            out.append(r.url)
    return list(dict.fromkeys(out))


def _status_for(sources: list[str]) -> str:
    hosts = {_host(u) for u in sources}
    if len(hosts) >= 2 and any(any(rh in h for rh in _REFERENCE_HOSTS) for h in hosts):
        return "VERIFIED"
    if len(hosts) >= 2:
        return "CANDIDATE"
    return "RETRIEVED"


def record(topic: str, picks: list[tuple[str, str]], results: list) -> list[ResearchResult]:
    """Ledger every finding eLo just spoke, advance its status, and promote
    VERIFIED + significant (asked about on ≥2 separate turns) to KNOWLEDGE."""
    now = time.time()
    out: list[ResearchResult] = []
    with _lock:
        d = _load()
        tkey = topic.lower().strip()
        tinfo = d["topics"].setdefault(tkey, {"asks": 0, "first": now})
        tinfo["asks"] += 1
        tinfo["last"] = now
        for sentence, src in picks:
            key = ws._key(sentence)
            c = d["claims"].setdefault(key, {
                "topic": topic, "content": sentence, "sources": [], "status": "RETRIEVED",
                "retrieved_at": now, "history": [],
            })
            for u in [src] + _corroborating(sentence, src, results):
                if u and u not in c["sources"]:
                    c["sources"].append(u)
            new = _status_for(c["sources"])
            if c["status"] != "KNOWLEDGE" and STATUSES.index(new) > STATUSES.index(c["status"]):
                c["history"].append({"from": c["status"], "to": new, "ts": now})
                c["status"] = new
            if c["status"] == "VERIFIED" and tinfo["asks"] >= 2:
                res = _submit_knowledge(c)
                if res.get("action") in ("write", "reinforce"):
                    c["history"].append({"from": "VERIFIED", "to": "KNOWLEDGE", "ts": now,
                                         "spot": res.get("spot")})
                    c["status"] = "KNOWLEDGE"
            out.append(ResearchResult(
                query=topic, source=src, content=sentence, retrieved_at=c["retrieved_at"],
                verified=c["status"] in ("VERIFIED", "KNOWLEDGE"),
                epistemic_status=c["status"], corroborated_by=[u for u in c["sources"] if u != src],
            ))
        _save(d)
    return out


def _submit_knowledge(claim: dict) -> dict:
    """KNOWLEDGE = handed to MemoryFaculty (sole memory writer; it owns the WKG
    write and its gate). source_ref carries the checkable source pointers."""
    try:
        from memory.memory_faculty import MemoryFaculty, MemoryCandidate
        return MemoryFaculty().submit(MemoryCandidate(
            source_faculty="research",
            content=f"{claim['content']}\n\nSources: " + ", ".join(claim["sources"]),
            proposed_type="semantic",
            proposed_weight=5,
            significance=0.6,
            verified=True,
            project="general",
            summary=claim["content"][:200],
            tags=("research", "retrieved"),
            epistemic_class="verified",
            source_ref=" ".join(claim["sources"]),
        ))
    except Exception as e:
        return {"action": "drop", "reason": str(e)}


def ledger_entry(sentence: str) -> dict | None:
    return _load()["claims"].get(ws._key(sentence))


# ── the whole pass ────────────────────────────────────────────────────────────

_VERB_CUES = {
    "invented": r"\binvent", "wrote": r"\b(?:wr(?:o|i)te|written|author)", "created": r"\bcreat",
    "founded": r"\bfound(?:ed|er|ing)", "discovered": r"\bdiscover", "designed": r"\bdesign",
    "directed": r"\bdirect", "painted": r"\bpaint", "built": r"\b(?:built|construct)",
}
_HOW_CUES = {
    "tall": r"\b(?:tall|height|high)\b|\d[\d,.]*\s*(?:m|metres|meters|ft|feet)\b",
    "old": r"\b(?:age|aged|years?\s+old|born|founded|built)\b|\b(?:1[0-9]{3}|20[0-9]{2})\b",
}


def _cue(question: str) -> re.Pattern | None:
    q = question.lower()
    m = re.match(r"\s*who\s+(\w+)", q)
    if m and m.group(1) in _VERB_CUES:
        return re.compile(_VERB_CUES[m.group(1)], re.I)
    if q.lstrip().startswith("when"):
        return re.compile(r"\b(?:1[0-9]{3}|20[0-9]{2})\b")
    if q.lstrip().startswith("where"):
        return re.compile(r"\b(?:in|at|located|near|on)\s+[A-Z]")
    m = re.match(r"\s*how\s+(\w+)", q)
    if m:
        return re.compile(_HOW_CUES.get(m.group(1), r"\d"), re.I)
    return None


def _answer_fact(question: str, topic: str) -> tuple[str, list[tuple[str, str]], list] | None:
    """The sentence that answers the question: Google's answer box if it gave
    one, else a sentence carrying the question's cue (a year, a height, an
    inventor…) from the topic's Wikipedia lead, then the web results. None when
    no source states it."""
    results = ws.search(question, max_results=6, engine="google")
    ab = ws.last_answer_box
    if ab and (ab.get("snippet") or ab.get("answer")):
        src = ab.get("link") or "google:answer_box"
        sents = ws._sentences(ab.get("snippet", ""))
        sentence = sents[0] if sents else f"{ab['answer']}."
        return f"Didn't know that one — looked it up on {ws.source_label(src)}: {sentence}", [(sentence, src)], results
    cue = _cue(question)
    if not cue:
        return None
    words = ws._content_words(topic)
    pool: list[tuple[str, str]] = []
    wiki = ws.wiki_summary(topic) or ws.wiki_summary(re.sub(r"^(?:the|a|an)\s+", "", topic, flags=re.I))
    if wiki:
        pool += [(s, wiki.url) for s in ws._sentences(wiki.snippet)]
        results = [wiki] + results
    for r in results[1 if wiki else 0:]:
        if not ws._usable_source(r.url):
            continue
        pool += [(s, r.url) for s in ws._sentences(r.snippet)
                 if not ws._FIRST_PERSON_RE.search(s) and not ws._PROMO_START_RE.match(s)]
    on_topic = {r.url for r in results
                if not words or any(w in f"{r.title} {r.snippet}".lower() for w in words)}
    is_who = question.lower().lstrip().startswith("who")
    hits = [(sentence, src) for sentence, src in pool
            if src in on_topic and cue.search(sentence) and not sentence.endswith("?")
            # "who …" is answered by a name (a capitalised word past the first).
            and (not is_who or re.search(r"(?<=\s)[A-Z][a-z]+", sentence))]
    # A sentence that states a number answers "how tall / how many / when" better
    # than one that only says "height" ("now 1,083 feet tall" over "dizzying height").
    if not is_who:
        hits.sort(key=lambda h: 0 if re.search(r"\d", h[0]) else 1)
    if not hits:
        return None
    sentence, src = hits[0]
    return (f"Didn't know that one — looked it up on {ws.source_label(src)}: {sentence}",
            [(sentence, src)], results)


_last_recall = ""


def _recall(topic: str) -> str | None:
    """eLo already researched this topic: say what he found, with how sure he
    is. Asking again is significance — a VERIFIED claim asked about on a second
    turn is promoted to KNOWLEDGE (MemoryFaculty) and said as known. Never the
    same line twice running — the response gate blanks a verbatim repeat."""
    global _last_recall
    key = topic.lower().strip()
    with _lock:
        d = _load()
        claims = [c for c in d["claims"].values()
                  if c.get("topic", "").lower().strip() == key
                  or key in c.get("topic", "").lower() or c.get("topic", "").lower() in key]
        if not claims:
            return None
        now = time.time()
        tinfo = d["topics"].setdefault(key, {"asks": 0, "first": now})
        tinfo["asks"] += 1
        tinfo["last"] = now
        for c in claims:
            if c["status"] == "VERIFIED" and tinfo["asks"] >= 2:
                res = _submit_knowledge(c)
                if res.get("action") in ("write", "reinforce"):
                    c["history"].append({"from": "VERIFIED", "to": "KNOWLEDGE", "ts": now,
                                         "spot": res.get("spot")})
                    c["status"] = "KNOWLEDGE"
        _save(d)
    claims.sort(key=lambda c: STATUSES.index(c["status"]), reverse=True)
    lines = []
    for c in claims:
        if c["status"] == "KNOWLEDGE":
            lines.append(f"I know this one — {c['content']}")
        elif c["status"] == "VERIFIED":
            names = " and ".join(dict.fromkeys(ws.source_label(u) for u in c["sources"][:2]))
            lines.append(f"Looked that up before — {names} agree: {c['content']}")
        else:
            src = c["sources"][0] if c["sources"] else ""
            lines.append(f"Looked that up before, on {ws.source_label(src)}: {c['content']}")
    line = next((l for l in lines if l != _last_recall), None)
    if line is None:
        line = "Same as I said before — " + lines[0].split(" — ", 1)[-1].split(": ", 1)[-1]
    _last_recall = line
    return line


def research(text: str) -> dict | None:
    """B3 result standard around answer_gap: {success, result: {line, topic,
    status}, error}; None when the text isn't a research question. Recorded
    for the execution-confirmation gate."""
    from tools.capability_status import tool_result, record_result
    try:
        line = _answer_gap(text)
    except Exception as e:
        return record_result("research", tool_result(False, {"line": None}, f"{type(e).__name__}: {e}"))
    if line is None:
        return None
    found = not line.startswith("Don't know that one")
    return record_result("research", tool_result(found, {
        "line": line, "topic": factual_topic(text),
        "status": ("KNOWLEDGE" if line.startswith("I know this one") else
                   "RECALLED" if line.startswith(("Looked that up before", "Same as I said")) else
                   "RETRIEVED" if found else "NOT_FOUND"),
    }, None if found else "no source stated it"))


def answer_gap(text: str) -> str | None:
    r = research(text)
    return r["result"]["line"] if r and r["result"] else None


def _answer_gap(text: str) -> str | None:
    """A factual question eLo can't answer from what he holds → look it up and
    say so. None when it isn't a factual question or he already knows."""
    q = factual_question(text)
    if not q:
        return None
    kind, topic = q
    if internal(topic):
        return None   # known — the normal path answers from eLo's own knowledge
    recalled = _recall(topic)
    if recalled:
        return recalled
    if kind == "fact":
        got = _answer_fact((text or "").strip(), topic)
        if not got:
            return f"Don't know that one, and I couldn't find a straight answer on {topic} either."
        line, picks, results = got
        record(topic, picks, results)
        return line
    name, results = ws.search_topic(topic, max_results=5)
    found = ws.compose_found(name, results)
    if not found:
        return f"Don't know that one, and I couldn't find anything solid on {name} either."
    record(name, ws.last_picks, results)
    # "Looked it up on X — …" → "Didn't know that one — looked it up on X: …"
    return re.sub(r"^Looked it up on (.+?) —", r"Didn't know that one — looked it up on \1:", found, count=1)
