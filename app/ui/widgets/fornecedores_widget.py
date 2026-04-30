from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class FornecedoresWidget(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self._dados = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        title = QLabel("Auditoria por Fornecedor")
        title.setObjectName("sectionTitle")
        root.addWidget(title)
        top = QHBoxLayout()
        self.cb = QComboBox()
        btn = QPushButton("Analisar")
        btn.clicked.connect(self._analisar)
        top.addWidget(QLabel("Fornecedor"))
        top.addWidget(self.cb, 1)
        top.addWidget(btn)
        root.addLayout(top)
        self.lbl_stats = QLabel("Total: R$ 0,00 | Pedidos: 0 | Obras: 0 | Ultima compra: -")
        root.addWidget(self.lbl_stats)
        self.tbl = QTableWidget(0, 6)
        self.tbl.setHorizontalHeaderLabels(["Pedido", "Data", "Obra", "Empresa", "Valor", "Status"])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.horizontalHeader().setStretchLastSection(False)
        self.tbl.setColumnWidth(0, 70)
        self.tbl.setColumnWidth(1, 90)
        self.tbl.setColumnWidth(2, 200)
        self.tbl.setColumnWidth(3, 90)
        self.tbl.setColumnWidth(4, 100)
        self.tbl.setColumnWidth(5, 90)
        root.addWidget(self.tbl, 1)

    def set_data(self, dados):
        self._dados = dados
        fornecedores = sorted({(d.get("fornecedor_nome") or "").strip() for d in dados if (d.get("fornecedor_nome") or "").strip()})
        self.cb.clear()
        self.cb.addItems(fornecedores)
        self._analisar()

    def _analisar(self):
        fornecedor = self.cb.currentText()
        res = self.service.fornecedor_auditoria(self._dados, fornecedor)
        self.lbl_stats.setText(
            f"Total: {self._fmt(res.get('total', 0))} | Pedidos: {res.get('qtd_pedidos', 0)} | "
            f"Obras: {res.get('obras', 0)} | Ultima compra: {res.get('ultima_compra', '-')}"
        )
        rows = res.get("rows") or []
        self.tbl.setRowCount(0)
        for i, r in enumerate(rows):
            self.tbl.insertRow(i)
            self.tbl.setRowHeight(i, 28)
            vals = [
                str(r.get("numero") or ""),
                str(r.get("data_pedido") or ""),
                str(r.get("obra_nome") or ""),
                str(r.get("empresa_faturadora") or ""),
                self._fmt(r.get("valor_total")),
                str(r.get("status_auditoria") or ""),
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if c in (0, 1, 4, 5):
                    it.setTextAlignment(Qt.AlignCenter)
                self.tbl.setItem(i, c, it)

    def _fmt(self, v):
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
