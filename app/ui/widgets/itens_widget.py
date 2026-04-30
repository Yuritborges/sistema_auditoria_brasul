from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class ItensWidget(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self._dados = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        title = QLabel("Auditoria por Item/Material")
        title.setObjectName("sectionTitle")
        root.addWidget(title)
        top = QHBoxLayout()
        self.ed_item = QLineEdit()
        self.ed_item.setPlaceholderText("Buscar item/material (ex: cimento)")
        btn = QPushButton("Auditar")
        btn.clicked.connect(self._auditar)
        top.addWidget(self.ed_item, 1)
        top.addWidget(btn)
        root.addLayout(top)

        self.lbl_stats = QLabel("Qtd: 0 | Obras: 0 | Preco medio: R$ 0,00 | Min: R$ 0,00 | Max: R$ 0,00")
        root.addWidget(self.lbl_stats)

        self.tbl = QTableWidget(0, 5)
        self.tbl.setHorizontalHeaderLabels(["Item", "Obra", "Fornecedor", "Valor", "Data"])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.horizontalHeader().setStretchLastSection(False)
        self.tbl.setColumnWidth(0, 290)
        self.tbl.setColumnWidth(1, 180)
        self.tbl.setColumnWidth(2, 180)
        self.tbl.setColumnWidth(3, 100)
        self.tbl.setColumnWidth(4, 90)
        root.addWidget(self.tbl, 1)

    def set_data(self, dados):
        self._dados = dados
        self._auditar()

    def _auditar(self):
        termo = self.ed_item.text()
        res = self.service.item_auditoria(self._dados, termo)
        st = res.get("stats") or {}
        self.lbl_stats.setText(
            f"Qtd: {st.get('qtd', 0)} | Obras: {st.get('obras', 0)} | "
            f"Preco medio: {self._fmt(st.get('preco_medio', 0))} | "
            f"Min: {self._fmt(st.get('preco_min', 0))} | Max: {self._fmt(st.get('preco_max', 0))} | "
            f"Fornecedor barato: {st.get('fornecedor_mais_barato', '-')}"
        )
        rows = res.get("rows") or []
        self.tbl.setRowCount(0)
        for i, r in enumerate(rows):
            self.tbl.insertRow(i)
            self.tbl.setRowHeight(i, 28)
            vals = [r["item"], r["obra"], r["fornecedor"], self._fmt(r["valor"]), r["data"]]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if c in (3, 4):
                    it.setTextAlignment(Qt.AlignCenter)
                self.tbl.setItem(i, c, it)

    def _fmt(self, v):
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
