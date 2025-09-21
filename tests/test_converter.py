from utils import converter


def test_to_ats_and_creative_roundtrip():
    text = "John Doe\nExperience: Did things.\nSkills: Python"
    ats = converter.to_ats(text)
    creative = converter.to_creative(ats)
    assert isinstance(ats, str)
    assert isinstance(creative, str)


def test_export_txt_and_docx_and_zip():
    text = "Hello World"
    txt_b = converter.export_txt(text)
    assert isinstance(txt_b, bytes)
    try:
        docx_b = converter.export_docx(text)
        assert isinstance(docx_b, bytes)
    except RuntimeError:
        # python-docx may not be installed in some environments
        pass

    z = converter.export_zip({"a.txt": txt_b, "b.txt": b"B"})
    assert isinstance(z, bytes)


def test_template_render_and_job_matcher():
    from utils.job_matcher import match_keywords
    s = "Python, SQL, Machine Learning"
    jd = "Looking for Python and Data skills"
    match = match_keywords(s, jd)
    assert isinstance(match.get("score"), float)

    # template rendering
    html = converter.render_template("plain", "Title", "Content")
    assert "Title" in html and "Content" in html
