"""
Sistema de Auditoria Brasul — ponto de entrada da aplicação.

Autoria / manutenção principal: Marlyson Iury T Borges
"""
import sys
import os
import ctypes
import logging
from logging.handlers import RotatingFileHandler

# Barra de tarefas do Windows: ID fixo antes de importar Qt (igual ao sistema de pedidos).
if sys.platform.startswith("win"):
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "brasul.sistema.auditoria"
        )
    except Exception:
        pass

from PySide6.QtWidgets import QApplication
from app.config import resolve_app_icon_path
from app.ui.app_icon import criar_icone_aplicativo
from app.ui.main_window import MainWindowPatrao
from app.ui.style import APP_STYLESHEET
from app.ui.win_icon import aplicar_icone_janela_win32


def _aplicar_icone(app, janela=None):
    ic = criar_icone_aplicativo()
    if not ic.isNull():
        app.setWindowIcon(ic)
        if janela is not None:
            janela.setWindowIcon(ic)
    return ic


def _configure_logging():
    base = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base, "logs")
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, "auditoria_app.log")
    handler = RotatingFileHandler(path, maxBytes=1_500_000, backupCount=4, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    handler.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not root.handlers:
        root.addHandler(handler)


def main():
    _configure_logging()
    log = logging.getLogger(__name__)

    if sys.platform.startswith("win"):
        try:
            from app.confiar_rede_windows import aplicar_se_necessario
            from app.rede_paths import resolver_base_rede_dir

            aplicar_se_necessario(resolver_base_rede_dir())
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("SistemaAuditoriaBrasul")
    app.setApplicationDisplayName("Sistema de Auditoria Brasul")
    app.setOrganizationName("Brasul")
    # Fusion aplica melhor QSS no Windows (barras de rolagem legíveis, menos artefatos visuais).
    app.setStyle("Fusion")
    # Aplica identidade visual global (inclui popups/combobox/messagebox).
    app.setStyleSheet(APP_STYLESHEET)
    win = MainWindowPatrao()
    ic = _aplicar_icone(app, win)
    if ic.isNull():
        log.warning(
            "Icone .ico nao carregado (ver assets/iconebrasul2.ico e _internal/assets no .exe)."
        )
    win.show()
    ic_path = resolve_app_icon_path()
    _aplicar_icone(app, win)
    if ic_path:
        aplicar_icone_janela_win32(win, ic_path)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()