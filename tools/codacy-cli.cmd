@echo off
REM Codacy CLI wrapper for Windows (executes in WSL)
wsl -d Ubuntu -- bash -lc "cd /mnt/c/dev/python-email && codacy-cli %*"
