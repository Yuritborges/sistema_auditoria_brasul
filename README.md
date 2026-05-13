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

O script faz primeiro um backup em `Z:\0 OBRAS\sistema_auditoria_brasul_BACKUP_AAAAMMDD_HHMM` (cópia completa exceto `.venv` e `__pycache__`), depois o PyInstaller, `releases\…` e `current\`.

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

**Atualizar o consolidado** (Iury + Thamyres → `cotacao_rede.db`):

```powershell
cd "Z:\0 OBRAS\sistema_de_pedidos_brasulv2"
.\.venv\Scripts\python.exe tools\consolidar_rede.py
```

No **Sistema de Auditoria**, o botão da barra lateral **«Atualizar pedidos (rede)»** executa o mesmo script (se existir em `Z:\0 OBRAS\sistema_de_pedidos_brasulv2\tools\`) e em seguida recarrega o `cotacao_rede.db`. Caminhos alternativos: variáveis `AUDITORIA_CONSOLIDAR_SCRIPT` e opcionalmente `AUDITORIA_CONSOLIDAR_PYTHON`.

Feche o sistema de pedidos nas máquinas se o script acusar banco em uso. Depois de consolidar, reabra a auditoria (ou use *Atualizar* / recarregar se existir) para ver pedidos novos.

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
