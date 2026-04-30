from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class ObrasWidget(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self._dados = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        title = QLabel("Consulta por Obra")
        title.setObjectName("sectionTitle")
        root.addWidget(title)

        card = QFrame()
        card.setObjectName("panelCard")
        c_layout = QVBoxLayout(card)
        filtros = QGridLayout()
        self.cb_obra = QComboBox()
        self.ed_fornecedor = QLineEdit()
        self.ed_fornecedor.setPlaceholderText("Fornecedor...")
        self.ed_item = QLineEdit()
        self.ed_item.setPlaceholderText("Material/item...")
        self.ed_comprador = QLineEdit()
        self.ed_comprador.setPlaceholderText("Comprador...")
        self.ed_periodo = QLineEdit()
        self.ed_periodo.setPlaceholderText("Periodo (dd/mm/aaaa-dd/mm/aaaa)")
        btn = QPushButton("Aplicar")
        btn.clicked.connect(self._aplicar)
        filtros.addWidget(QLabel("Obra"), 0, 0)
        filtros.addWidget(self.cb_obra, 0, 1)
        filtros.addWidget(QLabel("Fornecedor"), 0, 2)
        filtros.addWidget(self.ed_fornecedor, 0, 3)
        filtros.addWidget(QLabel("Item"), 1, 0)
        filtros.addWidget(self.ed_item, 1, 1)
        filtros.addWidget(QLabel("Comprador"), 1, 2)
        filtros.addWidget(self.ed_comprador, 1, 3)
        filtros.addWidget(QLabel("Periodo"), 2, 0)
        filtros.addWidget(self.ed_periodo, 2, 1, 1, 2)
        filtros.addWidget(btn, 2, 3)
        c_layout.addLayout(filtros)
        root.addWidget(card)

        kpis = QHBoxLayout()
        self.lbl_total = QLabel("Valor total: R$ 0,00")
        self.lbl_qtd = QLabel("Pedidos: 0")
        kpis.addWidget(self.lbl_total)
        kpis.addWidget(self.lbl_qtd)
        kpis.addStretch()
        root.addLayout(kpis)

        self.tbl = QTableWidget(0, 8)
        self.tbl.setHorizontalHeaderLabels(["Pedido", "Data", "Fornecedor", "Comprador", "Empresa", "Valor", "Status", "PDF"])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.horizontalHeader().setStretchLastSection(False)
        self.tbl.setColumnWidth(0, 70)
        self.tbl.setColumnWidth(1, 90)
        self.tbl.setColumnWidth(2, 160)
        self.tbl.setColumnWidth(3, 95)
        self.tbl.setColumnWidth(4, 90)
        self.tbl.setColumnWidth(5, 100)
        self.tbl.setColumnWidth(6, 95)
        self.tbl.setColumnWidth(7, 80)
        root.addWidget(self.tbl, 1)

    def set_data(self, dados):
        self._dados = dados
        obras = sorted({(d.get("obra_nome") or "").strip() for d in dados if (d.get("obra_nome") or "").strip()})
        self.cb_obra.clear()
        self.cb_obra.addItem("TODAS")
        self.cb_obra.addItems(obras)
        self._aplicar()

    def _aplicar(self):
        obra = self.cb_obra.currentText().strip().upper()
        fornecedor = self.ed_fornecedor.text().strip().upper()
        item = self.ed_item.text().strip().upper()
        comprador = self.ed_comprador.text().strip().upper()
        filtrados = []
        for d in self._dados:
            if obra != "TODAS" and obra != (d.get("obra_nome") or "").strip().upper():
                continue
            if fornecedor and fornecedor not in (d.get("fornecedor_nome") or "").upper():
                continue
            if item and item not in (d.get("itens_texto") or "").upper():
                continue
            if comprador and comprador not in (d.get("comprador") or "").upper():
                continue
            filtrados.append(d)
        det = self.service.obra_details(filtrados, obra if obra != "TODAS" else (filtrados[0].get("obra_nome") if filtrados else ""))
        self.lbl_total.setText(f"Valor total: {self._fmt(det.get('valor_total', 0))}")
        self.lbl_qtd.setText(f"Pedidos: {len(filtrados)}")
        self.tbl.setRowCount(0)
        for i, p in enumerate(filtrados):
            self.tbl.insertRow(i)
            self.tbl.setRowHeight(i, 28)
            vals = [
                str(p.get("numero") or ""),
                str(p.get("data_pedido") or ""),
                str(p.get("fornecedor_nome") or ""),
                str(p.get("comprador") or ""),
                str(p.get("empresa_faturadora") or ""),
                self._fmt(p.get("valor_total")),
                str(p.get("status_auditoria") or ""),
                "OK" if p.get("pdf_rede") else "Sem PDF",
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if c in (0, 1, 5, 6, 7):
                    it.setTextAlignment(Qt.AlignCenter)
                self.tbl.setItem(i, c, it)

    def _fmt(self, v):
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
