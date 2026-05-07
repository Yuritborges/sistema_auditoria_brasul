# Copia dist\\SISTEMA AUDITORIA BRASUL para current\ sem rodar PyInstaller.
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$src = Join-Path $Root "dist\\SISTEMA AUDITORIA BRASUL"
$cur = Join-Path $Root "current"

if (-not (Test-Path (Join-Path $src "SISTEMA AUDITORIA BRASUL.exe"))) {
    throw "Nao encontrei $src\SISTEMA AUDITORIA BRASUL.exe. Rode build_release.ps1 ou pyinstaller antes."
}
New-Item -ItemType Directory -Path $cur -Force | Out-Null

. (Join-Path $PSScriptRoot "robocopy_mirror.ps1")
$rc = Invoke-RobocopyMirror -Source $src -Destination $cur
if ($rc -ge 8) {
    throw "robocopy falhou (codigo $rc). Feche o SistemaAuditoriaBrasul em todos os PCs e tente novamente."
}

Write-Host "OK: $cur\SISTEMA AUDITORIA BRASUL.exe"
