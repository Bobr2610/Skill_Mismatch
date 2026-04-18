# DevMetrics Backend

Python Flask backend with SQLite storage for employee data.

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Server runs at **http://localhost:5000**

## Scripts

| Script | Description |
|--------|--------------|
| `start.bat` / `start.ps1` | Start the backend server |
| `stop.bat` / `stop.ps1` | Stop the server (kills process on port 5000) |

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | Team KPIs, commits chart, recent activity, employees |
| GET | `/api/employees` | List all employees |
| GET | `/api/employees/<id>` | Get single employee |
| POST | `/api/employees` | Create employee |
| PUT | `/api/employees/<id>` | Update employee |
| DELETE | `/api/employees/<id>` | Delete employee |

## Database

- **SQLite** file: `devmetrics.db` (created in `backend/` on first run)
- Tables: `employees`, `dashboard_config`
- Seed data is loaded automatically on first start

## Re-seed database

To reset and re-seed:

```bash
# Delete DB and restart
del devmetrics.db   # Windows
python app.py       # Recreates and seeds
```
