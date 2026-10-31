@echo off
title MalamSMP_StoryVN Auto Deployer
echo ========================================================
echo       MalamSMP_StoryVN Automatic Resource Pack Deployer
echo ========================================================
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0deploy_malamsmp_pack.ps1"
echo.
echo Selesai! Resource pack telah berhasil dipasang ke ATLauncher.
pause

