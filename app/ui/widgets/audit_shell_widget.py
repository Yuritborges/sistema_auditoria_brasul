from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from app.core.auth import can_access
from app.ui.style import APP_STYLESHEET
from app.ui.widgets.auditoria_widget import AuditoriaWidget
from app.ui.widgets.dashboard_widget import DashboardWidget
from app.ui.widgets.fornecedores_widget import FornecedoresWidget
from app.ui.widgets.itens_widget import ItensWidget
from app.ui.widgets.locacoes_widget import LocacoesWidget
from app.ui.widgets.obras_widget import ObrasWidget
from app.ui.widgets.orcamentos_widget import OrcamentosWidget
from app.ui.widgets.pedidos_widget import PedidosWidget
from app.ui.widgets.relatorios_widget import RelatoriosWidget
from app.ui.widgets.usuarios_widget import UsuariosWidget


class AuditShellWidget(QWidget):
    MODULES = [
        ("dashboard", "Dashboard Geral"),
        ("obras", "Obras"),
        ("pedidos", "Pedidos"),
        ("itens", "Itens/Materiais"),
        ("fornecedores", "Fornecedores"),
        ("locacoes", "Locacoes"),
        ("orcamentos", "Orcamentos"),
        ("relatorios", "Relatorios"),
        ("auditoria", "Auditoria/Historico"),
        ("configuracoes", "Configuracoes"),
    ]

    def __init__(self, service):
        super().__init__()
        self.service = service
        self.profile = "PATRAO"
        self.current_user = "PATRAO"
        self._dados = []
        self._build()
        self.recarregar()

    def _build(self):
        self.setStyleSheet(APP_STYLESHEET)
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        top = QFrame()
        top.setObjectName("topbar")
        top_l = QHBoxLayout(top)
        self.lbl_title = QLabel("Sistema de Auditoria Brasul")
        self.lbl_title.setObjectName("pageTitle")
        self.lbl_subtitle = QLabel("Resumo executivo, auditoria e controle gerencial")
        self.lbl_subtitle.setObjectName("pageSubtitle")
        self.lbl_source = QLabel("Fonte: carregando...")
        self.lbl_source.setObjectName("muted")
        self.lbl_user = QLabel(f"Perfil: {self.profile} | Usuario: {self.current_user}")
        self.lbl_user.setObjectName("muted")
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.addWidget(self.lbl_title)
        text_col.addWidget(self.lbl_subtitle)
        top_l.addLayout(text_col)
        top_l.addStretch()
        top_l.addWidget(self.lbl_source)
        top_l.addWidget(self.lbl_user)
        self.btn_refresh = QPushButton("Recarregar")
        self.btn_refresh.setObjectName("secondaryButton")
        self.btn_refresh.clicked.connect(self.recarregar)
        top_l.addWidget(self.btn_refresh)
        root.addWidget(top)

        body = QHBoxLayout()
        menu_wrap = QFrame()
        menu_wrap.setObjectName("menu")
        menu_wrap.setMaximumWidth(260)
        menu_layout = QVBoxLayout(menu_wrap)
        lbl_mod = QLabel("Modulos")
        lbl_mod.setObjectName("sectionTitle")
        menu_layout.addWidget(lbl_mod)
        self.menu = QListWidget()
        self.menu.currentRowChanged.connect(self._switch)
        menu_layout.addWidget(self.menu, 1)
        body.addWidget(menu_wrap)

        self.stack = QStackedWidget()
        body.addWidget(self.stack, 1)
        root.addLayout(body, 1)

        self.w_dashboard = DashboardWidget(self.service)
        self.w_obras = ObrasWidget(self.service)
        self.w_pedidos = PedidosWidget(self.service)
        self.w_itens = ItensWidget(self.service)
        self.w_fornecedores = FornecedoresWidget(self.service)
        self.w_locacoes = LocacoesWidget()
        self.w_orcamentos = OrcamentosWidget(self.service, self._usuario)
        self.w_relatorios = RelatoriosWidget(self.service)
        self.w_auditoria = AuditoriaWidget(self.service)
        self.w_usuarios = UsuariosWidget(self.service, self._usuario)

        self.widgets_map = {
            "dashboard": self.w_dashboard,
            "obras": self.w_obras,
            "pedidos": self.w_pedidos,
            "itens": self.w_itens,
            "fornecedores": self.w_fornecedores,
            "locacoes": self.w_locacoes,
            "orcamentos": self.w_orcamentos,
            "relatorios": self.w_relatorios,
            "auditoria": self.w_auditoria,
            "configuracoes": self.w_usuarios,
        }

        self.menu_keys = []
        for key, label in self.MODULES:
            if can_access(self.profile, key):
                self.menu.addItem(QListWidgetItem(label))
                self.stack.addWidget(self.widgets_map[key])
                self.menu_keys.append(key)

        if self.menu.count():
            self.menu.setCurrentRow(0)

    def _usuario(self):
        return self.current_user

    def recarregar(self):
        try:
            dados, origem = self.service.carregar()
            self._dados = dados
            self.lbl_source.setText(origem)
            for _, widget in self.widgets_map.items():
                if hasattr(widget, "set_data"):
                    widget.set_data(self._dados)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar dados.\n\n{e}")

    def _switch(self, idx):
        if idx < 0:
            return
        self.stack.setCurrentIndex(idx)
        if idx < len(self.menu_keys):
            label = self.menu.item(idx).text()
            self.lbl_subtitle.setText(f"Modulo ativo: {label}")
