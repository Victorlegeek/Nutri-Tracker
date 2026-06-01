@echo off
setlocal enabledelayedexpansion
title NutriTracker - Installation
color 0A

echo.
echo  =====================================================
echo   NutriTracker -- Installation des dependances
echo  =====================================================
echo.

:: Verification Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERREUR] Python n'est pas installe ou non trouve dans le PATH.
    echo.
    echo  Telechargez Python 3.10 ou superieur sur :
    echo  https://www.python.org/downloads/
    echo.
    echo  Cochez bien "Add Python to PATH" lors de l'installation.
    echo.
    pause
    exit /b 1
)

:: Verification version Python >= 3.10
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set PYMAJ=%%a
    set PYMIN=%%b
)

echo  Python detecte : %PYVER%

if %PYMAJ% LSS 3 (
    echo.
    echo  [ERREUR] Python 3.10 minimum requis. Version detectee : %PYVER%
    echo  Telechargez la derniere version sur https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
if %PYMAJ% EQU 3 (
    if %PYMIN% LSS 10 (
        echo.
        echo  [ERREUR] Python 3.10 minimum requis. Version detectee : %PYVER%
        echo  Telechargez la derniere version sur https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    )
)

echo  [OK] Version Python compatible.
echo.

:: Mise a jour pip
echo  Mise a jour de pip...
python -m pip install --upgrade pip --quiet
echo  [OK] pip mis a jour.
echo.

:: Installation des dependances principales
echo  Installation de ttkbootstrap...
pip install ttkbootstrap --quiet
if %errorlevel% neq 0 (
    echo  [AVERT] ttkbootstrap non installe. L'app fonctionnera avec le theme par defaut.
) else (
    echo  [OK] ttkbootstrap installe.
)
echo.

:: Dependances optionnelles
echo  Installation des modules optionnels...
echo.

echo   - requests (recherche web)...
pip install requests --quiet
if %errorlevel% equ 0 (echo   [OK] requests) else (echo   [AVERT] requests ignoré)

echo   - beautifulsoup4 (scraping nutritionnel)...
pip install beautifulsoup4 --quiet
if %errorlevel% equ 0 (echo   [OK] beautifulsoup4) else (echo   [AVERT] beautifulsoup4 ignoré)

echo   - Pillow (traitement images)...
pip install Pillow --quiet
if %errorlevel% equ 0 (echo   [OK] Pillow) else (echo   [AVERT] Pillow ignoré)

echo   - opencv-python (OCR images)...
pip install opencv-python --quiet
if %errorlevel% equ 0 (echo   [OK] opencv-python) else (echo   [AVERT] opencv-python ignoré)

echo.
echo  =====================================================
echo   Installation terminee !
echo  =====================================================
echo.
echo  Vous pouvez maintenant lancer NutriTracker avec :
echo    lancer_nutri.bat
echo  ou
echo    python main.py
echo.
pause
