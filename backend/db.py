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

    # Migration: add new columns if table exists with old schema
    try:
        cur.execute("ALTER TABLE employees ADD COLUMN activity_summary TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE employees ADD COLUMN activity_stats TEXT")
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

    employees = [
        {
            "id": "sarah-chen",
            "name": "Sarah Chen",
            "role": "Staff",
            "title": "Senior Frontend Engineer",
            "location": "San Francisco, US",
            "email": "sarah.chen@devmetrics.io",
            "avatar": "https://ui-avatars.com/api/?name=Sarah+Chen&background=135bec&color=fff",
            "metrics": json.dumps({
                "avgCommitsPerDay": 9.2,
                "commitsTrend": "+15%",
                "codeReviewParticipation": 96,
                "codeReviewTrend": "Stable",
                "bugsResolved": 142,
                "bugsTrend": "-8%",
            }),
            "commits": 248,
            "prs_active": 12,
            "impact_score": 92,
            "commits_history": [{"message": "feat: optimize data fetching hooks for dashboard widgets"}, {"message": "fix: resolve hydration mismatch in SSR"}, {"message": "refactor: extract shared components to design system"}, {"message": "chore: update eslint config"}, {"message": "docs: add component documentation"}],
            "tech_stack": json.dumps(["React", "TypeScript", "Node.js", "GraphQL", "Jest", "Webpack"]),
            "primary_tech": "React",
            "collaborators": json.dumps([
                {"id": "marcus-wright", "name": "Marcus Wright", "reviews": 98},
                {"id": "elena-rossi", "name": "Elena Rossi", "reviews": 76},
                {"id": "david-kim", "name": "David Kim", "reviews": 54},
            ]),
        },
        {
            "id": "marcus-wright",
            "name": "Marcus Wright",
            "role": "Senior",
            "title": "Backend Engineer",
            "location": "Austin, US",
            "email": "marcus.w@devmetrics.io",
            "avatar": "https://ui-avatars.com/api/?name=Marcus+Wright&background=135bec&color=fff",
            "metrics": json.dumps({
                "avgCommitsPerDay": 7.8,
                "commitsTrend": "+8%",
                "codeReviewParticipation": 91,
                "codeReviewTrend": "Stable",
                "bugsResolved": 98,
                "bugsTrend": "-12%",
            }),
            "commits": 192,
            "prs_active": 8,
            "impact_score": 84,
            "commits_history": [{"message": "feat(api): add rate limiting middleware"}, {"message": "fix: handle null in user serializer"}, {"message": "refactor: migrate to async/await"}, {"message": "test: add integration tests for webhooks"}, {"message": "chore: bump redis client version"}],
            "tech_stack": json.dumps(["Go", "Python", "PostgreSQL", "Redis", "Docker", "Kubernetes"]),
            "primary_tech": "Go",
            "collaborators": json.dumps([
                {"id": "alex-rivers", "name": "Alex Rivers", "reviews": 112},
                {"id": "sarah-chen", "name": "Sarah Chen", "reviews": 89},
                {"id": "elena-rossi", "name": "Elena Rossi", "reviews": 67},
            ]),
        },
        {
            "id": "elena-rossi",
            "name": "Elena Rossi",
            "role": "Senior",
            "title": "Full Stack Engineer",
            "location": "Berlin, DE",
            "email": "elena.r@devmetrics.io",
            "avatar": "https://ui-avatars.com/api/?name=Elena+Rossi&background=135bec&color=fff",
            "metrics": json.dumps({
                "avgCommitsPerDay": 6.9,
                "commitsTrend": "+5%",
                "codeReviewParticipation": 94,
                "codeReviewTrend": "+2%",
                "bugsResolved": 118,
                "bugsTrend": "-6%",
            }),
            "commits": 176,
            "prs_active": 14,
            "impact_score": 78,
            "commits_history": [{"message": "fix: memory leak in worker threads"}, {"message": "feat: add websocket support for real-time updates"}, {"message": "refactor: simplify state management"}, {"message": "test: add e2e tests for checkout flow"}, {"message": "docs: update API documentation"}],
            "tech_stack": json.dumps(["TypeScript", "Node.js", "React", "PostgreSQL", "GraphQL", "Docker"]),
            "primary_tech": "TypeScript",
            "collaborators": json.dumps([
                {"id": "sarah-chen", "name": "Sarah Chen", "reviews": 82},
                {"id": "marcus-wright", "name": "Marcus Wright", "reviews": 71},
                {"id": "alex-rivers", "name": "Alex Rivers", "reviews": 58},
            ]),
        },
        {
            "id": "david-kim",
            "name": "David Kim",
            "role": "Mid",
            "title": "DevOps Engineer",
            "location": "Seoul, KR",
            "email": "david.k@devmetrics.io",
            "avatar": "https://ui-avatars.com/api/?name=David+Kim&background=135bec&color=fff",
            "metrics": json.dumps({
                "avgCommitsPerDay": 5.8,
                "commitsTrend": "+18%",
                "codeReviewParticipation": 87,
                "codeReviewTrend": "Stable",
                "bugsResolved": 65,
                "bugsTrend": "-15%",
            }),
            "commits": 154,
            "prs_active": 5,
            "impact_score": 65,
            "commits_history": [{"message": "docs: update architecture diagrams for v3.0"}, {"message": "feat: add blue-green deployment pipeline"}, {"message": "fix: correct k8s resource limits"}, {"message": "chore: migrate to terraform 1.5"}, {"message": "fix: resolve DNS propagation in staging"}],
            "tech_stack": json.dumps(["Kubernetes", "Terraform", "AWS", "Docker", "Python", "Go"]),
            "primary_tech": "Kubernetes",
            "collaborators": json.dumps([
                {"id": "alex-rivers", "name": "Alex Rivers", "reviews": 45},
                {"id": "marcus-wright", "name": "Marcus Wright", "reviews": 38},
                {"id": "elena-rossi", "name": "Elena Rossi", "reviews": 29},
            ]),
        },
        {
            "id": "alex-rivers",
            "name": "Alex Rivers",
            "role": "Staff",
            "title": "Senior Backend Engineer",
            "location": "London, UK",
            "email": "alex.r@devmetrics.io",
            "avatar": "https://ui-avatars.com/api/?name=Alex+Rivers&background=135bec&color=fff",
            "metrics": json.dumps({
                "avgCommitsPerDay": 8.4,
                "commitsTrend": "+12%",
                "codeReviewParticipation": 94,
                "codeReviewTrend": "Stable",
                "bugsResolved": 127,
                "bugsTrend": "-5%",
            }),
            "commits": 214,
            "prs_active": 10,
            "impact_score": 88,
            "commits_history": [{"message": "feat(api): optimize database indexing for payment history"}, {"message": "fix(worker): handle timeout in stripe webhook consumer"}, {"message": "docs: update readme with deployment instructions"}, {"message": "refactor: migrate user schema to v3 format"}, {"message": "chore: bump dependencies for security update"}],
            "tech_stack": json.dumps(["Python", "Go", "PostgreSQL", "Redis", "Kubernetes", "gRPC", "Docker"]),
            "primary_tech": "Go",
            "collaborators": json.dumps([
                {"id": "sarah-chen", "name": "Sarah Chen", "reviews": 124},
                {"id": "marcus-wright", "name": "Marcus Wright", "reviews": 89},
                {"id": "elena-rossi", "name": "Elena Rossi", "reviews": 62},
            ]),
        },
        {
            "id": "julia-park",
            "name": "Julia Park",
            "role": "Senior",
            "title": "Data Engineer",
            "location": "Toronto, CA",
            "email": "julia.p@devmetrics.io",
            "avatar": "https://ui-avatars.com/api/?name=Julia+Park&background=135bec&color=fff",
            "metrics": json.dumps({
                "avgCommitsPerDay": 6.2,
                "commitsTrend": "+22%",
                "codeReviewParticipation": 89,
                "codeReviewTrend": "+5%",
                "bugsResolved": 78,
                "bugsTrend": "-10%",
            }),
            "commits": 168,
            "prs_active": 6,
            "impact_score": 72,
            "commits_history": [{"message": "feat: add incremental ETL pipeline for analytics"}, {"message": "fix: handle timezone in date aggregation"}, {"message": "refactor: optimize spark job partitioning"}, {"message": "test: add unit tests for data validators"}, {"message": "docs: document data pipeline architecture"}],
            "tech_stack": json.dumps(["Python", "Spark", "Airflow", "PostgreSQL", "dbt", "Snowflake"]),
            "primary_tech": "Python",
            "collaborators": json.dumps([
                {"id": "alex-rivers", "name": "Alex Rivers", "reviews": 52},
                {"id": "elena-rossi", "name": "Elena Rossi", "reviews": 41},
                {"id": "david-kim", "name": "David Kim", "reviews": 38},
            ]),
        },
        {
            "id": "omar-hassan",
            "name": "Omar Hassan",
            "role": "Mid",
            "title": "Mobile Engineer",
            "location": "Dubai, AE",
            "email": "omar.h@devmetrics.io",
            "avatar": "https://ui-avatars.com/api/?name=Omar+Hassan&background=135bec&color=fff",
            "metrics": json.dumps({
                "avgCommitsPerDay": 5.4,
                "commitsTrend": "+14%",
                "codeReviewParticipation": 82,
                "codeReviewTrend": "Stable",
                "bugsResolved": 91,
                "bugsTrend": "-7%",
            }),
            "commits": 142,
            "prs_active": 9,
            "impact_score": 68,
            "commits_history": [{"message": "feat(ios): add dark mode support"}, {"message": "fix(android): crash on rotation"}, {"message": "refactor: extract shared UI components"}, {"message": "chore: update react-native to 0.72"}, {"message": "fix: memory leak in image cache"}],
            "tech_stack": json.dumps(["React Native", "TypeScript", "Swift", "Kotlin", "Firebase"]),
            "primary_tech": "React Native",
            "collaborators": json.dumps([
                {"id": "sarah-chen", "name": "Sarah Chen", "reviews": 67},
                {"id": "elena-rossi", "name": "Elena Rossi", "reviews": 54},
                {"id": "marcus-wright", "name": "Marcus Wright", "reviews": 43},
            ]),
        },
        {
            "id": "nina-volkova",
            "name": "Nina Volkova",
            "role": "Staff",
            "title": "Security Engineer",
            "location": "Warsaw, PL",
            "email": "nina.v@devmetrics.io",
            "avatar": "https://ui-avatars.com/api/?name=Nina+Volkova&background=135bec&color=fff",
            "metrics": json.dumps({
                "avgCommitsPerDay": 4.8,
                "commitsTrend": "+9%",
                "codeReviewParticipation": 98,
                "codeReviewTrend": "+3%",
                "bugsResolved": 156,
                "bugsTrend": "-18%",
            }),
            "commits": 128,
            "prs_active": 11,
            "impact_score": 90,
            "commits_history": [{"message": "fix(security): patch SQL injection in user search"}, {"message": "feat: add OWASP dependency check to CI"}, {"message": "refactor: migrate to bcrypt for password hashing"}, {"message": "docs: security audit report Q3"}, {"message": "fix: disable debug endpoints in production"}],
            "tech_stack": json.dumps(["Python", "Go", "Vault", "OWASP", "Kubernetes", "Terraform"]),
            "primary_tech": "Go",
            "collaborators": json.dumps([
                {"id": "marcus-wright", "name": "Marcus Wright", "reviews": 134},
                {"id": "alex-rivers", "name": "Alex Rivers", "reviews": 98},
                {"id": "david-kim", "name": "David Kim", "reviews": 76},
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

    # Dashboard config
    team_kpis = json.dumps({
        "totalCommits": 1842,
        "totalCommitsTrend": "+14.2%",
        "activePRs": 61,
        "activePRsTrend": "+8%",
        "avgCycleTimeDays": 2.1,
        "avgCycleTimeTrend": "-0.3 Days",
        "deploymentFreq": 9.5,
        "deploymentFreqTrend": "+1.3/day",
    })
    commits_over_time = json.dumps([
        52, 48, 61, 55, 58, 62, 49, 54, 67, 59, 52, 48, 55, 61, 58, 64, 57, 53, 59, 62, 55, 51, 58, 65, 60, 54, 57, 61, 56, 52, 59
    ])
    # Activity feed — icon/color from constants
    _raw_activity = [
        {"type": "commit", "userId": "sarah-chen", "repo": "main", "message": "feat: optimize data fetching hooks for dashboard widgets", "timeAgo": "2 minutes ago"},
        {"type": "review", "userId": "marcus-wright", "prNumber": 432, "prTitle": "Update auth flow validation", "timeAgo": "15 minutes ago"},
        {"type": "merge", "userId": "elena-rossi", "message": "Resolved memory leak in worker threads", "timeAgo": "1 hour ago"},
        {"type": "commit", "userId": "david-kim", "repo": "dev", "message": "docs: update architecture diagrams for v3.0", "timeAgo": "3 hours ago"},
        {"type": "deploy", "userId": "sarah-chen", "env": "Staging", "timeAgo": "4 hours ago"},
        {"type": "commit", "userId": "alex-rivers", "repo": "main-api", "message": "fix: resolve race condition in payment processor", "timeAgo": "5 hours ago"},
        {"type": "review", "userId": "elena-rossi", "prNumber": 431, "prTitle": "Add retry logic for external API calls", "timeAgo": "6 hours ago"},
        {"type": "commit", "userId": "marcus-wright", "repo": "auth-service", "message": "chore: upgrade dependencies", "timeAgo": "8 hours ago"},
        {"type": "commit", "userId": "julia-park", "repo": "data-warehouse", "message": "feat: add incremental ETL pipeline for analytics", "timeAgo": "10 hours ago"},
        {"type": "fix", "userId": "nina-volkova", "repo": "main-api", "message": "patch SQL injection in user search", "timeAgo": "12 hours ago"},
        {"type": "commit", "userId": "omar-hassan", "repo": "mobile-app", "message": "feat(ios): add dark mode support", "timeAgo": "14 hours ago"},
        {"type": "review", "userId": "alex-rivers", "prNumber": 430, "prTitle": "Optimize database indexing", "timeAgo": "16 hours ago"},
        {"type": "merge", "userId": "david-kim", "message": "Blue-green deployment pipeline merged", "timeAgo": "18 hours ago"},
        {"type": "deploy", "userId": "elena-rossi", "env": "Production", "timeAgo": "20 hours ago"},
        {"type": "commit", "userId": "sarah-chen", "repo": "ui-kit", "message": "refactor: extract shared components to design system", "timeAgo": "Yesterday"},
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
