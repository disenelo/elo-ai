"""
memory/spg_faculty.py — WO-ELO-LEARN-001

SPG link layer production module.
Bridges CCM dims → WKG entity clusters.
Adds nodes and edges to spg_graph per new WKG claim.

This is the production entry point — spg_graph.py (R&D) is the underlying store.
"""
from __future__ import annotations

import hashlib
import logging
import time

_log = logging.getLogger(__name__)


def _get_graph():
    from memory.spg_graph import SPGGraph
    return SPGGraph.load()


# CCM dim → WKG relationship types that are relevant in that context.
#
# Every name here must exist in memory/wkg/relationship_types.json. Until
# 2026-10-03 almost none did: the map named FEELS, WORKING_ON, STATED,
# DECIDED, FACT, OBSERVATION, BELIEF and RELATIONSHIP, and not one of the
# eight is in the 19-type vocabulary. Eleven of twelve entries could never
# match a claim, so get_claims_by_type() returned [] for every dim on every
# turn and this filter selected nothing, ever. ASSOCIATED_WITH was the only
# real name in the map.
#
# It survived because an unknown relationship name costs nothing — the lookup
# just comes back empty. _unknown_relationship_types() below makes it loud,
# which matters more than the remap: without the guard the next edit
# reintroduces exactly this.
#
# HONEST LIMIT, not papered over: 2212 of the 2226 live claims are
# ASSOCIATED_WITH. A dim that includes it passes nearly everything; a dim that
# does not selects nearly nothing. The filter is no longer DEAD, but on the
# current data it is close to a no-op either way, and it only becomes useful
# as the writers start using the rest of the vocabulary. That is a data
# problem and it is David's and Board's to weigh, not something to hide
# behind a greener test.
_CCM_DIM_RELEVANT_RELS: dict[str, list[str]] = {
    "emotional_tone":     ["INFLUENCES", "INTERPRETED_AS", "SYMBOLISES"],
    "creative_mode":      ["PROPOSED_BY", "DERIVED_FROM", "ANALOGOUS_TO",
                           "REPRESENTS"],
    "learning_interest":  ["IS", "OBSERVED_AS", "SUPPORTS", "CAUSES"],
    "street_language":    ["REPRESENTS", "SYMBOLISES", "CORRESPONDS_TO"],
    "project_focus":      ["PART_OF", "ASSOCIATED_WITH", "CORRESPONDS_TO"],
    "memory_depth":       ["DERIVED_FROM", "TEMPORALLY_PRECEDES",
                           "OBSERVED_AS", "HYPOTHESISED_AS"],
}


def _relationship_vocabulary() -> set[str]:
    """The relationship types a claim is actually allowed to carry."""
    try:
        from runtime.wkg_faculty import _load
        return set(_load("relationship_types"))
    except Exception:
        return set()


def _unknown_relationship_types(mapping: dict | None = None) -> dict[str, list[str]]:
    """
    Names in the CCM map that cannot exist on a claim. Warns and returns them.

    An empty vocabulary means the file is missing or unreadable, which is not
    evidence that every name is wrong — returns {} rather than condemning the
    whole map on a failed read.
    """
    vocab = _relationship_vocabulary()
    if not vocab:
        return {}
    bad = {
        dim: [r for r in rels if r not in vocab]
        for dim, rels in (mapping or _CCM_DIM_RELEVANT_RELS).items()
    }
    bad = {dim: rels for dim, rels in bad.items() if rels}
    if bad:
        _log.warning(
            "SPG CCM filter: relationship types that cannot exist on a claim "
            "— these dims can never select anything: %s", bad,
        )
    return bad


# Checked once at import. The whole reason the old map lived so long is that
# nothing ever said it was wrong.
_unknown_relationship_types()


