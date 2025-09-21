import pytest
from utils import analyzer


def test_detect_resume_type_at_friendly():
    text = "John Doe\nemail: john@example.com\nExperience: ...\nEducation: ...\nSkills: Python"
    assert analyzer.detect_resume_type(text) == "ATS-Friendly"


def test_detect_resume_type_creative():
    text = "This is a very short one-liner"
    assert analyzer.detect_resume_type(text) == "Not a Resume"


def test_generate_summary():
    text = "First sentence. Second sentence! Third sentence?"
    summary = analyzer.generate_summary(text)
    assert "First sentence." in summary
    assert "Second sentence" in summary


def test_highlight_keywords_escapes_html():
    text = "<b>Python</b> and SQL"
    highlighted = analyzer.highlight_keywords(text)
    assert '<span class="highlight">Python</span>' in highlighted


def test_ats_score_weighted():
    text = "Experience: Worked on Python projects. Education: BSc. Skills: Python, SQL." * 2
    score = analyzer.ats_score(text)
    assert isinstance(score, int)
    assert 0 <= score <= 100


def test_keyword_suggestions():
    text = "Python, SQL"
    suggestions = analyzer.keyword_suggestions(text)
    assert isinstance(suggestions, list)
    assert "Machine Learning" in suggestions


def test_ai_summary_fallback(monkeypatch):
    from utils.ai_summary import generate_ai_summary

    # ensure no OPENAI_API_KEY is present
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    text = "Experienced engineer with Python and SQL. Worked on projects."
    s = generate_ai_summary(text)
    assert isinstance(s, str)
