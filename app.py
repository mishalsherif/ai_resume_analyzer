"""AI Resume Helper Streamlit app

Features implemented:
- Detect resume type immediately after upload and compute `converted_text`.
- Show summary, keyword suggestions and AI recommendations.
- Preview and safely apply AI suggestions (per-line hash check + fallback replace).
- Tailor resume to a job description with diff preview and apply/undo.
- Export TXT/DOCX/PDF and a ZIP bundle built from `converted_text`.
"""

import hashlib
import streamlit as st

from utils import parser, converter
from utils.analyzer import (
    detect_resume_type,
    generate_summary,
    keyword_suggestions,
    section_recommendations,
)
from utils.ai_summary import generate_recommendations, rewrite_bullet
from utils.converter import to_ats, to_creative
from utils.tailor import tailor_resume
from utils.diff import inline_diff_highlight


st.set_page_config(page_title="AI Resume Helper", layout="wide")


# Session state defaults
if 'resume_text' not in st.session_state:
    st.session_state['resume_text'] = None
if 'resume_history' not in st.session_state:
    st.session_state['resume_history'] = []


def safe_apply_by_index(s_text: str, line_index: int, new_line: str, target_hash: str | None = None):
    """Attempt safe replacement at a specific line index.

    - If `target_hash` is provided, only apply when the current line's SHA1 matches.
    - If index is out of range or hash doesn't match, do not modify.
    Returns: (new_text, applied_bool)
    """
    lines = s_text.splitlines()
    if 0 <= line_index < len(lines):
        cur = lines[line_index].rstrip('\n')
        if target_hash:
            cur_hash = hashlib.sha1(cur.encode('utf-8')).hexdigest()
            if cur_hash == target_hash:
                lines[line_index] = new_line
                return "\n".join(lines), True
            return s_text, False
        lines[line_index] = new_line
        return "\n".join(lines), True
    return s_text, False


def fallback_replace_first(original: str, suggested: str, s_text: str):
    """Replace the first occurrence of `original` with `suggested` in `s_text`.
    Returns (new_text, applied_bool).
    """
    if not original:
        return s_text, False
    idx = s_text.find(original)
    if idx == -1:
        return s_text, False
    new = s_text.replace(original, suggested, 1)
    return new, True


def build_bundle_bytes(base_name: str, text: str):
    """Create a dict of files for zipping. Keys are filenames, values are bytes."""
    files = {}
    files[f"{base_name}.txt"] = converter.export_txt(text)
    try:
        files[f"{base_name}.docx"] = converter.export_docx(text)
    except Exception:
        # DOCX optional
        pass
    try:
        files[f"{base_name}.pdf"] = converter.export_pdf(text)
    except Exception:
        # PDF optional (weasyprint may not be installed)
        pass
    return files


