# Move pastas sistema_auditoria_brasul_BACKUP_* de Z:\0 OBRAS\ para backups\legacy_snapshots\ dentro do projeto.
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$parent = Split-Path $Root -Parent
$destRoot = Join-Path $Root "backups\legacy_snapshots"
New-Item -ItemType Directory -Path $destRoot -Force | Out-Null
$pattern = "sistema_auditoria_brasul_BACKUP_*"
$moved = 0
Get-ChildItem -LiteralPath $parent -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like $pattern } | ForEach-Object {
    $target = Join-Path $destRoot $_.Name
    if (Test-Path $target) {
        Write-Host "[SKIP] Ja existe: $target"
    } else {
        Write-Host "[MOVE] $($_.FullName) -> $target"
        Move-Item -LiteralPath $_.FullName -Destination $target
        $moved++
    }
}
Write-Host "Concluido. Pastas movidas: $moved"
