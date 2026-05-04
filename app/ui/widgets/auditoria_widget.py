from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class AuditoriaWidget(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        head = QHBoxLayout()
        head.setSpacing(16)
        hero = QVBoxLayout()
        hero.setSpacing(4)
        ht = QLabel("Histórico de alterações")
        ht.setObjectName("moduleHeroTitle")
        hd = QLabel("Trilha local de inclusões e ajustes (orçamentos, usuários e demais entidades).")
        hd.setObjectName("moduleHeroDesc")
        hero.addWidget(ht)
        hero.addWidget(hd)
        head.addLayout(hero, 1)
        btn = QPushButton("Atualizar histórico")
        btn.setObjectName("secondaryButton")
        btn.clicked.connect(self.refresh)
        head.addWidget(btn, 0, Qt.AlignTop)
        root.addLayout(head)

        tbl_card = QFrame()
        tbl_card.setObjectName("panelCard")
        tbl_l = QVBoxLayout(tbl_card)
        tbl_l.setContentsMargins(12, 12, 12, 12)
        self.tbl = QTableWidget(0, 8)
        self.tbl.setHorizontalHeaderLabels(
            ["Data/Hora", "Usuário", "Entidade", "ID", "Ação", "Campo", "Anterior", "Novo"]
        )
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setShowGrid(False)
        self.tbl.setFocusPolicy(Qt.NoFocus)
        self.tbl.horizontalHeader().setStretchLastSection(True)
        self.tbl.setColumnWidth(0, 136)
        self.tbl.setColumnWidth(1, 96)
        self.tbl.setColumnWidth(2, 112)
        self.tbl.setColumnWidth(3, 88)
        self.tbl.setColumnWidth(4, 88)
        self.tbl.setColumnWidth(5, 120)
        tbl_l.addWidget(self.tbl)
        root.addWidget(tbl_card, 1)

    def set_data(self, _dados):
        self.refresh()

    def refresh(self):
        logs = self.service.listar_logs(limit=1000)
        self.tbl.setRowCount(0)
        for i, l in enumerate(logs):
            self.tbl.insertRow(i)
            self.tbl.setRowHeight(i, 30)
            vals = [
                l.get("data_hora", ""),
                l.get("usuario", ""),
                l.get("entidade", ""),
                l.get("entidade_id", ""),
                l.get("acao", ""),
                l.get("campo", ""),
                l.get("valor_anterior", ""),
                l.get("valor_novo", ""),
            ]
            for c, v in enumerate(vals):
                self.tbl.setItem(i, c, QTableWidgetItem(str(v)))
