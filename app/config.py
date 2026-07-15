import os
import sys

from app.rede_paths import DEFAULT_BASE_REDE_SUFFIX, resolver_base_rede_dir


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
    """Arquivo .ico para janela e barra de tarefas (somente ICO — PNG não serve bem no Windows)."""
    ico_names = ("iconebrasul2.ico",)

    def _first_existing(*paths):
        for p in paths:
            if p and os.path.isfile(p):
                return os.path.abspath(p)
        return ""

    if getattr(sys, "frozen", False):
        asset_roots = []
        meipass = getattr(sys, "_MEIPASS", None) or ""
        if meipass:
            asset_roots.append(os.path.join(meipass, "assets"))
        asset_roots.extend(
            [
                os.path.join(BASE_DIR, "_internal", "assets"),
                os.path.join(BASE_DIR, "assets"),
            ]
        )
        for root in asset_roots:
            for name in ico_names:
                found = _first_existing(os.path.join(root, name))
                if found:
                    return found
        return ""

    for name in ico_names:
        found = _first_existing(os.path.join(ASSETS_DIR, name), os.path.join(LOGOS_DIR, name))
        if found:
            return found
    return ""

# Mesma árvore do sistema de pedidos — detecta Z:, Y:, mapeamento novo e UNC
# (ver app/rede_paths.py).
BASE_REDE_PEDIDOS = resolver_base_rede_dir()
_OBRAS_ROOT = os.path.dirname(BASE_REDE_PEDIDOS)
CADASTROS_COMPARTILHADOS_DIR = os.path.join(BASE_REDE_PEDIDOS, "cadastros_compartilhados")
OBRAS_JSON_PATH = os.path.join(CADASTROS_COMPARTILHADOS_DIR, "obras.json")
FORNECEDORES_JSON_PATH = os.path.join(CADASTROS_COMPARTILHADOS_DIR, "fornecedores.json")

# Ordem de prioridade para localizar o banco consolidado (igual ao pedidos: rede + por comprador no script consolidar_rede).
DB_CANDIDATES = [
    os.environ.get("AUDITORIA_DB_PATH", "").strip(),
    os.path.join(BASE_REDE_PEDIDOS, "cotacao_rede.db"),
    os.path.join(BASE_DIR, "database", "cotacao_rede.db"),
]

# Logo na interface (login, menu, topo): PNG horizontal BRASUL CONSTRUTORA — não usar o ícone quadrado.
LOGO_CANDIDATES = [
    os.environ.get("AUDITORIA_LOGO_PATH", "").strip(),
    os.path.join(LOGOS_DIR, "logo_brasul.png"),
    os.path.join(ASSETS_DIR, "logos", "logo_brasul.png"),
]


def resolve_logo_path():
    """Somente logo horizontal (logo_brasul.png). Ícone quadrado é só .ico na barra do Windows."""
    explicit = (os.environ.get("AUDITORIA_LOGO_PATH") or "").strip()
    if explicit and os.path.isfile(explicit):
        return os.path.abspath(explicit)
    for candidate in LOGO_CANDIDATES:
        if not candidate or not os.path.isfile(candidate):
            continue
        if "logo_brasul" in os.path.basename(candidate).lower():
            return os.path.abspath(candidate)
    return ""


PDF_ROOT_CANDIDATES = [
    os.environ.get("AUDITORIA_PDF_ROOT", "").strip(),
    os.path.join(_OBRAS_ROOT, "00 - PEDIDO DE COMPRA"),
    BASE_REDE_PEDIDOS,
    os.path.join(_OBRAS_ROOT, "01 - OBRAS BRASUL"),
    os.path.join(_OBRAS_ROOT, "01 - OBRAS INTERIORANA"),
    os.path.join(BASE_DIR, "pedidos_gerados"),
]


def resolve_db_path():
    for candidate in DB_CANDIDATES:
        if candidate and os.path.exists(candidate):
            return candidate
    return ""


