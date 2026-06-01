# 🔍 Sistema de Auditoria Brasul

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/PySide6-Qt%20Framework-41CD52?style=for-the-badge&logo=qt&logoColor=white"/>
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white"/>
  <img src="https://img.shields.io/badge/PyInstaller-Executable-4B8BBE?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/GitHub%20Actions-CI-2088FF?style=for-the-badge&logo=githubactions&logoColor=white"/>
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white"/>
</p>

> Painel executivo de auditoria para obras da construção civil — analisa pedidos de compra, detecta pendências, controla conformidade por obra e fornece visão consolidada de gastos, integrado ao banco do sistema de pedidos.

**Repositório:** [github.com/Yuritborges/sistema_auditoria_brasul](https://github.com/Yuritborges/sistema_auditoria_brasul)

Complementa o [Sistema de Pedidos de Compra](https://github.com/Yuritborges/sistema_de_pedidos_de_compra).

---

## 📋 Sobre o Projeto

O **Sistema de Auditoria Brasul** é um painel para gestores e auditores da Brasul Construtora Ltda.

Enquanto o sistema de pedidos é usado pelos compradores para **emitir** pedidos, a auditoria é usada pela gestão para **analisar** o que foi emitido — inconsistências, PDFs ausentes, gastos por obra e período.

### Problemas que resolve

- Pedidos **sem PDF vinculado**
- Pedidos **sem responsável** (comprador não identificado)
- **Gastos por empresa** faturadora ao longo do tempo
- Visão consolidada entre compradores em rede
- **Consolidação na rede** (atualização de `cotacao_rede.db` sem relançar o `.exe` da auditoria)

---

## 🚀 Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| ✅ **Conformidade por obra** | Pedidos fora do padrão ou com dados incompletos |
| 📄 **Pendências de PDF** | Lista e busca automática em pastas de rede |
| 👤 **Pendências de responsável** | Pedidos sem comprador identificado |
| 💰 **Análise de gastos** | Custos por empresa com evolução mensal |
| 🔎 **Filtros avançados** | Comprador, obra, fornecedor e item |
| 🔄 **Atualizar pedidos (rede)** | Recarrega dados na mesma janela |
| 🧪 **Modo demonstração** | Dados fictícios se nenhum banco for encontrado |

---

## 🛠️ Stack Tecnológica

```
Python 3.11+       → linguagem principal
PySide6 (Qt6)      → interface gráfica desktop
SQLite             → cotacao_rede.db (rede) + auditoria_local.db (local)
PyInstaller        → executável .exe
PowerShell         → build, release e publicação na rede
GitHub Actions     → build Windows na nuvem (CI)
```

---

## 🗂️ Estrutura do Projeto

```
sistema_auditoria_brasul/
├── .github/workflows/
│   └── build-auditoria.yml           # CI: PyInstaller + artefato + Release (tags v*)
├── app/
│   ├── ui/                           # Painel, filtros, grades
│   ├── data/                         # Leitura do SQLite consolidado
│   ├── services/                     # Consolidação rede, auditoria
│   └── core/                         # AuditStore (usuários locais)
├── assets/                           # Ícones e recursos visuais
├── database/                         # auditoria_local.db (não versionado)
├── docs/
│   ├── BUILD_REMOTO.md
│   ├── CHECKLIST_BUILD_RELEASE.md
│   └── ENTREGA_0KM.md
├── tools/
│   ├── build_release.ps1             # Build local → releases + current
│   ├── publicar_build_na_rede.ps1    # Publica zip/dist em current/
│   └── tag_release.ps1               # Tag vX.Y.Z → GitHub Actions
├── current/                          # Atalho da equipe (não versionado)
├── main.py
├── INICIAR_AUDITORIA.bat
├── requirements.txt
└── SistemaAuditoriaBrasul.spec
```

---

## 🗄️ Fonte de Dados

Prioridade para localizar `cotacao_rede.db`:

| Prioridade | Caminho |
|---|---|
| 1 | `AUDITORIA_DB_PATH` (variável de ambiente) |
| 2 | `Z:\0 OBRAS\brasul_pedidos\cotacao_rede.db` |
| 3 | `database/cotacao_rede.db` no projeto |

**Banco local da auditoria:** `database/auditoria_local.db` (usuários, trilha — não vai para o Git).

### Atualizar o consolidado

```powershell
cd "Z:\0 OBRAS\sistema_de_pedidos_brasulv2"
.\.venv\Scripts\python.exe tools\consolidar_rede.py
```

> Feche o sistema de pedidos antes. Reabra a auditoria para ver dados novos.

---

## 📄 Busca Automática de PDFs

Raízes de varredura (em ordem):

1. `AUDITORIA_PDF_ROOT`
2. `Z:\0 OBRAS\brasul_pedidos`
3. `Z:\0 OBRAS\01 - OBRAS BRASUL`
4. `Z:\0 OBRAS\01 - OBRAS INTERIORANA`
5. `pedidos_gerados/` no projeto

Modo recomendado: aplique filtros → **Buscar PDFs** (varredura só no contexto filtrado).

---

## 🖥️ Instalação e Execução (desenvolvimento)

```powershell
git clone https://github.com/Yuritborges/sistema_auditoria_brasul.git
cd sistema_auditoria_brasul

python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

python main.py
```

Ou use `INICIAR_AUDITORIA.bat`. Em produção, a equipe abre:

`Z:\0 OBRAS\sistema_auditoria_brasul\current\SISTEMA AUDITORIA BRASUL.exe`

---

## 📦 Build e release

### Opção 1 — Tag de versão (recomendado)

```powershell
git push origin main
powershell -ExecutionPolicy Bypass -File tools\tag_release.ps1 -Versao 1.0.2
```

1. GitHub **Actions** → build verde  
2. **Releases** → baixar `SistemaAuditoriaBrasul-v1.0.2.zip`  
3. Extrair em `C:\Temp`, testar o `.exe` localmente  
4. Publicar:

```powershell
powershell -ExecutionPolicy Bypass -File tools\publicar_build_na_rede.ps1 -Origem "C:\Temp\SISTEMA AUDITORIA BRASUL"
```

**Tags existentes:** `v1.0.0`, `v1.0.1` (build sem UPX — corrige erro `zlib` / pacote corrompido na abertura).

### Opção 2 — Build na nuvem sem tag

**Actions** → **Build Sistema Auditoria** → **Run workflow** (`main`).

### Opção 3 — Build local na rede

```powershell
powershell -ExecutionPolicy Bypass -File tools\build_release.ps1
```

| Script | Descrição |
|---|---|
| `tag_release.ps1` | Tag `vX.Y.Z` + CI + Release no GitHub |
| `publicar_build_na_rede.ps1` | Atualiza `releases/` e `current/` |
| `build_release.ps1` | PyInstaller + espelha em `current/` |
| `prepare_fresh_delivery.py` | Entrega 0 km (banco local limpo) |

📄 [`docs/BUILD_REMOTO.md`](docs/BUILD_REMOTO.md) · [`docs/CHECKLIST_BUILD_RELEASE.md`](docs/CHECKLIST_BUILD_RELEASE.md)

### ⚠️ Erro ao abrir o `.exe`

Mensagem `invalid stored block lengths` / zlib → pacote **corrompido ou cópia incompleta**.

1. Baixe o zip de novo (ou gere `v1.0.2+`)  
2. Extraia em **`C:\Temp`**, teste antes de copiar para a rede  
3. Use **`publicar_build_na_rede.ps1`** — nunca copie só o `.exe` sem a pasta `_internal`

O `.spec` usa **UPX desligado** para builds mais estáveis em rede.

---

## 🔗 Integração com o Sistema de Pedidos

- Mesmo `cotacao_rede.db` consolidado  
- Mesmo cadastro de obras (`obras.json`)  
- Mesma árvore `Z:\0 OBRAS\...`  
- Consolidação via `tools/consolidar_rede.py` no repositório de pedidos

---

## 📁 O que versionar no Git

| Caminho | Versionar? |
|---|---|
| `app/`, `main.py`, `tools/`, `.github/` | ✅ Sim |
| `SistemaAuditoriaBrasul.spec` | ✅ Sim |
| `database/*.db`, `current/`, `dist/`, `releases/` | ❌ Não |

---

## 🔗 Trabalhar sem IDE / de casa

| Sozinho | Com VPN / rede |
|---|---|
| Código + `git push` + tag | `publicar_build_na_rede.ps1` em `Z:` |
| Download em **Releases** | Fechar auditoria nos PCs antes do robocopy |

---

## 👨‍💻 Autor

**Yuri Borges** — Desenvolvedor do sistema no âmbito da Brasul Construtora Ltda.

[![GitHub](https://img.shields.io/badge/GitHub-Yuritborges-181717?style=flat-square&logo=github)](https://github.com/Yuritborges)

---

## 📄 Licença

Software de **uso interno** da Brasul Construtora Ltda. Não é distribuição pública genérica; reprodução fora do contexto autorizado deve seguir a política da empresa.
