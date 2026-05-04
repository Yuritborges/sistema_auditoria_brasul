from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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


class OrcamentosWidget(QWidget):
    def __init__(self, service, usuario_getter):
        super().__init__()
        self.service = service
        self.usuario_getter = usuario_getter
        self._dados = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        hero = QVBoxLayout()
        hero.setSpacing(4)
        ht = QLabel("Orçamentos e alertas")
        ht.setObjectName("moduleHeroTitle")
        hd = QLabel("Compare previsto x gasto por obra e acompanhe alertas automáticos da base.")
        hd.setObjectName("moduleHeroDesc")
        hero.addWidget(ht)
        hero.addWidget(hd)
        root.addLayout(hero)

        info_card = QFrame()
        info_card.setObjectName("panelCard")
        il = QVBoxLayout(info_card)
        il.setContentsMargins(16, 12, 16, 12)
        self.lbl_info = QLabel(
            "Obras carregadas a partir da base do sistema de pedidos; o valor previsto pode ser ajustado aqui e fica registrado na auditoria."
        )
        self.lbl_info.setObjectName("muted")
        self.lbl_info.setWordWrap(True)
        il.addWidget(self.lbl_info)
        root.addWidget(info_card)

        form_card = QFrame()
        form_card.setObjectName("panelCard")
        top = QHBoxLayout(form_card)
        top.setContentsMargins(16, 14, 16, 14)
        top.setSpacing(12)
        self.ed_obra = QLineEdit()
        self.ed_obra.setPlaceholderText("Nome da obra")
        self.ed_prev = QLineEdit()
        self.ed_prev.setPlaceholderText("Valor previsto")
        btn = QPushButton("Salvar orçamento")
        btn.clicked.connect(self._salvar)
        top.addWidget(self.ed_obra, 2)
        top.addWidget(self.ed_prev, 1)
        top.addWidget(btn)
        root.addWidget(form_card)

        tbl_card = QFrame()
        tbl_card.setObjectName("panelCard")
        tbl_l = QVBoxLayout(tbl_card)
        tbl_l.setContentsMargins(12, 12, 12, 12)
        self.tbl = QTableWidget(0, 6)
        self.tbl.setHorizontalHeaderLabels(["Obra", "Previsto", "Gasto", "Saldo", "Consumo", "Alerta"])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setShowGrid(False)
        self.tbl.setFocusPolicy(Qt.NoFocus)
        self.tbl.horizontalHeader().setStretchLastSection(False)
        self.tbl.setColumnWidth(0, 280)
        self.tbl.setColumnWidth(1, 112)
        self.tbl.setColumnWidth(2, 112)
        self.tbl.setColumnWidth(3, 112)
        self.tbl.setColumnWidth(4, 96)
        self.tbl.setColumnWidth(5, 100)
        tbl_l.addWidget(self.tbl)
        root.addWidget(tbl_card, 1)

        alert_head = QHBoxLayout()
        ah = QLabel("Alertas automáticos")
        ah.setObjectName("sectionTitle")
        alert_head.addWidget(ah)
        alert_head.addStretch()
        root.addLayout(alert_head)

        alert_card = QFrame()
        alert_card.setObjectName("panelCard")
        al = QVBoxLayout(alert_card)
        al.setContentsMargins(12, 12, 12, 12)
        self.tbl_alertas = QTableWidget(0, 2)
        self.tbl_alertas.setHorizontalHeaderLabels(["Tipo", "Descrição"])
        self.tbl_alertas.verticalHeader().setVisible(False)
        self.tbl_alertas.setAlternatingRowColors(True)
        self.tbl_alertas.setShowGrid(False)
        self.tbl_alertas.setFocusPolicy(Qt.NoFocus)
        self.tbl_alertas.horizontalHeader().setStretchLastSection(True)
        self.tbl_alertas.setColumnWidth(0, 140)
        al.addWidget(self.tbl_alertas)
        root.addWidget(alert_card, 1)

    def set_data(self, dados):
        self._dados = dados
        self._refresh()

    def _salvar(self):
        obra = self.ed_obra.text().strip()
        try:
            valor = float((self.ed_prev.text() or "0").replace(".", "").replace(",", "."))
        except Exception:
            QMessageBox.warning(self, "Valor inválido", "Informe um valor numérico válido.")
            return
        if not obra:
            QMessageBox.warning(self, "Obra", "Informe a obra.")
            return
        self.service.salvar_orcamento(obra, valor, self.usuario_getter())
        self.ed_prev.clear()
        self._refresh()

    def _refresh(self):
        rows = self.service.listar_orcamentos_com_consumo(self._dados)
        self.tbl.setRowCount(0)
        for i, r in enumerate(rows):
            self.tbl.insertRow(i)
            self.tbl.setRowHeight(i, 32)
            vals = [
                r["obra"],
                self._fmt(r["previsto"]),
                self._fmt(r["gasto"]),
                self._fmt(r["saldo"]),
                f"{r['consumo']:.1f}%",
                r["alerta"],
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if c > 0:
                    it.setTextAlignment(Qt.AlignCenter)
                self.tbl.setItem(i, c, it)

        alerts = self.service.alertas_automaticos(self._dados)
        self.tbl_alertas.setRowCount(0)
        for i, (tipo, desc) in enumerate(alerts):
            self.tbl_alertas.insertRow(i)
            self.tbl_alertas.setRowHeight(i, 30)
            self.tbl_alertas.setItem(i, 0, QTableWidgetItem(tipo))
            self.tbl_alertas.setItem(i, 1, QTableWidgetItem(desc))

    def _fmt(self, v):
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
