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
    
    prompt = f"""You are an expert HR analytics system that evaluates developer contributions using a rigorous mathematical model. You must apply the formulas and grading criteria below. When exact formula inputs are unavailable, approximate them from the provided activity data.

=== DEVELOPER ACTIVITY DATA ===
Name: {summary.get('name')}
Title: {summary.get('title')}
Role: {summary.get('role')}
Commits (30 days): {summary.get('commits')}
Avg commits/day: {summary.get('avgCommitsPerDay')}
Active PRs: {summary.get('prsActive')}
Impact score (0-100): {summary.get('impactScore')}
Bugs resolved (monthly): {summary.get('bugsResolved')}
Code review participation: {summary.get('codeReviewParticipation')}%
Tech stack: {', '.join(summary.get('techStack', []))}
Primary technology: {summary.get('primaryTech')}
Recent commit messages: {'; '.join(summary.get('lastCommitTitles', []))}

=== MATHEMATICAL MODEL — 6 PARAMETERS (each 0-100) ===

1. PRODUCTIVITY (maps to "productivity")
   Core formula: W = E / N, where E = work output (features, tickets), N = effort (time).
   Supporting metrics:
   - Velocity = sum of completed Story Points per sprint
   - DORA Deployment Frequency (DF) = rate of successful releases
   Proxy mapping: commits → E (output volume); avgCommitsPerDay → delivery rate; PRs → features delivered; impactScore → weighted output.
   Scoring guide: avgCommitsPerDay < 0.5 → low (20-40); 0.5-2 → medium (40-65); 2-5 → good (65-85); > 5 → high (85-100). Adjust by impactScore and PR count.

2. QUALITY (maps to "quality")
   Core formulas:
   - Defect Density = Defects / KLOC (lower is better)
   - Technical Debt Ratio: TDR = (Remediation Cost / Development Cost) × 100%
   - Maintainability Index: MI = max(0, (171 - 5.2·ln(HV) - 0.23·CC - 16.2·ln(LOC)) / 171 × 100)
   - Maintainability Delta: ΔMI = MI_after - MI_before (positive = code improved)
   Proxy mapping: bugsResolved → inverse defect density (more fixes = better quality stewardship); commit messages containing "fix", "refactor", "cleanup", "test" → positive ΔMI; ratio of fix/refactor commits to total → TDR improvement signal.
   Scoring guide: bugsResolved 0-2 with no fix commits → low (30-45); 3-8 bugs + some fix commits → medium (50-70); > 8 bugs + frequent refactors → high (75-95).

3. COLLABORATION (maps to "collaboration")
   Core formula: Collaborative Impact CI = Σ(PR_Comments) / Lead_Time_Review
   High CI means active, fast reviewing. Also considers cross-team communication.
   Proxy mapping: codeReviewParticipation% → direct proxy for CI numerator; prsActive → review volume; commit messages with "review", "merge", "pair" → teamwork signal.
   Scoring guide: codeReviewParticipation < 20% → low (25-40); 20-50% → medium (45-65); 50-80% → good (65-85); > 80% → high (85-100). Adjust by PR activity.

4. RELIABILITY (maps to "reliability")
   Core formulas:
   - DORA Mean Time to Restore (MTTR) — lower is better
   - DORA Change Failure Rate (CFR) = failed changes / total changes — lower is better
   Measures consistency and stability of delivery.
   Proxy mapping: consistency of avgCommitsPerDay (steady > spiky) → low CFR; bugsResolved relative to commits → inverse CFR; impactScore → overall dependability; commit messages with "hotfix", "revert", "rollback" → higher MTTR (negative signal).
   Scoring guide: stable commit rate + low revert ratio → high (75-95); erratic commits or many reverts → low (30-50); role "Junior" inherently caps at ~70 unless exceptional data.

5. INITIATIVE (maps to "initiative")
   Core formula: Role Fidelity RF = (Commits_Arch + Commits_Refac) / Total_Commits
   Higher RF means more architectural/refactoring work vs simple code.
   Grade thresholds from model: Junior RF < 0.2; Mid RF 0.2-0.5; Senior RF > 0.5; Lead RF > 0.5 + team focus.
   Proxy mapping: classify each commit message — "arch", "design", "migrate", "refactor", "restructure", "ci/cd", "infra", "docs", "new feature" → architectural/proactive commits; divide by total commits.
   Scoring guide: RF < 0.1 → low (20-35); RF 0.1-0.25 → medium (40-55); RF 0.25-0.5 → good (60-80); RF > 0.5 → high (80-100).

6. EXPERTISE (maps to "expertise")
   Core formulas:
   - Stack Versatility: SV = Σ(λ_i × Usage_i) / Required_Stack, where λ_i = weight for each technology
   - Cognitive Agility: CA = Cyclomatic_Complexity / Cycle_Time (lower cycle time for complexity = better)
   Proxy mapping: number of technologies in techStack → SV breadth; primaryTech presence → depth; commit messages involving complex topics ("algorithm", "optimization", "architecture", "security", "database", "API design") → high CA; role seniority modulates expectation.
   Scoring guide: 1-2 techs + simple commits → low (30-45); 3-4 techs + moderate complexity → medium (50-70); 5+ techs or deep specialization + complex commits → high (75-95).

=== GRADING CONTEXT (for calibration) ===
Junior: high LOC/day but low RF (<0.2), high AI dependency, simple tasks.
Mid: moderate RF (0.2-0.5), stable ΔMI ≈ 0, moderate CI.
Senior: high RF (>0.5) from refactoring/arch work, positive ΔMI, high CI.
Lead: maximum CI (deep reviews), high SV (cross-stack), team throughput focus.

Evaluate honestly — do NOT inflate scores. Use the role as context but score based on actual data.

OUTPUT: Respond ONLY with a valid JSON object, no explanation. Example:
{{"productivity": 85, "quality": 78, "collaboration": 92, "reliability": 88, "initiative": 72, "expertise": 90}}"""

    try:
        content = _call_openrouter(prompt)
        return parse_ai_stats(content) if content else {k: 50 for k in STAT_KEYS}
    except Exception as e:
        print(f'AI stats error: {e}')
        return {k: 50 for k in STAT_KEYS}


