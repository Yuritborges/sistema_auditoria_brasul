from PySide6.QtWidgets import QApplication, QMainWindow

from app.config import resolve_app_icon_path
from app.ui.app_icon import criar_icone_aplicativo
from app.ui.win_icon import aplicar_icone_janela_win32
from app.services.auditoria_service import AuditoriaService
from app.ui.widgets.audit_shell_widget import AuditShellWidget


class MainWindowPatrao(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sistema de Auditoria Brasul")
        self.resize(1500, 900)

        ic = criar_icone_aplicativo()
        if not ic.isNull():
            self.setWindowIcon(ic)

        self.setStyleSheet("""
            QMainWindow {
                background: #f4f5f7;
            }
        """)

        self.service = AuditoriaService()
        self.audit_shell = AuditShellWidget(self.service)
        self.setCentralWidget(self.audit_shell)

    def showEvent(self, event):
        super().showEvent(event)
        # Windows: reforça o ícone na barra de tarefas após a janela nativa existir (evita ícone genérico).
        ic = criar_icone_aplicativo()
        path = resolve_app_icon_path()
        if not ic.isNull():
            self.setWindowIcon(ic)
            app = QApplication.instance()
            if app is not None:
                app.setWindowIcon(ic)
        if path:
            aplicar_icone_janela_win32(self, path)

    def closeEvent(self, event):
        try:
            self.service.shutdown()
        except Exception:
            pass
        super().closeEvent(event)