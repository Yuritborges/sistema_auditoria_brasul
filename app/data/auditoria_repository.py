import sqlite3


class AuditoriaRepository:
    def __init__(self, db_path):
        self.db_path = db_path

    def listar_pedidos(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA query_only = ON")
            conn.execute("PRAGMA temp_store = MEMORY")
            conn.execute("PRAGMA cache_size = -20000")
            rows = conn.execute(
                """
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
                    COALESCE(GROUP_CONCAT(i.descricao, ' | '), '') AS itens_texto
                FROM pedidos p
                LEFT JOIN itens_pedido i ON i.pedido_id = p.id
                GROUP BY
                    p.id,
                    p.numero,
                    p.data_pedido,
                    p.emitido_em,
                    p.obra_nome,
                    p.fornecedor_nome,
                    p.empresa_faturadora, p.condicao_pagamento, p.forma_pagamento,
                    p.valor_total, p.caminho_pdf, p.comprador
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
