from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.core.auth import PERMISSIONS_BY_PROFILE


class UsuariosWidget(QWidget):
    def __init__(self, service, usuario_getter):
        super().__init__()
        self.service = service
        self.usuario_getter = usuario_getter
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        title = QLabel("Usuarios e Permissoes")
        title.setObjectName("sectionTitle")
        root.addWidget(title)
        top = QHBoxLayout()
        self.ed_nome = QLineEdit()
        self.ed_nome.setPlaceholderText("Nome")
        self.cb_perfil = QComboBox()
        self.cb_perfil.addItems(sorted(PERMISSIONS_BY_PROFILE.keys()))
        self.ck_ativo = QCheckBox("Ativo")
        self.ck_ativo.setChecked(True)
        btn = QPushButton("Salvar usuario")
        btn.clicked.connect(self._salvar)
        top.addWidget(self.ed_nome, 2)
        top.addWidget(self.cb_perfil, 1)
        top.addWidget(self.ck_ativo)
        top.addWidget(btn)
        root.addLayout(top)
        self.tbl = QTableWidget(0, 4)
        self.tbl.setHorizontalHeaderLabels(["Nome", "Perfil", "Ativo", "Permissoes"])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.horizontalHeader().setStretchLastSection(False)
        self.tbl.setColumnWidth(0, 140)
        self.tbl.setColumnWidth(1, 120)
        self.tbl.setColumnWidth(2, 70)
        self.tbl.setColumnWidth(3, 620)
        root.addWidget(self.tbl, 1)

    def set_data(self, _dados):
        self.refresh()

    def _salvar(self):
        nome = self.ed_nome.text().strip().upper()
        if not nome:
            return
        perfil = self.cb_perfil.currentText().strip().upper()
        ativo = self.ck_ativo.isChecked()
        self.service.salvar_usuario(nome, perfil, ativo, self.usuario_getter())
        self.ed_nome.clear()
        self.refresh()

    def refresh(self):
        users = self.service.listar_usuarios()
        self.tbl.setRowCount(0)
        for i, u in enumerate(users):
            self.tbl.insertRow(i)
            self.tbl.setRowHeight(i, 26)
            perms = ", ".join(sorted(PERMISSIONS_BY_PROFILE.get((u.get("perfil") or "").upper(), set())))
            vals = [
                u.get("nome", ""),
                u.get("perfil", ""),
                "SIM" if int(u.get("ativo", 0)) == 1 else "NAO",
                perms,
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(str(v))
                if c == 2:
                    it.setTextAlignment(Qt.AlignCenter)
                self.tbl.setItem(i, c, it)
