# Gera SistemaAuditoriaBrasul com PyInstaller, copia para releases/ (timestamp) e current/.
# Uso: powershell -ExecutionPolicy Bypass -File tools\build_release.ps1
#
# Backup opcional ANTES do build (desligado por defeito):
#   $env:AUDITORIA_RELEASE_BACKUP = "1"
# Copia o codigo-fonte para backups\pre_build_YYYYMMDD_HHmm DENTRO do projeto (nao em Z:\0 OBRAS\).

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$stamp = Get-Date -Format "yyyyMMdd_HHmm"
$wb = if ($null -ne $env:AUDITORIA_RELEASE_BACKUP) { "$env:AUDITORIA_RELEASE_BACKUP" } else { "" }
$wantBackup = @("1", "true", "yes", "sim") -contains $wb.Trim().ToLowerInvariant()
$backupDest = $null
if ($wantBackup) {
    $backupDest = Join-Path $Root "backups\pre_build_$stamp"
    Write-Host "[0/4] Backup do codigo (AUDITORIA_RELEASE_BACKUP=1) -> $backupDest ..."
    New-Item -ItemType Directory -Path (Join-Path $Root "backups") -Force | Out-Null
    New-Item -ItemType Directory -Path $backupDest -Force | Out-Null
    # So codigo-fonte (sem dist/build/releases nem copias anteriores em backups/).
    & robocopy.exe $Root $backupDest /E /XD .venv __pycache__ backups dist build releases .pytest_cache /NFL /NDL /NJH /NJS /NP /R:2 /W:2 | Out-Null
    $rc = $LASTEXITCODE
    if ($rc -ge 8) {
        throw "Backup (robocopy) falhou com codigo $rc. Verifique espaco em $backupDest"
    }
} else {
    Write-Host "[0/4] Backup pre-build desativado (omitido). Defina AUDITORIA_RELEASE_BACKUP=1 para copia em backups\pre_build_* dentro do projeto."
}

$PyInstaller = Join-Path $Root ".venv\Scripts\pyinstaller.exe"
if (-not (Test-Path $PyInstaller)) {
    throw "Nao encontrei $PyInstaller. Crie/ative .venv e instale: pip install pyinstaller"
}

Write-Host "[1/4] PyInstaller..."
& $PyInstaller (Join-Path $Root "SistemaAuditoriaBrasul.spec") --clean --noconfirm
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$src = Join-Path $Root "dist\\SISTEMA AUDITORIA BRASUL"
if (-not (Test-Path (Join-Path $src "SISTEMA AUDITORIA BRASUL.exe"))) {
    throw "Build incompleto: nao achei $src\SISTEMA AUDITORIA BRASUL.exe."
}

$destRelease = Join-Path $Root "releases\SistemaAuditoriaBrasul_$stamp"

Write-Host "[2/4] Copiando para $destRelease ..."
New-Item -ItemType Directory -Path (Join-Path $Root "releases") -Force | Out-Null
Copy-Item -Path $src -Destination $destRelease -Recurse -Force

Write-Host "[3/4] Atualizando pasta current (atalhos da rede) ..."
$cur = Join-Path $Root "current"
New-Item -ItemType Directory -Path $cur -Force | Out-Null
. (Join-Path $PSScriptRoot "robocopy_mirror.ps1")
$rc = Invoke-RobocopyMirror -Source $src -Destination $cur
if ($rc -ge 8) {
    throw "Falha ao copiar para current (robocopy codigo $rc). Feche o sistema em todos os PCs e rode tools\sync_current_from_dist.ps1"
}

Write-Host "[4/4] Concluido."
if ($backupDest) {
    Write-Host "OK backup:  $backupDest"
} else {
    Write-Host "OK backup:  (omitido)"
}
Write-Host "OK releases: $destRelease\SISTEMA AUDITORIA BRASUL.exe"
Write-Host "OK current:  $cur\SISTEMA AUDITORIA BRASUL.exe"
Write-Host "Quem usa o atalho em current recebe esta versao na proxima abertura."
