@echo off
echo Stopping DevMetrics backend...

for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5000" ^| findstr "LISTENING"') do (
    taskkill /pid %%a /f >nul 2>&1
    echo Stopped process on port 5000.
    goto :done
)
echo No process found on port 5000.
:done
