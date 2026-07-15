# Diagnostica mapeamento de rede da Auditoria (Z:, Y:, etc.)
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File tools\diagnostico_rede_auditoria.ps1

$ErrorActionPreference = "Continue"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

Write-Host "=== Diagnostico rede — Sistema de Auditoria ===" -ForegroundColor Cyan
Write-Host ""

$venvPy = Join-Path $Root ".venv\Scripts\python.exe"
$py = if (Test-Path $venvPy) { $venvPy } else { "python" }

& $py -c @"
from app.rede_paths import resolver_base_rede_dir, DEFAULT_BASE_REDE_SUFFIX
from app.config import BASE_REDE_PEDIDOS, resolve_db_path
import os
base = resolver_base_rede_dir()
print('Pasta detectada (rede.py):', base)
print('BASE_REDE_PEDIDOS (config):', BASE_REDE_PEDIDOS)
print('Banco consolidado:', resolve_db_path() or '(nao encontrado)')
for nome in ('cotacao_rede.db', 'cadastros_compartilhados', 'Iury', 'Thamyres'):
    p = os.path.join(base, nome)
    print(f'  {nome}:', 'OK' if os.path.exists(p) else 'NAO')
print('Sufixo esperado:', DEFAULT_BASE_REDE_SUFFIX)
"@

Write-Host ""
Write-Host "Unidades mapeadas (letra -> caminho):" -ForegroundColor Yellow
Get-PSDrive -PSProvider FileSystem |
    Where-Object { $_.Name -match '^[A-Z]$' } |
    ForEach-Object {
        $letra = $_.Name
        $candidato = Join-Path ($letra + ':\') '0 OBRAS\brasul_pedidos'
        $ok = Test-Path $candidato
        $tag = if ($ok) { ' [brasul_pedidos OK]' } else { '' }
        Write-Host ("  {0}: {1}{2}" -f $letra, $_.DisplayRoot, $tag)
    }

Write-Host ""
Write-Host "Atalho do sistema (current):" -ForegroundColor Yellow
$cur = Join-Path $Root 'current\SISTEMA AUDITORIA BRASUL.exe'
if (Test-Path $cur) {
    Write-Host "  OK $cur"
} else {
    Write-Host "  NAO ENCONTRADO — ajuste o atalho para a letra correta (ex.: Y:\0 OBRAS\...\current\)"
}

Write-Host ""
Write-Host "Se precisar fixar neste PC (mesma variavel do sistema de pedidos):" -ForegroundColor DarkGray
Write-Host '  setx BRASUL_REDE_DIR "Y:\0 OBRAS\brasul_pedidos"'
