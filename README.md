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

O sistema tenta localizar o banco nesta ordem:

1. variavel de ambiente `AUDITORIA_DB_PATH`
2. `Z:\0 OBRAS\brasul_pedidos\cotacao_rede.db`
3. `database/cotacao_rede.db` dentro do projeto

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
