"""
Remove ou redefine senha de um usuário no auditoria_local.db.

Exemplos:
    python tools/reset_user_password.py PRISCILA --limpar --base-dir current
    python tools/reset_user_password.py PRISCILA "1234" --base-dir current
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
    p = argparse.ArgumentParser(description="Senha de usuário no auditoria_local.db")
    p.add_argument("usuario", help="Nome do usuário (ex.: PRISCILA, ADMIN)")
    p.add_argument("senha", nargs="?", default="", help="Nova senha (mín. 4 caracteres)")
    p.add_argument("--limpar", action="store_true", help="Remove a senha (primeiro acesso no login)")
    p.add_argument(
        "--base-dir",
        default="",
        help="Pasta que contém database/ (ex.: current ou raiz do projeto)",
    )
    args = p.parse_args()

    nome = (args.usuario or "").strip().upper()
    if not nome:
        print("Erro: informe o usuário.", file=sys.stderr)
        return 1

    if args.base_dir.strip():
        base_dir = os.path.abspath(args.base_dir.strip())
        if not os.path.isabs(args.base_dir.strip()):
            base_dir = os.path.join(ROOT, args.base_dir.strip())
    else:
        from app.config import BASE_DIR

        base_dir = BASE_DIR

    store = AuditStore(base_dir)
    users = {str(u.get("nome", "")).strip().upper() for u in store.list_users()}
    if nome not in users:
        store.upsert_user(nome, "ADMIN", True)

    if args.limpar:
        store.clear_user_password(nome)
        print(f"Senha de {nome} removida (primeiro acesso).")
        print("No login: digite a senha desejada (mín. 4 caracteres) e clique em Entrar.")
        print(f"Banco: {store.db_path}")
        return 0

    senha = args.senha or ""
    if len(senha) < 4:
        print("Erro: senha com pelo menos 4 caracteres ou use --limpar.", file=sys.stderr)
        return 1

    store.set_user_password(nome, senha)
    print(f"Senha de {nome} atualizada.")
    print(f"Banco: {store.db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
