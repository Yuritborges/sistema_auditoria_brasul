import sqlite3


def _pedidos_columns(conn) -> set:
    return {row[1] for row in conn.execute("PRAGMA table_info(pedidos)").fetchall()}


def ensure_material_solicitado_por_column(db_path: str) -> bool:
    """
    Garante coluna material_solicitado_por no banco consolidado (bases antigas).
    Retorna True se a coluna existe ou foi criada.
    """
    if not db_path:
        return False
    try:
        conn = sqlite3.connect(db_path)
        try:
            cols = _pedidos_columns(conn)
            if "material_solicitado_por" in cols:
                return True
            conn.execute(
                "ALTER TABLE pedidos ADD COLUMN material_solicitado_por TEXT DEFAULT ''"
            )
            conn.commit()
            return True
        finally:
            conn.close()
    except sqlite3.Error:
        return False


class AuditoriaRepository:
    def __init__(self, db_path):
        self.db_path = db_path
        self._tem_material_solicitado = False

    def _resolver_coluna_solicitante(self, conn) -> str:
        self._tem_material_solicitado = "material_solicitado_por" in _pedidos_columns(conn)
        if self._tem_material_solicitado:
            return "p.material_solicitado_por"
        return "'' AS material_solicitado_por"

    def _group_by_pedidos(self) -> str:
        base = """
            p.id,
            p.numero,
            p.data_pedido,
            p.emitido_em,
            p.obra_nome,
            p.fornecedor_nome,
            p.empresa_faturadora, p.condicao_pagamento, p.forma_pagamento,
            p.valor_total, p.caminho_pdf, p.comprador
        """
        if self._tem_material_solicitado:
            return base + ", p.material_solicitado_por"
        return base

    def listar_pedidos(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA query_only = ON")
            conn.execute("PRAGMA temp_store = MEMORY")
            conn.execute("PRAGMA cache_size = -20000")
            col_sol = self._resolver_coluna_solicitante(conn)
            group_by = self._group_by_pedidos()
            rows = conn.execute(
                f"""
                SELECT
                    p.id AS pedido_id,
                    p.numero,
                    p.data_pedido,
                    p.emitido_em,
                    p.obra_nome,
                    p.fornecedor_nome,
                    p.empresa_faturadora,
                    p.condicao_pagamento,
                    p.forma_pagamento,
                    p.valor_total,
                    p.caminho_pdf,
                    p.comprador,
                    {col_sol},
                    COALESCE(GROUP_CONCAT(i.descricao, ' | '), '') AS itens_texto
                FROM pedidos p
                LEFT JOIN itens_pedido i ON i.pedido_id = p.id
                GROUP BY {group_by}
                ORDER BY p.emitido_em DESC, p.id DESC
                """
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def listar_itens_por_pedido(self):
        """Linhas de itens_pedido indexadas por pedido_id (quantidade e unidade por material)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA query_only = ON")
            rows = conn.execute(
                """
                SELECT
                    pedido_id,
                    descricao,
                    quantidade,
                    unidade,
                    valor_unitario,
                    valor_total
                FROM itens_pedido
                ORDER BY pedido_id, id
                """
            ).fetchall()
            por_pedido = {}
            for row in rows:
                pid = row["pedido_id"]
                por_pedido.setdefault(pid, []).append(
                    {
                        "descricao": (row["descricao"] or "").strip(),
                        "quantidade": float(row["quantidade"] or 0),
                        "unidade": (row["unidade"] or "").strip(),
                        "valor_unitario": float(row["valor_unitario"] or 0),
                        "valor_total": float(row["valor_total"] or 0),
                    }
                )
            return por_pedido
        finally:
            conn.close()
