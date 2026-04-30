from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class DashboardWidget(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self._dados = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        title = QLabel("Dashboard Executivo")
        title.setObjectName("sectionTitle")
        root.addWidget(title)

        cards = QGridLayout()
        cards.setHorizontalSpacing(10)
        cards.setVerticalSpacing(10)
        self.lbl_mes = self._kpi("Total gasto no mes", "R$ 0,00")
        self.lbl_ano = self._kpi("Total gasto no ano", "R$ 0,00")
        self.lbl_pend = self._kpi("Pedidos pendentes", "0")
        self.lbl_sem_pdf = self._kpi("Pedidos sem PDF", "0")
        cards.addWidget(self.lbl_mes.parentWidget(), 0, 0)
        cards.addWidget(self.lbl_ano.parentWidget(), 0, 1)
        cards.addWidget(self.lbl_pend.parentWidget(), 0, 2)
        cards.addWidget(self.lbl_sem_pdf.parentWidget(), 0, 3)
        root.addLayout(cards)

        split = QHBoxLayout()
        self.tbl_top_obras = self._table(["Obra", "Valor"])
        self.tbl_top_forn = self._table(["Fornecedor", "Valor"])
        self.tbl_top_itens = self._table(["Item", "Qtd"])
        split.addWidget(self._table_card("Top Obras", self.tbl_top_obras), 1)
        split.addWidget(self._table_card("Top Fornecedores", self.tbl_top_forn), 1)
        split.addWidget(self._table_card("Top Itens", self.tbl_top_itens), 1)
        root.addLayout(split)

        mensal_wrap = QFrame()
        mensal_wrap.setObjectName("panelCard")
        m_layout = QVBoxLayout(mensal_wrap)
        ttl = QLabel("Evolucao mensal (valor)")
        ttl.setObjectName("sectionTitle")
        m_layout.addWidget(ttl)
        self.mensal_bars = []
        for i in range(12):
            row = QHBoxLayout()
            lb = QLabel(f"{i+1:02d}")
            bar = QProgressBar()
            bar.setRange(0, 100)
            val = QLabel("R$ 0,00")
            row.addWidget(lb)
            row.addWidget(bar, 1)
            row.addWidget(val)
            m_layout.addLayout(row)
            self.mensal_bars.append((bar, val))
        root.addWidget(mensal_wrap)

    def _kpi(self, titulo, valor):
        card = QFrame()
        card.setObjectName("panelCard")
        card.setStyleSheet("QLabel#v{font-size:22px;font-weight:800;}")
        lay = QVBoxLayout(card)
        lay.addWidget(QLabel(titulo))
        lbl = QLabel(valor)
        lbl.setObjectName("v")
        lay.addWidget(lbl)
        setattr(lbl, "_card", card)
        return lbl

    def _table(self, headers):
        tbl = QTableWidget(0, len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.setSelectionBehavior(QTableWidget.SelectRows)
        tbl.setAlternatingRowColors(True)
        tbl.horizontalHeader().setStretchLastSection(True)
        return tbl

    def _table_card(self, title, table):
        card = QFrame()
        card.setObjectName("panelCard")
        lay = QVBoxLayout(card)
        ttl = QLabel(title)
        ttl.setObjectName("sectionTitle")
        lay.addWidget(ttl)
        lay.addWidget(table)
        return card

    def set_data(self, dados):
        self._dados = dados
        s = self.service.dashboard_summary(dados)
        self.lbl_mes.setText(self._fmt(s["total_mes"]))
        self.lbl_ano.setText(self._fmt(s["total_ano"]))
        self.lbl_pend.setText(str(s["pendentes"]))
        self.lbl_sem_pdf.setText(str(s["sem_pdf"]))
        self._fill_pairs(self.tbl_top_obras, s["top_obras"][:10], money=True)
        self._fill_pairs(self.tbl_top_forn, s["top_fornecedores"][:10], money=True)
        self._fill_pairs(self.tbl_top_itens, s["top_itens"][:10], money=False)

        max_v = max(s["mensal"].values()) if s["mensal"] else 0
        if max_v <= 0:
            max_v = 1
        for mes in range(1, 13):
            v = s["mensal"].get(mes, 0)
            bar, lbl = self.mensal_bars[mes - 1]
            bar.setValue(int((v / max_v) * 100))
            lbl.setText(self._fmt(v))

    def _fill_pairs(self, tbl, rows, money):
        tbl.setRowCount(0)
        for i, (a, b) in enumerate(rows):
            tbl.insertRow(i)
            tbl.setItem(i, 0, QTableWidgetItem(str(a)))
            txt = self._fmt(b) if money else str(b)
            it = QTableWidgetItem(txt)
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            tbl.setItem(i, 1, it)

    def _fmt(self, v):
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