def query_spg_entities(turn_text: str, ccm: dict | None = None) -> list[str]:
    """
    CCM dims → relevant WKG entity_ids to retrieve for this turn.

    Returns list of entity_ids ranked by SPG significance, then text relevance.
    Falls back to direct WKG entity search when SPG has no nodes.

    WO-ELO-LEARN-001 Component 2: SPG nodes are now used as a real ranking signal.
    Previously, the 129 SPG nodes were loaded but never consulted during entity
    retrieval — the function did pure text search and CCM filtering only. Now:
      1. Text search → candidate entity_ids
      2. Entity → associated claims (subject or object)
      3. Claim → SPG node significance score
      4. Entity ranked by max SPG significance of its claims (higher = more meaningful)
      5. CCM filter applied as secondary sort before capping
    """
    try:
        from runtime.wkg_faculty import search_entities, get_claims_by_type
    except Exception:
        return []

    relevant_entity_ids: list[str] = []
    seen: set = set()

    # Step 1: search WKG for entities mentioned in the turn
    words = turn_text.lower().split()
    # Unigrams matter. This built the full text plus BIGRAMS only, so any
    # one-word entity was invisible unless it happened to sit inside a matching
    # two-word phrase. "what is eLo" produced ['what is eLo', 'what is',
    # 'is elo'] -- none of which match -- while the unigram 'elo' hits. eLo,
    # identity, Chunk, K-7: all single-label entities, none ever retrieved.
    # The len >= 3 filter below already drops "is"/"a" noise.
    # Function words are excluded from the UNIGRAM pass. Adding unigrams was
    # mine (0372243) and it was half a change: "what is the weather in Lisbon
    # tomorrow" started matching an entity called What, because the WKG writer
    # had created one from a sentence opener. The writer is fixed, but
    # searching the store for "what" was never right on its own terms — a
    # function word identifies no entity, whatever the store happens to hold.
    # Bigrams and the full text are left alone; "the shell" is a real phrase.
    try:
        from memory.memory_faculty import _WKG_STOP as _stop
    except Exception:
        _stop = frozenset()
    search_terms = (
        [turn_text]
        + [" ".join(words[i:i + 2]) for i in range(max(0, len(words) - 1))]
        + [w for w in words if w.strip(".,!?;:'\"").lower() not in _stop]
    )
    for term in search_terms:
        if len(term) < 3:
            continue
        try:
            hits = search_entities(term)
            for e in hits:
                eid = e.get("entity_id", "")
                if eid and eid not in seen:
                    relevant_entity_ids.append(eid)
                    seen.add(eid)
        except Exception:
            pass

    if not relevant_entity_ids:
        return []

    # Step 2: Build SPG significance index — claim_id → significance
    # Load SPG graph and index its 129 nodes by claim_id (same UUID namespace as WKG claims).
    spg_sig: dict[str, float] = {}
    try:
        g = _get_graph()
        spg_sig = {nid: node.significance for nid, node in g._nodes.items()}
    except Exception:
        pass  # SPG unavailable — fall back to text-order

    # Step 3: If SPG has nodes, rank entities by max significance of their associated claims.
    if spg_sig:
        try:
            # Through the owning module, not a path of our own. This reopened
            # memory/wkg/claims.json directly, so two modules held independent
            # ideas of where claims live and the reader could silently miss
            # whatever the writer had put elsewhere.
            from runtime.wkg_faculty import all_claims as _wkg_all_claims
            _all_claims = _wkg_all_claims()

            # entity_id → max SPG significance across all claims where it appears
            entity_sig: dict[str, float] = {eid: 0.0 for eid in relevant_entity_ids}
            for claim in _all_claims:
                cid = claim.get("claim_id", "")
                sig = spg_sig.get(cid, 0.0)
                if sig <= 0.0:
                    continue
                for role_key in ("subject_entity_id", "object_entity_id"):
                    eid = claim.get(role_key, "")
                    if eid in entity_sig:
                        entity_sig[eid] = max(entity_sig[eid], sig)

            # ROOT-4 join. Two node populations live in one graph and this
            # ranker could only ever see one of them:
            #
            #   claim-keyed   add_node_for_claim(), one per claim
            #   turn-keyed    the backfill, "bf-00788-2026-08-13T02:49:33",
            #                 3,321 of them covering four months
            #
            # So filling the graph with everything David has ever said changed
            # retrieval by nothing, because none of it was keyed the way this
            # lookup reads.
            #
            # It also fixes the FLAT case the comment below describes: 2,212
            # of 2,226 claims are SOURCE_ATTRIBUTED at confidence 0.7, so
            # every claim-derived score is identical and sorting on them is a
            # no-op even when they link. Topic significance varies — 1,241
            # distinct values across the backfill — so it can actually order
            # things.
            #
            # An entity is scored by the strongest signal available to it:
            # its claims, or what David keeps returning to. "robot" appears in
            # 239 of his turns; "quantum chromodynamics" in none and scores
            # 0.0, which is the test that this reads HIM and not generic
            # salience.
            try:
                from memory.spg_topic_index import score_label, topic_significance
                from runtime.wkg_faculty import get_entity as _get_entity

                _topic_idx = topic_significance()
                if _topic_idx:
                    for eid in list(entity_sig):
                        ent = _get_entity(eid) or {}
                        label = str(ent.get("label", "") or "")
                        if label:
                            entity_sig[eid] = max(
                                entity_sig[eid], score_label(label, _topic_idx)
                            )
            except Exception as _tp_e:
                _log.debug("SPG topic ranking unavailable (non-fatal): %s", _tp_e)

            # Does any SPG node actually correspond to a claim we hold?
            #
            # The comment above this block asserts the node ids share the WKG
            # claim_id namespace. On the live store that is false: 214 node
            # ids, 2220 claim ids, ZERO intersection. Every entity_sig stayed
            # 0.0, so this sort was a no-op and the ranking came from text
            # order -- while the debug line below reported a successful
            # rerank. Inverting every significance in the store changed the
            # retrieved order by nothing, which is how it was found.
            #
            # The nodes are orphaned: add_node_for_claim() keys correctly by
            # claim_id, so claims written from here on link properly, but the
            # legacy nodes point at claims that were since regenerated, and
            # content_hash cannot re-link them because claims.json stores no
            # claim text to hash.
            #
            # Silence was the real defect. A dead ranking that logs success is
            # worse than one that is absent.
            # Three outcomes, and all three are reported. Linking claims to
            # nodes (WO-SPG-LINK-001) opened a new way for this to go quietly
            # wrong: 2212 of the 2226 live claims are SOURCE_ATTRIBUTED at
            # confidence 0.7, so they all land on the SAME significance.
            # Backfill nodes for them and _linked jumps from zero to
            # thousands, the INERT warning stops, and the sort runs — on a key
            # identical for every entity. The ordering would still be text
            # relevance and nothing would say so any more.
            #
            # An honest "this is doing nothing" replaced by a silent "this is
            # working" is worse than the original defect, because nobody looks
            # again. So a rerank that cannot discriminate says so.
            _linked = sum(1 for v in entity_sig.values() if v > 0.0)
            _distinct = {round(v, 4) for v in entity_sig.values() if v > 0.0}
            if _linked == 0:
                # Two signals feed entity_sig now, so "nothing scored" has
                # two possible causes and conflating them sends the next
                # reader to the wrong place. Measured on the live store:
                # 83 of 249 entity labels DO score through the topic index,
                # 46 distinct values — so an INERT turn usually means these
                # particular entities are not things David returns to, not
                # that the index is dead.
                try:
                    from memory.spg_topic_index import topic_significance as _tsig
                    _n_topics = len(_tsig())
                except Exception:
                    _n_topics = 0
                _log.warning(
                    "SPG rerank INERT: %d nodes, %d recurring topics, and none "
                    "of the %d retrieved entities matched either — ordering is "
                    "text-relevance only for this turn. %s",
                    len(spg_sig), _n_topics, len(relevant_entity_ids),
                    "The topic index is empty — run scripts/spg_backfill_run.py."
                    if _n_topics == 0 else
                    "The index is live; these entities simply are not recurring.",
                )
            elif len(_distinct) <= 1:
                _log.warning(
                    "SPG rerank FLAT: %d entities linked but every one scores "
                    "%.2f — a sort on an identical key is a no-op, so ordering "
                    "is still text-relevance. Linked is not the same as ranking.",
                    _linked, next(iter(_distinct)),
                )
            else:
                relevant_entity_ids.sort(
                    key=lambda eid: entity_sig.get(eid, 0.0), reverse=True)
                _log.debug(
                    "SPG rerank: %d entities, %d linked, %d distinct scores; "
                    "top sig=%.2f",
                    len(relevant_entity_ids), _linked, len(_distinct),
                    max(entity_sig.values()) if entity_sig else 0.0,
                )
        except Exception as _e:
            _log.debug("SPG rerank failed (non-fatal): %s", _e)

    else:
        # The quietest state of the three: no nodes at all meant this entire
        # block was skipped and nothing was logged at any level, so an empty
        # graph looked exactly like a working one from the outside.
        _log.warning(
            "SPG rerank INERT: the graph holds no nodes — ordering is "
            "text-relevance only. Nothing is feeding SPG."
        )

    # Step 4: CCM dim filter — prioritise entities with relevant relationship types
    if ccm and relevant_entity_ids:
        active_rels: set[str] = set()
        for dim, val in (ccm or {}).items():
            try:
                if float(val or 0) >= 0.4:
                    active_rels.update(_CCM_DIM_RELEVANT_RELS.get(dim, []))
            except (TypeError, ValueError):
                pass

        if active_rels:
            filtered = []
            for eid in relevant_entity_ids:
                for rel in active_rels:
                    try:
                        claims = get_claims_by_type(eid, rel)
                        if claims:
                            filtered.append(eid)
                            break
                    except Exception:
                        pass
            if filtered:
                return filtered

    return relevant_entity_ids[:10]  # cap to prevent over-retrieval


