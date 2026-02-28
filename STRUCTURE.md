# DevMetrics — File Structure

Professional file structure for an employee evaluation platform (как в настоящих фирмах).

> **Команды запуска/остановки** — см. [RULE.md](RULE.md)

## Directory Tree

```
Skill_Mismatch/
├── index.html                 # Entry point, redirects to dashboard
├── STRUCTURE.md               # This file
│
├── backend/                   # Python Flask backend
│   ├── app.py                 # Flask app, API routes, static serving
│   ├── constants.py           # Activity types, icons, defaults
│   ├── db.py                  # SQLite DB init, seed data
│   ├── requirements.txt       # Python dependencies
│   └── devmetrics.db          # SQLite database (created on first run)
│
├── assets/                    # Static assets
│   ├── css/
│   │   ├── base.css           # Base styles, fonts, contribution grid
│   │   └── variables.css      # Design tokens (colors, spacing, radius)
│   ├── js/
│   │   ├── config/            # Configuration (enterprise-style grouping)
│   │   │   ├── theme.js       # Theme tokens, colors, Tailwind values
│   │   │   ├── icons.js       # Icon registry (nav, activity, UI)
│   │   │   ├── routes.js      # Routes, nav items
│   │   │   └── index.js       # Aggregated APP_CONFIG
│   │   ├── api.js             # API client for backend
│   │   ├── app.js             # Main application logic, component loader
│   │   ├── charts.js          # Chart rendering
│   │   ├── config.js          # Config loader (backward compat)
│   │   └── pages.js           # Page-specific data binding
│   ├── images/                # Images, icons (optional)
│   └── fonts/                 # Custom fonts (optional)
│
├── components/                # Reusable UI components (templates)
│   ├── header.html            # Top navigation header
│   ├── sidebar.html           # Dashboard sidebar
│   └── breadcrumbs.html       # Breadcrumb navigation
│
├── pages/                     # Application pages
│   ├── dashboard.html         # Team productivity overview
│   ├── profile.html           # Individual employee profile & analytics
│   ├── comparison.html       # Employee comparison tool
│   └── team.html              # Engineering team, add employee
│
└── docs/                      # Documentation & reference
    └── Infograrf.png          # Infographics, diagrams
```

## Responsibilities

| Folder | Purpose |
|--------|---------|
| **assets/** | All static resources: CSS, JS, images. Shared across pages. |
| **components/** | Reusable HTML fragments. Use as templates or with `data-include` when served over HTTP. |
| **pages/** | Full page templates. Each file is a complete HTML document. |
| **docs/** | Project documentation, infographics, diagrams. |

## Path Conventions

- Pages use relative paths: `../assets/css/base.css`, `../assets/js/app.js`
- Internal links: `dashboard.html`, `profile.html`, `comparison.html` (same folder)
- From root: `pages/dashboard.html`

## Running Locally

**Recommended: Use the Python backend** (serves both API and static files):

```powershell
# PowerShell
cd backend
.\start.ps1
```

```cmd
REM CMD
cd backend
start.bat
```

Or manually:

```powershell
cd backend
pip install -r requirements.txt
python app.py
```

Then open: **http://localhost:5000**

**Stop the server:**

```powershell
# PowerShell
.\stop.ps1
```

```cmd
REM CMD
stop.bat
```

The backend provides:
- REST API at `/api/` (employees, dashboard)
- Static files (HTML, CSS, JS, assets)
- SQLite storage for employee data

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|--------------|
| GET | `/api/dashboard` | Team KPIs, commits chart, recent activity, employees |
| GET | `/api/employees` | List all employees |
| GET | `/api/employees/<id>` | Get single employee |
| POST | `/api/employees` | Create employee |
| PUT | `/api/employees/<id>` | Update employee |
| DELETE | `/api/employees/<id>` | Delete employee |
| POST | `/api/employees/<id>/refresh-stats` | Recompute 6 activity stats via AI (OpenRouter) |
| POST | `/api/employees/<id>/recommendation` | AI career recommendation: promote / demote / keep |

## Activity Stats (AI-powered)

Instead of storing heavy chart data (heatmaps, full commit history), each employee has:
- **activity_summary** — compact JSON: commits, avg/day, PRs, bugs, reviews, tech stack, last 5 commit titles
- **activity_stats** — 6 game-like params (0–100): productivity, quality, collaboration, reliability, initiative, expertise

Stats are computed by AI via OpenRouter (`z-ai/glm-4.5-air:free`). Set `Openrouter_API_Key` in `.env`.

## Configuration Architecture

Config is grouped by domain (enterprise-style):

| Module | Purpose |
|--------|---------|
| **config/theme.js** | Design tokens: colors, spacing, Tailwind values |
| **config/icons.js** | Icon registry: nav, activity types, UI icons |
| **config/routes.js** | Routes, nav items |
| **config/index.js** | Aggregated `APP_CONFIG` |
| **backend/constants.py** | Activity types, icon mapping, defaults |

Theme and icons are single source of truth — change once, applies everywhere.

## Extending the Structure

For a production setup, consider:

- **Build step**: Vite, Parcel, or webpack for bundling
- **Framework**: React/Vue/Svelte for component-based UI
- **Database**: Migrate from SQLite to PostgreSQL
- **Tests**: `tests/` or `__tests__/` for unit/e2e tests
