from typing import Tuple
from utils.job_matcher import match_keywords
from utils.ai_summary import rewrite_bullet


def tailor_resume(resume_text: str, jd_text: str) -> Tuple[str, dict]:
    """Tailor resume to job description: rewrite top bullets and add missing keywords.

    Returns (new_resume_text, details)
    """
    details = {}
    match = match_keywords(resume_text, jd_text)
    details['match'] = match

    # rewrite first detected bullet
    lines = resume_text.splitlines()
    for i, l in enumerate(lines):
        if l.strip().startswith('-') or l.strip().startswith('•'):
            new = rewrite_bullet(l)
            lines[i] = new
            details['rewritten_index'] = i
            details['rewritten'] = new
            break

    # append missing keywords at end
    missing = match.get('missing', [])
    if missing:
        lines.append('')
        lines.append('Suggested keywords to add:')
        for k in missing:
            lines.append(f"- {k}")
        details['appended_keywords'] = missing

    return '\n'.join(lines), details
