@echo off

REM Source runtime environment
set FOAMDIR="/home/oliver/OpenFOAM/OpenFOAM-plus"
set CWD=%CD%
call %FOAMDIR%/setEnvVariables-vNone.bat
cd %CWD%

REM Run PowerShell script
PowerShell -File Allmesh.ps1
