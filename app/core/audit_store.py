import os
import sqlite3
from datetime import datetime


class AuditStore:
    def __init__(self, base_dir):
        self.db_path = os.path.join(base_dir, "database", "auditoria_local.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entidade TEXT NOT NULL,
                    entidade_id TEXT NOT NULL,
                    acao TEXT NOT NULL,
                    campo TEXT,
                    valor_anterior TEXT,
                    valor_novo TEXT,
                    usuario TEXT NOT NULL,
                    data_hora TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orcamentos_obra (
                    obra TEXT PRIMARY KEY,
                    valor_previsto REAL NOT NULL,
                    atualizado_em TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    nome TEXT PRIMARY KEY,
                    perfil TEXT NOT NULL,
                    ativo INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def log(self, entidade, entidade_id, acao, campo, valor_anterior, valor_novo, usuario):
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO audit_log (entidade, entidade_id, acao, campo, valor_anterior, valor_novo, usuario, data_hora)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entidade,
                    str(entidade_id),
                    acao,
                    campo or "",
                    str(valor_anterior or ""),
                    str(valor_novo or ""),
                    usuario or "SISTEMA",
                    datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def list_logs(self, limit=500):
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def upsert_budget(self, obra, valor_previsto):
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO orcamentos_obra (obra, valor_previsto, atualizado_em)
                VALUES (?, ?, ?)
                ON CONFLICT(obra) DO UPDATE SET
                    valor_previsto=excluded.valor_previsto,
                    atualizado_em=excluded.atualizado_em
                """,
                (obra, float(valor_previsto), datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
            )
            conn.commit()
        finally:
            conn.close()

    def list_budgets(self):
        conn = self._connect()
        try:
            rows = conn.execute("SELECT * FROM orcamentos_obra ORDER BY obra").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def upsert_user(self, nome, perfil, ativo=True):
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO usuarios (nome, perfil, ativo)
                VALUES (?, ?, ?)
                ON CONFLICT(nome) DO UPDATE SET perfil=excluded.perfil, ativo=excluded.ativo
                """,
                (nome.strip().upper(), perfil.strip().upper(), 1 if ativo else 0),
            )
            conn.commit()
        finally:
            conn.close()

    def list_users(self):
        conn = self._connect()
        try:
            rows = conn.execute("SELECT * FROM usuarios ORDER BY nome").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
