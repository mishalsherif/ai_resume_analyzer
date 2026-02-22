import os

import os
from typing import Optional

def generate_ai_summary(text: str, max_tokens: int = 150) -> str:
    """Generate a short professional summary using OpenAI if API key present,
    otherwise fall back to the local heuristic summary.
    """
    try:
        from utils.analyzer import generate_summary as local_summary
    except Exception:
        local_summary = lambda t: t[:200]
import importlib
import json
import os
import time
from typing import Optional, List
import hashlib


def _load_openai():
    try:
        return importlib.import_module('openai')
    except Exception:
        return None


def _call_openai_chat(messages: list, max_tokens: int = 150, retries: int = 3, backoff: float = 0.8) -> Optional[str]:
    openai = _load_openai()
    if not openai:
        return None
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return None
    openai.api_key = api_key
    for attempt in range(retries):
        try:
            resp = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=messages, max_tokens=max_tokens)
            return resp.choices[0].message.content
        except Exception:
            time.sleep(backoff * (2 ** attempt))
    return None


def _call_openai_completion(prompt: str, max_tokens: int = 150, retries: int = 3, backoff: float = 0.8) -> Optional[str]:
    openai = _load_openai()
    if not openai:
        return None
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return None
    openai.api_key = api_key
    for attempt in range(retries):
        try:
            resp = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=max_tokens)
            return resp.choices[0].text
        except Exception:
            time.sleep(backoff * (2 ** attempt))
    return None


def generate_ai_summary(text: str, max_tokens: int = 150) -> str:
    """Generate a short professional summary using OpenAI if available, otherwise fallback.

    Returns a sanitized 1-3 sentence summary.
    """
    try:
        from utils.analyzer import generate_summary as local_summary
    except Exception:
        local_summary = lambda t: t[:200]

    system = "You are a concise, professional resume writer. Return ONLY the requested text without any explanation or metadata."
    user = (
        "Write a 2-3 sentence professional summary for this resume. Focus on role, domain, and key achievements. "
        f"Return only the summary. Resume text:\n\n{text[:3000]}"
    )

    out = _call_openai_chat([{"role": "system", "content": system}, {"role": "user", "content": user}], max_tokens=max_tokens)
    if out:
        return sanitize_ai_output(out)

    out = _call_openai_completion(user, max_tokens=max_tokens)
    if out:
        return sanitize_ai_output(out)

    return local_summary(text)


def rewrite_bullet(bullet: str) -> str:
    """Rewrite a resume bullet into an achievement-focused line using AI if available.

    Always returns a single-line string (fallback to original bullet when AI not available).
    """
    api_key = os.environ.get('OPENAI_API_KEY')
    # preserve original marker if present
    marker = ''
    content = bullet
    if bullet.strip().startswith('-') or bullet.strip().startswith('•'):
        marker = bullet.strip()[0]
        content = bullet.strip()[1:].strip()

    if not api_key:
        return bullet

    system = "You are a resume writing assistant. Return ONLY the rewritten bullet as a single sentence, no labels or extraneous text."
    user = f"Rewrite this resume bullet to focus on impact and metrics (one sentence):\n\n{content}\n"

    out = _call_openai_chat([{"role": "system", "content": system}, {"role": "user", "content": user}], max_tokens=120)
    if not out:
        out = _call_openai_completion(user, max_tokens=120)

    if not out:
        return bullet

    out = sanitize_ai_output(out)
    # Ensure marker preserved
    if marker and not out.lstrip().startswith(marker):
        out = f"{marker} {out.lstrip()}"
    return out