def analyze_commit_contribution(commit_message: str, role: str) -> dict:
    """
    Analyze a single commit message and determine its contribution to 6 stats.
    Returns dict with increments (0-5 each) for the 6 parameters.
    """
    if not OPENROUTER_API_KEY:
        return {k: 1 for k in STAT_KEYS}

    prompt = f"""You are an HR analytics system. Analyze ONE commit and determine how much it contributes to each of 6 developer parameters (0-5 points each).

COMMIT MESSAGE: "{commit_message}"
DEVELOPER ROLE: {role}

PARAMETER DEFINITIONS (from MathModel):

1. productivity — W = E/N (output per effort). Commit adds to productivity if it delivers features, closes tickets, implements functionality.
   Keywords: "feat", "add", "implement", "create", "build", "endpoint", "page", "component"

2. quality — Defect Density, TDR, ΔMI (Maintainability Delta). Commit adds to quality if it fixes bugs, improves code, adds tests, reduces tech debt.
   Keywords: "fix", "bugfix", "test", "refactor", "cleanup", "lint", "type-safe", "validate"

3. collaboration — CI = Σ(PR_Comments) / Lead_Time_Review. Commit adds to collaboration if it involves reviews, merges, pair work, documentation for others.
   Keywords: "merge", "review", "pair", "docs", "readme", "onboarding", "shared", "common"

4. reliability — DORA MTTR, CFR. Commit adds to reliability if it improves stability, monitoring, error handling, recovery.
   Keywords: "stable", "monitor", "logging", "error handling", "fallback", "retry", "health check", "ci/cd"

5. initiative — RF = (Commits_Arch + Commits_Refac) / Total. Commit adds to initiative if it's architectural, migration, proactive improvement, new tooling.
   Keywords: "arch", "migrate", "restructure", "infra", "upgrade", "design", "rfc", "proposal", "ci", "docker"

6. expertise — SV (Stack Versatility), CA (Cognitive Agility). Commit adds to expertise if it shows deep technical knowledge, complex algorithms, multi-stack work.
   Keywords: "algorithm", "optimize", "security", "database", "api design", "performance", "cache", "concurrency"

RULES:
- Each parameter: 0 (not related) to 5 (strongly related)
- Most commits affect 2-3 parameters, NOT all 6
- A simple typo fix = low across all (maybe quality: 1)
- A major feature = productivity: 4-5, maybe expertise: 2-3
- A complex refactor = quality: 4-5, initiative: 3-4
- Be precise, not generous

Respond ONLY with JSON. Example: {{"productivity": 3, "quality": 1, "collaboration": 0, "reliability": 0, "initiative": 2, "expertise": 1}}"""

    try:
        content = _call_openrouter(prompt, max_tokens=256)
        if not content:
            return {k: 1 for k in STAT_KEYS}
        return _parse_commit_increments(content)
    except Exception as e:
        print(f'AI commit analysis error: {e}')
        return {k: 1 for k in STAT_KEYS}


