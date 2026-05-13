import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from app.core.auth import normalize_profile
from app.ui.branding import scaled_logo_pixmap
from app.ui.style import APP_STYLESHEET


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
        self._build()

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
        pix = scaled_logo_pixmap(160, 54)
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
        self.ed_password.textChanged.connect(self._on_password_edited)
        card_l.addWidget(self.ed_password)

        self.lbl_hint = QLabel("")
        self.lbl_hint.setObjectName("loginHint")
        self.lbl_hint.setWordWrap(True)
        card_l.addWidget(self.lbl_hint)

        self.lbl_error = QLabel("")
        self.lbl_error.setObjectName("loginError")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.hide()
        card_l.addWidget(self.lbl_error)

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
        # Esc fecha o diálogo por padrão; usuários costumam apertar Esc para “apagar” a senha
        # e o app encerrava sem explicação (AuditShellWidget chama quit se o login falhar).
        if event.key() == Qt.Key.Key_Escape:
            if (self.ed_password.text() or "").strip():
                self.ed_password.clear()
                self.lbl_error.hide()
                event.accept()
                return
        super().keyPressEvent(event)

    def reject(self):
        logging.getLogger(__name__).info("Login encerrado sem sucesso (Cancelar, Esc ou fechar janela).")
        super().reject()

    def _on_password_edited(self, _t):
        try:
            self.lbl_error.hide()
        except Exception:
            logging.getLogger(__name__).exception("Falha ao atualizar estado do campo de senha")

    def _atualizar_dica_senha(self):
        if not self._logged_user:
            self.lbl_hint.setText("")
            return
        if self.service.usuario_tem_senha(self._logged_user):
            self.lbl_hint.setText(
                "Digite sua senha e clique em Entrar. (Esc limpa a senha; não fecha o programa enquanto houver texto.)"
            )
        else:
            self.lbl_hint.setText(
                "Primeiro acesso para este usuário: digite a senha que deseja usar "
                "(mínimo 4 caracteres) e clique em Entrar — ela será salva e usada daqui em diante. "
                "Esc limpa o campo sem encerrar, se já houver texto."
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
        self.lbl_selected.setText(f"Usuário selecionado: {nome.title()}  •  Perfil: {self._logged_profile}")
        self.lbl_error.hide()
        self._atualizar_dica_senha()
        self.ed_password.clear()
        self.ed_password.setFocus()

    def _accept_login(self):
        log = logging.getLogger(__name__)
        self.lbl_error.hide()
        try:
            if not self._logged_user:
                self.lbl_error.setText("Selecione um usuário (botão acima).")
                self.lbl_error.show()
                return
            senha = self.ed_password.text()
            if not self.service.usuario_tem_senha(self._logged_user):
                if not senha or len(senha) < 4:
                    self.lbl_error.setText("A senha deve ter pelo menos 4 caracteres.")
                    self.lbl_error.show()
                    self.ed_password.setFocus()
                    return
                self.service.definir_senha_usuario(self._logged_user, senha, self._logged_user)
                self.accept()
                return
            if not self.service.autenticar_usuario(self._logged_user, senha):
                self.lbl_error.setText(
                    "Senha incorreta. Confira Caps Lock e tente de novo.\n"
                    "Esqueceu? Peça ao TI ou use: python tools/reset_admin_password.py --limpar"
                )
                self.lbl_error.show()
                self.ed_password.selectAll()
                self.ed_password.setFocus()
                return
            self.accept()
        except Exception as e:
            log.exception("Falha ao autenticar")
            self.lbl_error.setText(
                "Erro ao gravar ou validar a senha (detalhes em logs/auditoria_app.log).\n\n"
                f"{type(e).__name__}: {e}\n\n"
                "Verifique permissão de escrita na pasta do programa (database/)."
            )
            self.lbl_error.show()
            self.ed_password.setFocus()

    def selected(self):
        return self._logged_user or "ADMIN", normalize_profile(self._logged_profile)
