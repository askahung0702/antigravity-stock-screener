@echo off
setlocal
set "PROJECT_ROOT=%~dp0"
"%PROJECT_ROOT%backend\venv\Scripts\python.exe" "%PROJECT_ROOT%backend\scripts\run_daily_pipeline.py" %*
exit /b %ERRORLEVEL%
