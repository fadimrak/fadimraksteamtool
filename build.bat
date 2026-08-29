@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================================================
echo   Fadimrak Steam Tool - Build Script
echo ================================================================
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo [0/4] Python kontrol ediliyor...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo HATA: Python sistemde bulunamadi veya PATH'e eklenmemis!
    pause & exit /b 1
)

echo [1/4] PyInstaller kontrol ediliyor...
python -m PyInstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller bulunamadi, yukleniyor...
    python -m pip install pyinstaller --quiet
    if %errorlevel% neq 0 (
        echo HATA: PyInstaller yuklenemedi.
        pause & exit /b 1
    )
)
echo      PyInstaller hazir.
echo.

echo [2/4] Eski build temizleniyor...
if exist "dist\FadimrakSteamTool.exe" del /f /q "dist\FadimrakSteamTool.exe"
if exist "build" rmdir /s /q "build"
echo      Temizleme tamam.
echo.

echo [3/4] EXE build ediliyor...
python -m PyInstaller fadimrak.spec --noconfirm --clean
if %errorlevel% neq 0 (
    echo.
    echo HATA: PyInstaller build basarisiz oldu!
    echo Yukaridaki hata mesajini kontrol edin.
    pause & exit /b 1
)
echo.
echo      EXE basariyla olusturuldu: dist\FadimrakSteamTool.exe
echo.

echo [4/4] Kurulum paketi olusturuluyor...

set "ISCC="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 5\ISCC.exe"

if not defined ISCC (
    echo.
    echo UYARI: Inno Setup bulunamadi.
    echo Lutfen Inno Setup 6'yi indirip yukleyin:
    echo https://jrsoftware.org/isdl.php
    echo.
    echo EXE dosyasi hazir: dist\FadimrakSteamTool.exe
    echo Inno Setup yukledikten sonra su komutu calistirin:
    echo   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
    pause & exit /b 0
)

if not exist "output" mkdir "output"

"%ISCC%" installer.iss
if %errorlevel% neq 0 (
    echo.
    echo HATA: Inno Setup build basarisiz oldu!
    pause & exit /b 1
)

echo.
echo ================================================================
echo   BUILD TAMAMLANDI!
echo.
echo   EXE     : dist\FadimrakSteamTool.exe
echo   Setup   : output\FadimrakSteamTool_Setup_v5.2.exe
echo ================================================================
echo.
pause