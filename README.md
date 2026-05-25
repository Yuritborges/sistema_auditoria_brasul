# 🔍 Sistema de Auditoria Brasul

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/PySide6-Qt%20Framework-41CD52?style=for-the-badge&logo=qt&logoColor=white"/>
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white"/>
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white"/>
</p>

> Painel executivo de auditoria para obras da construção civil — analisa pedidos de compra, detecta pendências, controla conformidade por obra e fornece visão consolidada de gastos, tudo integrado ao banco de dados do sistema de pedidos existente.

---

## 📋 Sobre o Projeto

O **Sistema de Auditoria Brasul** é um painel de controle desenvolvido para gestores e auditores da Brasul Construtora Ltda, complementando o [sistema de pedidos de compra](https://github.com/Yuritborges/sistema_de_pedidos_de_compra).

Enquanto o sistema de pedidos é usado pelos compradores para **emitir** pedidos, a auditoria é usada pela gestão para **analisar** o que foi emitido — detectando inconsistências, ausência de documentos e permitindo rastrear gastos por obra e período.

### Problemas que resolve

- Pedidos emitidos **sem PDF vinculado** (documento ausente)
- Pedidos **sem responsável** (comprador não identificado)
- Dificuldade de visualizar **gastos por empresa** ao longo do tempo
- Falta de visão consolidada entre múltiplos compradores operando em rede

---

## 🚀 Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| ✅ **Conformidade por obra** | Identifica pedidos fora do padrão ou com dados incompletos |
| 📄 **Pendências de PDF** | Lista pedidos sem documento PDF vinculado, com busca automática em pastas de rede |
| 👤 **Pendências de responsável** | Detecta pedidos sem comprador identificado |
| 💰 **Análise de gastos** | Custos por empresa faturadora com evolução mensal |
| 🔎 **Filtros avançados** | Filtragem por comprador, obra, fornecedor e item |
| 🗂️ **Busca automática de PDFs** | Varredura nas pastas de rede cruzando pelo número do pedido |
| 🧪 **Modo demonstração** | Abre com dados fictícios quando nenhum banco é encontrado |

---

## 🛠️ Stack Tecnológica

```
Python 3.11+    → linguagem principal
PySide6 (Qt6)   → interface gráfica desktop
SQLite          → leitura do banco consolidado cotacao_rede.db
```

---

## 🗂️ Estrutura do Projeto

```
sistema_auditoria_brasul/
├── app/
│   ├── ui/          # Widgets e janelas do painel de auditoria
│   ├── data/        # Leitura do banco SQLite consolidado
│   └── core/        # Regras de negócio de auditoria e análise
├── assets/          # Ícones e recursos visuais
├── docs/            # Documentação adicional
├── main.py          # Entrada do sistema
├── INICIAR_AUDITORIA.bat   # Atalho de inicialização para Windows
└── requirements.txt
```

---

## 🗄️ Fonte de Dados

O painel lê o **banco consolidado** gerado e mantido pelo sistema de pedidos. A resolução do banco segue esta prioridade:

| Prioridade | Caminho |
|---|---|
| 1 | Variável de ambiente `AUDITORIA_DB_PATH` (caminho absoluto para um `.db`) |
| 2 | `Z:\0 OBRAS\brasul_pedidos\cotacao_rede.db` (padrão de rede) |
| 3 | `database/cotacao_rede.db` dentro do projeto (fallback local) |

> Se nenhum banco for encontrado, o sistema abre em **modo demonstração** com dados fictícios.

### Atualizar o banco consolidado

Antes de auditar dados novos, consolide os bancos individuais dos compradores:

```bash
cd "Z:\0 OBRAS\sistema_de_pedidos_brasulv2"
.\.venv\Scripts\python.exe tools\consolidar_rede.py
```

> ⚠️ Feche o sistema de pedidos nas máquinas antes de rodar o consolidador. Após concluir, reabra a auditoria para carregar os dados mais recentes.

---

## 📄 Busca Automática de PDFs

Quando o campo `caminho_pdf` não estiver preenchido no banco, o sistema tenta localizar o PDF automaticamente nas pastas de rede, cruzando o número do pedido com o nome dos arquivos.

**Raízes de varredura (em ordem):**
1. Variável de ambiente `AUDITORIA_PDF_ROOT`
2. `Z:\0 OBRAS\brasul_pedidos`
3. `Z:\0 OBRAS\01 - OBRAS BRASUL`
4. `Z:\0 OBRAS\01 - OBRAS INTERIORANA`
5. `pedidos_gerados/` dentro do projeto

**Exemplos de nomes de arquivo reconhecidos:**
```
pedido_8374.pdf
8374 - area electrics.pdf
PEDIDO 2510 OBRA X.pdf
```

**Modo recomendado para busca rápida:**
1. Aplique os filtros desejados (comprador / obra / fornecedor / item)
2. Clique em **Buscar PDFs**
3. O sistema faz a varredura apenas no contexto filtrado, sem travar a interface

---

## 🖥️ Instalação e Execução

**Pré-requisitos:** Windows 10/11, Python 3.11+, acesso à pasta de rede da construtora.

```bash
# 1. Clone o repositório
git clone https://github.com/Yuritborges/sistema_auditoria_brasul.git
cd sistema_auditoria_brasul

# 2. Crie e ative o ambiente virtual
python -m venv .venv
.venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute
python main.py
```

Ou simplesmente clique duas vezes em `INICIAR_AUDITORIA.bat`.

---

## 🔗 Integração com o Sistema de Pedidos

Este projeto é o complemento de auditoria do [Sistema de Pedidos de Compra](https://github.com/Yuritborges/sistema_de_pedidos_de_compra). Os dois sistemas compartilham:

- O mesmo banco SQLite consolidado (`cotacao_rede.db`)
- O mesmo cadastro de obras (`obras.json`)
- A mesma estrutura de pastas de rede

---

## 👨‍💻 Autor

**Yuri Borges** — Desenvolvedor do sistema no âmbito da Brasul Construtora Ltda.

[![GitHub](https://img.shields.io/badge/GitHub-Yuritborges-181717?style=flat-square&logo=github)](https://github.com/Yuritborges)

---

## 📄 Licença

Software de **uso interno** da Brasul Construtora Ltda. Não é distribuição pública genérica; reprodução fora do contexto autorizado deve seguir a política da empresa.
