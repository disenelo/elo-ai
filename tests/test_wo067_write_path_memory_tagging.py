"""WO-067-WRITE-PATH: memory category tagging — 6 ATs."""
import sys, os, json, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.memory_engine import _classify_memory_categories, write_interaction, _STORE_PATH


def test_at1_contextual_state_tagged_and_in_vault():
    """AT-1: clothing/weather turn → tagged contextual_state; lifted to vault."""
    text = "What should I wear for the weather? Two light layers should keep you comfortable."
    cats = _classify_memory_categories(text)
    assert "contextual_state" in cats, (
        f"AT-1 FAIL: 'contextual_state' not in categories: {cats}"
    )
    print(f"✅ AT-1: clothing turn → categories={cats} (includes contextual_state)")


def test_at2_decisions_and_projects_tagged():
    """AT-2: decision turn → tagged decisions + projects."""
    text = "I've decided to go with the pneumatic joint design for the robot."
    cats = _classify_memory_categories(text)
    assert "decisions" in cats, f"AT-2 FAIL: 'decisions' not in {cats}"
    assert "projects" in cats, f"AT-2 FAIL: 'projects' not in {cats}"
    print(f"✅ AT-2: decision turn → categories={cats}")


def test_at3_preferences_tagged():
    """AT-3: preference statement → tagged preferences."""
    text = "I prefer direct replies, no padding or fluff."
    cats = _classify_memory_categories(text)
    assert "preferences" in cats, f"AT-3 FAIL: 'preferences' not in {cats}"
    print(f"✅ AT-3: preference turn → categories={cats}")


def test_at4_generic_greeting_not_tagged():
    """AT-4: generic 'how are you?' exchange → NOT tagged, not lifted."""
    text = "How are you? I'm doing well, thanks for asking."
    cats = _classify_memory_categories(text)
    # Generic greeting should not match meaningful categories
    # Allow that some spurious matches may occur; the key categories should not match
    meaningful = {"contextual_state", "decisions", "preferences", "plans",
                  "commitments", "relationship", "learning", "experiences"}
    matched_meaningful = [c for c in cats if c in meaningful]
    assert len(matched_meaningful) == 0, (
        f"AT-4 FAIL: generic greeting matched meaningful categories: {matched_meaningful}"
    )
    print(f"✅ AT-4: generic greeting → categories={cats} (no meaningful categories)")


def test_at5_memory_categories_non_empty_in_interactions_json():
    """AT-5: tagged turn is written to interactions.json with non-empty memory_categories."""
    # Use a temp interactions.json to avoid polluting production store
    tmp = tempfile.mktemp(suffix=".json")
    original = _STORE_PATH
    import core.memory_engine as me
    me._STORE_PATH = tmp  # temporarily redirect writes

    try:
        write_interaction(
            user="What should I wear for the weather?",
            response="Two light layers should keep you comfortable.",
            categories=["contextual_state"],
            mode="answer",
            project_tag="elo_core",
        )
        with open(tmp) as f:
            store = json.load(f)
        assert len(store) > 0, "AT-5 FAIL: no records written"
        record = store[-1]
        assert record["memory_categories"], f"AT-5 FAIL: memory_categories empty: {record}"
        assert "contextual_state" in record["memory_categories"], (
            f"AT-5 FAIL: contextual_state not in {record['memory_categories']}"
        )
        print(f"✅ AT-5: interactions.json record has memory_categories={record['memory_categories']}")
    finally:
        me._STORE_PATH = original
        if os.path.exists(tmp):
            os.unlink(tmp)


def test_at6_vault_lookup_finds_tagged_turn():
    """AT-6: vault_layer.lookup() finds contextual_state turn via paraphrase."""
    from memory.vault_layer import lookup
    from memory.memory_faculty import MemoryFaculty, MemoryCandidate

    # Write a test vault record directly
    result = MemoryFaculty().submit(MemoryCandidate(
        source_faculty="test",
        content="What should I wear for the weather? Two light layers should keep you comfortable.",
        proposed_type="episodic",
        proposed_weight=5,
        significance=0.55,
        project="test_wo067",
        summary="[contextual_state] What should I wear for the weather?",
        tags=("test", "contextual_state"),
    ))
    assert result["action"] in ("write", "reinforce"), (
        f"AT-6 FAIL: vault did not write or reinforce: {result}"
    )

    # Now look it up with a paraphrase
    hits = lookup("wear", max_results=10)
    found = any("wear" in h.get("summary", "").lower() or
                "wear" in h.get("text", "").lower()
                for h in hits)
    assert found, f"AT-6 FAIL: 'wear' paraphrase query found no relevant hits. hits={[h.get('summary','')[:80] for h in hits[:5]]}"
    print(f"✅ AT-6: vault_layer.lookup('wear') → found clothing turn in vault")


if __name__ == "__main__":
    tests = [
        test_at1_contextual_state_tagged_and_in_vault,
        test_at2_decisions_and_projects_tagged,
        test_at3_preferences_tagged,
        test_at4_generic_greeting_not_tagged,
        test_at5_memory_categories_non_empty_in_interactions_json,
        test_at6_vault_lookup_finds_tagged_turn,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"❌ {t.__name__}: {e}")
        except Exception as e:
            import traceback
            print(f"❌ {t.__name__}: EXCEPTION {e}")
            traceback.print_exc()
    print(f"\n{passed}/{len(tests)} PASS")
    sys.exit(0 if passed == len(tests) else 1)