def bulk_rewrite_bullets(bullets: List[str], max_tokens: int = 400) -> List[str]:
    """Rewrite multiple bullets in one call. Returns sanitized rewritten bullets in same order.
    Falls back to per-bullet rewrite or original bullets if no AI available."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key or not bullets:
        return bullets

    system = "You are a resume-writing assistant. Rewrite each bullet into a concise achievement-focused sentence. Return a JSON array of strings only."
    joined = "\n".join([b.lstrip('-• ').strip() for b in bullets])
    user = f"Rewrite these bullets into achievement-focused single-sentence bullets. Return only a JSON array of rewritten bullets in the same order.\n\n{joined}"

    out = _call_openai_chat([{"role": "system", "content": system}, {"role": "user", "content": user}], max_tokens=max_tokens)
    if not out:
        out = _call_openai_completion(user, max_tokens=max_tokens)

    if not out:
        # fallback to individual rewrites
        return [rewrite_bullet(b) for b in bullets]

    # try to parse JSON-like output gracefully
    s = out.strip()
    try:
        arr = json.loads(s)
        return [sanitize_ai_output(a) for a in arr]
    except Exception:
        # best-effort: split by lines
        lines = [ln for ln in s.splitlines() if ln.strip()]
        if len(lines) >= len(bullets):
            return [sanitize_ai_output(ln) for ln in lines[: len(bullets)]]
        return [rewrite_bullet(b) for b in bullets]


def sanitize_ai_output(out: str) -> str:
    """Sanitize raw AI output: remove prompt echoes, instruction fragments, and keep only the main sentence(s).

    This function returns a single-line sanitized string or an empty string if nothing safe.
    """
    if out is None:
        return ""
    # strip surrounding whitespace and markdown fences
    s = out.strip()
    # remove common instruction prefixes (case-insensitive)
    prefixes = ["rewrite this resume bullet", "rewritten:", "response:", "output:", "sure:", "1."]
    low = s.lower()
    for p in prefixes:
        if low.startswith(p):
            s = s[len(p):].strip()
            low = s.lower()

    # remove any leading/ trailing quote markers or code fences
    s = s.strip('\n `')

    # If the AI returned multiple lines, prefer the first non-empty meaningful line
    lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
    if not lines:
        return ""
    candidate = lines[0]

    # Normalize whitespace
    candidate = ' '.join(candidate.split())

    # remove leading labels like bullets or numbering
    candidate = candidate.lstrip('-*•\u2022 ').lstrip('0123456789.). ')

    return candidate.strip()


def rewrite_bullet_raw(bullet: str) -> str:
    """Return raw AI output for a rewritten bullet (no sanitization). Uses the same call path but returns model text as-is.

    This is intended for debugging and tests; callers should prefer `rewrite_bullet`.
    """
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return bullet
    content = bullet.strip()
    if content.startswith('-') or content.startswith('•'):
        content = content[1:].strip()
    prompt = f"Rewrite this resume bullet to focus on impact and metrics (one sentence):\n\n{content}\n"
    out = _call_openai_chat([{"role": "user", "content": prompt}], max_tokens=120)
    if out:
        return out
    out = _call_openai_completion(prompt, max_tokens=120)
    if out:
        return out
    return bullet


def generate_recommendations(resume_text: str, job_text: str) -> dict:
    """Generate basic job-matching recommendations.

    Returns a dict with keys:
      - matched: list of matched sections/keywords
      - missing: list of missing keywords
      - score: float between 0 and 1
      - detected_bullets: list of bullets found in the resume
      - rewritten_bullets: list of rewritten bullets (uses bulk_rewrite_bullets when available)
    """
    # Simple keyword extraction from job_text: split on non-word and lower
    import re

    job_words = [w.lower() for w in re.findall(r"\w+", job_text) if len(w) > 2]
    # common stopwords to ignore for matching
    stop = set(["and", "the", "with", "for", "from", "that", "this", "have", "has", "are", "was"])
    job_keywords = [w for w in job_words if w not in stop]

    resume_words = [w.lower() for w in re.findall(r"\w+", resume_text) if len(w) > 2]

    matched = []
    missing = []
    seen = set(resume_words)
    for kw in job_keywords:
        if kw in seen:
            matched.append(kw)
        else:
            missing.append(kw)

    total = max(1, len(job_keywords))
    score = len(matched) / total

    # detect bullets: simple heuristic lines that start with bullet markers or •
    raw_lines = resume_text.splitlines()
    bullets_with_index = []
    for idx, ln in enumerate(raw_lines):
        s = ln.strip()
        if not s:
            continue
        if s.startswith('-') or s.startswith('•') or s.startswith('*'):
            h = hashlib.sha1(s.encode('utf-8')).hexdigest()
            bullets_with_index.append({"text": s, "line_index": idx, "hash": h})

    # If no bullets found, try to take candidate lines (short with commas)
    if not bullets_with_index:
        for idx, ln in enumerate(raw_lines):
            if len(ln.strip()) < 200 and ',' in ln:
                h = hashlib.sha1(ln.strip().encode('utf-8')).hexdigest()
                bullets_with_index.append({"text": ln.strip(), "line_index": idx, "hash": h})
                if len(bullets_with_index) >= 30:
                    break

    bullets = [b["text"] for b in bullets_with_index]

    # Attempt to rewrite bullets using bulk API or per-bullet fallback
    rewritten = bulk_rewrite_bullets(bullets)

    # Align rewritten bullets with bullets_with_index
    rewritten_aligned = []
    for i, binfo in enumerate(bullets_with_index):
        rewritten_aligned.append({
            "original": binfo["text"],
            "line_index": binfo["line_index"],
            "hash": binfo.get("hash"),
            "suggested": rewritten[i] if i < len(rewritten) else (rewritten[-1] if rewritten else binfo["text"]),
        })

    # Build the heuristic result
    heuristic = {
        "matched": matched[:20],
        "missing": missing[:50],
        "score": round(score, 3),
        "detected_bullets": bullets_with_index,
        "rewritten_bullets": rewritten_aligned,
    }

    # If OpenAI is available, attempt to get a strict JSON recommendation object
    openai_mod = _load_openai()
    if openai_mod and os.environ.get('OPENAI_API_KEY'):
        # Prepare a concise prompt requesting strict JSON with fields matching heuristic
        payload = {
            "instructions": "Return a strict JSON object with keys: matched (array of strings), missing (array of strings), score (number between 0 and 1), detected_bullets (array of {text,line_index}), rewritten_bullets (array of {original,line_index,suggested}). Do NOT include any additional text.",
            "resume_excerpt": "\n".join(raw_lines[:200]),
            "job_excerpt": job_text[:1000],
        }
        system = "You are a resume matching assistant. Output ONLY valid JSON and nothing else."
        user = (
            f"{payload['instructions']}\nResume (excerpt):\n{payload['resume_excerpt']}\nJob description (excerpt):\n{payload['job_excerpt']}"
        )
        try:
            out = _call_openai_chat([{"role": "system", "content": system}, {"role": "user", "content": user}], max_tokens=800)
            if out:
                s = out.strip()
                # Find first brace to avoid accidental lead-in
                start = s.find('{')
                if start != -1:
                    s = s[start:]
                parsed = json.loads(s)
                # basic validation of keys
                valid = False
                # If jsonschema is available, validate strictly
                try:
                    import importlib as _il
                    _js = _il.import_module('jsonschema')
                    schema = {
                        "type": "object",
                        "properties": {
                            "matched": {"type": "array"},
                            "missing": {"type": "array"},
                            "score": {"type": "number"},
                            "detected_bullets": {"type": "array"},
                            "rewritten_bullets": {"type": "array"},
                        },
                        "required": ["matched", "missing", "score", "detected_bullets", "rewritten_bullets"],
                    }
                    _js.validate(parsed, schema)
                    valid = True
                except Exception:
                    # fallback to basic structural check
                    if isinstance(parsed, dict) and set(["matched", "missing", "score", "detected_bullets", "rewritten_bullets"]).issubset(set(parsed.keys())):
                        valid = True

                if valid:
                    return parsed
        except Exception:
            pass

    return heuristic
