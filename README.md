# Sistema de Auditoria Brasul

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

Feche o sistema de pedidos nas máquinas se o script acusar banco em uso. Depois de consolidar, reabra a auditoria (ou use *Atualizar* / recarregar se existir) para ver pedidos novos.

**Cadastro de obras (módulo orçamentos):** as obras também são lidas de `brasul_pedidos\cadastros_compartilhados\obras.json`, alinhado ao sistema de pedidos.

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
