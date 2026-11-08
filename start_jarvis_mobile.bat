@echo off
title JARVIS Mobile Edition - Companion Server
cd /d "%~dp0mobile"
echo ========================================================
echo    JARVIS MOBILE COMPANION - BIKE & TRAVEL EDITION
echo ========================================================
echo.
echo Starting Expo Metro Bundler for JARVIS Mobile...
echo Scan the QR code using Expo Go app on your Android phone.
echo.
npx expo start
pause
