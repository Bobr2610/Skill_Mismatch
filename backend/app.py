"""
DevMetrics - Flask backend for employee evaluation platform
"""
import os
import json
import urllib.request
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from db import get_connection, init_db, seed_db
from ai import compute_activity_stats, build_activity_summary as ai_build_summary, get_career_recommendation
from constants import ROLE_DECAY_COEFFICIENTS

app = Flask(__name__, static_folder='../', static_url_path='')
CORS(app)
GITHUB_REPO = os.getenv("GITHUB_REPO", "Bobr2610/FIIT")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Initialize database on startup
with app.app_context():
    init_db()
    seed_db()


def _github_headers():
    headers = {
        "User-Agent": "DevMetrics-App",
        "Accept": "application/vnd.github+json",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def _fetch_github_commits(owner_repo: str, days: int = 30):
    """
    Fetch recent commits from GitHub and aggregate by day.
    Returns (daily_counts, recent_activity).
    """
    if not owner_repo:
        return [], []

    now = datetime.now(timezone.utc)
    since_dt = now - timedelta(days=days)
    since_str = since_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"https://api.github.com/repos/{owner_repo}/commits?since={since_str}&per_page=100"

    try:
        req = urllib.request.Request(url, headers=_github_headers())
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return [], []

    by_day = {}
    events = []

    for item in data or []:
        commit = item.get("commit") or {}
        author = commit.get("author") or {}
        date_str = author.get("date")
        msg = (commit.get("message") or "").splitlines()[0]
        login = (item.get("author") or {}).get("login") or author.get("name") or "unknown"

        try:
            commit_dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except Exception:
            continue

        day_key = commit_dt.date().isoformat()
        by_day[day_key] = by_day.get(day_key, 0) + 1

        diff = now - commit_dt
        seconds = int(diff.total_seconds())
        if seconds < 60:
            time_ago = "just now"
        elif seconds < 3600:
            time_ago = f"{seconds // 60} min ago"
        elif seconds < 86400:
            time_ago = f"{seconds // 3600} h ago"
        else:
            time_ago = f"{seconds // 86400} d ago"

        events.append({
            "userId": login, "type": "commit", "repo": owner_repo,
            "message": msg, "timeAgo": time_ago, "timestamp": commit_dt.isoformat(),
        })

    days_range = [since_dt.date() + timedelta(days=i) for i in range(days)]
    daily_counts = [by_day.get(d.isoformat(), 0) for d in days_range]
    events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return daily_counts, events[:30]


def _fetch_github_contributor_stats(owner_repo: str):
    """
    Fetch per-contributor weekly commit statistics via GitHub Stats API.
    Returns list of {login, avatar, total, weeks: [{w, c, a, d}]}.
    GitHub may return 202 while computing — we retry once.
    """
    import time as _time

    if not owner_repo:
        return []

    url = f"https://api.github.com/repos/{owner_repo}/stats/contributors"
    data = None

    try:
        for _attempt in range(3):
            req = urllib.request.Request(url, headers=_github_headers())
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 202:
                    _time.sleep(2)
                    continue
                data = json.loads(resp.read().decode("utf-8"))
                break
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    result = []
    for c in data:
        author = c.get("author") or {}
        weeks = [{"w": w["w"], "c": w.get("c", 0), "a": w.get("a", 0), "d": w.get("d", 0)}
                 for w in (c.get("weeks") or [])]
        result.append({
            "login": author.get("login", "unknown"),
            "avatar": author.get("avatar_url", ""),
            "total": c.get("total", 0),
            "weeks": weeks,
        })

    result.sort(key=lambda x: x["total"], reverse=True)
    return result


def row_to_employee(row):
    """Convert DB row to employee dict (frontend format)."""
    row = dict(row)
    return {
        "id": row["id"],
        "name": row["name"],
        "role": row["role"],
        "title": row["title"],
        "location": row["location"],
        "email": row["email"],
        "avatar": row["avatar"],
        "metrics": json.loads(row["metrics"]) if row.get("metrics") else {},
        "commits": row.get("commits", 0),
        "prsActive": row.get("prs_active", 0),
        "impactScore": row.get("impact_score", 0),
        "activityStats": json.loads(row["activity_stats"]) if row.get("activity_stats") else None,
        "activitySummary": json.loads(row["activity_summary"]) if row.get("activity_summary") else {},
        "techStack": json.loads(row["tech_stack"]) if row.get("tech_stack") else [],
        "primaryTech": row.get("primary_tech", ""),
        "collaborators": json.loads(row["collaborators"]) if row.get("collaborators") else [],
        "lastRecalculation": row.get("last_recalculation"),
    }


def _get_decay_coefficient(role: str) -> float:
    """Get Green's principle decay coefficient for a role."""
    r = (role or "").strip()
    for level in ("Lead", "Staff", "Senior", "Junior", "Mid"):
        if level.lower() in r.lower():
            return ROLE_DECAY_COEFFICIENTS[level]
    return ROLE_DECAY_COEFFICIENTS["Mid"]


def _apply_green_formula(current_stats: dict, monthly_value: dict, coefficient: float) -> dict:
    """Apply Green's principle: new_stat = current_stat * K + monthly_value, clamped 0-100."""
    stat_keys = ['productivity', 'quality', 'collaboration', 'reliability', 'initiative', 'expertise']
    result = {}
    for k in stat_keys:
        old = current_stats.get(k, 50)
        fresh = monthly_value.get(k, 50)
        result[k] = min(100, max(0, int(old * coefficient + fresh)))
    return result


# --- API Routes ---

@app.route("/api/employees", methods=["GET"])
def list_employees():
    """Get all employees."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees ORDER BY impact_score DESC")
    rows = cur.fetchall()
    conn.close()
    employees = [row_to_employee(dict(r)) for r in rows]
    return jsonify(employees)


@app.route("/api/employees/<employee_id>", methods=["GET"])
def get_employee(employee_id):
    """Get single employee by ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Employee not found"}), 404
    return jsonify(row_to_employee(dict(row)))


@app.route("/api/employees", methods=["POST"])
def create_employee():
    """Create new employee."""
    data = request.get_json()
    if not data or "id" not in data or "name" not in data:
        return jsonify({"error": "id and name are required"}), 400

    emp_id = data["id"]
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM employees WHERE id = ?", (emp_id,))
    if cur.fetchone():
        conn.close()
        return jsonify({"error": "Employee with this id already exists"}), 409

    metrics = json.dumps(data.get("metrics", {}))
    tech_stack = json.dumps(data.get("techStack", []))
    collaborators = json.dumps(data.get("collaborators", []))
    emp_for_summary = {
        "name": data.get("name", ""),
        "title": data.get("title", ""),
        "role": data.get("role", ""),
        "commits": data.get("commits", 0),
        "metrics": data.get("metrics", {}),
        "prs_active": data.get("prsActive", 0),
        "impact_score": data.get("impactScore", 0),
        "tech_stack": data.get("techStack", []),
        "primary_tech": data.get("primaryTech", ""),
        "commits_history": data.get("commitsHistory", []),
    }
    activity_summary = json.dumps(ai_build_summary(emp_for_summary))
    default_stats = {"productivity": 50, "quality": 50, "collaboration": 50, "reliability": 50, "initiative": 50, "expertise": 50}
    activity_stats = json.dumps(data.get("activityStats", default_stats))

    cur.execute("""
        INSERT INTO employees (
            id, name, role, title, location, email, avatar,
            metrics, commits, prs_active, impact_score,
            activity_summary, activity_stats,
            tech_stack, primary_tech, collaborators
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        emp_id,
        data.get("name", ""),
        data.get("role", ""),
        data.get("title", ""),
        data.get("location", ""),
        data.get("email", ""),
        data.get("avatar", f"https://ui-avatars.com/api/?name={data.get('name', 'User').replace(' ', '+')}&background=135bec&color=fff"),
        metrics,
        data.get("commits", 0),
        data.get("prsActive", 0),
        data.get("impactScore", 0),
        activity_summary,
        activity_stats,
        tech_stack,
        data.get("primaryTech", ""),
        collaborators,
    ))
    conn.commit()
    conn.close()
    return jsonify({"id": emp_id, "message": "Employee created"}), 201


@app.route("/api/employees/<employee_id>", methods=["PUT"])
def update_employee(employee_id):
    """Update existing employee."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Employee not found"}), 404

    existing = dict(row)
    metrics = json.dumps(data.get("metrics", json.loads(existing.get("metrics") or "{}")))
    tech_stack = json.dumps(data.get("techStack", json.loads(existing.get("tech_stack") or "[]")))
    collaborators = json.dumps(data.get("collaborators", json.loads(existing.get("collaborators") or "[]")))
    emp_for_summary = {
        "name": data.get("name", existing["name"]),
        "title": data.get("title", existing["title"]),
        "role": data.get("role", existing["role"]),
        "commits": data.get("commits", existing.get("commits", 0)),
        "metrics": json.loads(metrics),
        "prs_active": data.get("prsActive", existing.get("prs_active", 0)),
        "impact_score": data.get("impactScore", existing.get("impact_score", 0)),
        "tech_stack": json.loads(tech_stack),
        "primary_tech": data.get("primaryTech", existing.get("primary_tech", "")),
        "commits_history": data.get("commitsHistory", []),
        "activity_summary": json.loads(existing["activity_summary"]) if existing.get("activity_summary") else {},
    }
    activity_summary = json.dumps(ai_build_summary(emp_for_summary))
    activity_stats = existing.get("activity_stats")
    if data.get("activityStats"):
        activity_stats = json.dumps(data["activityStats"])
    elif not activity_stats:
        activity_stats = json.dumps({"productivity": 50, "quality": 50, "collaboration": 50, "reliability": 50, "initiative": 50, "expertise": 50})

    cur.execute("""
        UPDATE employees SET
            name = ?, role = ?, title = ?, location = ?, email = ?, avatar = ?,
            metrics = ?, commits = ?, prs_active = ?, impact_score = ?,
            activity_summary = ?, activity_stats = ?,
            tech_stack = ?, primary_tech = ?, collaborators = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        data.get("name", existing["name"]),
        data.get("role", existing["role"]),
        data.get("title", existing["title"]),
        data.get("location", existing["location"]),
        data.get("email", existing["email"]),
        data.get("avatar", existing["avatar"]),
        metrics,
        data.get("commits", existing.get("commits", 0)),
        data.get("prsActive", existing.get("prs_active", 0)),
        data.get("impactScore", existing.get("impact_score", 0)),
        activity_summary,
        activity_stats,
        tech_stack,
        data.get("primaryTech", existing.get("primary_tech", "")),
        collaborators,
        employee_id,
    ))
    conn.commit()
    conn.close()
    return jsonify({"message": "Employee updated"})


@app.route("/api/employees/<employee_id>/refresh-stats", methods=["POST"])
def refresh_employee_stats(employee_id):
    """Recompute activity stats via AI (OpenRouter GLM 4.5 Air)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Employee not found"}), 404

    emp_dict = dict(row)
    activity_summary_data = {}
    if emp_dict.get("activity_summary"):
        try:
            activity_summary_data = json.loads(emp_dict["activity_summary"])
        except Exception:
            pass
    emp_for_ai = {
        "name": emp_dict["name"],
        "title": emp_dict["title"],
        "role": emp_dict["role"],
        "metrics": json.loads(emp_dict["metrics"]) if emp_dict.get("metrics") else {},
        "commits": emp_dict.get("commits", 0),
        "prs_active": emp_dict.get("prs_active", 0),
        "impact_score": emp_dict.get("impact_score", 0),
        "tech_stack": json.loads(emp_dict["tech_stack"]) if emp_dict.get("tech_stack") else [],
        "primary_tech": emp_dict.get("primary_tech", ""),
        "activity_summary": activity_summary_data,
    }

    stats = compute_activity_stats(emp_for_ai)

    cur.execute(
        "UPDATE employees SET activity_stats = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (json.dumps(stats), employee_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"activityStats": stats, "message": "Stats refreshed via AI"})


def _do_green_recalculate(employee_id, monthly_value_override=None):
    """
    Core Green's principle recalculation logic.
    new_stat = current_stat * K(role) + monthly_value
    Returns dict with results or raises ValueError.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("Employee not found")

    emp_dict = dict(row)
    role = emp_dict.get("role", "Mid")
    coefficient = _get_decay_coefficient(role)

    current_stats = {}
    if emp_dict.get("activity_stats"):
        try:
            current_stats = json.loads(emp_dict["activity_stats"])
        except Exception:
            pass
    if not current_stats:
        current_stats = {k: 50 for k in ['productivity', 'quality', 'collaboration', 'reliability', 'initiative', 'expertise']}

    if monthly_value_override:
        monthly_value = monthly_value_override
    else:
        activity_summary_data = {}
        if emp_dict.get("activity_summary"):
            try:
                activity_summary_data = json.loads(emp_dict["activity_summary"])
            except Exception:
                pass
        emp_for_ai = {
            "name": emp_dict["name"],
            "title": emp_dict["title"],
            "role": emp_dict["role"],
            "metrics": json.loads(emp_dict["metrics"]) if emp_dict.get("metrics") else {},
            "commits": emp_dict.get("commits", 0),
            "prs_active": emp_dict.get("prs_active", 0),
            "impact_score": emp_dict.get("impact_score", 0),
            "tech_stack": json.loads(emp_dict["tech_stack"]) if emp_dict.get("tech_stack") else [],
            "primary_tech": emp_dict.get("primary_tech", ""),
            "activity_summary": activity_summary_data,
        }
        monthly_value = compute_activity_stats(emp_for_ai)

    new_stats = _apply_green_formula(current_stats, monthly_value, coefficient)
    current_month = datetime.now().strftime("%Y-%m")

    cur.execute("""
        INSERT INTO stats_history (employee_id, month, stats_before, monthly_value, stats_after, decay_coefficient)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        employee_id, current_month,
        json.dumps(current_stats), json.dumps(monthly_value),
        json.dumps(new_stats), coefficient,
    ))

    cur.execute(
        "UPDATE employees SET activity_stats = ?, last_recalculation = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (json.dumps(new_stats), current_month, employee_id),
    )
    conn.commit()
    conn.close()

    return {
        "activityStats": new_stats,
        "statsBefore": current_stats,
        "monthlyValue": monthly_value,
        "coefficient": coefficient,
        "role": role,
        "month": current_month,
    }


