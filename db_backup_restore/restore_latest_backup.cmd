@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Find latest *.tar.gz (exclude .sha256)
for /f "tokens=4" %%F in ('
  aws s3 ls s3://polydial/mysql-backups/ --recursive ^
  ^| findstr /R /I "\.tar\.gz$" ^
  ^| sort
') do set "LATEST_KEY=%%F"

if not defined LATEST_KEY (
  echo No *.tar.gz found under s3://polydial/mysql-backups/
  exit /b 1
)

REM Extract filename only
for %%X in (%LATEST_KEY%) do set "LATEST_FILE=%%~nxX"

echo Latest key  = %LATEST_KEY%
echo Latest file = %LATEST_FILE%

REM Ensure ../database_backup exists
set "TARGET_DIR=..\database_backup"
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

REM Ensure ../database_backup exists
if not exist "..\database_backup" mkdir "..\database_backup"

REM IMPORTANT: use s3://polydial/%LATEST_KEY% (no double mysql-backups/)
aws s3 cp "s3://polydial/%LATEST_KEY%" "..\database_backup\%LATEST_FILE%"
if errorlevel 1 (
  echo Failed to copy file from S3
  exit /b 1
)

REM ===== Also copy matching .sha256 file =====
aws s3 cp "s3://polydial/%LATEST_KEY%.sha256" "%TARGET_DIR%\%LATEST_FILE%.sha256" 1>nul 2>nul
if exist "%TARGET_DIR%\%LATEST_FILE%.sha256" (
  echo Downloaded checksum file: %LATEST_FILE%.sha256
) else (
  echo No checksum file found for %LATEST_FILE%
)
REM Extract the .tar.gz into the target dir
echo Extracting %LATEST_FILE% into %TARGET_DIR%
tar -xvzf "%TARGET_DIR%\%LATEST_FILE%" -C "%TARGET_DIR%"

REM ===== Delete archive after successful extraction =====
del "%TARGET_DIR%\%LATEST_FILE%"
echo Deleted archive %LATEST_FILE%

echo Done.