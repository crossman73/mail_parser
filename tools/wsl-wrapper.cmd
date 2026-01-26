@echo off
rem Wrapper to invoke the real wsl.exe in either Sysnative (for 32-bit processes)
rem or System32 (normal 64-bit path). This avoids execvpe(wsl) not found errors
rem when VS Code is running in a 32-bit process context.
setlocal
if exist "%windir%\Sysnative\wsl.exe" (
  "%windir%\Sysnative\wsl.exe" %*
) else (
  "%windir%\System32\wsl.exe" %*
)
endlocal
