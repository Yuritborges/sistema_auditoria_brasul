import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.core.auth import normalize_profile
from app.ui.app_icon import criar_icone_aplicativo
from app.ui.branding import scaled_logo_pixmap
from app.ui.win_icon import aplicar_icone_janela_win32
from app.config import resolve_app_icon_path
from app.ui.style import APP_STYLESHEET

_MSG_SENHA_INCORRETA = "A senha foi digitada incorretamente."

_ESTILO_HINT_OK = ""
_ESTILO_HINT_ERRO = (
    "color: #9b1c1c;"
    "font-size: 13px;"
    "font-weight: 700;"
    "background: #fef2f2;"
    "border: 1px solid #fecaca;"
    "border-radius: 8px;"
    "padding: 10px 12px;"
)


class UserSessionDialog(QDialog):
    def __init__(self, service, users, parent=None):
        super().__init__(parent)
        self.service = service
        self.setObjectName("loginDialog")
        self.setWindowTitle("Acesso ao Sistema")
        self.setWindowFlag(Qt.Window, True)
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setStyleSheet(APP_STYLESHEET)
        self._users = users or []
        self._logged_user = ""
        self._logged_profile = "COMPRADOR"
        self._login_em_andamento = False
        ic = criar_icone_aplicativo()
        if not ic.isNull():
            self.setWindowIcon(ic)
        self._build()

    def showEvent(self, event):
        super().showEvent(event)
        path = resolve_app_icon_path()
        if path:
            aplicar_icone_janela_win32(self, path)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)

        card = QFrame()
        card.setObjectName("loginCard")
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(22, 20, 22, 20)
        card_l.setSpacing(14)

        logo = QLabel()
        logo.setObjectName("loginLogo")
        pix = scaled_logo_pixmap(300, 72)
        if pix is not None:
            logo.setPixmap(pix)
        else:
            logo.setText("BRASUL")
            logo.setObjectName("sidebarBrand")
        logo.setAlignment(Qt.AlignCenter)
        card_l.addWidget(logo)

        title = QLabel("Sistema de Auditoria")
        title.setObjectName("loginTitle")
        title.setAlignment(Qt.AlignCenter)
        self.subtitle = QLabel("Selecione o usuário e informe a senha")
        self.subtitle.setObjectName("muted")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setWordWrap(True)
        card_l.addWidget(title)
        card_l.addWidget(self.subtitle)

        self.users_box = QVBoxLayout()
        self.users_box.setSpacing(10)
        card_l.addLayout(self.users_box)

        self.ed_password = QLineEdit()
        self.ed_password.setEchoMode(QLineEdit.Password)
        self.ed_password.setPlaceholderText("Senha")
        self.ed_password.returnPressed.connect(self._accept_login)
        card_l.addWidget(self.ed_password)

        self.lbl_hint = QLabel("")
        self.lbl_hint.setObjectName("loginHint")
        self.lbl_hint.setWordWrap(True)
        self.lbl_hint.setAlignment(Qt.AlignCenter)
        self.lbl_hint.setMinimumHeight(32)
        card_l.addWidget(self.lbl_hint)

        self.lbl_selected = QLabel("Usuário selecionado: -")
        self.lbl_selected.setObjectName("muted")
        card_l.addWidget(self.lbl_selected)

        row_actions = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setObjectName("secondaryButton")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_enter = QPushButton("Entrar")
        self.btn_enter.setDefault(True)
        self.btn_enter.setAutoDefault(True)
        self.btn_cancel.setAutoDefault(False)
        self.btn_enter.clicked.connect(self._accept_login)
        row_actions.addStretch()
        row_actions.addWidget(self.btn_cancel)
        row_actions.addWidget(self.btn_enter)
        card_l.addLayout(row_actions)

        root.addWidget(card)

        self._reload_users()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            if (self.ed_password.text() or "").strip():
                self.ed_password.clear()
                self._limpar_erro_login()
                event.accept()
                return
        super().keyPressEvent(event)

    def reject(self):
        logging.getLogger(__name__).info("Login encerrado sem sucesso (Cancelar, Esc ou fechar janela).")
        super().reject()

    def _mostrar_erro(self, texto: str, alerta_modal: bool = False):
        self.lbl_hint.setStyleSheet(_ESTILO_HINT_ERRO)
        self.lbl_hint.setText(texto)
        self.lbl_hint.show()
        self.lbl_hint.raise_()
        if alerta_modal:
            QMessageBox.warning(self, "Acesso negado", texto)
        self.ed_password.setFocus()

    def _limpar_erro_login(self):
        self.lbl_hint.setStyleSheet(_ESTILO_HINT_OK)
        self._atualizar_dica_senha()

    def _atualizar_dica_senha(self):
        if not self._logged_user:
            self.lbl_hint.setText("")
            return
        if self.service.usuario_tem_senha(self._logged_user):
            self.lbl_hint.setText("Digite sua senha e clique em Entrar.")
        else:
            self.lbl_hint.setText(
                "Primeiro acesso: escolha uma senha com no mínimo 4 caracteres e clique em Entrar. "
                "Ela ficará registrada para os próximos acessos."
            )

    def _reload_users(self):
        self._users = self.service.listar_usuarios()
        while self.users_box.count():
            item = self.users_box.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        first_active = None
        for user in self._users:
            nome = (user.get("nome") or "").strip().upper()
            perfil = normalize_profile(user.get("perfil") or "COMPRADOR")
            ativo = int(user.get("ativo", 1)) == 1
            if not nome or not ativo:
                continue
            if first_active is None:
                first_active = (nome, perfil)
            btn = QPushButton(nome.title())
            btn.setObjectName("userTileButton")
            btn.clicked.connect(lambda _=False, n=nome, p=perfil: self._select_user(n, p))
            self.users_box.addWidget(btn)

        if first_active is None:
            self._select_user("ADMIN", "ADMIN")
        else:
            self._select_user(first_active[0], first_active[1])

    def _select_user(self, nome, perfil):
        self._logged_user = nome
        self._logged_profile = normalize_profile(perfil)
        self.lbl_selected.setText(f"Usuário selecionado: {nome.title()}")
        self.ed_password.clear()
        self._limpar_erro_login()
        self.ed_password.setFocus()

    def _accept_login(self):
        if self._login_em_andamento:
            return
        self._login_em_andamento = True
        log = logging.getLogger(__name__)
        try:
            if not self._logged_user:
                self._mostrar_erro("Selecione um usuário (botão acima).", alerta_modal=True)
                return
            senha = self.ed_password.text()
            if not self.service.usuario_tem_senha(self._logged_user):
                if not senha or len(senha) < 4:
                    self._mostrar_erro("A senha deve ter pelo menos 4 caracteres.", alerta_modal=True)
                    return
                self._limpar_erro_login()
                self.service.definir_senha_usuario(self._logged_user, senha, self._logged_user)
                self.accept()
                return
            if not (senha or "").strip():
                self._mostrar_erro("Digite sua senha.", alerta_modal=True)
                return
            if not self.service.autenticar_usuario(self._logged_user, senha):
                log.info("Login recusado: senha incorreta para %s", self._logged_user)
                self._mostrar_erro(_MSG_SENHA_INCORRETA, alerta_modal=True)
                return
            self._limpar_erro_login()
            self.accept()
        except Exception:
            log.exception("Falha ao autenticar")
            self._mostrar_erro(
                "Não foi possível validar o acesso. Tente novamente ou peça ajuda ao suporte.",
                alerta_modal=True,
            )
        finally:
            self._login_em_andamento = False

    def selected(self):
        return self._logged_user or "ADMIN", normalize_profile(self._logged_profile)
