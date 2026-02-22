from utils.ai_summary import bulk_rewrite_bullets


def test_bulk_rewrite_fallback_no_api_key():
    bullets = ["- did X", "- did Y"]
    out = bulk_rewrite_bullets(bullets)
    # With no OPENAI_API_KEY in CI, should return same number of bullets
    assert isinstance(out, list)
    assert len(out) == len(bullets)

