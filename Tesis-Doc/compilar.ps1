# Compila la tesis en Windows con MiKTeX (pdfLaTeX + latexmk) dejando todo en build\.
#   .\compilar.ps1          -> build\main.pdf
#   .\compilar.ps1 -Abrir   -> y lo abre al terminar
#   .\compilar.ps1 -Limpiar -> borra build\ y recompila desde cero
# Requisitos (una sola vez): doble clic en instalar-miktex.cmd (instala MiKTeX con winget y compila).
#                            latexmk es opcional (necesita Perl); sin él se hacen tres pasadas de pdflatex.
# Esta es la forma oficial de generar el PDF de la tesis (build\main.pdf).
param([switch]$Abrir, [switch]$Limpiar)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# MiKTeX instalado por usuario no siempre está en el PATH de la sesión actual
$miktex = Join-Path $env:LOCALAPPDATA "Programs\MiKTeX\miktex\bin\x64"
if (Test-Path $miktex) { $env:PATH = "$miktex;$env:PATH" }
if (-not (Get-Command pdflatex -ErrorAction SilentlyContinue)) {
    Write-Host "No se encontró pdflatex. Ejecuta instalar-miktex.cmd (o: winget install MiKTeX.MiKTeX)" -ForegroundColor Red
    exit 1
}
if ($Limpiar -and (Test-Path "build")) { Remove-Item "build" -Recurse -Force }
New-Item -ItemType Directory -Force -Path "build" | Out-Null

if (Get-Command latexmk -ErrorAction SilentlyContinue) {
    latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
    $ok = ($LASTEXITCODE -eq 0)
} else {
    # Sin latexmk (necesita Perl): tres pasadas de pdflatex bastan para índices y referencias cruzadas
    $ok = $true
    foreach ($i in 1..3) {
        pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
        if ($LASTEXITCODE -ne 0) { $ok = $false; break }
    }
}
if (-not $ok) {
    Write-Host "Error de compilación. Busca las líneas que empiezan con '!' en build\main.log" -ForegroundColor Red
    exit 1
}
Write-Host "OK -> build\main.pdf" -ForegroundColor Green
if ($Abrir) { Invoke-Item "build\main.pdf" }
