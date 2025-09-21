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

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return local_summary(text)

    # Helper: robustly call OpenAI (try chat completions if available)
    try:
        import importlib
        try:
            openai = importlib.import_module('openai')
        except Exception:
            return local_summary(text)

        openai.api_key = api_key

        system = "You are a concise professional resume writer."
        user = f"Write a professional 2-3 sentence summary for this resume:\n\n{text[:2000]}"

        # Prefer ChatCompletion if available
        if hasattr(openai, 'ChatCompletion'):
            try:
                resp = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=[{"role": "system", "content": system}, {"role": "user", "content": user}], max_tokens=max_tokens)
                out = resp.choices[0].message.content
                return sanitize_ai_output(out)
            except Exception:
                pass

        # Fallback to older Completion API
        resp = openai.Completion.create(engine="text-davinci-003", prompt=user, max_tokens=max_tokens)
        out = resp.choices[0].text
        return sanitize_ai_output(out)
    except Exception:
        return local_summary(text)


    return bullet


def rewrite_bullet(bullet: str) -> str:
    """Rewrite a resume bullet into an achievement-focused line using AI if available."""
    api_key = os.environ.get("OPENAI_API_KEY")
    try:
        from utils.analyzer import generate_summary as local_summary
    except Exception:
        local_summary = lambda t: t

    # preserve original marker if present
    marker = ''
    content = bullet
    if bullet.strip().startswith('-') or bullet.strip().startswith('•'):
        marker = bullet.strip()[0]
        content = bullet.strip()[1:].strip()

    if not api_key:
        return bullet
    try:
        import importlib
        try:
            openai = importlib.import_module('openai')
        except Exception:
            return bullet

        openai.api_key = api_key

        system = "You are a resume writing assistant. Rewrite the user's bullet into a single concise achievement-focused bullet. Return only the rewritten bullet." 
        user = f"Rewrite this resume bullet to focus on impact and metrics (one sentence):\n\n{content}\n"

        # Try ChatCompletion first
        if hasattr(openai, 'ChatCompletion'):
            try:
                resp = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=[{"role":"system","content":system},{"role":"user","content":user}], max_tokens=120)
                out = resp.choices[0].message.content
                out = sanitize_ai_output(out)
            except Exception:
                out = None
        else:
            out = None

        # Fallback to Completion
        if not out:
            try:
                resp = openai.Completion.create(engine="text-davinci-003", prompt=user, max_tokens=120)
                out = resp.choices[0].text
                out = sanitize_ai_output(out)
            except Exception:
                out = None

        if not out:
            return bullet

        # Ensure marker preserved
        if marker and not out.lstrip().startswith(marker):
            out = f"{marker} {out.lstrip()}"

        return out
    except Exception:
        return bullet


def sanitize_ai_output(out: str) -> str:
    """Sanitize raw AI output: remove prompt echoes, instruction fragments, and keep only the main sentence(s).

    This function returns a single-line sanitized string or an empty string if nothing safe.
    """
    if out is None:
        return ""
    # strip surrounding whitespace and markdown fences
    s = out.strip()
    # remove common instruction prefixes
    prefixes = ["Rewrite this resume bullet", "Rewritten:", "Response:", "Output:", "Sure:\n"]
    for p in prefixes:
        if s.startswith(p):
            s = s[len(p):].strip()

    # remove any leading/ trailing quote markers or code fences
    s = s.strip('\n `')

    # If the AI returned multiple lines, prefer the first non-empty meaningful line
    lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
    if not lines:
        return ""
    candidate = lines[0]

    # If candidate contains the original prompt text, remove it
    # (best-effort: drop repeated substrings)
    # Normalize whitespace
    candidate = ' '.join(candidate.split())

    # remove leading labels like "- " or numbering
    if candidate.startswith('- '):
        candidate = candidate[2:]
    if candidate.startswith('* '):
        candidate = candidate[2:]

    return candidate.strip()


def rewrite_bullet_raw(bullet: str) -> str:
    """Return raw AI output for a rewritten bullet (no sanitization). Uses the same call path but returns model text as-is.

    This is intended for debugging and tests; callers should prefer `rewrite_bullet`.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return bullet
    try:
        import importlib
        try:
            openai = importlib.import_module('openai')
        except Exception:
            return bullet

        openai.api_key = api_key
        content = bullet.strip()
        if content.startswith('-') or content.startswith('•'):
            content = content[1:].strip()
        prompt = f"Rewrite this resume bullet to focus on impact and metrics (one sentence):\n\n{content}\n"
        if hasattr(openai, 'ChatCompletion'):
            try:
                resp = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=[{"role":"user","content":prompt}], max_tokens=120)
                return resp.choices[0].message.content
            except Exception:
                pass
        resp = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=120)
        return resp.choices[0].text
    except Exception:
        return bullet