@app.route("/api/employees/<employee_id>/monthly-recalculate", methods=["POST"])
def monthly_recalculate(employee_id):
    """Green's principle monthly recalculation endpoint."""
    data = request.get_json(silent=True) or {}
    try:
        result = _do_green_recalculate(employee_id, data.get("monthlyValue"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    result["message"] = f"Green's recalculation applied (K={result['coefficient']})"
    return jsonify(result)


@app.route("/api/employees/recalculate-all", methods=["POST"])
def recalculate_all_employees():
    """Apply Green's principle monthly recalculation to all employees."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM employees")
    rows = cur.fetchall()
    conn.close()

    results = []
    for row in rows:
        emp = dict(row)
        try:
            _do_green_recalculate(emp["id"])
            results.append({"id": emp["id"], "name": emp["name"], "status": "ok"})
        except Exception as e:
            results.append({"id": emp["id"], "name": emp["name"], "status": str(e)})

    return jsonify({"results": results, "message": f"Recalculated {len(results)} employees"})


@app.route("/api/employees/<employee_id>/stats-history", methods=["GET"])
def get_stats_history(employee_id):
    """Get monthly stats history for an employee."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM stats_history WHERE employee_id = ? ORDER BY created_at DESC LIMIT 12",
        (employee_id,),
    )
    rows = cur.fetchall()
    conn.close()

    history = []
    for r in rows:
        r = dict(r)
        history.append({
            "month": r["month"],
            "statsBefore": json.loads(r["stats_before"]) if r.get("stats_before") else {},
            "monthlyValue": json.loads(r["monthly_value"]) if r.get("monthly_value") else {},
            "statsAfter": json.loads(r["stats_after"]) if r.get("stats_after") else {},
            "decayCoefficient": r.get("decay_coefficient"),
            "createdAt": r.get("created_at"),
        })
    return jsonify(history)


@app.route("/api/decay-coefficients", methods=["GET"])
def get_decay_coefficients():
    """Return the role decay coefficients used by Green's formula."""
    return jsonify(ROLE_DECAY_COEFFICIENTS)


@app.route("/api/employees/<employee_id>/recommendation", methods=["POST"])
def get_employee_recommendation(employee_id):
    """AI recommendation: promote, demote, or keep based on 6 stats and position."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Employee not found"}), 404

    row = dict(row)
    activity_stats = {}
    if row.get("activity_stats"):
        try:
            activity_stats = json.loads(row["activity_stats"])
        except Exception:
            pass
    title = row.get("title", "")
    role = row.get("role", "")

    rec = get_career_recommendation(activity_stats, title, role)
    return jsonify(rec)


@app.route("/api/employees/<employee_id>", methods=["DELETE"])
def delete_employee(employee_id):
    """Delete employee."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
    if cur.rowcount == 0:
        conn.close()
        return jsonify({"error": "Employee not found"}), 404
    conn.commit()
    conn.close()
    return jsonify({"message": "Employee deleted"})


@app.route("/api/github/contributors", methods=["GET"])
def github_contributors():
    """Per-contributor weekly commit stats from GitHub Stats API."""
    stats = _fetch_github_contributor_stats(GITHUB_REPO)
    return jsonify(stats)


@app.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    """Get dashboard data: team KPIs, commits over time, recent activity, employees."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT team_kpis, commits_over_time, recent_activity FROM dashboard_config WHERE id = 'default'")
    row = cur.fetchone()
    cur.execute("SELECT * FROM employees ORDER BY impact_score DESC")
    emp_rows = cur.fetchall()
    conn.close()

    if not row:
        return jsonify({"error": "Dashboard config not found"}), 500

    team_kpis = json.loads(row["team_kpis"]) if row["team_kpis"] else {}
    commits_over_time = json.loads(row["commits_over_time"]) if row["commits_over_time"] else []
    recent_activity = json.loads(row["recent_activity"]) if row["recent_activity"] else []

    # Try to enhance dashboard with live GitHub activity for the configured repo.
    gh_commits, gh_activity = _fetch_github_commits(GITHUB_REPO)
    if gh_commits:
        commits_over_time = gh_commits
    if gh_activity:
        recent_activity = gh_activity

    employees = [row_to_employee(dict(r)) for r in emp_rows]

    return jsonify({
        "teamKPIs": team_kpis,
        "commitsOverTime": commits_over_time,
        "recentActivity": recent_activity,
        "employees": employees,
    })


# --- Static file serving (for development) ---

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/pages/<path:path>")
def pages(path):
    return send_from_directory(os.path.join(app.static_folder, "pages"), path)


@app.route("/assets/<path:path>")
def assets(path):
    return send_from_directory(os.path.join(app.static_folder, "assets"), path)


@app.route("/components/<path:path>")
def components(path):
    return send_from_directory(os.path.join(app.static_folder, "components"), path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
