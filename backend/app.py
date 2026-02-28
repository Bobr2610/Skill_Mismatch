"""
DevMetrics - Flask backend for employee evaluation platform
"""
import os
import json
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from db import get_connection, init_db, seed_db
from ai import compute_activity_stats, build_activity_summary as ai_build_summary, get_career_recommendation

app = Flask(__name__, static_folder='../', static_url_path='')
CORS(app)

# Initialize database on startup
with app.app_context():
    init_db()
    seed_db()


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
    }


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
