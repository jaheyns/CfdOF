@echo off

REM Source runtime environment
set FOAMDIR="%(system/TranslatedFoamPath%)"
set CWD=%CD%
call %FOAMDIR%/setEnvVariables-v%(system/FoamVersion%).bat
cd /d %CWD%

REM Run PowerShell script
PowerShell -NoProfile -ExecutionPolicy Bypass -File Allrun.ps1
