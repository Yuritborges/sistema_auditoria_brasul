# Publica na rede um build ja gerado (local ou baixado do GitHub Actions).
# Uso:
#   powershell -ExecutionPolicy Bypass -File tools\publicar_build_na_rede.ps1
#   powershell -ExecutionPolicy Bypass -File tools\publicar_build_na_rede.ps1 -Origem "C:\Temp\SISTEMA AUDITORIA BRASUL"

param(
    [string]$Origem = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

if (-not $Origem) {
    $Origem = Join-Path $Root "dist\SISTEMA AUDITORIA BRASUL"
}

$Origem = (Resolve-Path $Origem -ErrorAction Stop).Path
$exe = Join-Path $Origem "SISTEMA AUDITORIA BRASUL.exe"
if (-not (Test-Path $exe)) {
    throw "Nao encontrei $exe. Extraia o zip do GitHub ou rode tools\build_release.ps1 antes."
}

$stamp = Get-Date -Format "yyyyMMdd_HHmm"
$destRelease = Join-Path $Root "releases\SistemaAuditoriaBrasul_$stamp"
$cur = Join-Path $Root "current"

Write-Host "[1/2] Snapshot em releases\$stamp ..."
New-Item -ItemType Directory -Path $destRelease -Force | Out-Null
Copy-Item -Path "$Origem\*" -Destination $destRelease -Recurse -Force

Write-Host "[2/2] Atualizando current\ (atalhos da rede) ..."
New-Item -ItemType Directory -Path $cur -Force | Out-Null
. (Join-Path $PSScriptRoot "robocopy_mirror.ps1")
$rc = Invoke-RobocopyMirror -Source $Origem -Destination $cur
if ($rc -ge 8) {
    throw "Falha ao copiar para current (robocopy $rc). Feche o sistema em todos os PCs e tente novamente."
}

Write-Host "OK current:  $cur\SISTEMA AUDITORIA BRASUL.exe"
Write-Host "OK releases: $destRelease\SISTEMA AUDITORIA BRASUL.exe"
