@echo off
REM One-command deploy: push to GitHub + update live server
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy.ps1" -Push %*