def add_node_for_claim(
    claim_id: str,
    claim_text: str,
    significance: float = 0.5,
    embodiment: str = "desktop",
) -> bool:
    """
    Add an SPG node for a newly written WKG claim.

    Returns True if node was added, False on error.
    """
    try:
        from memory.spg_graph import SPGGraph, Node
        graph = SPGGraph.load()
        content_hash = hashlib.sha1(claim_text.encode()).hexdigest()[:16]
        node = Node(
            id=claim_id,
            content_hash=content_hash,
            significance=significance,
            embodiment=embodiment,
            ts=time.time(),
        )
        graph.add_node(node)
        graph.save()
        _log.debug("spg_faculty: node added claim_id=%s sig=%.2f", claim_id, significance)
        return True
    except Exception as _e:
        _log.debug("spg_faculty: node add failed: %s", _e)
        return False


def add_edge_between_claims(
    from_claim_id: str,
    to_claim_id: str,
    link_type: str = "semantic",
    weight: float = 0.5,
    evidence: str = "",
) -> bool:
    """
    Add an SPG edge between two claim nodes.

    link_type: temporal | semantic | relational | significance_chain | embodiment_continuity
    """
    try:
        from memory.spg_graph import SPGGraph, Edge
        graph = SPGGraph.load()
        edge = Edge(
            from_node=from_claim_id,
            to_node=to_claim_id,
            link_type=link_type,
            weight=weight,
            evidence=evidence or "",
        )
        graph.add_edge(edge)
        graph.save()
        _log.debug("spg_faculty: edge added %s→%s type=%s", from_claim_id[:8], to_claim_id[:8], link_type)
        return True
    except Exception as _e:
        _log.debug("spg_faculty: edge add failed: %s", _e)
        return False


