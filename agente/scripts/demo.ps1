# Demo del walking skeleton (Sprint Review): levanta la API, sube un PDF e imprime los hallazgos.
#
#   .\scripts\demo.ps1                                   -> usa tests/fixtures/pdfs/figuras_baja_dpi.pdf
#   .\scripts\demo.ps1 -Pdf muestras\pdf\Ejm1-388.pdf    -> cualquier PDF
#   .\scripts\demo.ps1 -Pdf x.pdf -Port 8010 -NoStart    -> contra una API ya levantada
#
# Requisitos: dependencias instaladas (.\scripts\dev.ps1 -SinTests). Sin Docker: usa SQLite local.
param(
    [string]$Pdf = "tests\fixtures\pdfs\figuras_baja_dpi.pdf",
    [int]$Port = 8000,
    [int]$SubmissionId = 1,
    [string]$Token = "demo-token",
    [switch]$NoStart
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$root = Resolve-Path (Join-Path $PSScriptRoot "..")

function Get-Json([string]$Url, [hashtable]$Headers = @{}) {
    # Invoke-RestMethod en PowerShell 5.1 decodifica como Latin-1 si la respuesta no declara charset.
    $r = Invoke-WebRequest -Uri $Url -Headers $Headers -UseBasicParsing
    $ms = New-Object IO.MemoryStream
    $r.RawContentStream.CopyTo($ms)
    [Text.Encoding]::UTF8.GetString($ms.ToArray()) | ConvertFrom-Json
}
Set-Location $root
$Pdf = (Resolve-Path $Pdf).Path
$base = "http://127.0.0.1:$Port"
$proc = $null

try {
    if (-not $NoStart) {
        $env:DATABASE_URL = "sqlite:///./demo.sqlite"
        $env:AGENT_SERVICE_TOKEN = $Token
        $env:STORAGE_DIR = (Join-Path $root "storage")
        if (Test-Path "demo.sqlite") { Remove-Item "demo.sqlite" -Force }
        Write-Host "Aplicando migraciones (demo.sqlite)..." -ForegroundColor Cyan
        # Alembic escribe sus INFO por stderr; con ErrorActionPreference=Stop eso rompería el script.
        & { $ErrorActionPreference = "Continue"; alembic upgrade head 2>&1 | Out-Null }
        if ($LASTEXITCODE -ne 0) { throw "alembic upgrade head falló (código $LASTEXITCODE)" }
        Write-Host "Levantando la API en $base ..." -ForegroundColor Cyan
        $proc = Start-Process -FilePath "python" -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port $Port --log-level warning" -PassThru -NoNewWindow
        $ready = $false
        for ($i = 0; $i -lt 40; $i++) {
            Start-Sleep -Milliseconds 500
            try { if ((Invoke-RestMethod "$base/health").status -eq "ok") { $ready = $true; break } } catch {}
        }
        if (-not $ready) { throw "La API no respondió en $base" }
    }

    $headers = @{ Authorization = "Bearer $Token" }
    $rules = Get-Json "$base/rules?section=original" $headers
    Write-Host ("Reglas cargadas: {0} (hash {1}...)  not_implemented: {2}" -f $rules.total, $rules.rules_hash.Substring(0, 12), ($rules.not_implemented -join ", "))

    Write-Host "Enviando $Pdf ..." -ForegroundColor Cyan
    $meta = @{ submission_id = $SubmissionId; section_id = 2; title = [IO.Path]::GetFileNameWithoutExtension($Pdf); locale = "es_ES" } | ConvertTo-Json -Compress
    $tmpMeta = New-TemporaryFile
    # UTF-8 sin BOM: Set-Content -Encoding utf8 añade BOM en PowerShell 5.1
    [IO.File]::WriteAllText($tmpMeta.FullName, $meta, (New-Object Text.UTF8Encoding $false))
    $curlOut = & curl.exe -s -S -X POST "$base/manuscripts" -H "Authorization: Bearer $Token" -F "file=@$Pdf;type=application/pdf" -F "metadata=<$tmpMeta"
    Remove-Item $tmpMeta -Force
    $resp = ($curlOut -join "") | ConvertFrom-Json
    if (-not $resp.manuscript_id) { throw "Respuesta inesperada: $curlOut" }
    $id = $resp.manuscript_id
    Write-Host ("manuscript_id = {0}  status = {1}" -f $id, $resp.status)

    # El análisis corre en segundo plano (BackgroundTasks): esperar hasta un estado final.
    $final = @("validated", "unreadable", "out_of_scope", "failed", "ready_for_review")
    for ($i = 0; $i -lt 120; $i++) {
        $f = Get-Json "$base/manuscripts/$id/findings" $headers
        if ($final -contains $f.status) { break }
        Start-Sleep -Milliseconds 500
    }

    Write-Host ""
    Write-Host ("Estado final: {0} {1}" -f $f.status, $(if ($f.status_reason) { "($($f.status_reason))" } else { "" })) -ForegroundColor Green
    Write-Host ("Hallazgos: {0}   rule_error: {1}" -f $f.total, $f.rule_errors.Count)
    if ($f.total -gt 0) {
        $f.findings | ForEach-Object {
            [pscustomobject]@{
                Regla      = $_.rule_id
                Severidad  = $_.severidad
                Pagina     = $_.pagina
                Figura     = $_.ubicacion.etiqueta
                Encontrado = $_.valor_encontrado
                Esperado   = $_.valor_esperado
                Evidencia  = $_.evidencia.ruta
            }
        } | Format-Table -AutoSize | Out-String -Width 200 | Write-Host
    }
    Write-Host "JSON completo: $base/manuscripts/$id/findings  (OpenAPI: $base/docs)"
}
finally {
    if ($proc -and -not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force
        Write-Host "API detenida." -ForegroundColor DarkGray
    }
}
