@echo off

REM Source runtime environment
set FOAMDIR="%(TranslatedFoamPath%)"
set CWD=%CD%
call %FOAMDIR%/setEnvVariables-v%(FoamVersion%).bat
cd %CWD%

REM Run PowerShell script
type Allmesh.ps1 | PowerShell -NoProfile -
