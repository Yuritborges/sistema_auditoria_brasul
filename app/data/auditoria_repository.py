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
                    p.numero,
                    p.data_pedido,
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
                    p.id, p.numero, p.data_pedido, p.obra_nome, p.fornecedor_nome,
                    p.empresa_faturadora, p.condicao_pagamento, p.forma_pagamento,
                    p.valor_total, p.caminho_pdf, p.comprador
                ORDER BY p.emitido_em DESC, p.id DESC
                """
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
