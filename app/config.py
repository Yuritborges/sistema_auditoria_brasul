import os


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGOS_DIR = os.path.join(ASSETS_DIR, "logos")

# Mesma árvore do sistema de pedidos (Z:\0 OBRAS\brasul_pedidos\...).
BASE_REDE_PEDIDOS = r"Z:\0 OBRAS\brasul_pedidos"
CADASTROS_COMPARTILHADOS_DIR = os.path.join(BASE_REDE_PEDIDOS, "cadastros_compartilhados")
OBRAS_JSON_PATH = os.path.join(CADASTROS_COMPARTILHADOS_DIR, "obras.json")
FORNECEDORES_JSON_PATH = os.path.join(CADASTROS_COMPARTILHADOS_DIR, "fornecedores.json")

# Ordem de prioridade para localizar o banco consolidado (igual ao pedidos: rede + por comprador no script consolidar_rede).
DB_CANDIDATES = [
    os.environ.get("AUDITORIA_DB_PATH", "").strip(),
    os.path.join(BASE_REDE_PEDIDOS, "cotacao_rede.db"),
    os.path.join(BASE_DIR, "database", "cotacao_rede.db"),
]

# Identidade visual: PNG/SVG rasterizado não é suportado direto no QPixmap para SVG sem QtSvg — prefira PNG.
LOGO_CANDIDATES = [
    os.environ.get("AUDITORIA_LOGO_PATH", "").strip(),
    os.path.join(LOGOS_DIR, "logo_brasul.png"),
    os.path.join(LOGOS_DIR, "brasul.png"),
    os.path.join(ASSETS_DIR, "logos", "logo_brasul.png"),
    os.path.join(ASSETS_DIR, "logo_brasul.png"),
    os.path.join(ASSETS_DIR, "brasul.png"),
    os.path.join(ASSETS_DIR, "iconebrasul.png"),
    os.path.join(ASSETS_DIR, "iconebrasul2.ico"),
]


def resolve_logo_path():
    for candidate in LOGO_CANDIDATES:
        if candidate and os.path.isfile(candidate):
            return candidate
    return ""


PDF_ROOT_CANDIDATES = [
    os.environ.get("AUDITORIA_PDF_ROOT", "").strip(),
    r"Z:\0 OBRAS\00 - PEDIDO DE COMPRA",
    BASE_REDE_PEDIDOS,
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
