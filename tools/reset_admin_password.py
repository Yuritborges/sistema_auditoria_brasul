"""
Redefine ou remove a senha do ADMIN no SQLite local (database/auditoria_local.db).

Definir nova senha (na pasta do repositório):
    python tools/reset_admin_password.py "SuaNovaSenha"

Só limpar a senha (próxima abertura: digite no login a senha desejada, mín. 4 caracteres):
    python tools/reset_admin_password.py --limpar

Instalação pelo .exe (pasta que contém database\\auditoria_local.db):
    python tools/reset_admin_password.py --limpar --base-dir "C:\\caminho\\para\\pasta_do_exe"
"""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.core.audit_store import AuditStore  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Senha do ADMIN no auditoria_local.db")
    p.add_argument(
        "senha",
        nargs="?",
        default="",
        help="Nova senha (mínimo 4 caracteres), omitida se usar --limpar",
    )
    p.add_argument(
        "--limpar",
        action="store_true",
        help="Remove a senha: na próxima abertura o ADMIN define a senha digitando no login.",
    )
    p.add_argument(
        "--base-dir",
        default="",
        help="Pasta que contém database/ (padrão: raiz do código; use a pasta do .exe na rede).",
    )
    args = p.parse_args()

    if args.base_dir.strip():
        base_dir = os.path.abspath(args.base_dir.strip())
    else:
        from app.config import BASE_DIR

        base_dir = BASE_DIR

    store = AuditStore(base_dir)

    if args.limpar:
        store.upsert_user("ADMIN", "ADMIN", True)
        store.clear_user_password("ADMIN")
        print("Senha do ADMIN removida (primeiro acesso).")
        print("Na próxima abertura: digite a senha que quiser usar (mín. 4 caracteres) e clique em Entrar.")
        print(f"Banco: {store.db_path}")
        return 0

    senha = args.senha or ""
    if len(senha) < 4:
        print("Erro: informe uma senha com pelo menos 4 caracteres ou use --limpar.", file=sys.stderr)
        return 1

    store.upsert_user("ADMIN", "ADMIN", True)
    store.set_user_password("ADMIN", senha)
    print("Senha do usuário ADMIN atualizada.")
    print(f"Banco: {store.db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
