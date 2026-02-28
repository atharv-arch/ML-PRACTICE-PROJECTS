# ──────────────────────────────────────────────────────────────────────
# build_mobile.ps1 — Build script for the RoutineAI mobile app
#
# This script automates the Capacitor mobile build process:
#   1. Copies the latest web assets (CSS, JS) into the www/ directory
#   2. Syncs the www/ assets into the Android native project
#   3. Builds a debug APK using the Android Gradle wrapper
#
# Prerequisites:
#   - Node.js and npm installed
#   - Android SDK installed (or Android Studio)
#   - Capacitor dependencies installed (npm install in frontend/)
#
# Usage:
#   cd ai_productive/frontend
#   .\build_mobile.ps1
#
# Output:
#   The debug APK will be at:
#   android/app/build/outputs/apk/debug/app-debug.apk
# ──────────────────────────────────────────────────────────────────────

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RoutineAI Mobile Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Step 1: Copy latest web assets into the www/ build directory
# This ensures the mobile app has the most recent frontend code
Write-Host "`n[1/4] Copying web assets to www/..." -ForegroundColor Yellow
Copy-Item -Recurse -Force "css" "www/css"
Copy-Item -Recurse -Force "js" "www/js"
Write-Host "  Done - CSS and JS copied." -ForegroundColor Green

# Step 2: Sync web assets into the Android native project
# This copies www/ contents into android/app/src/main/assets/public/
Write-Host "`n[2/4] Syncing to Android project..." -ForegroundColor Yellow
npx cap sync android
Write-Host "  Done - Android project synced." -ForegroundColor Green

# Step 3: Build the debug APK using Gradle
# This compiles the Android project into an installable APK file
Write-Host "`n[3/4] Building debug APK..." -ForegroundColor Yellow
Set-Location android

# Use the Gradle wrapper (gradlew) to build the debug variant
if (Test-Path "gradlew.bat") {
    # Run the Gradle assembleDebug task
    .\gradlew.bat assembleDebug
} else {
    Write-Host "  ERROR: gradlew.bat not found!" -ForegroundColor Red
    Write-Host "  Please open the android/ folder in Android Studio first." -ForegroundColor Red
    Set-Location ..
    exit 1
}

Set-Location ..

# Step 4: Report the output location
$apkPath = "android/app/build/outputs/apk/debug/app-debug.apk"
Write-Host "`n[4/4] Build complete!" -ForegroundColor Green

if (Test-Path $apkPath) {
    # Show the APK file size and location
    $apkSize = [math]::Round((Get-Item $apkPath).Length / 1MB, 2)
    Write-Host "  APK: $apkPath ($apkSize MB)" -ForegroundColor Cyan
    Write-Host "`n  To install on device:" -ForegroundColor Yellow
    Write-Host "    adb install $apkPath" -ForegroundColor White
} else {
    Write-Host "  APK not found at expected path." -ForegroundColor Red
    Write-Host "  Try opening android/ in Android Studio and building from there." -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
