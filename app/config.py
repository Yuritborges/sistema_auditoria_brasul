import os
import sys


def _resolve_base_dir():
    # No .exe (PyInstaller), gravar dados ao lado do executável (persistente), não em pasta temporária.
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(__file__))


BASE_DIR = _resolve_base_dir()


def _resolve_assets_dir():
    """Pasta assets: dev em ./assets; no .exe PyInstaller pode ser sys._MEIPASS/assets ou ./_internal/assets."""
    if not getattr(sys, "frozen", False):
        return os.path.abspath(os.path.join(BASE_DIR, "assets"))
    candidates = []
    meipass = getattr(sys, "_MEIPASS", None) or ""
    if meipass:
        candidates.append(os.path.join(meipass, "assets"))
    candidates.append(os.path.join(BASE_DIR, "_internal", "assets"))
    candidates.append(os.path.join(BASE_DIR, "assets"))
    marker = "iconebrasul2.ico"
    for c in candidates:
        if c and os.path.isfile(os.path.join(c, marker)):
            return os.path.abspath(c)
    for c in candidates:
        if c and os.path.isdir(c):
            return os.path.abspath(c)
    return os.path.abspath(os.path.join(BASE_DIR, "assets"))


ASSETS_DIR = _resolve_assets_dir()
LOGOS_DIR = os.path.join(ASSETS_DIR, "logos")


def resolve_app_icon_path():
    """Arquivo de ícone para QApplication / janela (caminho absoluto)."""
    for name in ("iconebrasul2.ico", "iconebrasul.png"):
        p = os.path.join(ASSETS_DIR, name)
        if os.path.isfile(p):
            return os.path.abspath(p)
    p = os.path.join(LOGOS_DIR, "logo_brasul.png")
    if os.path.isfile(p):
        return os.path.abspath(p)
    return ""

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
