from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.auth import PERMISSIONS_BY_PROFILE, assignable_profiles, normalize_profile
from app.ui.widgets.brasul_combo import BrasulComboBox


class UsuariosWidget(QWidget):
    def __init__(self, service, usuario_getter, perfil_getter):
        super().__init__()
        self.service = service
        self.usuario_getter = usuario_getter
        self.perfil_getter = perfil_getter
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        hero = QVBoxLayout()
        hero.setSpacing(4)
        ht = QLabel("Usuários e permissões")
        ht.setObjectName("moduleHeroTitle")
        hd = QLabel(
            "Cadastro local de perfis. Clique na linha do usuário para selecionar; use Perfil para alterar função ou "
            "Remover selecionado para excluir (não é possível remover o último ADMIN ativo)."
        )
        hd.setObjectName("moduleHeroDesc")
        hero.addWidget(ht)
        hero.addWidget(hd)
        root.addLayout(hero)

        form_card = QFrame()
        form_card.setObjectName("panelCard")
        top = QHBoxLayout(form_card)
        top.setContentsMargins(16, 14, 16, 14)
        top.setSpacing(12)
        self.ed_nome = QLineEdit()
        self.ed_nome.setPlaceholderText("Nome")
        self.cb_perfil = BrasulComboBox()
        self._refresh_perfis()
        self.ed_senha = QLineEdit()
        self.ed_senha.setEchoMode(QLineEdit.Password)
        self.ed_senha.setPlaceholderText("Nova senha (opcional)")
        self.ed_senha2 = QLineEdit()
        self.ed_senha2.setEchoMode(QLineEdit.Password)
        self.ed_senha2.setPlaceholderText("Confirmar senha")
        self.ck_ativo = QCheckBox("Ativo")
        self.ck_ativo.setChecked(True)
        btn = QPushButton("Salvar usuário")
        btn.clicked.connect(self._salvar)
        btn_del = QPushButton("Remover selecionado")
        btn_del.setObjectName("secondaryButton")
        btn_del.clicked.connect(self._remover_selecionado)
        top.addWidget(self.ed_nome, 2)
        top.addWidget(self.cb_perfil, 1)
        top.addWidget(self.ed_senha, 1)
        top.addWidget(self.ed_senha2, 1)
        top.addWidget(self.ck_ativo)
        top.addWidget(btn)
        top.addWidget(btn_del)
        root.addWidget(form_card)

        tbl_card = QFrame()
        tbl_card.setObjectName("panelCard")
        tbl_l = QVBoxLayout(tbl_card)
        tbl_l.setContentsMargins(12, 12, 12, 12)
        self.tbl = QTableWidget(0, 4)
        self.tbl.setHorizontalHeaderLabels(["Nome", "Perfil", "Ativo", "Permissões"])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setShowGrid(False)
        self.tbl.setFocusPolicy(Qt.ClickFocus)
        self.tbl.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.horizontalHeader().setStretchLastSection(True)
        self.tbl.setColumnWidth(0, 148)
        self.tbl.setColumnWidth(1, 168)
        self.tbl.setColumnWidth(2, 80)
        tbl_l.addWidget(self.tbl)
        root.addWidget(tbl_card, 1)

    def set_data(self, _dados):
        self._refresh_perfis()
        self.refresh()

    def _refresh_perfis(self):
        current = self.cb_perfil.currentText() if hasattr(self, "cb_perfil") else ""
        perfis = assignable_profiles(self.perfil_getter())
        self.cb_perfil.clear()
        self.cb_perfil.addItems(perfis)
        if current:
            idx = self.cb_perfil.findText(normalize_profile(current))
            if idx >= 0:
                self.cb_perfil.setCurrentIndex(idx)

    def _salvar(self):
        nome = self.ed_nome.text().strip().upper()
        if not nome:
            return
        perfil = normalize_profile(self.cb_perfil.currentText())
        ativo = self.ck_ativo.isChecked()
        if not self.service.pode_atribuir_perfil(self.perfil_getter(), perfil):
            QMessageBox.warning(self, "Permissão", "Seu perfil não pode atribuir esse nível de acesso.")
            return
        senha = self.ed_senha.text()
        senha2 = self.ed_senha2.text()
        if senha or senha2:
            if len(senha) < 4:
                QMessageBox.warning(self, "Senha", "A senha deve ter pelo menos 4 caracteres.")
                return
            if senha != senha2:
                QMessageBox.warning(self, "Senha", "As senhas não conferem.")
                return
            self.service.salvar_usuario_com_senha(nome, perfil, ativo, senha, self.usuario_getter())
        else:
            self.service.salvar_usuario(nome, perfil, ativo, self.usuario_getter())
        self.ed_nome.clear()
        self.ed_senha.clear()
        self.ed_senha2.clear()
        self.refresh()

    def refresh(self):
        users = self.service.listar_usuarios()
        perfis_opts = assignable_profiles(self.perfil_getter())
        self.tbl.setRowCount(0)
        for i, u in enumerate(users):
            self.tbl.insertRow(i)
            self.tbl.setRowHeight(i, 38)
            nome_display = str(u.get("nome") or "").strip()
            nome_key = nome_display.upper()
            perfil = normalize_profile(u.get("perfil"))
            perms = ", ".join(sorted(PERMISSIONS_BY_PROFILE.get(perfil, set())))

            it_nome = QTableWidgetItem(nome_display or nome_key)
            self.tbl.setItem(i, 0, it_nome)

            cb = BrasulComboBox()
            cb.setProperty("usuario_nome", nome_key)
            cb.addItems(perfis_opts)
            if perfil not in perfis_opts:
                cb.addItem(perfil)
            ix = cb.findText(perfil)
            cb.blockSignals(True)
            cb.setCurrentIndex(ix if ix >= 0 else 0)
            cb.blockSignals(False)
            cb.currentIndexChanged.connect(self._on_row_perfil_changed)
            cb.installEventFilter(self)
            self.tbl.setCellWidget(i, 1, cb)

            it_ativo = QTableWidgetItem("SIM" if int(u.get("ativo", 0)) == 1 else "NÃO")
            it_ativo.setTextAlignment(Qt.AlignCenter)
            self.tbl.setItem(i, 2, it_ativo)

            it_perm = QTableWidgetItem(perms)
            self.tbl.setItem(i, 3, it_perm)

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.FocusIn):
            for r in range(self.tbl.rowCount()):
                if self.tbl.cellWidget(r, 1) is obj:
                    self.tbl.selectRow(r)
                    self.tbl.setCurrentCell(r, 0)
                    break
        return super().eventFilter(obj, event)

    def _on_row_perfil_changed(self, _idx):
        combo = self.sender()
        if combo is None:
            return
        nome = (combo.property("usuario_nome") or "").strip().upper()
        if not nome:
            return
        novo = normalize_profile(combo.currentText())
        row_user = next(
            (x for x in self.service.listar_usuarios() if (x.get("nome") or "").strip().upper() == nome),
            None,
        )
        if not row_user:
            return
        atual = normalize_profile(row_user.get("perfil"))
        ativo = int(row_user.get("ativo", 0)) == 1
        if novo == atual:
            return
        if not self.service.pode_atribuir_perfil(self.perfil_getter(), novo):
            QMessageBox.warning(self, "Permissão", "Seu perfil não pode atribuir esse nível de acesso.")
            combo.blockSignals(True)
            ri = combo.findText(atual)
            combo.setCurrentIndex(ri if ri >= 0 else 0)
            combo.blockSignals(False)
            return
        self.service.salvar_usuario(nome, novo, ativo, self.usuario_getter())
        self.refresh()

    def _remover_selecionado(self):
        row = self.tbl.currentRow()
        rows = self.tbl.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
        if row < 0:
            QMessageBox.warning(
                self,
                "Remoção",
                "Selecione uma linha na tabela (clique no nome, na permissão ou no combo de perfil) antes de remover.",
            )
            return
        nome_item = self.tbl.item(row, 0)
        if not nome_item:
            QMessageBox.warning(self, "Remoção", "Usuário inválido.")
            return
        nome = (nome_item.text() or "").strip().upper()
        ok, msg = self.service.remover_usuario(nome, self.usuario_getter(), self.perfil_getter())
        if ok:
            QMessageBox.information(self, "Remoção", msg)
            self.refresh()
        else:
            QMessageBox.warning(self, "Remoção", msg)
