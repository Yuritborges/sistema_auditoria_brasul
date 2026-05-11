import sys
import os
import ctypes
import logging
from logging.handlers import RotatingFileHandler
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from app.config import resolve_app_icon_path
from app.ui.main_window import MainWindowPatrao
from app.ui.style import APP_STYLESHEET


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
    # Garante icone proprio na barra de tarefas do Windows.
    if sys.platform.startswith("win"):
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "brasul.sistema.auditoria"
            )
        except Exception:
            logging.getLogger(__name__).exception("Falha ao configurar AppUserModelID do Windows")

    app = QApplication(sys.argv)
    # Fusion aplica melhor QSS no Windows (barras de rolagem legíveis, menos artefatos visuais).
    app.setStyle("Fusion")
    # Aplica identidade visual global (inclui popups/combobox/messagebox).
    app.setStyleSheet(APP_STYLESHEET)
    icon_path = resolve_app_icon_path()
    if icon_path:
        ic = QIcon(icon_path)
        app.setWindowIcon(ic)
    win = MainWindowPatrao()
    if icon_path:
        win.setWindowIcon(QIcon(icon_path))
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()