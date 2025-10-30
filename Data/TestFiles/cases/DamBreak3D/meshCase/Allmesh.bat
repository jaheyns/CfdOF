@echo off

REM Source runtime environment

set FOAMDIR="/opt/openfoam13"
set CWD=%CD%

if None GEQ 1000 goto OPENCFD

:FOUNDATION
set OLDPATH=%PATH%
call %FOAMDIR%\setvars_OFNone.bat
set PATH=%PATH%;%OLDPATH%

REM Fix for error in FOAM_MPI in setvars-OF.bat
FOR /F "tokens=* USEBACKQ" %%F IN (`dir /b %%FOAM_LIBBIN%%\MS-MPI*`) DO (
SET FOAM_MPI=%%F
)
set PATH=%FOAM_LIBBIN%\%FOAM_MPI%;%PATH%
goto CONTINUE

:OPENCFD
call %FOAMDIR%\setEnvVariables-vNone.bat

:CONTINUE

cd /d %CWD%

REM Run PowerShell script
PowerShell -NoProfile -ExecutionPolicy Bypass -File Allmesh.ps1
