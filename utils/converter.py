from typing import Tuple
import io

def to_ats(text: str) -> str:
    """Simple heuristic to convert a creative-style resume text into a more ATS-friendly plain text.

    This function strips decorative bullets, collapses columns, and ensures section headers exist.
    It's a heuristic — for best results manual editing is recommended.
    """
    # remove common decorative bullets
    cleaned = text.replace('•', '-').replace('♦', '-').replace('★', '-')
    # normalize multiple spaces and fancy dashes
    cleaned = cleaned.replace('\t', ' ')
    # ensure section headers are capitalized and on their own lines
    for sec in ['Experience', 'Education', 'Skills', 'Projects', 'Summary']:
        cleaned = cleaned.replace(sec.lower() + ':', sec + ':')
        cleaned = cleaned.replace(sec + ' -', sec + ':')
    return cleaned


def to_creative(text: str) -> str:
    """Apply light creative formatting: add bullets, short one-line highlights, and a small header block."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    header = lines[0] if lines else 'Name'
    body = lines[1:]
    creative = [f"=== {header} ===", '']
    for l in body:
        if ':' in l and len(l.split(':')[0]) < 20:
            # section header
            creative.append(f"-- {l}")
        else:
            creative.append(f"• {l}")
    return '\n'.join(creative)


def export_txt(text: str) -> bytes:
    return text.encode('utf-8')


def export_docx(text: str) -> bytes:
    try:
        from docx import Document
    except Exception:
        raise RuntimeError('python-docx is required to export DOCX')

    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    f = io.BytesIO()
    doc.save(f)
    f.seek(0)
    return f.read()


def export_pdf(text: str, title: str = "Resume") -> bytes:
    try:
        from weasyprint import HTML
    except Exception:
        raise RuntimeError("weasyprint is required to export PDF")

    # simple HTML wrapper
    html = f"""
    <html>
      <head><meta charset='utf-8'><title>{title}</title></head>
      <body>
        <pre style='font-family: sans-serif; white-space: pre-wrap;'>{text}</pre>
      </body>
    </html>
    """
    pdf = HTML(string=html).write_pdf()
    return pdf


def export_zip(files: dict) -> bytes:
    """Create a ZIP from a dict of filename->bytes and return bytes."""
    import zipfile

    import io

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    buf.seek(0)
    return buf.read()


def export_pdf_from_html(html_string: str) -> bytes:
    try:
        from weasyprint import HTML
    except Exception:
        raise RuntimeError("weasyprint is required to export PDF")

    return HTML(string=html_string).write_pdf()


def render_template(template_name: str, title: str, content: str) -> str:
    from pathlib import Path

    tpath = Path(__file__).resolve().parents[1] / "templates" / f"{template_name}.html"
    if not tpath.exists():
        raise RuntimeError("Template not found")
    txt = tpath.read_text(encoding="utf-8")
    return txt.replace("{{ title }}", title).replace("{{ content }}", content)
