import sys
import os
import ctypes
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindowPatrao


def _icone_app_path():
    base = os.path.dirname(os.path.abspath(__file__))
    candidatos = [
        os.path.join(base, "assets", "iconebrasul2.ico"),
        os.path.join(base, "assets", "iconebrasul.png"),
        os.path.join(base, "assets", "logos", "logo_brasul.png"),
    ]
    return next((p for p in candidatos if os.path.exists(p)), "")


def main():
    # Garante icone proprio na barra de tarefas do Windows.
    if sys.platform.startswith("win"):
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "brasul.sistema.auditoria"
            )
        except Exception:
            pass

    app = QApplication(sys.argv)
    icon_path = _icone_app_path()
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))
    win = MainWindowPatrao()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()