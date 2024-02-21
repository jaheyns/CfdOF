@echo off

REM Source runtime environment
set FOAMDIR="%(TranslatedFoamPath%)"
set CWD=%CD%
call %FOAMDIR%/setEnvVariables-v%(FoamVersion%).bat
cd %CWD%

REM Run PowerShell script
PowerShell -File Allmesh.ps1
