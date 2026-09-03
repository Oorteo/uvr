@echo off
setlocal
set "ROOT=%~dp0..\.."
uv run --project "%ROOT%" python "%~dp0windows_smoke_test.py" %*
exit /b %ERRORLEVEL%