@echo off
REM ============================================
REM Kompres File - Launcher
REM Menjalankan compressor.py dengan file yang dipilih
REM ============================================

set "SCRIPT_DIR=%~dp0"
pythonw "%SCRIPT_DIR%compressor.py" "%~1"
