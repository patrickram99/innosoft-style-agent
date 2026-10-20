@echo off
REM Instala MiKTeX (usuario actual, sin admin) con winget y compila la tesis a build\main.pdf.
REM Doble clic sobre este archivo. Al terminar deja la ventana abierta para ver el resultado.
setlocal
cd /d "%~dp0"

echo === 1/3 Instalando MiKTeX con winget (puede tardar varios minutos) ===
winget install --id MiKTeX.MiKTeX -e --scope user --accept-package-agreements --accept-source-agreements
if errorlevel 1 echo (winget devolvio un codigo distinto de 0; si MiKTeX ya estaba instalado, es normal)

set "MIKTEX=%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64"
if not exist "%MIKTEX%\pdflatex.exe" set "MIKTEX=%ProgramFiles%\MiKTeX\miktex\bin\x64"
if not exist "%MIKTEX%\pdflatex.exe" (
  echo No se encontro pdflatex.exe. Abre "MiKTeX Console" desde el menu Inicio y vuelve a ejecutar este archivo.
  pause
  exit /b 1
)
set "PATH=%MIKTEX%;%PATH%"

echo === 2/3 Permitir que MiKTeX instale paquetes al vuelo ===
initexmf --set-config-value [MPM]AutoInstall=1
miktex packages update-package-database >nul 2>&1

echo === 3/3 Compilando (3 pasadas de pdflatex) ===
if not exist build mkdir build
for /L %%i in (1,1,3) do (
  pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
  if errorlevel 1 (
    echo ERROR en la pasada %%i. Revisa build\main.log ^(lineas que empiezan con "!"^).
    pause
    exit /b 1
  )
)
echo.
echo OK: build\main.pdf
start "" "build\main.pdf"
pause
