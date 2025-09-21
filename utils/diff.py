import html
import difflib
from typing import List


def html_side_by_side(a: str, b: str, fromdesc: str = "Original", todesc: str = "Tailored") -> str:
    """Return a side-by-side HTML diff using difflib.HtmlDiff."""
    a_lines = a.splitlines()
    b_lines = b.splitlines()
    d = difflib.HtmlDiff(tabsize=4, wrapcolumn=80)
    return d.make_file(a_lines, b_lines, fromdesc=fromdesc, todesc=todesc, context=True)


def inline_diff_highlight(a: str, b: str) -> str:
    """Return HTML where added words are highlighted green and removed words red.

    This produces a single HTML string that can be embedded in the preview area.
    """
    a_words = a.split()
    b_words = b.split()
    matcher = difflib.SequenceMatcher(None, a_words, b_words)

    parts: List[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            parts.append(html.escape(' '.join(a_words[i1:i2])))
        elif tag == 'replace':
            # show removed then added
            removed = html.escape(' '.join(a_words[i1:i2]))
            added = html.escape(' '.join(b_words[j1:j2]))
            if removed:
                parts.append(f"<span style='background:#ffecec;color:#7f1d1d;padding:2px 4px;border-radius:4px;margin-right:4px'>- {removed}</span>")
            if added:
                parts.append(f"<span style='background:#ecffef;color:#0b6623;padding:2px 4px;border-radius:4px;margin-right:4px'>+ {added}</span>")
        elif tag == 'delete':
            removed = html.escape(' '.join(a_words[i1:i2]))
            parts.append(f"<span style='background:#ffecec;color:#7f1d1d;padding:2px 4px;border-radius:4px;margin-right:4px'>- {removed}</span>")
        elif tag == 'insert':
            added = html.escape(' '.join(b_words[j1:j2]))
            parts.append(f"<span style='background:#ecffef;color:#0b6623;padding:2px 4px;border-radius:4px;margin-right:4px'>+ {added}</span>")

    return '<div style="line-height:1.6;">' + ' '.join(parts) + '</div>'

