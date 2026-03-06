@echo off
REM ============================================
REM Install Context Menu - Kompres Video & Foto
REM Jalankan sebagai Administrator!
REM ============================================

echo.
echo ==========================================
echo   Install Kompres File - Context Menu
echo ==========================================
echo.

REM Cek apakah dijalankan sebagai Administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Script ini harus dijalankan sebagai Administrator!
    echo Klik kanan file ini dan pilih "Run as administrator"
    echo.
    pause
    exit /b 1
)

REM Dapatkan path direktori script ini
set "SCRIPT_DIR=%~dp0"
set "VBS_PATH=%SCRIPT_DIR%compress.vbs"

echo Script directory: %SCRIPT_DIR%
echo Launcher path:    %VBS_PATH%
echo.

REM ============================================
REM CONTEXT MENU UNTUK VIDEO
REM ============================================
echo [1/2] Menambahkan Context Menu untuk VIDEO...

REM .mp4
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.mp4\shell\KompresVideo" /ve /d "Kompres Video" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.mp4\shell\KompresVideo" /v "Icon" /d "%SCRIPT_DIR%kompres.ico" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.mp4\shell\KompresVideo\command" /ve /d "wscript.exe \"%VBS_PATH%\" \"%%1\"" /f >nul 2>&1

REM .avi
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.avi\shell\KompresVideo" /ve /d "Kompres Video" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.avi\shell\KompresVideo" /v "Icon" /d "%SCRIPT_DIR%kompres.ico" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.avi\shell\KompresVideo\command" /ve /d "wscript.exe \"%VBS_PATH%\" \"%%1\"" /f >nul 2>&1

REM .mkv
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.mkv\shell\KompresVideo" /ve /d "Kompres Video" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.mkv\shell\KompresVideo" /v "Icon" /d "%SCRIPT_DIR%kompres.ico" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.mkv\shell\KompresVideo\command" /ve /d "wscript.exe \"%VBS_PATH%\" \"%%1\"" /f >nul 2>&1

REM .mov
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.mov\shell\KompresVideo" /ve /d "Kompres Video" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.mov\shell\KompresVideo" /v "Icon" /d "%SCRIPT_DIR%kompres.ico" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.mov\shell\KompresVideo\command" /ve /d "wscript.exe \"%VBS_PATH%\" \"%%1\"" /f >nul 2>&1

REM .wmv
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.wmv\shell\KompresVideo" /ve /d "Kompres Video" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.wmv\shell\KompresVideo" /v "Icon" /d "%SCRIPT_DIR%kompres.ico" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.wmv\shell\KompresVideo\command" /ve /d "wscript.exe \"%VBS_PATH%\" \"%%1\"" /f >nul 2>&1

REM .flv
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.flv\shell\KompresVideo" /ve /d "Kompres Video" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.flv\shell\KompresVideo" /v "Icon" /d "%SCRIPT_DIR%kompres.ico" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.flv\shell\KompresVideo\command" /ve /d "wscript.exe \"%VBS_PATH%\" \"%%1\"" /f >nul 2>&1

REM .webm
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.webm\shell\KompresVideo" /ve /d "Kompres Video" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.webm\shell\KompresVideo" /v "Icon" /d "%SCRIPT_DIR%kompres.ico" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.webm\shell\KompresVideo\command" /ve /d "wscript.exe \"%VBS_PATH%\" \"%%1\"" /f >nul 2>&1

REM .m4v
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.m4v\shell\KompresVideo" /ve /d "Kompres Video" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.m4v\shell\KompresVideo" /v "Icon" /d "%SCRIPT_DIR%kompres.ico" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.m4v\shell\KompresVideo\command" /ve /d "wscript.exe \"%VBS_PATH%\" \"%%1\"" /f >nul 2>&1

REM .3gp
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.3gp\shell\KompresVideo" /ve /d "Kompres Video" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.3gp\shell\KompresVideo" /v "Icon" /d "%SCRIPT_DIR%kompres.ico" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.3gp\shell\KompresVideo\command" /ve /d "wscript.exe \"%VBS_PATH%\" \"%%1\"" /f >nul 2>&1

echo    [OK] Context menu video berhasil ditambahkan!
echo.

REM ============================================
REM CONTEXT MENU UNTUK FOTO
REM ============================================
echo [2/2] Menambahkan Context Menu untuk FOTO...

REM .jpg
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.jpg\shell\KompresFoto" /ve /d "Kompres Foto" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.jpg\shell\KompresFoto" /v "Icon" /d "%SCRIPT_DIR%kompres.ico" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.jpg\shell\KompresFoto\command" /ve /d "wscript.exe \"%VBS_PATH%\" \"%%1\"" /f >nul 2>&1

REM .jpeg
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.jpeg\shell\KompresFoto" /ve /d "Kompres Foto" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.jpeg\shell\KompresFoto" /v "Icon" /d "%SCRIPT_DIR%kompres.ico" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.jpeg\shell\KompresFoto\command" /ve /d "wscript.exe \"%VBS_PATH%\" \"%%1\"" /f >nul 2>&1

REM .png
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.png\shell\KompresFoto" /ve /d "Kompres Foto" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.png\shell\KompresFoto" /v "Icon" /d "%SCRIPT_DIR%kompres.ico" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.png\shell\KompresFoto\command" /ve /d "wscript.exe \"%VBS_PATH%\" \"%%1\"" /f >nul 2>&1

REM .bmp
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.bmp\shell\KompresFoto" /ve /d "Kompres Foto" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.bmp\shell\KompresFoto" /v "Icon" /d "%SCRIPT_DIR%kompres.ico" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.bmp\shell\KompresFoto\command" /ve /d "wscript.exe \"%VBS_PATH%\" \"%%1\"" /f >nul 2>&1

REM .tiff
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.tiff\shell\KompresFoto" /ve /d "Kompres Foto" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.tiff\shell\KompresFoto" /v "Icon" /d "%SCRIPT_DIR%kompres.ico" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.tiff\shell\KompresFoto\command" /ve /d "wscript.exe \"%VBS_PATH%\" \"%%1\"" /f >nul 2>&1

REM .tif
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.tif\shell\KompresFoto" /ve /d "Kompres Foto" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.tif\shell\KompresFoto" /v "Icon" /d "%SCRIPT_DIR%kompres.ico" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.tif\shell\KompresFoto\command" /ve /d "wscript.exe \"%VBS_PATH%\" \"%%1\"" /f >nul 2>&1

REM .webp
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.webp\shell\KompresFoto" /ve /d "Kompres Foto" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.webp\shell\KompresFoto" /v "Icon" /d "%SCRIPT_DIR%kompres.ico" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.webp\shell\KompresFoto\command" /ve /d "wscript.exe \"%VBS_PATH%\" \"%%1\"" /f >nul 2>&1

REM .gif
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.gif\shell\KompresFoto" /ve /d "Kompres Foto" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.gif\shell\KompresFoto" /v "Icon" /d "%SCRIPT_DIR%kompres.ico" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.gif\shell\KompresFoto\command" /ve /d "wscript.exe \"%VBS_PATH%\" \"%%1\"" /f >nul 2>&1

echo    [OK] Context menu foto berhasil ditambahkan!
echo.

echo ==========================================
echo   INSTALASI BERHASIL!
echo ==========================================
echo.
echo Context menu telah ditambahkan:
echo   - Klik kanan file VIDEO  = "Kompres Video"
echo   - Klik kanan file FOTO   = "Kompres Foto"
echo.
echo Catatan: Jika context menu tidak muncul,
echo restart Windows Explorer atau restart PC.
echo.
pause
