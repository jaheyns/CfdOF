@echo off

REM Source runtime environment
set FOAMDIR="/opt/openfoam12"
set CWD=%CD%
call %FOAMDIR%/setEnvVariables-vNone.bat
cd /d %CWD%

REM Run PowerShell script
type Allrun.ps1 | PowerShell -NoProfile -
