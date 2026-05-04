from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class ItensWidget(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self._dados = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        hero = QVBoxLayout()
        hero.setSpacing(4)
        ht = QLabel("Auditoria por item / material")
        ht.setObjectName("moduleHeroTitle")
        hd = QLabel("Busque descrições consolidadas dos pedidos e compare valores entre obras.")
        hd.setObjectName("moduleHeroDesc")
        hero.addWidget(ht)
        hero.addWidget(hd)
        root.addLayout(hero)

        filt_card = QFrame()
        filt_card.setObjectName("panelCard")
        top = QHBoxLayout(filt_card)
        top.setContentsMargins(16, 14, 16, 14)
        top.setSpacing(12)
        self.ed_item = QLineEdit()
        self.ed_item.setPlaceholderText("Ex.: cimento, tubo, disjuntor…")
        btn = QPushButton("Auditar")
        btn.clicked.connect(self._auditar)
        top.addWidget(self.ed_item, 1)
        top.addWidget(btn)
        root.addWidget(filt_card)

        stats_card = QFrame()
        stats_card.setObjectName("panelCard")
        sl = QVBoxLayout(stats_card)
        sl.setContentsMargins(16, 12, 16, 12)
        self.lbl_stats = QLabel("Qtd: 0 | Obras: 0 | Preço médio: R$ 0,00 | Min: R$ 0,00 | Max: R$ 0,00")
        self.lbl_stats.setObjectName("muted")
        self.lbl_stats.setWordWrap(True)
        sl.addWidget(self.lbl_stats)
        root.addWidget(stats_card)

        tbl_card = QFrame()
        tbl_card.setObjectName("panelCard")
        tbl_l = QVBoxLayout(tbl_card)
        tbl_l.setContentsMargins(12, 12, 12, 12)
        self.tbl = QTableWidget(0, 5)
        self.tbl.setHorizontalHeaderLabels(["Item", "Obra", "Fornecedor", "Valor", "Data"])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setShowGrid(False)
        self.tbl.setFocusPolicy(Qt.NoFocus)
        self.tbl.horizontalHeader().setStretchLastSection(False)
        self.tbl.setColumnWidth(0, 300)
        self.tbl.setColumnWidth(1, 188)
        self.tbl.setColumnWidth(2, 188)
        self.tbl.setColumnWidth(3, 104)
        self.tbl.setColumnWidth(4, 96)
        tbl_l.addWidget(self.tbl)
        root.addWidget(tbl_card, 1)

    def set_data(self, dados):
        self._dados = dados
        self._auditar()

    def _auditar(self):
        termo = self.ed_item.text()
        res = self.service.item_auditoria(self._dados, termo)
        st = res.get("stats") or {}
        self.lbl_stats.setText(
            f"Qtd: {st.get('qtd', 0)} | Obras: {st.get('obras', 0)} | "
            f"Preço médio: {self._fmt(st.get('preco_medio', 0))} | "
            f"Min: {self._fmt(st.get('preco_min', 0))} | Max: {self._fmt(st.get('preco_max', 0))} | "
            f"Fornecedor mais barato: {st.get('fornecedor_mais_barato', '-')}"
        )
        rows = res.get("rows") or []
        self.tbl.setUpdatesEnabled(False)
        try:
            self.tbl.setRowCount(0)
            for i, r in enumerate(rows):
                self.tbl.insertRow(i)
                self.tbl.setRowHeight(i, 32)
                vals = [r["item"], r["obra"], r["fornecedor"], self._fmt(r["valor"]), r["data"]]
                for c, v in enumerate(vals):
                    it = QTableWidgetItem(v)
                    if c in (3, 4):
                        it.setTextAlignment(Qt.AlignCenter)
                    self.tbl.setItem(i, c, it)
        finally:
            self.tbl.setUpdatesEnabled(True)

    def _fmt(self, v):
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
