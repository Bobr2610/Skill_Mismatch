"""
Database initialization and connection for DevMetrics
"""
import sqlite3
import json
import os

from constants import ACTIVITY_ICONS, AVATAR_URL

DB_PATH = os.environ.get('DB_PATH') or os.path.join(os.path.dirname(__file__), 'devmetrics.db')


def get_connection():
    """Get SQLite connection with row factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables and seed initial data."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT,
            title TEXT,
            location TEXT,
            email TEXT,
            avatar TEXT,
            metrics TEXT,
            commits INTEGER DEFAULT 0,
            prs_active INTEGER DEFAULT 0,
            impact_score INTEGER DEFAULT 0,
            activity_summary TEXT,
            activity_stats TEXT,
            tech_stack TEXT,
            primary_tech TEXT,
            collaborators TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS dashboard_config (
            id TEXT PRIMARY KEY DEFAULT 'default',
            team_kpis TEXT,
            commits_over_time TEXT,
            recent_activity TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS stats_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            month TEXT NOT NULL,
            stats_before TEXT,
            monthly_value TEXT,
            stats_after TEXT,
            decay_coefficient REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
        )
    """)

    # Migration: add new columns if table exists with old schema
    try:
        cur.execute("ALTER TABLE employees ADD COLUMN activity_summary TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE employees ADD COLUMN activity_stats TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE employees ADD COLUMN last_recalculation TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


def seed_db():
    """Seed database with employee and dashboard data."""
    conn = get_connection()
    cur = conn.cursor()

    def build_activity_summary(emp):
        """Compact summary for AI - no heavy charts."""
        commits_history = emp.get("commits_history") or []
        if isinstance(commits_history, str):
            try:
                commits_history = json.loads(commits_history)
            except Exception:
                commits_history = []
        last_titles = []
        for c in commits_history[:5]:
            msg = c.get("message", "") if isinstance(c, dict) else str(c)
            if msg:
                last_titles.append(msg[:80])
        tech = emp.get("tech_stack") or []
        if isinstance(tech, str):
            try:
                tech = json.loads(tech)
            except Exception:
                tech = []
        metrics = emp.get("metrics") or {}
        if isinstance(metrics, str):
            try:
                metrics = json.loads(metrics)
            except Exception:
                metrics = {}
        return json.dumps({
            "commits": emp.get("commits", 0),
            "avgCommitsPerDay": metrics.get("avgCommitsPerDay", 0),
            "prsActive": emp.get("prs_active", 0),
            "impactScore": emp.get("impact_score", 0),
            "bugsResolved": metrics.get("bugsResolved", 0),
            "codeReviewParticipation": metrics.get("codeReviewParticipation", 0),
            "techStack": (tech or [])[:6],
            "primaryTech": emp.get("primary_tech", ""),
            "lastCommitTitles": last_titles,
        })

    def default_activity_stats(emp):
        """Default stats from impact_score (AI will override on refresh)."""
        s = emp.get("impact_score", 50)
        return json.dumps({
            "productivity": min(100, int(s * 1.05)),
            "quality": min(100, int(s * 0.95)),
            "collaboration": min(100, int(s * 0.9)),
            "reliability": min(100, int(s)),
            "initiative": min(100, int(s * 0.85)),
            "expertise": min(100, int(s * 1.1)),
        })

    # Replace default DevMetrics sample employees with FIIT team members
    # Source: https://github.com/Bobr2610/FIIT (README.md "Команда")
    employees = [
        {
            "id": "belyanskiy-kirill",
            "name": "Белянский Кирилл",
            "role": "Lead",
            "title": "Lead Frontend Developer",
            "location": "FIIT",
            "email": "kirill.belyanskiy@fiit.app",
            "avatar": "https://ui-avatars.com/api/?name=%D0%91%D0%B5%D0%BB%D1%8F%D0%BD%D1%81%D0%BA%D0%B8%D0%B9+%D0%9A%D0%B8%D1%80%D0%B8%D0%BB%D0%BB&background=135bec&color=fff",
            "metrics": json.dumps({
                "avgCommitsPerDay": 8.5,
                "commitsTrend": "+12%",
                "codeReviewParticipation": 90,
                "codeReviewTrend": "Stable",
                "bugsResolved": 80,
                "bugsTrend": "-10%",
            }),
            "commits": 210,
            "prs_active": 10,
            "impact_score": 88,
            "commits_history": [
                {"message": "feat(frontend): добавить экран портфеля инвестора"},
                {"message": "refactor(ui): унифицировать дизайн карточек активов"},
                {"message": "fix: исправить вычисление доходности за период"},
            ],
            "tech_stack": json.dumps(["React", "TypeScript", "Tailwind CSS", "Vite", "Chart.js"]),
            "primary_tech": "React",
            "collaborators": json.dumps([
                {"id": "salmanov-eldar", "name": "Сальманов Эльдар", "reviews": 95},
                {"id": "sedov-mikhail", "name": "Седов Михаил", "reviews": 76},
            ]),
        },
        {
            "id": "salmanov-eldar",
            "name": "Сальманов Эльдар",
            "role": "Lead",
            "title": "Lead Backend Developer",
            "location": "FIIT",
            "email": "eldar.salmanov@fiit.app",
            "avatar": "https://ui-avatars.com/api/?name=%D0%A1%D0%B0%D0%BB%D1%8C%D0%BC%D0%B0%D0%BD%D0%BE%D0%B2+%D0%AD%D0%BB%D1%8C%D0%B4%D0%B0%D1%80&background=135bec&color=fff",
            "metrics": json.dumps({
                "avgCommitsPerDay": 7.2,
                "commitsTrend": "+9%",
                "codeReviewParticipation": 92,
                "codeReviewTrend": "+3%",
                "bugsResolved": 70,
                "bugsTrend": "-8%",
            }),
            "commits": 185,
            "prs_active": 8,
            "impact_score": 82,
            "commits_history": [
                {"message": "feat(api): реализовать расчёт доходности портфеля по дням"},
                {"message": "chore(db): добавить индексы для таблицы сделок"},
                {"message": "fix(api): корректно обрабатывать отсутствие котировок по инструменту"},
            ],
            "tech_stack": json.dumps(["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"]),
            "primary_tech": "Python",
            "collaborators": json.dumps([
                {"id": "belyanskiy-kirill", "name": "Белянский Кирилл", "reviews": 88},
                {"id": "sedov-mikhail", "name": "Седов Михаил", "reviews": 64},
            ]),
        },
        {
            "id": "sedov-mikhail",
            "name": "Седов Михаил",
            "role": "Senior",
            "title": "Leader, Support Frontend & Backend Developer",
            "location": "FIIT",
            "email": "mikhail.sedov@fiit.app",
            "avatar": "https://ui-avatars.com/api/?name=%D0%A1%D0%B5%D0%B4%D0%BE%D0%B2+%D0%9C%D0%B8%D1%85%D0%B0%D0%B8%D0%BB&background=135bec&color=fff",
            "metrics": json.dumps({
                "avgCommitsPerDay": 6.5,
                "commitsTrend": "+15%",
                "codeReviewParticipation": 88,
                "codeReviewTrend": "Stable",
                "bugsResolved": 95,
                "bugsTrend": "-12%",
            }),
            "commits": 170,
            "prs_active": 7,
            "impact_score": 80,
            "commits_history": [
                {"message": "feat: интегрировать уведомления о ребалансировке портфеля"},
                {"message": "refactor: вынести общие компоненты в ui-библиотеку"},
                {"message": "fix: устранить дублирование расчёта комиссий брокера"},
            ],
            "tech_stack": json.dumps(["Python", "Flask", "React", "Docker", "NGINX"]),
            "primary_tech": "Python",
            "collaborators": json.dumps([
                {"id": "belyanskiy-kirill", "name": "Белянский Кирилл", "reviews": 71},
                {"id": "salmanov-eldar", "name": "Сальманов Эльдар", "reviews": 69},
            ]),
        },
    ]

    for emp in employees:
        activity_summary = build_activity_summary(emp)
        activity_stats = default_activity_stats(emp)
        cur.execute("""
            INSERT OR REPLACE INTO employees (
                id, name, role, title, location, email, avatar,
                metrics, commits, prs_active, impact_score,
                activity_summary, activity_stats,
                tech_stack, primary_tech, collaborators
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            emp["id"], emp["name"], emp["role"], emp["title"], emp["location"],
            emp["email"], emp["avatar"], emp["metrics"], emp["commits"],
            emp["prs_active"], emp["impact_score"],
            activity_summary, activity_stats,
            emp["tech_stack"], emp["primary_tech"], emp["collaborators"]
        ))

    # Dashboard config — adjusted for 3-person FIIT team
    team_kpis = json.dumps({
        "totalCommits": 565,
        "totalCommitsTrend": "+12%",
        "activePRs": 25,
        "activePRsTrend": "+6%",
        "avgCycleTimeDays": 1.8,
        "avgCycleTimeTrend": "-0.2 Days",
        "deploymentFreq": 4.2,
        "deploymentFreqTrend": "+0.8/day",
    })
    commits_over_time = json.dumps([
        18, 21, 15, 24, 19, 22, 17, 20, 25, 23, 18, 16, 22, 19, 26, 21, 17, 24, 20, 23, 18, 22, 19, 25, 21, 16, 20, 24, 22, 18, 23
    ])
    _raw_activity = [
        {"type": "commit", "userId": "belyanskiy-kirill", "repo": "frontend", "message": "feat(frontend): добавить экран портфеля инвестора", "timeAgo": "5 minutes ago"},
        {"type": "review", "userId": "salmanov-eldar", "prNumber": 87, "prTitle": "Добавить расчёт доходности портфеля", "timeAgo": "20 minutes ago"},
        {"type": "commit", "userId": "sedov-mikhail", "repo": "main", "message": "feat: интегрировать уведомления о ребалансировке портфеля", "timeAgo": "1 hour ago"},
        {"type": "merge", "userId": "belyanskiy-kirill", "message": "Унифицировать дизайн карточек активов", "timeAgo": "2 hours ago"},
        {"type": "commit", "userId": "salmanov-eldar", "repo": "backend", "message": "chore(db): добавить индексы для таблицы сделок", "timeAgo": "3 hours ago"},
        {"type": "deploy", "userId": "sedov-mikhail", "env": "Staging", "timeAgo": "4 hours ago"},
        {"type": "fix", "userId": "belyanskiy-kirill", "repo": "frontend", "message": "fix: исправить вычисление доходности за период", "timeAgo": "5 hours ago"},
        {"type": "review", "userId": "sedov-mikhail", "prNumber": 86, "prTitle": "Вынести общие компоненты в ui-библиотеку", "timeAgo": "6 hours ago"},
        {"type": "commit", "userId": "salmanov-eldar", "repo": "backend", "message": "fix(api): корректно обрабатывать отсутствие котировок", "timeAgo": "8 hours ago"},
        {"type": "deploy", "userId": "belyanskiy-kirill", "env": "Production", "timeAgo": "10 hours ago"},
        {"type": "commit", "userId": "sedov-mikhail", "repo": "main", "message": "refactor: вынести общие компоненты в ui-библиотеку", "timeAgo": "12 hours ago"},
        {"type": "review", "userId": "salmanov-eldar", "prNumber": 85, "prTitle": "Оптимизировать запросы к БД", "timeAgo": "14 hours ago"},
        {"type": "merge", "userId": "sedov-mikhail", "message": "Устранить дублирование расчёта комиссий брокера", "timeAgo": "16 hours ago"},
        {"type": "commit", "userId": "belyanskiy-kirill", "repo": "frontend", "message": "refactor(ui): унифицировать дизайн карточек активов", "timeAgo": "Yesterday"},
        {"type": "commit", "userId": "salmanov-eldar", "repo": "backend", "message": "feat(api): реализовать расчёт доходности портфеля по дням", "timeAgo": "Yesterday"},
    ]
    recent_activity = json.dumps([
        {**a, "icon": ACTIVITY_ICONS.get(a["type"], ("commit", "emerald"))[0],
         "iconColor": ACTIVITY_ICONS.get(a["type"], ("commit", "emerald"))[1]}
        for a in _raw_activity
    ])

    cur.execute("""
        INSERT OR REPLACE INTO dashboard_config (id, team_kpis, commits_over_time, recent_activity)
        VALUES ('default', ?, ?, ?)
    """, (team_kpis, commits_over_time, recent_activity))

    conn.commit()
    conn.close()
    print("Database seeded successfully.")


if __name__ == "__main__":
    init_db()
    seed_db()
