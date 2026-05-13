import logging
import os

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config import AUDITORIA_AUTO_RELOAD_MS_DEFAULT, resolve_consolidar_argv
from app.core.auth import PERMISSIONS_BY_PROFILE, can_access, normalize_profile
from app.ui.branding import logo_label_compact, logo_label_sidebar
from app.ui.style import APP_STYLESHEET
from app.ui.widgets.auditoria_widget import AuditoriaWidget
from app.ui.widgets.conciliacao_widget import ConciliacaoWidget
from app.ui.widgets.contratos_widget import ContratosWidget
from app.ui.widgets.dashboard_widget import DashboardWidget
from app.ui.widgets.fiscalizacao_widget import FiscalizacaoWidget
from app.ui.widgets.fornecedores_widget import FornecedoresWidget
from app.ui.widgets.itens_widget import ItensWidget
from app.ui.widgets.medicoes_widget import MedicoesWidget
from app.ui.widgets.obras_widget import ObrasWidget
from app.ui.widgets.pedidos_widget import PedidosWidget
from app.ui.widgets.relatorios_widget import RelatoriosWidget
from app.ui.widgets.user_session_dialog import UserSessionDialog
from app.ui.widgets.usuarios_widget import UsuariosWidget


class AuditShellWidget(QWidget):
    AUTO_RELOAD_MS = AUDITORIA_AUTO_RELOAD_MS_DEFAULT
    MODULES = [
        ("dashboard", "Dashboard Geral"),
        ("obras", "Obras"),
        ("pedidos", "Pedidos"),
        ("itens", "Itens/Materiais"),
        ("fornecedores", "Fornecedores"),
        ("relatorios", "Relatórios"),
        ("auditoria", "Auditoria/Histórico"),
        ("contratos", "Contratos"),
        ("medicoes", "Medições"),
        ("conciliacao", "Conciliação"),
        ("fiscalizacao", "Fiscalização"),
        ("configuracoes", "Configurações"),
    ]

    def __init__(self, service):
        super().__init__()
        self.service = service
        self._dados = []
        self._widget_data_version = {}
        self._data_version = 0

        # Sessão sempre exige autenticação por diálogo (sem bypass automático por ambiente).
        raw_prof = (os.environ.get("AUDITORIA_PERFIL") or "COMPRADOR").strip().upper()
        self.profile = normalize_profile(raw_prof)
        if self.profile not in PERMISSIONS_BY_PROFILE:
            self.profile = "COMPRADOR"
        raw_user = ""
        self.current_user = raw_user or self.profile
        if not self._ask_session_user():
            QTimer.singleShot(0, self._quit_app)
            return
        self._build()
        self._auto_reload_timer = QTimer(self)
        self._auto_reload_timer.timeout.connect(self._auto_recarregar)
        try:
            reload_ms = int(
                (os.environ.get("AUDITORIA_AUTO_RELOAD_MS") or str(self.AUTO_RELOAD_MS)).strip()
            )
        except ValueError:
            reload_ms = self.AUTO_RELOAD_MS
        if reload_ms > 0:
            self._auto_reload_timer.setInterval(reload_ms)
            self._auto_reload_timer.start()
        QTimer.singleShot(0, lambda: self.recarregar(force=False))

    def _sincronizar_pedidos_rede(self):
        if not resolve_consolidar_argv():
            QMessageBox.warning(
                self,
                "Consolidação",
                "Não foi encontrado tools/consolidar_rede.py no sistema de pedidos.\n"
                "Defina AUDITORIA_CONSOLIDAR_SCRIPT (caminho absoluto do .py).",
            )
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            ok, err = self.service.sincronizar_consolidado_pedidos()
            if ok:
                self.recarregar(force=True)
            else:
                QMessageBox.warning(self, "Consolidação", err or "Falha desconhecida.")
        finally:
            QApplication.restoreOverrideCursor()

    def _ask_session_user(self):
        log = logging.getLogger(__name__)
        dlg = None
        try:
            users = self.service.listar_usuarios()
            dlg = UserSessionDialog(self.service, users, None)
            if dlg.exec() != QDialog.Accepted:
                return False
            user, profile = dlg.selected()
            self.current_user = user
            self.profile = normalize_profile(profile)
            return True
        except Exception as e:
            log.exception("Falha no diálogo de sessão")
            QMessageBox.critical(
                dlg,
                "Erro de acesso",
                "Não foi possível concluir o login.\n\n"
                f"{type(e).__name__}: {e}\n\n"
                "Veja logs/auditoria_app.log para o detalhe completo.",
            )
            return False

    def _quit_app(self):
        app = QApplication.instance()
        if app:
            app.quit()

    def _build(self):
        self.setStyleSheet(APP_STYLESHEET)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(268)
        side_l = QVBoxLayout(self.sidebar)
        side_l.setContentsMargins(14, 20, 14, 18)
        side_l.setSpacing(16)

        self.logo_sidebar = logo_label_sidebar(self.sidebar)
        if self.logo_sidebar:
            side_l.addWidget(self.logo_sidebar)

        brand_box = QVBoxLayout()
        brand_box.setSpacing(4)
        self.lbl_brand = QLabel("Brasul")
        self.lbl_brand.setObjectName("sidebarBrand")
        self.lbl_tagline = QLabel("Auditoria & compras")
        self.lbl_tagline.setObjectName("sidebarTagline")
        if self.logo_sidebar:
            brand_box.addWidget(self.lbl_tagline)
        else:
            brand_box.addWidget(self.lbl_brand)
            brand_box.addWidget(self.lbl_tagline)
        side_l.addLayout(brand_box)

        lbl_mod = QLabel("Módulos")
        lbl_mod.setObjectName("sectionTitle")
        side_l.addWidget(lbl_mod)

        self.menu = QListWidget()
        self.menu.setObjectName("navMenu")
        self.menu.setSpacing(2)
        self.menu.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.menu.currentRowChanged.connect(self._switch)
        side_l.addWidget(self.menu, 1)

        self.btn_refresh = QPushButton("Recarregar dados")
        self.btn_refresh.setObjectName("secondaryButton")
        self.btn_refresh.clicked.connect(lambda: self.recarregar(force=True))
        side_l.addWidget(self.btn_refresh)

        self.btn_sync_pedidos = QPushButton("Atualizar pedidos (rede)")
        self.btn_sync_pedidos.setObjectName("secondaryButton")
        self.btn_sync_pedidos.setToolTip(
            "Executa a consolidação do sistema de pedidos para o ficheiro cotacao_rede.db e volta a carregar."
        )
        self.btn_sync_pedidos.clicked.connect(self._sincronizar_pedidos_rede)
        side_l.addWidget(self.btn_sync_pedidos)

        root.addWidget(self.sidebar)

        self.content_host = QWidget()
        self.content_host.setObjectName("contentHost")
        content_outer = QVBoxLayout(self.content_host)
        content_outer.setContentsMargins(18, 18, 18, 18)
        content_outer.setSpacing(14)

        top = QFrame()
        top.setObjectName("topbar")
        top_l = QHBoxLayout(top)
        top_l.setContentsMargins(18, 14, 18, 14)
        top_l.setSpacing(14)

        self.lbl_title = QLabel("Sistema de Auditoria Brasul")
        self.lbl_title.setObjectName("pageTitle")
        self.lbl_subtitle = QLabel("Resumo executivo, auditoria e controle gerencial")
        self.lbl_subtitle.setObjectName("pageSubtitle")
        self.lbl_source = QLabel("Fonte: carregando...")
        self.lbl_source.setObjectName("muted")
        self.lbl_source.setWordWrap(True)
        self.lbl_user = QLabel(f"Perfil: {self.profile}  •  Usuário: {self.current_user}")
        self.lbl_user.setObjectName("muted")

        head_row = QHBoxLayout()
        head_row.setSpacing(14)
        self.logo_topbar = logo_label_compact(top)
        if self.logo_topbar:
            head_row.addWidget(self.logo_topbar, 0, Qt.AlignVCenter | Qt.AlignLeft)
        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        text_col.addWidget(self.lbl_title)
        text_col.addWidget(self.lbl_subtitle)
        head_row.addLayout(text_col, 1)
        top_l.addLayout(head_row, 1)

        meta_col = QVBoxLayout()
        meta_col.setSpacing(6)
        meta_col.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        meta_col.addWidget(self.lbl_source, 0, Qt.AlignRight)
        meta_col.addWidget(self.lbl_user, 0, Qt.AlignRight)
        top_l.addLayout(meta_col)

        content_outer.addWidget(top)

        self.stack = QStackedWidget()
        content_outer.addWidget(self.stack, 1)

        root.addWidget(self.content_host, 1)

        # Carregamento preguiçoso dos módulos: cria widget só quando o usuário abre.
        self.widget_factories = {
            "dashboard": lambda: DashboardWidget(self.service),
            "obras": lambda: ObrasWidget(self.service),
            "pedidos": lambda: PedidosWidget(self.service),
            "itens": lambda: ItensWidget(self.service),
            "fornecedores": lambda: FornecedoresWidget(self.service),
            "relatorios": lambda: RelatoriosWidget(self.service),
            "auditoria": lambda: AuditoriaWidget(self.service),
            "contratos": lambda: ContratosWidget(self.service, self._usuario),
            "medicoes": lambda: MedicoesWidget(self.service, self._usuario),
            "conciliacao": lambda: ConciliacaoWidget(self.service, self._usuario),
            "fiscalizacao": lambda: FiscalizacaoWidget(self.service, self._usuario),
            "configuracoes": lambda: UsuariosWidget(self.service, self._usuario, self._perfil),
        }
        self.widgets_map = {}
        self.placeholders = {}
        self.stack_index_by_key = {}

        self.menu_keys = []
        for key, label in self.MODULES:
            if can_access(self.profile, key):
                self.menu.addItem(QListWidgetItem(label))
                holder = QWidget()
                self.stack.addWidget(holder)
                self.placeholders[key] = holder
                self.stack_index_by_key[key] = self.stack.indexOf(holder)
                self.menu_keys.append(key)

        if self.menu.count():
            self.menu.setCurrentRow(0)
            self._ensure_widget(self.menu_keys[0])

    def _ensure_widget(self, key):
        if key in self.widgets_map:
            return self.widgets_map[key]
        widget = self.widget_factories[key]()
        placeholder = self.placeholders.get(key)
        idx = self.stack_index_by_key.get(key, -1)
        if placeholder is not None and idx >= 0:
            self.stack.insertWidget(idx, widget)
            self.stack.removeWidget(placeholder)
            placeholder.deleteLater()
            self.placeholders.pop(key, None)
        if key == "dashboard":
            widget.abrir_modulo_obras.connect(self._navegar_obras)
        self.widgets_map[key] = widget
        return widget

    def _navegar_obras(self, obra: str):
        if "obras" not in self.menu_keys:
            return
        idx = self.menu_keys.index("obras")
        self.menu.setCurrentRow(idx)
        widget = self._ensure_widget("obras")
        self.stack.setCurrentWidget(widget)
        self.lbl_subtitle.setText(f"Módulo ativo · {self.menu.item(idx).text()}")
        widget.focus_obra(obra)

    def _usuario(self):
        return self.current_user

    def _perfil(self):
        return self.profile

    def recarregar(self, force=False):
        try:
            dados, origem = self.service.carregar(force=force)
            self._dados = dados
            self._data_version += 1
            self._widget_data_version = {}
            self.lbl_source.setText(origem)
            self._push_data_to_current_widget()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar dados.\n\n{e}")

    def _push_data_to_current_widget(self):
        idx = self.menu.currentRow()
        if idx < 0 or idx >= len(self.menu_keys):
            return
        key = self.menu_keys[idx]
        widget = self._ensure_widget(key)
        if self.stack.currentWidget() is not widget:
            self.stack.setCurrentWidget(widget)
        if hasattr(widget, "set_data") and self._widget_data_version.get(key) != self._data_version:
            widget.set_data(self._dados)
            self._widget_data_version[key] = self._data_version

    def _switch(self, idx):
        if idx < 0:
            return
        if idx < len(self.menu_keys):
            key = self.menu_keys[idx]
            widget = self._ensure_widget(key)
            self.stack.setCurrentWidget(widget)
            label = self.menu.item(idx).text()
            self.lbl_subtitle.setText(f"Módulo ativo · {label}")
            self._push_data_to_current_widget()

    def _auto_recarregar(self):
        # Atualização periódica: sem invalidar, carregar(False) devolve só a cache se mtime/size
        # do .db na rede não mudou — comum em SMB mesmo com INSERT já consolidados.
        self.service.invalidate_consolidated_cache()
        self.recarregar(force=False)
