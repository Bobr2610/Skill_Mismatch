@echo off
cd /d "%~dp0"

echo Starting DevMetrics backend...
pip install -r requirements.txt --quiet
echo Open http://localhost:5000
python app.py
