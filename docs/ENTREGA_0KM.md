# Entrega 0 km — Sistema de Auditoria Brasul

## O que foi zerado (`auditoria_local.db`)

| Mantido | Removido |
|---------|----------|
| Usuários e perfis (9 cadastros) | Histórico (`audit_log`) |
| — | Orçamentos por obra, contratos, medições, NF, vistorias, RNC, SINAPI |
| Senhas (todas vazias → primeiro acesso no login) | — |

**Pedidos, obras e fornecedores** não ficam neste arquivo: vêm de `Z:\0 OBRAS\brasul_pedidos\cotacao_rede.db` (atualizado pelo sistema de pedidos).

## Primeiro login de cada usuário

1. Selecionar o nome na lista.
2. Digitar a senha desejada (mínimo 4 caracteres) e **Entrar**.
3. Na próxima vez, usar a mesma senha.

## Repetir o reset numa pasta do `.exe`

```text
python tools\prepare_fresh_delivery.py --base-dir "Z:\0 OBRAS\sistema_auditoria_brasul\current"
```

(Feche o programa antes; use o Python do `.venv` do repositório.)

## Atualização do executável

```text
powershell -ExecutionPolicy Bypass -File tools\build_release.ps1
```

A pasta `current\` na rede recebe o novo `.exe`; `database\` **não** é sobrescrita pelo robocopy (cada PC mantém usuários/senhas locais).
