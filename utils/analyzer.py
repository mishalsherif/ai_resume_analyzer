import json
import re
from pathlib import Path

_BASE = Path(__file__).resolve().parents[1]


def _load_config():
    cfg_path = _BASE / "config" / "keywords.json"
    defaults = {
        "desired_keywords": ["Python", "Machine Learning", "SQL", "Project", "Experience", "Education"],
        "important_sections": ["Experience", "Education", "Skills", "Projects"],
        "weights": {"keywords": 0.5, "sections": 0.4, "length": 0.1},
    }
    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # merge defaults shallowly
            defaults.update({k: data.get(k, v) for k, v in defaults.items()})
        except Exception:
            pass
    return defaults


_CFG = _load_config()


def detect_resume_type(text):
    # quick resume verification: check for resume-like cues
    if not is_resume(text):
        return "Not a Resume"

    symbols = len(re.findall(r"[•♦★]", text))
    non_empty_lines = len([l for l in text.splitlines() if l.strip()])
    lowered = text.lower()

    if symbols > 5:
        return "Creative"

    has_common = any(h.lower() in lowered for h in _CFG.get("important_sections", []))
    if non_empty_lines < 6 and not has_common:
        return "Creative"

    return "ATS-Friendly"


def is_resume(text: str) -> bool:
    """Return True if text looks like a resume. Heuristics:
    - contains common resume section headings (Experience, Education, Skills, Projects)
    - contains contact cues (email, phone) OR has several short lines/ bullets
    - length is reasonable for a resume (at least 3 non-empty lines)
    """
    if not text or not text.strip():
        return False

    lowered = text.lower()
    # contact cues
    email_like = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text) is not None
    phone_like = re.search(r"\b\+?\d{7,15}\b", text) is not None

    sections = _CFG.get("important_sections", ["Experience", "Education", "Skills", "Projects"])
    has_section = any(re.search(rf"\b{re.escape(s)}\b", text, flags=re.I) for s in sections)

    non_empty_lines = len([l for l in text.splitlines() if l.strip()])

    # Strong indicator: section present + either contact or sufficient lines
    if has_section and (email_like or phone_like or non_empty_lines >= 6):
        return True

    # Moderate indicator: multiple bullets or many short lines
    bullets = len(re.findall(r"^\s*[-•♦]\s+", text, flags=re.M))
    if bullets >= 3 and non_empty_lines >= 4:
        return True

    return False


def ats_score(text):
    """Weighted ATS-like score between 0 and 100.

    Components:
    - keywords: fraction of desired keywords present
    - sections: fraction of important sections present
    - length: simple length heuristic (too short penalized)
    """
    cfg = _CFG
    keywords = cfg.get("desired_keywords", [])
    sections = cfg.get("important_sections", [])
    weights = cfg.get("weights", {"keywords": 0.5, "sections": 0.4, "length": 0.1})

    lower = text.lower()
    kw_found = sum(1 for kw in keywords if kw.lower() in lower)
    kw_score = kw_found / max(1, len(keywords))

    sec_found = sum(1 for s in sections if re.search(rf"\b{re.escape(s.rstrip('s'))}s?\b", text, flags=re.I))
    sec_score = sec_found / max(1, len(sections))

    length = len([l for l in text.splitlines() if l.strip()])
    if length < 5:
        length_score = 0.2
    elif length < 15:
        length_score = 0.6
    else:
        length_score = 1.0

    total = (
        kw_score * weights.get("keywords", 0.5)
        + sec_score * weights.get("sections", 0.4)
        + length_score * weights.get("length", 0.1)
    )
    # map to 0-100 with a base of 40 to avoid very low scores on minimal content
    return int(min(100, max(0, 40 + total * 60)))


def _has_section(text, sec):
    base = sec.rstrip("s")
    return re.search(rf"\b{re.escape(base)}s?\b", text, flags=re.I) is not None


def section_scores(text):
    sections = _CFG.get("important_sections", ["Experience", "Education", "Skills", "Projects"])
    return {sec: 90 if _has_section(text, sec) else 40 for sec in sections}


def section_recommendations(text):
    sections = _CFG.get("important_sections", ["Experience", "Education", "Skills", "Projects"])
    return {sec: "Good coverage." if _has_section(text, sec) else "Consider adding this section." for sec in sections}


def highlight_keywords(text):
    keywords = _CFG.get("desired_keywords", ["Python", "Machine Learning", "SQL", "Project", "Experience", "Education"])
    for kw in keywords:
        pattern = rf"\b({re.escape(kw)})\b"
        text = re.sub(pattern, r'<span class="highlight">\1</span>', text, flags=re.I)
    return text


def generate_summary(text):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if not sentences or sentences == [""]:
        return ""
    summary = " ".join(sentences[:2]).strip()
    if summary and summary[-1] not in ".!?":
        summary += "."
    return summary


def keyword_suggestions(text):
    desired_keywords = _CFG.get("desired_keywords", [])
    return [kw for kw in desired_keywords if kw.lower() not in text.lower()]


def color_code_score(score):
    if score >= 75:
        return "#4CAF50"
    elif score >= 50:
        return "#FF9800"
    return "#F44336"
