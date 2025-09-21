from utils.tailor import tailor_resume


def test_tailor_basic(monkeypatch):
    resume = "John Doe\n- did X\n- did Y\n"
    jd = "Looking for Python"

    # stub rewrite_bullet to avoid external API calls
    monkeypatch.setattr('utils.tailor.rewrite_bullet', lambda b: 'Rewritten: ' + b)

    new_text, details = tailor_resume(resume, jd)
    assert 'Rewritten:' in new_text
    assert 'Suggested keywords' in new_text or details.get('appended_keywords') is not None
