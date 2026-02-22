from utils.ai_summary import generate_recommendations


def test_generate_recommendations_structure():
    resume = """
    - Managed inventory and logistics for international shipments
    - Improved tracking systems and reduced delays by 15%
    """
    job = "Looking for logistics manager with experience in inventory, tracking, Python and SQL"
    out = generate_recommendations(resume, job)
    assert isinstance(out, dict)
    assert set(["matched", "missing", "score", "detected_bullets", "rewritten_bullets"]).issubset(set(out.keys()))
    assert isinstance(out["score"], float)
    assert isinstance(out["detected_bullets"], list)
    # detected_bullets should be list of dicts with text and line_index
    if out["detected_bullets"]:
        first = out["detected_bullets"][0]
        assert isinstance(first, dict)
        assert "text" in first and "line_index" in first
    # rewritten_bullets should be aligned dicts
    if out["rewritten_bullets"]:
        r0 = out["rewritten_bullets"][0]
        assert isinstance(r0, dict)
        assert set(["original", "line_index", "suggested"]).issubset(set(r0.keys()))
