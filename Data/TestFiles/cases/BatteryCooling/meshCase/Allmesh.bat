@echo off

REM Source runtime environment
set FOAMDIR="/opt/openfoam13"
set CWD=%CD%
call %FOAMDIR%/setEnvVariables-vNone.bat
cd /d %CWD%

REM Run PowerShell script
type Allmesh.ps1 | PowerShell -NoProfile -
