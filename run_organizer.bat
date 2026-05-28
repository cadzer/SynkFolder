@echo off
setlocal

powershell -ExecutionPolicy Bypass -File "%~dp0run_organizer.ps1" -Watch

endlocal
