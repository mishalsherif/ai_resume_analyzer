from typing import Dict, List
import re
from pathlib import Path
from utils.analyzer import _load_config


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[A-Za-z0-9\+\-]+", text.lower())


def match_keywords(resume_text: str, jd_text: str) -> Dict:
    """Return matched and missing keywords from config against a job description.

    Output: {matched: [...], missing: [...], score: 0.0-1.0}
    """
    cfg = _load_config()
    desired = [k.lower() for k in cfg.get("desired_keywords", [])]

    jd_tokens = set(_tokenize(jd_text))
    matched = [kw for kw in desired if kw.lower() in jd_tokens]
    missing = [kw for kw in desired if kw.lower() not in jd_tokens]
    score = len(matched) / max(1, len(desired))
    return {"matched": matched, "missing": missing, "score": score}
