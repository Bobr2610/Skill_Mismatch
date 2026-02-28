"""
AI service for computing employee activity stats via OpenRouter (GLM 4.5 Air)
"""
import os
import json
import re

# Load .env from project root (parent of backend/)
_env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(_env_path):
    try:
        with open(_env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except Exception:
        pass

OPENROUTER_API_KEY = os.environ.get('Openrouter_API_Key') or os.environ.get('OPENROUTER_API_KEY')
OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
MODEL = 'z-ai/glm-4.5-air:free'

STAT_KEYS = ['productivity', 'quality', 'collaboration', 'reliability', 'initiative', 'expertise']


def _call_openrouter(prompt: str, max_tokens: int = 512, temperature: float = 0.3) -> str:
    """Unified OpenRouter API call. Returns content string or empty."""
    import urllib.request
    body = {
        'model': MODEL,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': max_tokens,
        'temperature': temperature,
        'reasoning': {'enabled': False},
    }
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(body).encode(),
        headers={
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://devmetrics.local',
        },
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        out = json.loads(resp.read().decode())
    choices = out.get('choices') or []
    if not choices:
        err_msg = (out.get('error') or {}).get('message', str(out))[:200]
        print(f"[AI] No choices: {err_msg}")
        return ''
    first = choices[0]
    msg_obj = first.get('message') or first
    content = msg_obj.get('content') or msg_obj.get('text') or ''
    if not content:
        reasoning = msg_obj.get('reasoning') or msg_obj.get('reasoning_content') or ''
        if reasoning:
            print(f"[AI] Content empty but reasoning present ({len(reasoning)} chars). Model used thinking mode despite disabled flag.")
        else:
            print(f"[AI] Empty content. Full: {json.dumps(out)[:500]}")
    return content


def build_activity_summary(employee_data: dict) -> dict:
    """Build compact activity summary from employee data for AI input."""
    metrics = employee_data.get('metrics') or {}
    if isinstance(metrics, str):
        try:
            metrics = json.loads(metrics)
        except Exception:
            metrics = {}
    tech_stack = employee_data.get('tech_stack') or []
    if isinstance(tech_stack, str):
        try:
            tech_stack = json.loads(tech_stack)
        except Exception:
            tech_stack = []
    commits_history = employee_data.get('commits_history') or []
    
    last_titles = []
    for c in commits_history[:5]:
        msg = c.get('message', '') if isinstance(c, dict) else str(c)
        if msg:
            last_titles.append(msg[:80])
    
    return {
        'name': employee_data.get('name', ''),
        'title': employee_data.get('title', ''),
        'role': employee_data.get('role', ''),
        'commits': employee_data.get('commits', 0),
        'avgCommitsPerDay': metrics.get('avgCommitsPerDay', 0),
        'prsActive': employee_data.get('prs_active', 0),
        'impactScore': employee_data.get('impact_score', 0),
        'bugsResolved': metrics.get('bugsResolved', 0),
        'codeReviewParticipation': metrics.get('codeReviewParticipation', 0),
        'techStack': tech_stack[:6] if isinstance(tech_stack, list) else [],
        'primaryTech': employee_data.get('primary_tech', ''),
        'lastCommitTitles': last_titles,
    }


def parse_ai_stats(response_text: str) -> dict:
    """Parse AI response to extract 6 stats. Expects JSON object."""
    text = response_text.strip()
    # Remove markdown code blocks if present
    if '```' in text:
        match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
        if match:
            text = match.group(1)
    # Try to find JSON object with our keys
    match = re.search(r'\{[^{}]*(?:"productivity"|"quality")[^{}]*\}', text, re.DOTALL)
    if not match:
        match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            data = json.loads(match.group())
            return {k: min(100, max(0, int(data.get(k, 50)))) for k in STAT_KEYS}
        except (json.JSONDecodeError, ValueError):
            pass
    try:
        data = json.loads(text)
        return {k: min(100, max(0, int(data.get(k, 50)))) for k in STAT_KEYS}
    except (json.JSONDecodeError, ValueError):
        pass
    return {k: 50 for k in STAT_KEYS}  # default


def compute_activity_stats(employee_data: dict) -> dict:
    """
    Call OpenRouter AI to compute 6 activity stats from employee summary.
    Returns dict with keys: productivity, quality, collaboration, reliability, initiative, expertise (0-100 each).
    """
    if not OPENROUTER_API_KEY:
        return {k: 50 for k in STAT_KEYS}
    
    summary = build_activity_summary(employee_data)
    if isinstance(employee_data.get('activity_summary'), dict):
        summary = {**summary, **employee_data['activity_summary']}
    
    prompt = f"""You are an HR analytics assistant. Based on the following developer activity summary, compute 6 stats (0-100 each) like in an RPG game.

Summary:
- Name: {summary.get('name')}
- Title: {summary.get('title')}
- Role: {summary.get('role')}
- Commits (30d): {summary.get('commits')}
- Avg commits/day: {summary.get('avgCommitsPerDay')}
- Active PRs: {summary.get('prsActive')}
- Impact score: {summary.get('impactScore')}
- Bugs resolved: {summary.get('bugsResolved')}
- Code review participation %: {summary.get('codeReviewParticipation')}
- Tech stack: {', '.join(summary.get('techStack', []))}
- Primary tech: {summary.get('primaryTech')}
- Recent commits: {'; '.join(summary.get('lastCommitTitles', []))}

Stats to compute (0-100 each):
- productivity: output volume, commits, delivery speed
- quality: code quality, bugs fixed, stability
- collaboration: teamwork, code reviews, communication
- reliability: consistency, meeting expectations
- initiative: new features, docs, proactivity
- expertise: technical depth, stack mastery

Respond ONLY with valid JSON, no other text. Example:
{{"productivity": 85, "quality": 78, "collaboration": 92, "reliability": 88, "initiative": 72, "expertise": 90}}"""

    try:
        content = _call_openrouter(prompt)
        return parse_ai_stats(content) if content else {k: 50 for k in STAT_KEYS}
    except Exception as e:
        print(f'AI stats error: {e}')
        return {k: 50 for k in STAT_KEYS}


def _get_role_for_requirements(role: str) -> str:
    """Map role string to canonical level for requirements lookup."""
    from constants import ROLE_REQUIREMENTS
    r = (role or "").strip().lower()
    for level in ("Lead", "Staff", "Senior", "Junior", "Mid"):
        if level.lower() in r or r == level.lower():
            return level
    return "Mid"


def get_career_recommendation(activity_stats: dict, title: str, role: str) -> dict:
    """
    AI recommends: promote, demote, or keep.
    Sends only: 6 stats + position + requirements for that position (no full employee data).
    """
    if not OPENROUTER_API_KEY:
        return {"action": "keep", "reason": "AI not configured. Add Openrouter_API_Key to .env"}

    from constants import ROLE_REQUIREMENTS

    stats = activity_stats or {k: 50 for k in STAT_KEYS}
    params = {k: min(100, max(0, int(stats.get(k, 50)))) for k in STAT_KEYS}

    role_level = _get_role_for_requirements(role)
    requirements = ROLE_REQUIREMENTS.get(role_level, ROLE_REQUIREMENTS["Mid"])

    prompt = f"""Compare employee stats against position requirements. Return promote, demote, or keep.

POSITION: {role_level} ({title or role_level})
Requirements for this position (minimum):
- productivity: {requirements['productivity']}, quality: {requirements['quality']}, collaboration: {requirements['collaboration']}
- reliability: {requirements['reliability']}, initiative: {requirements['initiative']}, expertise: {requirements['expertise']}

EMPLOYEE STATS (actual):
- productivity: {params['productivity']}, quality: {params['quality']}, collaboration: {params['collaboration']}
- reliability: {params['reliability']}, initiative: {params['initiative']}, expertise: {params['expertise']}

RULES:
- promote: stats clearly exceed requirements (e.g. most ≥ requirements + 15)
- demote: stats below requirements (e.g. several ≥ 10 below)
- keep: stats roughly match requirements

Respond ONLY with JSON: {{"action": "promote"|"demote"|"keep", "reason": "brief explanation"}}"""

    try:
        content = _call_openrouter(prompt)
        if not content:
            return {"action": "keep", "reason": "AI returned empty response."}
        return _parse_recommendation(content)
    except Exception as e:
        print(f'AI recommendation error: {e}')
        return {"action": "keep", "reason": f"AI error: {str(e)[:150]}"}


def _parse_recommendation(text: str) -> dict:
    text = text.strip()
    # Extract JSON block (markdown code block or raw)
    if '```' in text:
        m = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
        if m:
            text = m.group(1)
    # Find JSON object - try greedy match for nested braces
    for match in re.finditer(r'\{[^{}]*(?:"action"|"reason")[^{}]*\}', text):
        try:
            d = json.loads(match.group())
            action = str(d.get('action', d.get('Action', 'keep'))).lower()
            if action not in ('promote', 'demote', 'keep'):
                action = 'keep'
            reason = str(d.get('reason', d.get('Reason', d.get('explanation', ''))))[:300]
            return {"action": action, "reason": reason or "No reason provided."}
        except (json.JSONDecodeError, ValueError):
            continue
    # Fallback: try full {...} match
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        try:
            raw = m.group()
            # Fix common issues: trailing comma, single quotes
            raw = raw.replace("'", '"')
            d = json.loads(raw)
            action = str(d.get('action', 'keep')).lower()
            if action not in ('promote', 'demote', 'keep'):
                action = 'keep'
            return {"action": action, "reason": str(d.get('reason', ''))[:300] or "No reason provided."}
        except (json.JSONDecodeError, ValueError):
            pass
    # Last resort: detect action from plain text
    lower = text.lower()
    if 'promote' in lower and 'demote' not in lower[:lower.find('promote')]:
        return {"action": "promote", "reason": text[:300] if len(text) > 10 else "AI suggests promotion."}
    if 'demote' in lower:
        return {"action": "demote", "reason": text[:300] if len(text) > 10 else "AI suggests demotion."}
    return {"action": "keep", "reason": text[:300] if len(text) > 10 else "Could not parse AI response."}
