from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow

from app.config import resolve_app_icon_path
from app.services.auditoria_service import AuditoriaService
from app.ui.widgets.audit_shell_widget import AuditShellWidget


class MainWindowPatrao(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sistema de Auditoria Brasul")
        self.resize(1500, 900)

        icon_path = resolve_app_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet("""
            QMainWindow {
                background: #f1f5f9;
            }
        """)

        self.service = AuditoriaService()
        self.audit_shell = AuditShellWidget(self.service)
        self.setCentralWidget(self.audit_shell)

    def closeEvent(self, event):
        try:
            self.service.shutdown()
        except Exception:
            pass
        super().closeEvent(event)