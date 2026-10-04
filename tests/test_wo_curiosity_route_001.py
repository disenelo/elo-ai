"""WO-CURIOSITY-ROUTE-001: verify curiosity_faculty.top_question() injection + mark_surfaced."""
import json, tempfile, pathlib, pytest


def _write_questions(path, questions):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(questions))


def test_top_question_returns_unsurfaced():
    from faculties.curiosity import curiosity_faculty as cf
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "open_questions.json"
        _write_questions(p, [
            {"text": "Why does canvas fray at tight seams?", "topic": "canvas seams", "weight": 8, "surfaced": False},
            {"text": "Already shown", "topic": "other", "weight": 9, "surfaced": True},
        ])
        old = cf._QUESTIONS_PATH
        cf._QUESTIONS_PATH = str(p)
        try:
            q = cf.top_question()
            assert q is not None
            assert q["text"] == "Why does canvas fray at tight seams?"
        finally:
            cf._QUESTIONS_PATH = old


def test_mark_surfaced_sets_flag():
    from faculties.curiosity import curiosity_faculty as cf
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "open_questions.json"
        _write_questions(p, [
            {"text": "Test question?", "topic": "test", "weight": 5, "surfaced": False},
        ])
        old = cf._QUESTIONS_PATH
        cf._QUESTIONS_PATH = str(p)
        try:
            cf.mark_surfaced("Test question?")
            data = json.loads(p.read_text())
            assert data[0]["surfaced"] is True
        finally:
            cf._QUESTIONS_PATH = old


def test_top_question_none_when_all_surfaced():
    from faculties.curiosity import curiosity_faculty as cf
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "open_questions.json"
        _write_questions(p, [{"text": "Done?", "topic": "x", "weight": 5, "surfaced": True}])
        old = cf._QUESTIONS_PATH
        cf._QUESTIONS_PATH = str(p)
        try:
            q = cf.top_question()
            assert q is None
        finally:
            cf._QUESTIONS_PATH = old


def test_curiosity_prompt_block_empty_when_no_questions():
    from faculties.curiosity import curiosity_faculty as cf
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "open_questions.json"
        _write_questions(p, [])
        old = cf._QUESTIONS_PATH
        cf._QUESTIONS_PATH = str(p)
        try:
            block = cf.curiosity_prompt_block()
            assert block == ""
        finally:
            cf._QUESTIONS_PATH = old
