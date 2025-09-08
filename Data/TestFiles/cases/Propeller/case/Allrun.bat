@echo off

REM Source runtime environment
set FOAMDIR="C:\Program Files\ESI-OpenCFD\OpenFOAM\v2212"
set CWD=%CD%
call %FOAMDIR%/setEnvVariables-v2212.bat
cd /d %CWD%

REM Run PowerShell script
type Allrun.ps1 | PowerShell -NoProfile -