def main():
    st.title("AI Resume Helper")

    uploaded = st.file_uploader("Upload resume (PDF, DOCX, TXT)", key="resume_upload")
    if uploaded:
        data = uploaded.read()
        # parse text and store in session
        try:
            st.session_state['resume_text'] = parser.extract_text(data, filename=uploaded.name)
        except Exception as e:
            st.error(f"Failed to parse uploaded file: {e}")

    text = st.session_state.get('resume_text')
    if not text:
        st.info("Upload a resume to get started.")
        return

    # Detect resume type first (user requirement)
    rtype = detect_resume_type(text)
    st.sidebar.markdown(f"**Detected type:** {rtype}")

    # Compute converted_text according to detected type and use it for exports
    try:
        if rtype == 'ATS-Friendly':
            converted_text = to_ats(text)
        elif rtype == 'Creative':
            converted_text = to_creative(text)
        else:
            converted_text = text
    except Exception:
        converted_text = text

    col_main, col_side = st.columns([2, 1])

    with col_main:
        st.header("Summary & Recommendations")
        try:
            st.write(generate_summary(text))
        except Exception:
            st.write("Summary unavailable")

        st.write("**Keyword suggestions:**", keyword_suggestions(text))
        st.write(section_recommendations(text))

        st.markdown("---")
        st.header("Job Description Matching")
        jd_file = st.file_uploader("Upload a job description (TXT)", type=["txt"], key="jd_main")
        rec = None
        if jd_file and st.button("Analyze job match"):
            jd = jd_file.read().decode('utf-8')
            with st.spinner("Generating recommendations..."):
                rec = generate_recommendations(text, jd)
            st.write("Match score:", rec.get('score'))
            st.write("Matched:", rec.get('matched', [])[:40])
            st.write("Missing:", rec.get('missing', [])[:60])

            detected = rec.get('detected_bullets', [])
            rewritten = rec.get('rewritten_bullets', [])

            st.subheader("Detected bullets")
            for i, b in enumerate(detected[:30]):
                display = b.get('text') if isinstance(b, dict) else str(b)
                st.write(f"{i+1}. {display}")

            st.subheader("AI Suggestions")
            if rewritten:
                # Offer preview and apply-all
                if st.button("Preview all suggestions"):
                    preview_lines = st.session_state.get('resume_text', '').splitlines()
                    for rb in rewritten:
                        li = rb.get('line_index')
                        sug = rb.get('suggested')
                        if li is not None and 0 <= li < len(preview_lines):
                            preview_lines[li] = sug
                    st.text_area("Preview", "\n".join(preview_lines), height=300)

                if st.button("Apply all suggestions"):
                    preview_lines = st.session_state.get('resume_text', '').splitlines()
                    applied_any = False
                    for rb in rewritten:
                        li = rb.get('line_index')
                        sug = rb.get('suggested')
                        target_hash = rb.get('hash')
                        if li is not None and 0 <= li < len(preview_lines):
                            # Try to apply safely to the working copy
                            cur_hash = hashlib.sha1(preview_lines[li].strip().encode('utf-8')).hexdigest()
                            if target_hash is None or cur_hash == target_hash:
                                preview_lines[li] = sug
                                applied_any = True
                            else:
                                # fallback replace by original
                                orig = rb.get('original') or rb.get('text')
                                new_s, did = fallback_replace_first(orig, sug, "\n".join(preview_lines))
                                if did:
                                    preview_lines = new_s.splitlines()
                                    applied_any = True
                    if applied_any:
                        st.session_state['resume_history'].append(st.session_state.get('resume_text', ''))
                        st.session_state['resume_text'] = "\n".join(preview_lines)
                        st.success("Applied suggestions")
                    else:
                        st.info("No suggestions could be applied cleanly")

                # Individual suggestion apply controls
                for i, rb in enumerate(rewritten):
                    orig = rb.get('original') or rb.get('text')
                    sug = rb.get('suggested')
                    st.write(f"Suggestion {i+1}")
                    st.write("Original:", orig)
                    st.write("Suggested:", sug)
                    if st.button(f"Apply suggestion {i+1}", key=f"apply_{i}"):
                        s = st.session_state.get('resume_text', '')
                        li = rb.get('line_index')
                        target_hash = rb.get('hash')
                        applied = False
                        if li is not None:
                            new_s, ok = safe_apply_by_index(s, li, sug, target_hash)
                            if ok:
                                s = new_s
                                applied = True
                        if not applied:
                            s2, ok2 = fallback_replace_first(orig, sug, s)
                            if ok2:
                                s = s2
                                applied = True
                        if applied:
                            st.session_state['resume_history'].append(st.session_state.get('resume_text', ''))
                            st.session_state['resume_text'] = s
                            st.success("Applied suggestion")
                        else:
                            st.info("Could not apply suggestion (content changed)")

    with col_side:
        st.header("Preview & Export")
        edited = st.text_area("Resume (editable)", st.session_state.get('resume_text', ''), height=360)
        if edited != st.session_state.get('resume_text', ''):
            # update session text when user edits the preview box
            st.session_state['resume_history'].append(st.session_state.get('resume_text', ''))
            st.session_state['resume_text'] = edited
            st.experimental_rerun()

        # Export buttons always use `converted_text` (requirement)
        st.markdown("**Downloads (from converted text)**")
        try:
            st.download_button("Download TXT (converted)", data=converter.export_txt(converted_text), file_name="resume_converted.txt")
        except Exception:
            st.info("TXT export not available")

        try:
            st.download_button("Download DOCX (converted)", data=converter.export_docx(converted_text), file_name="resume_converted.docx")
        except Exception:
            st.info("DOCX export not available")

        try:
            st.download_button("Download PDF (converted)", data=converter.export_pdf(converted_text), file_name="resume_converted.pdf")
        except Exception:
            st.info("PDF export not available (optional dependency)")

        # ZIP bundle containing available formats
        files = build_bundle_bytes("resume_converted", converted_text)
        if files:
            try:
                zip_bytes = converter.export_zip(files)
                st.download_button("Download ZIP (all formats)", data=zip_bytes, file_name="resume_bundle.zip")
            except Exception:
                st.info("ZIP export not available")

        st.markdown("---")
        st.header("Tailor Resume")
        jd_tailor = st.file_uploader("(Tailor) Upload job description", type=["txt"], key="jd_tailor")
        if jd_tailor and st.button("Tailor to job description"):
            jd2 = jd_tailor.read().decode('utf-8')
            with st.spinner("Generating tailored resume..."):
                tailored_text, details = tailor_resume(text, jd2)
            st.markdown("### Tailoring Diff")
            st.markdown(inline_diff_highlight(text, tailored_text), unsafe_allow_html=True)
            if st.button("Apply tailored changes"):
                st.session_state['resume_history'].append(st.session_state.get('resume_text', ''))
                st.session_state['resume_text'] = tailored_text
                st.success("Applied tailored changes")

            # Offer tailored downloads
            files2 = build_bundle_bytes("resume_tailored", tailored_text)
            if files2:
                try:
                    st.download_button("Download Tailored ZIP", data=converter.export_zip(files2), file_name="resume_tailored_bundle.zip")
                except Exception:
                    st.info("Tailored ZIP export not available")

    # Undo controls in footer
    st.markdown("---")
    if st.button("Undo last change"):
        history = st.session_state.get('resume_history', [])
        if history:
            last = history.pop()
            st.session_state['resume_text'] = last
            st.session_state['resume_history'] = history
            st.success("Reverted to previous resume version")
        else:
            st.info("No previous versions to undo")


if __name__ == '__main__':
    main()
