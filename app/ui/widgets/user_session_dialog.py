from PySide6.QtCore import Qt
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
from app.ui.branding import scaled_logo_pixmap
from app.ui.style import APP_STYLESHEET


class UserSessionDialog(QDialog):
    def __init__(self, service, users, parent=None):
        super().__init__(parent)
        self.service = service
        self.setObjectName("loginDialog")
        self.setWindowTitle("Acesso ao Sistema")
        # Janela top-level para aparecer na barra de tarefas do Windows.
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
        subtitle = QLabel("Selecione o usuário para iniciar")
        subtitle.setObjectName("muted")
        subtitle.setAlignment(Qt.AlignCenter)
        card_l.addWidget(title)
        card_l.addWidget(subtitle)

        self.users_box = QVBoxLayout()
        self.users_box.setSpacing(10)
        card_l.addLayout(self.users_box)

        self.ed_password = QLineEdit()
        self.ed_password.setEchoMode(QLineEdit.Password)
        self.ed_password.setPlaceholderText("Senha")
        self.ed_password.returnPressed.connect(self._accept_login)
        card_l.addWidget(self.ed_password)

        self.lbl_selected = QLabel("Usuário selecionado: -")
        self.lbl_selected.setObjectName("muted")
        card_l.addWidget(self.lbl_selected)

        row_actions = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setObjectName("secondaryButton")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_enter = QPushButton("Entrar")
        self.btn_enter.clicked.connect(self._accept_login)
        row_actions.addStretch()
        row_actions.addWidget(self.btn_cancel)
        row_actions.addWidget(self.btn_enter)
        card_l.addLayout(row_actions)

        root.addWidget(card)

        self._reload_users()

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
        self.ed_password.setFocus()

    def _accept_login(self):
        if not self._logged_user:
            QMessageBox.warning(self, "Acesso", "Selecione um usuário.")
            return
        senha = self.ed_password.text()
        if not self.service.usuario_tem_senha(self._logged_user):
            if not senha or len(senha) < 4:
                QMessageBox.warning(self, "Primeiro acesso", "Defina uma senha com ao menos 4 caracteres.")
                return
            self.service.definir_senha_usuario(self._logged_user, senha, self._logged_user)
            QMessageBox.information(self, "Senha definida", "Senha criada com sucesso para este usuário.")
            self.accept()
            return
        if not self.service.autenticar_usuario(self._logged_user, senha):
            QMessageBox.warning(self, "Acesso", "Usuário/senha inválidos.")
            return
        self.accept()


    def selected(self):
        return self._logged_user or "ADMIN", normalize_profile(self._logged_profile)
