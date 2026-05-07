@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\prepare_current_from_releases.ps1"
if exist "%~dp0current\SISTEMA AUDITORIA BRASUL.exe" (
  start "" "%~dp0current\SISTEMA AUDITORIA BRASUL.exe"
  goto :eof
)
if exist "%~dp0dist\\SISTEMA AUDITORIA BRASUL\SISTEMA AUDITORIA BRASUL.exe" (
  start "" "%~dp0dist\\SISTEMA AUDITORIA BRASUL\SISTEMA AUDITORIA BRASUL.exe"
  goto :eof
)
python main.py
pause
