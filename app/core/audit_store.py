import os
import sqlite3
import hashlib
import hmac
import base64
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
                    ativo INTEGER NOT NULL DEFAULT 1,
                    senha_hash TEXT NOT NULL DEFAULT ''
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS contratos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero TEXT NOT NULL UNIQUE,
                    obra TEXT NOT NULL,
                    objeto TEXT NOT NULL,
                    valor_global REAL NOT NULL DEFAULT 0,
                    prazo_inicio TEXT,
                    prazo_fim TEXT,
                    status TEXT NOT NULL DEFAULT 'ATIVO',
                    criado_em TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS aditivos_contrato (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contrato_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL,
                    descricao TEXT,
                    valor REAL NOT NULL DEFAULT 0,
                    prazo_dias INTEGER NOT NULL DEFAULT 0,
                    data_aditivo TEXT NOT NULL,
                    FOREIGN KEY (contrato_id) REFERENCES contratos(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS medicoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contrato_id INTEGER NOT NULL,
                    obra TEXT NOT NULL,
                    competencia TEXT NOT NULL,
                    percentual_fisico REAL NOT NULL DEFAULT 0,
                    valor_medido REAL NOT NULL DEFAULT 0,
                    responsavel TEXT NOT NULL DEFAULT '',
                    observacoes TEXT,
                    data_registro TEXT NOT NULL,
                    UNIQUE (contrato_id, competencia),
                    FOREIGN KEY (contrato_id) REFERENCES contratos(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notas_fiscais (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_nf TEXT NOT NULL UNIQUE,
                    pedido_numero TEXT,
                    contrato_id INTEGER,
                    obra TEXT NOT NULL,
                    fornecedor TEXT NOT NULL,
                    valor REAL NOT NULL DEFAULT 0,
                    data_emissao TEXT NOT NULL,
                    status_conciliacao TEXT NOT NULL DEFAULT 'ABERTA',
                    justificativa TEXT,
                    FOREIGN KEY (contrato_id) REFERENCES contratos(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sinapi_precos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competencia TEXT NOT NULL,
                    codigo TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    unidade TEXT,
                    preco REAL NOT NULL DEFAULT 0,
                    uf TEXT NOT NULL DEFAULT 'SP',
                    UNIQUE (competencia, codigo, uf)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS vistorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    obra TEXT NOT NULL,
                    contrato_id INTEGER,
                    data_vistoria TEXT NOT NULL,
                    responsavel TEXT NOT NULL,
                    resumo TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ABERTA',
                    FOREIGN KEY (contrato_id) REFERENCES contratos(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rnc (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vistoria_id INTEGER NOT NULL,
                    obra TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ABERTA',
                    acao_corretiva TEXT,
                    prazo_solucao TEXT,
                    resolvida_em TEXT,
                    FOREIGN KEY (vistoria_id) REFERENCES vistorias(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rnc_anexos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rnc_id INTEGER NOT NULL,
                    caminho_arquivo TEXT NOT NULL,
                    tipo TEXT NOT NULL DEFAULT 'FOTO',
                    data_registro TEXT NOT NULL,
                    FOREIGN KEY (rnc_id) REFERENCES rnc(id)
                )
                """
            )
            # Compatibilidade com bases antigas sem a coluna senha_hash.
            cols = {r[1] for r in conn.execute("PRAGMA table_info(usuarios)").fetchall()}
            if "senha_hash" not in cols:
                conn.execute("ALTER TABLE usuarios ADD COLUMN senha_hash TEXT NOT NULL DEFAULT ''")
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

    def _hash_password(self, senha):
        raw = (senha or "").encode("utf-8")
        salt = os.urandom(16)
        deriv = hashlib.pbkdf2_hmac("sha256", raw, salt, 120000)
        return "pbkdf2_sha256$120000$%s$%s" % (
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(deriv).decode("ascii"),
        )

    def _verify_password(self, saved, senha):
        token = (saved or "").strip()
        if not token:
            return False
        if token.startswith("pbkdf2_sha256$"):
            try:
                _, rounds_s, salt_b64, hash_b64 = token.split("$", 3)
                rounds = int(rounds_s)
                salt = base64.b64decode(salt_b64.encode("ascii"))
                expected = base64.b64decode(hash_b64.encode("ascii"))
                got = hashlib.pbkdf2_hmac("sha256", (senha or "").encode("utf-8"), salt, rounds)
                return hmac.compare_digest(expected, got)
            except Exception:
                return False
        legacy = hashlib.sha256((senha or "").encode("utf-8")).hexdigest()
        return hmac.compare_digest(token, legacy)

    def upsert_user(self, nome, perfil, ativo=True, senha=None):
        conn = self._connect()
        try:
            senha_hash = self._hash_password(senha) if senha is not None else None
            conn.execute(
                """
                INSERT INTO usuarios (nome, perfil, ativo, senha_hash)
                VALUES (?, ?, ?, COALESCE(?, ''))
                ON CONFLICT(nome) DO UPDATE SET
                    perfil=excluded.perfil,
                    ativo=excluded.ativo,
                    senha_hash=CASE
                        WHEN ? IS NULL THEN usuarios.senha_hash
                        ELSE excluded.senha_hash
                    END
                """,
                (
                    nome.strip().upper(),
                    perfil.strip().upper(),
                    1 if ativo else 0,
                    senha_hash,
                    senha_hash,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def verify_user_password(self, nome, senha):
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT senha_hash FROM usuarios WHERE UPPER(TRIM(nome))=? AND ativo=1",
                (nome.strip().upper(),),
            ).fetchone()
            if not row:
                return False
            saved = (row["senha_hash"] or "").strip()
            if not saved:
                return False
            return self._verify_password(saved, senha)
        finally:
            conn.close()

    def user_has_password(self, nome):
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT senha_hash FROM usuarios WHERE UPPER(TRIM(nome))=? AND ativo=1",
                (nome.strip().upper(),),
            ).fetchone()
            if not row:
                return False
            return bool((row["senha_hash"] or "").strip())
        finally:
            conn.close()

    def set_user_password(self, nome, senha):
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE usuarios SET senha_hash=? WHERE UPPER(TRIM(nome))=?",
                (self._hash_password(senha), nome.strip().upper()),
            )
            conn.commit()
        finally:
            conn.close()

    def clear_user_password(self, nome):
        """Remove o hash para o usuario voltar ao fluxo de primeiro acesso (definir senha no login)."""
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE usuarios SET senha_hash=? WHERE UPPER(TRIM(nome))=?",
                ("", nome.strip().upper()),
            )
            conn.commit()
        finally:
            conn.close()

    def delete_user(self, nome):
        conn = self._connect()
        try:
            conn.execute("DELETE FROM usuarios WHERE UPPER(TRIM(nome))=?", (nome.strip().upper(),))
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

    def upsert_contract(self, numero, obra, objeto, valor_global, prazo_inicio, prazo_fim, status="ATIVO"):
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO contratos (numero, obra, objeto, valor_global, prazo_inicio, prazo_fim, status, criado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(numero) DO UPDATE SET
                    obra=excluded.obra,
                    objeto=excluded.objeto,
                    valor_global=excluded.valor_global,
                    prazo_inicio=excluded.prazo_inicio,
                    prazo_fim=excluded.prazo_fim,
                    status=excluded.status
                """,
                (
                    (numero or "").strip().upper(),
                    (obra or "").strip(),
                    (objeto or "").strip(),
                    float(valor_global or 0),
                    (prazo_inicio or "").strip(),
                    (prazo_fim or "").strip(),
                    (status or "ATIVO").strip().upper(),
                    datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def list_contracts(self):
        conn = self._connect()
        try:
            rows = conn.execute("SELECT * FROM contratos ORDER BY numero").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def delete_contract(self, contract_id):
        conn = self._connect()
        try:
            conn.execute("DELETE FROM aditivos_contrato WHERE contrato_id=?", (int(contract_id),))
            conn.execute("DELETE FROM medicoes WHERE contrato_id=?", (int(contract_id),))
            conn.execute("DELETE FROM contratos WHERE id=?", (int(contract_id),))
            conn.commit()
        finally:
            conn.close()

    def add_contract_addendum(self, contrato_id, tipo, descricao, valor, prazo_dias, data_aditivo):
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO aditivos_contrato (contrato_id, tipo, descricao, valor, prazo_dias, data_aditivo)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    int(contrato_id),
                    (tipo or "").strip().upper(),
                    (descricao or "").strip(),
                    float(valor or 0),
                    int(prazo_dias or 0),
                    (data_aditivo or "").strip(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def list_addenda(self, contrato_id=None):
        conn = self._connect()
        try:
            if contrato_id:
                rows = conn.execute(
                    "SELECT * FROM aditivos_contrato WHERE contrato_id=? ORDER BY data_aditivo DESC, id DESC",
                    (int(contrato_id),),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM aditivos_contrato ORDER BY data_aditivo DESC, id DESC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def upsert_medicao(self, contrato_id, obra, competencia, percentual_fisico, valor_medido, responsavel, observacoes):
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO medicoes (contrato_id, obra, competencia, percentual_fisico, valor_medido, responsavel, observacoes, data_registro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(contrato_id, competencia) DO UPDATE SET
                    obra=excluded.obra,
                    percentual_fisico=excluded.percentual_fisico,
                    valor_medido=excluded.valor_medido,
                    responsavel=excluded.responsavel,
                    observacoes=excluded.observacoes,
                    data_registro=excluded.data_registro
                """,
                (
                    int(contrato_id),
                    (obra or "").strip(),
                    (competencia or "").strip(),
                    float(percentual_fisico or 0),
                    float(valor_medido or 0),
                    (responsavel or "").strip().upper(),
                    (observacoes or "").strip(),
                    datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def list_medicoes(self, contrato_id=None):
        conn = self._connect()
        try:
            if contrato_id:
                rows = conn.execute(
                    "SELECT * FROM medicoes WHERE contrato_id=? ORDER BY competencia DESC, id DESC",
                    (int(contrato_id),),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM medicoes ORDER BY competencia DESC, id DESC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def upsert_nota_fiscal(
        self,
        numero_nf,
        pedido_numero,
        contrato_id,
        obra,
        fornecedor,
        valor,
        data_emissao,
        status_conciliacao="ABERTA",
        justificativa="",
    ):
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO notas_fiscais
                    (numero_nf, pedido_numero, contrato_id, obra, fornecedor, valor, data_emissao, status_conciliacao, justificativa)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(numero_nf) DO UPDATE SET
                    pedido_numero=excluded.pedido_numero,
                    contrato_id=excluded.contrato_id,
                    obra=excluded.obra,
                    fornecedor=excluded.fornecedor,
                    valor=excluded.valor,
                    data_emissao=excluded.data_emissao,
                    status_conciliacao=excluded.status_conciliacao,
                    justificativa=excluded.justificativa
                """,
                (
                    (numero_nf or "").strip().upper(),
                    (pedido_numero or "").strip(),
                    int(contrato_id) if contrato_id else None,
                    (obra or "").strip(),
                    (fornecedor or "").strip(),
                    float(valor or 0),
                    (data_emissao or "").strip(),
                    (status_conciliacao or "ABERTA").strip().upper(),
                    (justificativa or "").strip(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def list_notas_fiscais(self):
        conn = self._connect()
        try:
            rows = conn.execute("SELECT * FROM notas_fiscais ORDER BY data_emissao DESC, id DESC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def upsert_sinapi(self, competencia, codigo, descricao, unidade, preco, uf="SP"):
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO sinapi_precos (competencia, codigo, descricao, unidade, preco, uf)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(competencia, codigo, uf) DO UPDATE SET
                    descricao=excluded.descricao,
                    unidade=excluded.unidade,
                    preco=excluded.preco
                """,
                (
                    (competencia or "").strip(),
                    (codigo or "").strip().upper(),
                    (descricao or "").strip(),
                    (unidade or "").strip(),
                    float(preco or 0),
                    (uf or "SP").strip().upper(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def clear_sinapi_competencia(self, competencia, uf="SP"):
        conn = self._connect()
        try:
            conn.execute(
                "DELETE FROM sinapi_precos WHERE competencia=? AND uf=?",
                ((competencia or "").strip(), (uf or "SP").strip().upper()),
            )
            conn.commit()
        finally:
            conn.close()

    def list_sinapi(self, competencia=None, uf="SP"):
        conn = self._connect()
        try:
            if competencia:
                rows = conn.execute(
                    "SELECT * FROM sinapi_precos WHERE competencia=? AND uf=? ORDER BY codigo",
                    ((competencia or "").strip(), (uf or "SP").strip().upper()),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM sinapi_precos WHERE uf=? ORDER BY competencia DESC, codigo",
                    ((uf or "SP").strip().upper(),),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def add_vistoria(self, obra, contrato_id, data_vistoria, responsavel, resumo, status="ABERTA"):
        conn = self._connect()
        try:
            cur = conn.execute(
                """
                INSERT INTO vistorias (obra, contrato_id, data_vistoria, responsavel, resumo, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    (obra or "").strip(),
                    int(contrato_id) if contrato_id else None,
                    (data_vistoria or "").strip(),
                    (responsavel or "").strip().upper(),
                    (resumo or "").strip(),
                    (status or "ABERTA").strip().upper(),
                ),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def list_vistorias(self):
        conn = self._connect()
        try:
            rows = conn.execute("SELECT * FROM vistorias ORDER BY data_vistoria DESC, id DESC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def add_rnc(self, vistoria_id, obra, descricao, prazo_solucao, acao_corretiva=""):
        conn = self._connect()
        try:
            cur = conn.execute(
                """
                INSERT INTO rnc (vistoria_id, obra, descricao, status, acao_corretiva, prazo_solucao, resolvida_em)
                VALUES (?, ?, ?, 'ABERTA', ?, ?, '')
                """,
                (int(vistoria_id), (obra or "").strip(), (descricao or "").strip(), (acao_corretiva or "").strip(), (prazo_solucao or "").strip()),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def set_rnc_status(self, rnc_id, status, acao_corretiva="", resolvida_em=""):
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE rnc SET status=?, acao_corretiva=?, resolvida_em=? WHERE id=?",
                ((status or "").strip().upper(), (acao_corretiva or "").strip(), (resolvida_em or "").strip(), int(rnc_id)),
            )
            conn.commit()
        finally:
            conn.close()

    def list_rncs(self):
        conn = self._connect()
        try:
            rows = conn.execute("SELECT * FROM rnc ORDER BY id DESC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def add_rnc_anexo(self, rnc_id, caminho_arquivo, tipo="FOTO"):
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO rnc_anexos (rnc_id, caminho_arquivo, tipo, data_registro)
                VALUES (?, ?, ?, ?)
                """,
                (int(rnc_id), (caminho_arquivo or "").strip(), (tipo or "FOTO").strip().upper(), datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
            )
            conn.commit()
        finally:
            conn.close()

    def list_rnc_anexos(self, rnc_id=None):
        conn = self._connect()
        try:
            if rnc_id:
                rows = conn.execute(
                    "SELECT * FROM rnc_anexos WHERE rnc_id=? ORDER BY id DESC",
                    (int(rnc_id),),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM rnc_anexos ORDER BY id DESC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
