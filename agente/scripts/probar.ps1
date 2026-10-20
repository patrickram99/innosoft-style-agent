# Pruebas manuales de la API, una funcionalidad por subcomando (PowerShell 5.1+).
#
#   .\scripts\probar.ps1 api                                  -> levanta la API (SQLite) en una ventana aparte
#   .\scripts\probar.ps1 reglas                               -> GET /rules?section=original            (US-09)
#   .\scripts\probar.ps1 subir -Pdf muestras\pdf\Ejm1-388.pdf -> POST /manuscripts + espera + hallazgos  (US-01, US-04, US-06, US-10)
#   .\scripts\probar.ps1 docx  -Archivo muestras\Ejm1-388.docx -> debe responder 400 not_pdf            (US-01 AC-02)
#   .\scripts\probar.ps1 hallazgos -Id <manuscript_id>        -> GET /manuscripts/{id}/findings         (US-10)
#   .\scripts\probar.ps1 salud                                -> GET /health                             (US-00)
param(
    [Parameter(Position = 0)][ValidateSet("api", "salud", "reglas", "subir", "docx", "hallazgos")][string]$Que = "salud",
    [string]$Pdf = "tests\fixtures\pdfs\figuras_baja_dpi.pdf",
    [string]$Archivo = "",
    [string]$Id = "",
    [int]$Port = 8000,
    [int]$SubmissionId = (Get-Random -Minimum 1000 -Maximum 99999),
    [string]$Token = "demo-token"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root
$base = "http://127.0.0.1:$Port"
$headers = @{ Authorization = "Bearer $Token" }

function Get-Json([string]$Url) {
    try { $r = Invoke-WebRequest -Uri $Url -Headers $headers -UseBasicParsing }
    catch { $r = $_.Exception.Response; if (-not $r) { throw } }
    $ms = New-Object IO.MemoryStream
    if ($r -is [Microsoft.PowerShell.Commands.WebResponseObject]) { $r.RawContentStream.CopyTo($ms); $code = $r.StatusCode }
    else { $r.GetResponseStream().CopyTo($ms); $code = [int]$r.StatusCode }
    $body = [Text.Encoding]::UTF8.GetString($ms.ToArray())
    Write-Host "HTTP $code  $Url" -ForegroundColor DarkGray
    return ($body | ConvertFrom-Json)
}

function Post-Manuscrito([string]$Ruta, [string]$Mime) {
    $Ruta = (Resolve-Path $Ruta).Path
    $meta = @{ submission_id = $SubmissionId; section_id = 2; title = [IO.Path]::GetFileNameWithoutExtension($Ruta); locale = "es_ES" } | ConvertTo-Json -Compress
    $tmp = New-TemporaryFile
    [IO.File]::WriteAllText($tmp.FullName, $meta, (New-Object Text.UTF8Encoding $false))
    $out = & curl.exe -s -S -w "`n%{http_code}" -X POST "$base/manuscripts" -H "Authorization: Bearer $Token" -F "file=@$Ruta;type=$Mime" -F "metadata=<$tmp"
    Remove-Item $tmp -Force
    $lines = @($out -split "`n")
    $code = $lines[-1].Trim()
    $body = ($lines[0..($lines.Count - 2)] -join "")
    Write-Host "HTTP $code  POST $base/manuscripts  ($([IO.Path]::GetFileName($Ruta)), submission_id=$SubmissionId)" -ForegroundColor DarkGray
    Write-Host $body
    return @{ code = [int]$code; body = ($body | ConvertFrom-Json) }
}

function Mostrar-Hallazgos($f) {
    Write-Host ("Estado: {0} {1}" -f $f.status, $(if ($f.status_reason) { "($($f.status_reason))" } else { "" })) -ForegroundColor Green
    Write-Host ("Hallazgos: {0}   rule_error: {1}   rules_hash: {2}" -f $f.total, $f.rule_errors.Count, $f.rules_hash)
    if ($f.total -gt 0) {
        $f.findings | ForEach-Object {
            [pscustomobject]@{ Regla = $_.rule_id; Sev = $_.severidad; Pag = $_.pagina; Figura = $_.ubicacion.etiqueta
                               Encontrado = $_.valor_encontrado; Esperado = $_.valor_esperado; Evidencia = $_.evidencia.ruta }
        } | Format-Table -AutoSize | Out-String -Width 220 | Write-Host
    }
}

switch ($Que) {
    "api" {
        $env:DATABASE_URL = "sqlite:///./demo.sqlite"
        $env:AGENT_SERVICE_TOKEN = $Token
        $env:STORAGE_DIR = (Join-Path $root "storage")
        & { $ErrorActionPreference = "Continue"; alembic upgrade head 2>&1 | Out-Null }
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:DATABASE_URL='sqlite:///./demo.sqlite'; `$env:AGENT_SERVICE_TOKEN='$Token'; `$env:STORAGE_DIR='$env:STORAGE_DIR'; Set-Location '$root'; python -m uvicorn app.main:app --host 127.0.0.1 --port $Port --reload"
        Write-Host "API arrancando en $base (OpenAPI en $base/docs). Token: $Token"
    }
    "salud"     { Get-Json "$base/health" | ConvertTo-Json }
    "reglas"    {
        $r = Get-Json "$base/rules?section=original"
        Write-Host ("rules_hash: {0}   total: {1}   not_implemented: {2}" -f $r.rules_hash, $r.total, ($r.not_implemented -join ", "))
        $r.reglas | ForEach-Object { [pscustomobject]@{ Id = $_.id; Sev = $_.severidad; Det = $_.detectable; Estado = $_.estado; Evaluador = $_.condicion.evaluador; Parametros = ($_.condicion.parametros | ConvertTo-Json -Compress) } } | Format-Table -AutoSize | Out-String -Width 220 | Write-Host
    }
    "subir" {
        $r = Post-Manuscrito $Pdf "application/pdf"
        if ($r.code -notin 200, 202) { exit 1 }
        $mid = $r.body.manuscript_id
        $final = @("validated", "unreadable", "out_of_scope", "failed", "ready_for_review")
        for ($i = 0; $i -lt 240; $i++) {
            $f = Get-Json "$base/manuscripts/$mid/findings"
            if ($final -contains $f.status) { break }
            Start-Sleep -Milliseconds 500
        }
        Mostrar-Hallazgos $f
        Write-Host "Repetir: .\scripts\probar.ps1 hallazgos -Id $mid"
    }
    "docx" {
        if (-not $Archivo) { $Archivo = (Get-ChildItem muestras\*.docx | Select-Object -First 1).FullName }
        $r = Post-Manuscrito $Archivo "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if ($r.code -eq 400 -and $r.body.detail.error -eq "not_pdf") { Write-Host "OK: rechazado con 400 not_pdf (US-01 AC-02)" -ForegroundColor Green }
        else { Write-Host "FALLO: se esperaba 400 not_pdf" -ForegroundColor Red; exit 1 }
    }
    "hallazgos" {
        if (-not $Id) { throw "Falta -Id <manuscript_id>" }
        Mostrar-Hallazgos (Get-Json "$base/manuscripts/$Id/findings")
    }
}