def _parse_commit_increments(response_text: str) -> dict:
    """Parse AI response for commit increments (0-5 each)."""
    text = response_text.strip()
    if '```' in text:
        match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
        if match:
            text = match.group(1)
    match = re.search(r'\{[^{}]*(?:"productivity"|"quality")[^{}]*\}', text, re.DOTALL)
    if not match:
        match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            data = json.loads(match.group())
            return {k: min(5, max(0, int(data.get(k, 0)))) for k in STAT_KEYS}
        except (json.JSONDecodeError, ValueError):
            pass
    return {k: 1 for k in STAT_KEYS}


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

    prompt = f"""You are an HR analytics system using a mathematical model to evaluate developer grading.

The 6 stats below were computed from these formulas:
- productivity ← W = E/N (output/effort), DORA Deployment Frequency
- quality ← Defect Density, TDR, Maintainability Delta (ΔMI = MI_after - MI_before)
- collaboration ← Collaborative Impact CI = Σ(PR_Comments) / Lead_Time_Review
- reliability ← DORA MTTR, Change Failure Rate
- initiative ← Role Fidelity RF = (Commits_Arch + Commits_Refac) / Total_Commits
- expertise ← Stack Versatility SV = Σ(λ_i·Usage_i)/Required_Stack, Cognitive Agility CA

Grade expectations from the model:
- Junior: RF < 0.2, low CI, ΔMI ≈ 0 or negative → stats typically 30-50
- Mid: RF 0.2-0.5, stable ΔMI ≈ 0, moderate CI → stats typically 50-65
- Senior: RF > 0.5, positive ΔMI, high CI → stats typically 65-80
- Lead: max CI (deep reviews), high SV (cross-stack), team throughput → stats typically 80-95

CURRENT POSITION: {role_level} ({title or role_level})
REQUIREMENTS for {role_level} (minimum threshold):
  productivity: {requirements['productivity']}, quality: {requirements['quality']}, collaboration: {requirements['collaboration']}
  reliability: {requirements['reliability']}, initiative: {requirements['initiative']}, expertise: {requirements['expertise']}

EMPLOYEE ACTUAL STATS:
  productivity: {params['productivity']}, quality: {params['quality']}, collaboration: {params['collaboration']}
  reliability: {params['reliability']}, initiative: {params['initiative']}, expertise: {params['expertise']}

DECISION RULES:
- "promote": most stats exceed requirements by ≥ 15 points, indicating the employee operates at the next grade level
- "demote": several stats fall ≥ 10 below requirements, indicating the employee underperforms for current position
- "keep": stats roughly match requirements (within ±10-15 of thresholds)

Respond ONLY with JSON: {{"action": "promote"|"demote"|"keep", "reason": "brief explanation referencing specific stats"}}"""

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
