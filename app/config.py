import os


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGOS_DIR = os.path.join(ASSETS_DIR, "logos")

# Ordem de prioridade para localizar o banco consolidado.
DB_CANDIDATES = [
    os.environ.get("AUDITORIA_DB_PATH", "").strip(),
    r"Z:\0 OBRAS\brasul_pedidos\cotacao_rede.db",
    os.path.join(BASE_DIR, "database", "cotacao_rede.db"),
]

PDF_ROOT_CANDIDATES = [
    os.environ.get("AUDITORIA_PDF_ROOT", "").strip(),
    r"Z:\0 OBRAS\00 - PEDIDO DE COMPRA",
    r"Z:\0 OBRAS\brasul_pedidos",
    r"Z:\0 OBRAS\01 - OBRAS BRASUL",
    r"Z:\0 OBRAS\01 - OBRAS INTERIORANA",
    os.path.join(BASE_DIR, "pedidos_gerados"),
]


def resolve_db_path():
    for candidate in DB_CANDIDATES:
        if candidate and os.path.exists(candidate):
            return candidate
    return ""


def resolve_pdf_roots():
    roots = []
    for candidate in PDF_ROOT_CANDIDATES:
        if candidate and os.path.exists(candidate):
            roots.append(candidate)
    return roots


def pdf_index_cache_path():
    cache_dir = os.path.join(BASE_DIR, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, "pdf_index.json")