# Ao clicar «Recarregar dados» (carregar force=True), copiar o .db para ficheiro temporário local
# antes do SQLite abrir — reduz leituras «fantasma» do ficheiro antigo em pastas de rede (SMB).
AUDITORIA_DB_COPY_ON_FORCE_RELOAD = os.environ.get(
    "AUDITORIA_DB_COPY_ON_FORCE_RELOAD", "1"
).strip().lower() in ("1", "true", "sim", "yes")

# Polling silencioso da UI (ms). 0 desativa. Ver AuditShellWidget._auto_recarregar.
# Padrão 20 s: alinhado ao incremental do pedidos (cotacao_rede.db); só relê se mtime/size mudou.
AUDITORIA_AUTO_RELOAD_MS_DEFAULT = 20_000

# Consolida Iury+Thamyres → cotacao_rede.db quando defasado (0 = só pelo botão manual).
# Padrão 2 min — evita disputar lock com o timer do sistema de pedidos (300 s).
AUDITORIA_AUTO_CONSOLIDAR_MS_DEFAULT = 120_000

# Cada tick do timer chama carregar(force=True): copia o consolidado para ficheiro local
# antes de abrir (respeita AUDITORIA_DB_COPY_ON_FORCE_RELOAD). Em pastas de rede (SMB)
# o ficheiro cotacao_rede.db pode ser atualizado pelo sistema de pedidos e a auditoria
# ainda «ver» dados antigos com invalidate + force=False — isto alinha com «tempo real».
# Desative com AUDITORIA_AUTO_RELOAD_FORCE=0 se o .db for muito grande e o intervalo curto.
AUDITORIA_AUTO_RELOAD_FORCE = os.environ.get(
    "AUDITORIA_AUTO_RELOAD_FORCE", "1"
).strip().lower() in ("1", "true", "sim", "yes")


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


def _python_for_consolidar_subprocess():
    """Intérprete para correr consolidar_rede.py em subprocesso.

    Com a aplicação empacotada (PyInstaller), ``sys.executable`` é o próprio .exe da
    auditoria — usá-lo como «Python» relança a GUI (novo login / segunda janela).
    """
    explicit = (os.environ.get("AUDITORIA_CONSOLIDAR_PYTHON") or "").strip()
    if explicit and os.path.isfile(explicit):
        return os.path.abspath(explicit)
    if not getattr(sys, "frozen", False):
        return sys.executable
    ob = _OBRAS_ROOT
    for folder in ("sistema_de_pedidos_brasulv2", "sistema_de_pedidos_brasul", "sistema_auditoria_brasul"):
        cand = os.path.join(ob, folder, ".venv", "Scripts", "python.exe")
        if os.path.isfile(cand):
            return os.path.abspath(cand)
    return ""


def resolve_consolidar_argv():
    """[python, consolidar_rede.py] para atualizar cotacao_rede.db; None se o ficheiro não existir.

    AUDITORIA_CONSOLIDAR_SCRIPT — caminho absoluto do consolidar_rede.py (opcional).
    AUDITORIA_CONSOLIDAR_PYTHON — intérprete a usar (obrigatório em .exe se não existir
        .venv\\Scripts\\python.exe em sistema_de_pedidos_brasulv2 ou sistema_auditoria_brasul).
    """
    py = _python_for_consolidar_subprocess()
    script = os.environ.get("AUDITORIA_CONSOLIDAR_SCRIPT", "").strip()
    if script and os.path.isfile(script):
        if not py:
            return None
        return [py, os.path.abspath(script)]
    ob = _OBRAS_ROOT
    for folder in ("sistema_de_pedidos_brasulv2", "sistema_de_pedidos_brasul"):
        cand = os.path.join(ob, folder, "tools", "consolidar_rede.py")
        if os.path.isfile(cand):
            if not py:
                return None
            return [py, os.path.abspath(cand)]
    return None