def update_spg_from_claims(claims: list, significance_score: float = 0.5) -> dict:
    """
    WO-ELO-LEARN-001: add SPG nodes for a batch of newly written WKG claims,
    and connect them semantically.

    Returns {"nodes_added": int, "edges_added": int}
    """
    nodes_added = 0
    edges_added = 0
    claim_ids: list[str] = []

    for claim in claims:
        cid = claim.get("claim_id", "")
        ctext = claim.get("claim_text", "") or ""
        sig = float(claim.get("significance_score") or significance_score)
        if not cid:
            continue
        if add_node_for_claim(cid, ctext or cid, significance=sig):
            nodes_added += 1
            claim_ids.append(cid)

    # Connect new claims to each other (semantic, same-turn provenance)
    for i in range(len(claim_ids)):
        for j in range(i + 1, len(claim_ids)):
            if add_edge_between_claims(
                claim_ids[i], claim_ids[j],
                link_type="semantic",
                weight=0.5,
                evidence="same_turn",
            ):
                edges_added += 1

    return {"nodes_added": nodes_added, "edges_added": edges_added}


def write_world_causal_edge(
    action_spot: str,
    consequence_spot: str,
    agent_name: str = "",
) -> bool:
    """
    WO-WORLD-001 P3: write a causal SPG edge from an action vault spot to a
    consequence vault spot.  Called after WORLD_INTERACTION vault write when
    the turn also produced a memory write (consequence).

    link_type "causal" extends the standard set for world-interaction provenance.
    """
    try:
        evidence = f"world_interaction:{agent_name}" if agent_name else "world_interaction"
        return add_edge_between_claims(
            from_claim_id=action_spot,
            to_claim_id=consequence_spot,
            link_type="causal",
            weight=0.65,
            evidence=evidence,
        )
    except Exception as _e:
        _log.debug("write_world_causal_edge: failed: %s", _e)
        return False
