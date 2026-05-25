# Sistema de Auditoria Brasul

**Autoria:** Marlyson Iury T Borges (ver também `AUTHORS` na raiz do repositório).

Painel executivo para auditoria de pedidos de obras com foco em:

- conformidade de pedidos por obra
- pendencias de documentos (PDF ausente)
- pendencias de responsavel (comprador ausente)
- analise de gastos por empresa e evolucao mensal

## Como abrir a interface

1. Instale dependencias:

```powershell
pip install -r requirements.txt
```

2. Inicie o sistema:

```powershell
python main.py
```

Ou execute `INICIAR_AUDITORIA.bat`.

## Build .exe e atualização por abertura (modelo do sistema de pedidos)

### 1) Preparar ambiente de build

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
```

### 2) Gerar release (.exe)

```powershell
powershell -ExecutionPolicy Bypass -File tools\build_release.ps1
```

O script **não** duplica o projeto em `Z:\0 OBRAS\` por defeito (evita pastas `sistema_auditoria_brasul_BACKUP_*` fora da pasta do programa). Para ativar cópia de segurança antes do build: `AUDITORIA_RELEASE_BACKUP=1`. Snapshots antigos podem ficar em `backups\legacy_snapshots\` dentro do projeto.

Ou execute `ATUALIZAR_AUDITORIA.bat` na raiz do projeto (faz o mesmo build e copia para `current\`).

Esse fluxo:
- gera `dist\SISTEMA AUDITORIA BRASUL\SISTEMA AUDITORIA BRASUL.exe` (nome definido no `.spec`)
- cria snapshot em `releases\SistemaAuditoriaBrasul_yyyyMMdd_HHmm\`
- espelha o conteúdo em `current\` (atalho pode apontar para o `.bat`; ver abaixo)

### 3) Distribuição/atualização nas máquinas (igual ideia do sistema de pedidos)

**Atalho na rede:** use **`Brasul-Auditoria.bat`** ou **`ABRIR_AUDITORIA.bat`** na raiz do projeto (`Z:\0 OBRAS\sistema_auditoria_brasul\`), **não** o `.exe` direto.

A cada duplo clique, o sistema:
1. Compara `current\SISTEMA AUDITORIA BRASUL.exe` com a build mais recente em `dist\` ou no último snapshot em `releases\`.
2. Se houver versão mais nova na pasta da rede, copia (robocopy) para `current\` e só então abre o programa.

Assim, depois que alguém rodou o build na rede, **basta fechar o sistema e abrir de novo pelo atalho do `.bat`** para receber a versão nova — inclusive quando no momento do build o `current` não pôde ser atualizado porque o `.exe` estava em uso.

Se o atalho continuar apontando só para `current\...\SISTEMA AUDITORIA BRASUL.exe`, o Windows **não** executa esse passo de cópia; aí só muda o que já estiver fisicamente em `current`.

Se só quiser sincronizar `dist` -> `current` sem rebuild:

```powershell
powershell -ExecutionPolicy Bypass -File tools\sync_current_from_dist.ps1
```

## Fonte de dados

O painel de auditoria le o **mesmo banco consolidado** que o programa de pedidos mantém na rede:

| Prioridade | Caminho |
|------------|---------|
| 1 | Variável de ambiente `AUDITORIA_DB_PATH` (caminho absoluto para um `.db`) |
| 2 | `Z:\0 OBRAS\brasul_pedidos\cotacao_rede.db` |
| 3 | `database/cotacao_rede.db` dentro deste projeto (cópia local de fallback) |

**Sincronização quase em tempo real (padrão atual):**

| O quê | Como |
|-------|------|
| **Cada pedido salvo** (pedidos aberto) | Atualização **incremental** de `cotacao_rede.db` em poucos segundos (`sync_pedido_atual_para_cotacao_rede`) |
| Sistema de **pedidos** com o app aberto | Timer **300 s** (5 min): consolidação completa se Iury/Thamyres defasados; backup rolling **900 s** (`REDE_SYNC_*`, `BACKUP_REDE_*`) |
| Sistema de **auditoria** com o app aberto | **20 s**: relê o consolidado **só se** `mtime`/tamanho mudou; **120 s**: consolida via script se defasado |
| Botão **«Atualizar pedidos (rede)»** | Consolidação manual em segundo plano + recarga |

Variáveis opcionais: `BRASUL_REDE_SYNC_SEG` (ex. `60` para consolidar pedidos a cada minuto), `BRASUL_BACKUP_REDE_SEG`, `AUDITORIA_AUTO_RELOAD_MS` (ex. `15000`), `AUDITORIA_AUTO_CONSOLIDAR_MS` (use `0` para desligar).

**Perfil ENGENHEIRA:** use o perfil `ENGENHARIA` (Obras, Pedidos, Medições, Contratos) para medições físico-financeiras; cadastre contratos antes de medir.

**Consolidação manual** (Iury + Thamyres → `cotacao_rede.db`):

```powershell
cd "Z:\0 OBRAS\sistema_de_pedidos_brasulv2"
.\.venv\Scripts\python.exe tools\consolidar_rede.py
```

O botão **«Atualizar pedidos (rede)»** executa o mesmo script com o **Python do `.venv` na rede** (não o `.exe` da auditoria). Caminhos alternativos: `AUDITORIA_CONSOLIDAR_SCRIPT` e `AUDITORIA_CONSOLIDAR_PYTHON`.

Se a consolidação falhar por banco em uso, feche o sistema de pedidos nas duas máquinas e tente de novo. Com os timers ativos, em geral não é preciso clicar no botão.

**Cadastro de obras:** na consulta por obra, os nomes vêm dos pedidos consolidados e, quando existir, de `brasul_pedidos\cadastros_compartilhados\obras.json`, alinhado ao sistema de pedidos.

Se nao encontrar banco, abre em modo demonstracao para permitir validacao de layout e fluxo.

## Reconhecimento automatico de PDFs

Quando `caminho_pdf` nao vier preenchido no banco, o sistema tenta localizar PDFs automaticamente
em pastas de obras/pedidos, cruzando pelo numero do pedido encontrado no nome do arquivo.

Raizes usadas para varredura:

1. variavel de ambiente `AUDITORIA_PDF_ROOT`
2. `Z:\0 OBRAS\brasul_pedidos`
3. `Z:\0 OBRAS\01 - OBRAS BRASUL`
4. `Z:\0 OBRAS\01 - OBRAS INTERIORANA`
5. `pedidos_gerados` dentro do projeto

Exemplo de nomes de arquivo que ajudam no reconhecimento:

- `pedido_8374.pdf`
- `8374 - area electrics.pdf`
- `PEDIDO 2510 OBRA X.pdf`

### Modo recomendado (rapido, sem travar)

1. Aplique os filtros (comprador/obra/fornecedor/item).
2. Clique em `Buscar PDFs`.
3. O sistema procura PDFs apenas no contexto filtrado e atualiza os pedidos exibidos.
