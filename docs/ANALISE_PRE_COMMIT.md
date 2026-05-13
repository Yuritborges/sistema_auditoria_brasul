# Análise técnica — Sistema de Auditoria Brasul (pré-commit)

## Resumo

Aplicação **desktop PySide6** com SQLite (banco consolidado de pedidos + `auditoria_local.db` para usuários e trilha de auditoria). Ponto forte: separação `service` / `repository` / `ui`. Riscos principais: **acesso a rede (Z:)** no startup (mitigado com carga leve de PDF) e **dependência de caminhos fixos** no `config.py`.

---

## Correções já aplicadas (histórico recente)

- **Performance na abertura:** remoção de `os.path.exists` em massa no `pdf_index.json` e modo `_bulk_pdf_resolve` no primeiro `carregar()`.
- **UI Pedidos:** paginação + célula “Abrir PDF” sem um botão por linha.
- **Combos (Windows):** `BrasulComboBox` com pintura opaca no popup (evita fundo preto por `QWidget { background: transparent }` global).
- **Estilo:** listas, menus, cabeçalhos de tabela e foco de campos alinhados a **azul refinado** (`#3b82f6` / `#eff6ff`), sem blocos rosados em seleção.

---

## Itens a acompanhar (não bloqueantes)

| Área | Observação |
|------|------------|
| **Caminhos** | `config.py` usa `Z:\...` e `AUDITORIA_DB_PATH` / `AUDITORIA_PDF_ROOT`. Outro PC sem Z: quebra; documentar variáveis de ambiente no README. |
| **Requisitos** | `requirements.txt` só lista `PySide6` sem versão. Recomendado: fixar `PySide6==6.x` após teste. |
| **Banco** | `database/auditoria_local.db` no `.gitignore` — evita commit de senhas/hashes; bootstrap de usuários no primeiro run. |
| **PDF** | Carga inicial confia em caminhos do índice sem `exists` (troca de UX por velocidade). “Buscar PDFs” revalida. |
| **Exceções** | Vários `except: pass` em `auditoria_service.py` (JSON, CSV, etc.): silencioso; em manutenção, logar com `logging` no mínimo. |
| **Legado** | ~~`consulta_widget.py`~~ removido (não era referenciado pelo shell). |
| **Ortografia UI** | Filtro `Critico` → `Crítico` (opcional). Fornecedores: rótulo “Fomecedor” se ainda existir no .ui. |
| **Thread** | Não há worker de PDF automático (por escolha do usuário). Busca pesada só no botão. |

---

## Segurança (contexto)

- Senhas: **SHA-256** sem salt por usuário (adequado para ambiente controlado; não é padrão web).
- Perfil **ADMIN** em módulo Configurações: revisar se `can_access` restringe bem quem vê o menu (hoje FINANCEIRO não vê `configuracoes` em `auth.py`).

---

## Checklist Git sugerido

1. `git add` somente fontes + `requirements.txt` + `docs/` + assets necessários.  
2. Não versionar `__pycache__`, `.idea`, `*.db` (já no `.gitignore`).  
3. Commit sugerido: *“UI: tema azul refinado, gitignore, análise pré-commit; combo/menus/cabeçalhos”*  
4. Em equipe: definir se `cotacao_rede.db` entra no repositório ou fica só em rede/CI.

---

## Próximos passos opcionais

- `logging` básico em arquivo + nível INFO para `carregar` e `buscar_pdfs`.  
- Teste mínimo (`pytest`) em `auditoria_service._norm_numero` e `normalize_profile`.  
- Empacotar com **PyInstaller** e testar em máquina sem Python.

---

*Documento gerado para fechamento de entrega; atualize após mudanças de arquitetura.*
