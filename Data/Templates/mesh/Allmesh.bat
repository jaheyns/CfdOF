@echo off

REM Source runtime environment
set FOAMDIR="%(TranslatedFoamPath%)"
set CWD=%CD%
call %FOAMDIR%/setEnvVariables-v%(FoamVersion%).bat
cd /d %CWD%

REM Run PowerShell script
PowerShell -NoProfile -ExecutionPolicy Bypass -File Allmesh.ps1
