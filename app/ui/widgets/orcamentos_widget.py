from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class OrcamentosWidget(QWidget):
    def __init__(self, service, usuario_getter):
        super().__init__()
        self.service = service
        self.usuario_getter = usuario_getter
        self._dados = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        title = QLabel("Orcamentos e Alertas")
        title.setObjectName("sectionTitle")
        root.addWidget(title)
        self.lbl_info = QLabel("Obras carregadas da base do Sistema de Pedidos; campo Previsto pode ser ajustado aqui.")
        self.lbl_info.setObjectName("muted")
        root.addWidget(self.lbl_info)
        top = QHBoxLayout()
        self.ed_obra = QLineEdit()
        self.ed_obra.setPlaceholderText("Nome da obra")
        self.ed_prev = QLineEdit()
        self.ed_prev.setPlaceholderText("Valor previsto")
        btn = QPushButton("Salvar orcamento")
        btn.clicked.connect(self._salvar)
        top.addWidget(self.ed_obra, 2)
        top.addWidget(self.ed_prev, 1)
        top.addWidget(btn)
        root.addLayout(top)

        self.tbl = QTableWidget(0, 6)
        self.tbl.setHorizontalHeaderLabels(["Obra", "Previsto", "Gasto", "Saldo", "Consumo", "Alerta"])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.horizontalHeader().setStretchLastSection(False)
        self.tbl.setColumnWidth(0, 280)
        self.tbl.setColumnWidth(1, 110)
        self.tbl.setColumnWidth(2, 110)
        self.tbl.setColumnWidth(3, 110)
        self.tbl.setColumnWidth(4, 90)
        self.tbl.setColumnWidth(5, 90)
        root.addWidget(self.tbl, 1)

        self.tbl_alertas = QTableWidget(0, 2)
        self.tbl_alertas.setHorizontalHeaderLabels(["Tipo", "Descricao"])
        self.tbl_alertas.verticalHeader().setVisible(False)
        self.tbl_alertas.setAlternatingRowColors(True)
        self.tbl_alertas.horizontalHeader().setStretchLastSection(False)
        self.tbl_alertas.setColumnWidth(0, 120)
        self.tbl_alertas.setColumnWidth(1, 700)
        root.addWidget(QLabel("Alertas automaticos"), 0)
        root.addWidget(self.tbl_alertas, 1)

    def set_data(self, dados):
        self._dados = dados
        self._refresh()

    def _salvar(self):
        obra = self.ed_obra.text().strip()
        try:
            valor = float((self.ed_prev.text() or "0").replace(".", "").replace(",", "."))
        except Exception:
            QMessageBox.warning(self, "Valor invalido", "Informe um valor numerico valido.")
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
            self.tbl.setRowHeight(i, 28)
            vals = [r["obra"], self._fmt(r["previsto"]), self._fmt(r["gasto"]), self._fmt(r["saldo"]), f"{r['consumo']:.1f}%", r["alerta"]]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if c > 0:
                    it.setTextAlignment(Qt.AlignCenter)
                self.tbl.setItem(i, c, it)

        alerts = self.service.alertas_automaticos(self._dados)
        self.tbl_alertas.setRowCount(0)
        for i, (tipo, desc) in enumerate(alerts):
            self.tbl_alertas.insertRow(i)
            self.tbl_alertas.setRowHeight(i, 26)
            self.tbl_alertas.setItem(i, 0, QTableWidgetItem(tipo))
            self.tbl_alertas.setItem(i, 1, QTableWidgetItem(desc))

    def _fmt(self, v):
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
