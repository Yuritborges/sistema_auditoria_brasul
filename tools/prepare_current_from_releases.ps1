# Antes de abrir o .exe: garante que current\ espelha a build mais recente
# (dist\ ou o snapshot mais novo em releases\). Assim, basta fechar e abrir o atalho
# depois que alguem gerou uma release na rede — mesmo se na hora do build o
# robocopy para current falhou (arquivo em uso).

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$exeName = "SISTEMA AUDITORIA BRASUL.exe"

function Get-ExePath([string]$dir) {
    return Join-Path $dir $exeName
}

$sources = @()

$distDir = Join-Path $Root "dist\SISTEMA AUDITORIA BRASUL"
if (Test-Path (Get-ExePath $distDir)) {
    $sources += $distDir
}

$relBase = Join-Path $Root "releases"
if (Test-Path $relBase) {
    Get-ChildItem -Path $relBase -Directory -Filter "SistemaAuditoriaBrasul_*" -ErrorAction SilentlyContinue |
        ForEach-Object {
            if (Test-Path (Get-ExePath $_.FullName)) {
                $sources += $_.FullName
            }
        }
}

if ($sources.Count -eq 0) {
    exit 0
}

$best = $sources |
    Sort-Object { (Get-Item (Get-ExePath $_)).LastWriteTimeUtc } -Descending |
    Select-Object -First 1

$curDir = Join-Path $Root "current"
$curExe = Get-ExePath $curDir
$srcExe = Get-ExePath $best

$srcTime = (Get-Item $srcExe).LastWriteTimeUtc
$need = $true
if (Test-Path $curExe) {
    $need = $srcTime -gt (Get-Item $curExe).LastWriteTimeUtc
}

if (-not $need) {
    exit 0
}

. (Join-Path $PSScriptRoot "robocopy_mirror.ps1")
$rc = Invoke-RobocopyMirror -Source $best -Destination $curDir
if ($rc -ge 8) {
    Write-Warning "Nao foi possivel atualizar current (robocopy $rc). Outro usuario pode estar com o programa aberto. Abrindo a versao ja instalada."
}
exit 0
