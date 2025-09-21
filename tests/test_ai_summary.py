from utils.ai_summary import sanitize_ai_output


def test_sanitize_removes_prefixes_and_fences():
    raw = "Rewritten: \n- Increased revenue by 20%\n"
    out = sanitize_ai_output(raw)
    assert out.startswith("Increased revenue")


def test_sanitize_prefers_first_line():
    raw = "Sure:\nThis is the first line.\nSecond line with details."
    out = sanitize_ai_output(raw)
    assert out == "This is the first line."


def test_sanitize_strips_markers():
    raw = "- Led the migration of X to Y"
    out = sanitize_ai_output(raw)
    assert out == "Led the migration of X to Y"
