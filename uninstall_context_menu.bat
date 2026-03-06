@echo off
REM ============================================
REM Uninstall Context Menu - Kompres Video & Foto
REM Jalankan sebagai Administrator!
REM ============================================

echo.
echo ==========================================
echo   Uninstall Kompres File - Context Menu
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

echo Menghapus context menu...
echo.

REM Hapus context menu VIDEO
echo [1/2] Menghapus context menu VIDEO...
for %%e in (mp4 avi mkv mov wmv flv webm m4v 3gp) do (
    reg delete "HKEY_CLASSES_ROOT\SystemFileAssociations\.%%e\shell\KompresVideo" /f >nul 2>&1
)
echo    [OK] Context menu video berhasil dihapus!
echo.

REM Hapus context menu FOTO
echo [2/2] Menghapus context menu FOTO...
for %%e in (jpg jpeg png bmp tiff tif webp gif) do (
    reg delete "HKEY_CLASSES_ROOT\SystemFileAssociations\.%%e\shell\KompresFoto" /f >nul 2>&1
)
echo    [OK] Context menu foto berhasil dihapus!
echo.

echo ==========================================
echo   UNINSTALL BERHASIL!
echo ==========================================
echo.
echo Context menu telah dihapus.
echo Restart Windows Explorer jika perlu.
echo.
pause
