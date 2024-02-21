@echo off

REM Source runtime environment
set FOAMDIR="%(system/TranslatedFoamPath%)"
set CWD=%CD%
call %FOAMDIR%/setEnvVariables-v%(system/FoamVersion%).bat
cd %CWD%

REM Run PowerShell script
PowerShell -File Allrun.ps1
