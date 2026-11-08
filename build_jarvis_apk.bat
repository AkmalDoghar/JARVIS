@echo off
title JARVIS Mobile - Build Standalone APK
cd /d "%~dp0mobile"
echo ========================================================
echo    JARVIS MOBILE - STANDALONE APK BUILDER
echo ========================================================
echo.
echo Building standalone APK for your Android phone...
echo (This creates an installable .apk file that works without PC or Wi-Fi)
echo.
npx eas-cli build -p android --profile preview
pause

