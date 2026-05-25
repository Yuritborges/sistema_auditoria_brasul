"""
Prepara auditoria_local.db para entrega 0 km:
- apaga historico (audit_log) e cadastros locais (medicoes, contratos, orcamentos, etc.);
- mantem usuarios cadastrados, sem senha (cada um define no primeiro login).

Uso (repositorio):
    python tools/prepare_fresh_delivery.py

Instalacao .exe (pasta do executavel):
    python tools/prepare_fresh_delivery.py --base-dir "Z:\\0 OBRAS\\sistema_auditoria_brasul\\current"
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.core.audit_store import AuditStore  # noqa: E402


def _resumo(store: AuditStore) -> dict:
    import sqlite3

    conn = sqlite3.connect(store.db_path)
    try:
        cur = conn.cursor()
        out = {}
        for t in ("audit_log", "usuarios", "orcamentos_obra", "contratos", "medicoes"):
            out[t] = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        users = cur.execute(
            "SELECT nome, perfil, CASE WHEN trim(senha_hash)='' THEN 0 ELSE 1 END FROM usuarios ORDER BY nome"
        ).fetchall()
        out["usuarios_detalhe"] = users
        return out
    finally:
        conn.close()


def preparar(base_dir: str, copiar_para: str = "") -> None:
    store = AuditStore(base_dir)
    antes = _resumo(store)
    store.reset_para_entrega(manter_usuarios=True)
    depois = _resumo(store)
    print(f"OK: {store.db_path}")
    print(f"  audit_log: {antes['audit_log']} -> {depois['audit_log']}")
    print(f"  usuarios: {depois['usuarios']} (senhas zeradas)")
    for nome, perfil, tem_senha in depois.get("usuarios_detalhe") or []:
        print(f"    - {nome} ({perfil}) senha={'sim' if tem_senha else 'nao — primeiro acesso'}")
    if copiar_para:
        dest_dir = os.path.join(os.path.abspath(copiar_para), "database")
        os.makedirs(dest_dir, exist_ok=True)
        dest_db = os.path.join(dest_dir, "auditoria_local.db")
        shutil.copy2(store.db_path, dest_db)
        print(f"  copiado para: {dest_db}")


def main() -> int:
    p = argparse.ArgumentParser(description="Preparar auditoria_local.db para entrega 0 km")
    p.add_argument(
        "--base-dir",
        action="append",
        default=[],
        help="Pasta com database/ (repita para varias instalacoes). Padrao: raiz do repo.",
    )
    p.add_argument(
        "--sync-current",
        action="store_true",
        help="Copia o banco preparado da raiz do repo para current/database/.",
    )
    args = p.parse_args()

    bases = [os.path.abspath(b.strip()) for b in args.base_dir if b.strip()]
    if not bases:
        bases = [ROOT]
    if args.sync_current:
        current = os.path.join(ROOT, "current")
        if current not in bases:
            bases.append(current)

    for base in bases:
        copiar = ""
        if args.sync_current and os.path.abspath(base) == ROOT:
            copiar = os.path.join(ROOT, "current")
        preparar(base, copiar_para=copiar if copiar and base == ROOT else "")

    cache_dirs = [os.path.join(ROOT, "cache"), os.path.join(ROOT, "current", "cache")]
    for cache in cache_dirs:
        idx = os.path.join(cache, "pdf_index.json")
        if os.path.isfile(idx):
            os.remove(idx)
            print(f"  cache removido: {idx}")

    print("\nPedidos/obras/fornecedores continuam vindo de Z:\\0 OBRAS\\brasul_pedidos\\cotacao_rede.db")
    print("No login: cada usuario digita a senha desejada (min. 4 caracteres) no primeiro acesso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
