@echo off
cd /d %~dp0

set yr=%date:~0,4%
set mt=%date:~5,2%
set dy=%date:~8,2%
set hr=%time:~0,2%
set mn=%time:~3,2%
set se=%time:~6,2%
 
set logname=%yr%-%mt%-%dy%_%hr%-%mn%-%se%

python main.py
pause