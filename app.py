import streamlit as st
import altair as alt
import pandas as pd
from utils.analyzer import (
    detect_resume_type,
    ats_score,
    section_scores,
    section_recommendations,
    highlight_keywords,
    generate_summary,
    keyword_suggestions,
    color_code_score,
)
from utils.ai_summary import generate_ai_summary
from utils.job_matcher import match_keywords
from utils.tailor import tailor_resume
from utils.diff import html_side_by_side
from utils.diff import inline_diff_highlight
import streamlit.components.v1 as components
from utils import parser
import html
from utils import converter

st.set_page_config(page_title="AI Resume Analyzer", layout="wide")

# App header
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
    :root {
        --bg-a: #0f172a; --bg-b: #0b1220; --accent: #ff6b6b; --accent-2: #6bffdf;
        --card: rgba(255,255,255,0.04); --muted: #9fb6cf; --glass: rgba(255,255,255,0.03);
    }
    html, body { height:100%; }
    body {
        background: radial-gradient(800px 400px at 10% 8%, rgba(255,107,107,0.06), transparent),
                    radial-gradient(700px 350px at 95% 90%, rgba(107,255,223,0.04), transparent),
                    linear-gradient(180deg, var(--bg-a), var(--bg-b));
        color: #e6eef6; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
    }
    /* floating blob accents */
    .topbar::after {
        content: '';
        position: absolute; right: 18px; top: 12px; width:120px; height:120px; border-radius:50%;
        background: radial-gradient(circle at 30% 30%, rgba(255,107,107,0.18), transparent 40%), radial-gradient(circle at 70% 70%, rgba(107,255,223,0.12), transparent 40%);
        filter: blur(32px); z-index:-1; pointer-events:none;
    }
    .topbar { display:flex; align-items:center; justify-content:space-between; gap:12px; padding:14px 22px; margin-bottom:16px; position:relative }
    .logo { display:flex; align-items:center; gap:10px }
    .logo .mark { width:48px; height:48px; border-radius:12px; background: conic-gradient(from 200deg at 50% 50%, #ff6b6b, #6bffdf, #7c3aed); display:flex; align-items:center; justify-content:center; font-size:20px; box-shadow:0 6px 18px rgba(12,18,30,0.6); }
    .app-title { font-size:20px; margin:0; color: #fff; letter-spacing:0.2px }
    .nav { color:var(--muted); font-size:13px }
    .hero { display:flex; gap:20px; align-items:center; margin-bottom:18px }
    .hero-card { background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); padding:18px; border-radius:16px; box-shadow: 0 12px 40px rgba(2,6,23,0.5); }
    .hero h2 { margin:0 0 6px 0; font-size:22px; color:#fff }
    .hero p { margin:0; color:var(--muted) }
    .stat-badge { display:inline-block; background:linear-gradient(90deg, rgba(255,255,255,0.02), rgba(0,0,0,0.05)); padding:8px 12px; border-radius:999px; color: #fff; font-weight:700; margin-right:8px }
    .card { background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); padding:18px; border-radius:14px; box-shadow: 0 8px 30px rgba(5,10,20,0.6); margin-bottom:14px }
    .section-title { font-size:15px; font-weight:800; color: var(--accent); margin-bottom:10px }
    .resume-preview { background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(0,0,0,0.06)); padding:16px; border-radius:10px; color:#e6eef6; font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, 'Courier New', monospace; white-space:pre-wrap }
    .highlight { background: linear-gradient(90deg,#fff59d,#ffd36b); padding:2px 6px; border-radius:6px }
    .small-muted { color:var(--muted); font-size:13px }
    .btn-like { display:inline-block; background:linear-gradient(90deg,var(--accent), #7c3aed); color:white; padding:8px 12px; border-radius:10px; text-decoration:none }
    .muted-note { color:var(--muted); font-size:12px }
    .card:hover { transform:translateY(-4px); transition:all .18s ease }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "<div class='topbar'><div class='logo'><div class='mark'>AI</div><div><div class='app-title'>AI Resume Analyzer</div><div class='small-muted'>Analyze • Tailor • Export</div></div></div><div class='nav small-muted'>v1.0 • Local Mode</div></div>",
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader("Upload your resume (TXT, PDF or DOCX)", type=["txt", "pdf", "docx"]) 

# persist resume text in session state so we can apply changes
if 'resume_text' not in st.session_state:
    st.session_state['resume_text'] = None
    # history of resume versions for undo
    st.session_state['resume_history'] = []

if uploaded_file:
    file_bytes = uploaded_file.read()
    text = parser.extract_text(file_bytes, filename=uploaded_file.name)
    st.session_state['resume_text'] = text

text = st.session_state.get('resume_text')
if text:
    # Layout: two columns (analysis / tools)
    left, right = st.columns([2, 1], gap="large")

    # LEFT: main analysis and preview
    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Resume Summary</div>", unsafe_allow_html=True)
        rtype = detect_resume_type(text)
        st.markdown(f"<div class='small-muted'>Type: {rtype}</div>", unsafe_allow_html=True)
        # If not detected as a resume, show a warning and offer an override
        resume_override = False
        if rtype == 'Not a Resume':
            st.warning("This document does not look like a resume. Resume-only features are hidden.")
            resume_override = st.checkbox("Override and treat as resume (use with caution)")

        st.markdown("</div>", unsafe_allow_html=True)

        # ATS and section scores side-by-side
        with st.container():
            a, b = st.columns([1, 2])
            with a:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>ATS Score</div>", unsafe_allow_html=True)
                score = ats_score(text)
                color = color_code_score(score)
                st.markdown(f"<div style='font-size:36px;color:{color};font-weight:700'>{score}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with b:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>Section Scores</div>", unsafe_allow_html=True)
                scores = section_scores(text)
                df = pd.DataFrame({"section": list(scores.keys()), "score": list(scores.values())})
                chart = (
                    alt.Chart(df)
                    .mark_bar()
                    .encode(x=alt.X("section:N", title="Section"), y=alt.Y("score:Q", title="Score"), color=alt.Color("score:Q", scale=alt.Scale(domain=[0, 100], scheme="greens")))
                    .properties(height=220)
                )
                st.altair_chart(chart, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

        # Recommendations
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Recommendations</div>", unsafe_allow_html=True)
        st.write(section_recommendations(text))
        st.markdown("</div>", unsafe_allow_html=True)

        # Highlighted keywords
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Highlighted Keywords</div>", unsafe_allow_html=True)
        safe_text = html.escape(text)
        highlighted = highlight_keywords(safe_text)
        st.markdown(f"<div class='resume-preview'>{highlighted}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # AI Summary and suggestions
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Summary & Suggestions</div>", unsafe_allow_html=True)
        # Only show resume-specific AI summary if this is a resume or override enabled
        show_resume_features = (rtype != 'Not a Resume') or resume_override
        use_ai = st.checkbox("Use AI summary (requires OPENAI_API_KEY in environment)", value=False)
        if use_ai and show_resume_features:
            with st.spinner("Generating AI summary..."):
                ai_sum = generate_ai_summary(text)
            st.write(ai_sum)
        else:
            st.write(generate_summary(text))
        st.write("**Keyword Suggestions:**")
        st.write(keyword_suggestions(text))
        st.markdown("</div>", unsafe_allow_html=True)

        # Job description matching and bullets
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Job Matching & Rewrites</div>", unsafe_allow_html=True)
        jd_file = st.file_uploader("Upload a job description (TXT) to tailor suggestions", type=["txt"], key="jd")
        if jd_file:
            jd = jd_file.read().decode("utf-8")
            match = match_keywords(text, jd)
            st.write(match)

        bullets = [l for l in text.splitlines() if l.strip().startswith("-") or l.strip().startswith("•")]
        # Only enable rewrite when document is a resume (or overridden)
        if bullets and show_resume_features:
            st.write("Detected bullets:")
            for i, b in enumerate(bullets[:10]):
                st.write(f"{i+1}. {b}")
            if st.button("Rewrite top bullet using AI"):
                from utils.ai_summary import rewrite_bullet
                rewritten = rewrite_bullet(bullets[0])
                st.success("Rewritten:")
                st.write(rewritten)
        elif bullets:
            st.info("Bullets detected but resume features are disabled. Enable override to use AI rewrites.")
        st.markdown("</div>", unsafe_allow_html=True)

    # RIGHT: tools, templates, exports, tailoring actions
    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Templates & Export</div>", unsafe_allow_html=True)
        template = st.selectbox("Choose template", ("Plain", "Modern", "Creative"))
        # simple WYSIWYG: let user edit raw HTML for template and save to session
        if 'custom_template' not in st.session_state:
            st.session_state['custom_template'] = converter.render_template(template.lower(), "Preview", text)

        st.markdown("<div class='small-muted'>Edit template HTML (basic)</div>", unsafe_allow_html=True)
        tpl = st.text_area("Template HTML", st.session_state['custom_template'], height=180)
        if st.button("Save Template"):
            st.session_state['custom_template'] = tpl
            st.success("Template saved to session")
        html_preview = tpl
        st.text_area("Rendered Preview (HTML)", html_preview, height=140)
        try:
            pdf_bytes = converter.export_pdf_from_html(html_preview)
            st.download_button("Download PDF", data=pdf_bytes, file_name="resume_preview.pdf")
        except RuntimeError:
            st.warning("PDF export not available (weasyprint missing)")

        files = {"resume.txt": converter.export_txt(text)}
        try:
            files["resume.docx"] = converter.export_docx(text)
        except Exception:
            pass
        try:
            files["resume.pdf"] = converter.export_pdf(text)
        except Exception:
            pass
        zip_bytes = converter.export_zip(files)
        st.download_button("Download ZIP (all formats)", data=zip_bytes, file_name="resume_bundle.zip")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Transform Resume</div>", unsafe_allow_html=True)
        option = st.radio("Convert to:", ("ATS", "Creative", "None"))
        preview = None
        if option == "ATS":
            preview = converter.to_ats(text)
        elif option == "Creative":
            preview = converter.to_creative(text)
        if preview:
            st.text_area("Preview", preview, height=150)
            st.download_button("Download TXT", data=converter.export_txt(preview), file_name="resume_converted.txt")
            try:
                docx_bytes = converter.export_docx(preview)
                st.download_button("Download DOCX", data=docx_bytes, file_name="resume_converted.docx")
            except RuntimeError:
                st.warning("DOCX export not available (missing python-docx)")
        st.markdown("</div>", unsafe_allow_html=True)

        # Tailoring controls and diff (kept here for discoverability)
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Tailor Resume</div>", unsafe_allow_html=True)
        if jd_file is None:
            st.info("Upload a job description in the main area to enable tailoring")
        else:
            if st.button("Tailor resume to this job description"):
                tailored_text, details = tailor_resume(text, jd)
                st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
                view_mode = st.selectbox("Diff view", ("Side-by-side", "Inline"), index=0)
                if view_mode == "Side-by-side":
                    diff_html = html_side_by_side(text, tailored_text)
                    components.html(diff_html, height=500, scrolling=True)
                else:
                    inline_html = inline_diff_highlight(text, tailored_text)
                    st.markdown(inline_html, unsafe_allow_html=True)
                st.subheader("Tailoring Details")
                st.json(details)
                if st.button("Apply tailored changes"):
                    history = st.session_state.get('resume_history', [])
                    history.append(text)
                    st.session_state['resume_history'] = history
                    st.session_state['resume_text'] = tailored_text
                    st.success("Tailored changes applied — resume updated in session")
                if st.button("Undo last apply"):
                    history = st.session_state.get('resume_history', [])
                    if history:
                        last = history.pop()
                        st.session_state['resume_text'] = last
                        st.session_state['resume_history'] = history
                        st.success("Reverted to previous resume version")
                    else:
                        st.info("No previous versions to undo")

                st.download_button("Download Tailored TXT", data=converter.export_txt(tailored_text), file_name="resume_tailored.txt")
                try:
                    st.download_button("Download Tailored DOCX", data=converter.export_docx(tailored_text), file_name="resume_tailored.docx")
                except Exception:
                    st.warning("DOCX export not available")
                try:
                    pdfb = converter.export_pdf_from_html(converter.render_template(template.lower(), "Tailored Resume", tailored_text))
                    st.download_button("Download Tailored PDF", data=pdfb, file_name="resume_tailored.pdf")
                except Exception:
                    st.warning("Tailored PDF export not available")
                files2 = {"tailored.txt": converter.export_txt(tailored_text)}
                try:
                    files2["tailored.docx"] = converter.export_docx(tailored_text)
                except Exception:
                    pass
                try:
                    files2["tailored.pdf"] = converter.export_pdf(tailored_text)
                except Exception:
                    pass
                st.download_button("Download Tailored ZIP", data=converter.export_zip(files2), file_name="resume_tailored_bundle.zip")
        st.markdown("</div>", unsafe_allow_html=True)
