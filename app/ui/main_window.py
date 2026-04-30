from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow
from app.services.auditoria_service import AuditoriaService
from app.ui.widgets.audit_shell_widget import AuditShellWidget
import os


class MainWindowPatrao(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sistema de Auditoria Brasul")
        self.resize(1500, 900)

        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        icon_candidates = [
            os.path.join(base, "assets", "iconebrasul2.ico"),
            os.path.join(base, "assets", "iconebrasul.png"),
            os.path.join(base, "assets", "logos", "logo_brasul.png"),
        ]
        for icon_path in icon_candidates:
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                break

        self.setStyleSheet("""
            QMainWindow {
                background: #f3f5f8;
            }
        """)

        service = AuditoriaService()
        self.setCentralWidget(AuditShellWidget(service))