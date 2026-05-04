from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.core.auth import assignable_profiles, normalize_profile
from app.ui.widgets.brasul_combo import BrasulComboBox
from app.ui.branding import scaled_logo_pixmap
from app.ui.style import APP_STYLESHEET


class UserSessionDialog(QDialog):
    def __init__(self, service, users, parent=None):
        super().__init__(parent)
        self.service = service
        self.setObjectName("loginDialog")
        self.setWindowTitle("Acesso ao Sistema")
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setStyleSheet(APP_STYLESHEET)
        self._users = users or []
        self._logged_user = ""
        self._logged_profile = "COMPRADOR"
        self._mode_new_user = False
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
        self.ed_password.textChanged.connect(self._reload_new_profile_options)
        card_l.addWidget(self.ed_password)

        self.lbl_selected = QLabel("Usuário selecionado: -")
        self.lbl_selected.setObjectName("muted")
        card_l.addWidget(self.lbl_selected)

        self.form_new = QFrame()
        self.form_new.setObjectName("panelCard")
        fn_l = QVBoxLayout(self.form_new)
        fn_l.setContentsMargins(14, 12, 14, 12)
        fn_l.setSpacing(10)
        fn_title = QLabel("Novo usuário")
        fn_title.setObjectName("sectionTitle")
        fn_l.addWidget(fn_title)
        form = QFormLayout()
        self.ed_new_user = QLineEdit()
        self.ed_new_user.setPlaceholderText("Nome do usuário")
        self.cb_new_profile = BrasulComboBox()
        self.ed_new_password = QLineEdit()
        self.ed_new_password.setEchoMode(QLineEdit.Password)
        self.ed_new_password.setPlaceholderText("Senha")
        self.ed_new_password2 = QLineEdit()
        self.ed_new_password2.setEchoMode(QLineEdit.Password)
        self.ed_new_password2.setPlaceholderText("Confirmar senha")
        self.ck_new_active = QCheckBox("Ativo")
        self.ck_new_active.setChecked(True)
        form.addRow("Usuário", self.ed_new_user)
        form.addRow("Perfil", self.cb_new_profile)
        form.addRow("Senha", self.ed_new_password)
        form.addRow("Confirmar", self.ed_new_password2)
        form.addRow("", self.ck_new_active)
        fn_l.addLayout(form)
        fn_btns = QHBoxLayout()
        fn_btns.addStretch()
        self.btn_save_new = QPushButton("Salvar usuário")
        self.btn_save_new.clicked.connect(self._register_user)
        self.btn_cancel_new = QPushButton("Fechar cadastro")
        self.btn_cancel_new.setObjectName("secondaryButton")
        self.btn_cancel_new.clicked.connect(self._toggle_new_user_form)
        fn_btns.addWidget(self.btn_cancel_new)
        fn_btns.addWidget(self.btn_save_new)
        fn_l.addLayout(fn_btns)
        self.form_new.hide()
        card_l.addWidget(self.form_new)

        row_actions = QHBoxLayout()
        self.btn_new = QPushButton("+ Novo usuário")
        self.btn_new.clicked.connect(self._toggle_new_user_form)
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setObjectName("secondaryButton")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_enter = QPushButton("Entrar")
        self.btn_enter.clicked.connect(self._accept_login)
        row_actions.addWidget(self.btn_new)
        row_actions.addWidget(self.btn_cancel)
        row_actions.addWidget(self.btn_enter)
        card_l.addLayout(row_actions)

        root.addWidget(card)

        self._reload_users()
        self._reload_new_profile_options()

    def _toggle_new_user_form(self):
        self._mode_new_user = not self._mode_new_user
        self.form_new.setVisible(self._mode_new_user)
        if self._mode_new_user:
            self._reload_new_profile_options()

    def _reload_users(self):
        self._users = self.service.listar_usuarios()
        while self.users_box.count():
            item = self.users_box.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        for user in self._users:
            nome = (user.get("nome") or "").strip().upper()
            perfil = normalize_profile(user.get("perfil") or "COMPRADOR")
            ativo = int(user.get("ativo", 1)) == 1
            if not nome or not ativo:
                continue
            btn = QPushButton(nome.title())
            btn.setObjectName("userTileButton")
            btn.clicked.connect(lambda _=False, n=nome, p=perfil: self._select_user(n, p))
            self.users_box.addWidget(btn)

        if self.users_box.count() == 0:
            self._select_user("ADMIN", "ADMIN")
        else:
            first = self._users[0]
            self._select_user((first.get("nome") or "ADMIN").strip().upper(), normalize_profile(first.get("perfil") or "COMPRADOR"))

    def _select_user(self, nome, perfil):
        self._logged_user = nome
        self._logged_profile = normalize_profile(perfil)
        self.lbl_selected.setText(f"Usuário selecionado: {nome.title()}  •  Perfil: {self._logged_profile}")
        self._reload_new_profile_options()
        self.ed_password.setFocus()

    def _reload_new_profile_options(self):
        self.cb_new_profile.clear()
        allow_admin = not self.service.existe_admin()
        if self._is_logged_admin_authenticated():
            allow_admin = True
            operator_profile = "ADMIN"
        else:
            operator_profile = "COMPRADOR"
        self.cb_new_profile.addItems(assignable_profiles(operator_profile, allow_admin=allow_admin))

    def _is_logged_admin_authenticated(self):
        if self._logged_profile != "ADMIN":
            return False
        senha = self.ed_password.text() or ""
        if not senha:
            return False
        return self.service.autenticar_usuario(self._logged_user, senha)

    def _register_user(self):
        nome = self.ed_new_user.text().strip().upper()
        if not nome:
            QMessageBox.warning(self, "Usuário", "Informe o nome do usuário.")
            return
        senha = self.ed_new_password.text()
        senha2 = self.ed_new_password2.text()
        if not senha or len(senha) < 4:
            QMessageBox.warning(self, "Senha", "A senha deve ter pelo menos 4 caracteres.")
            return
        if senha != senha2:
            QMessageBox.warning(self, "Senha", "As senhas não conferem.")
            return
        perfil = normalize_profile(self.cb_new_profile.currentText())
        ativo = self.ck_new_active.isChecked()

        allow_admin_bootstrap = not self.service.existe_admin()
        admin_auth = self._is_logged_admin_authenticated()
        if not allow_admin_bootstrap and not admin_auth:
            QMessageBox.warning(self, "Permissão", "Somente ADMIN autenticado pode cadastrar usuários.")
            return
        if perfil == "ADMIN" and not (allow_admin_bootstrap or admin_auth):
            QMessageBox.warning(self, "Permissão", "Somente ADMIN autenticado pode cadastrar outro ADMIN.")
            return

        self.service.salvar_usuario_com_senha(nome, perfil, ativo, senha, self._logged_user or "SISTEMA")
        self.ed_new_user.clear()
        self.ed_new_password.clear()
        self.ed_new_password2.clear()
        self._reload_users()
        self._reload_new_profile_options()
        self._mode_new_user = False
        self.form_new.hide()
        QMessageBox.information(self, "Usuário", f"Usuário {nome.title()} cadastrado.")

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
