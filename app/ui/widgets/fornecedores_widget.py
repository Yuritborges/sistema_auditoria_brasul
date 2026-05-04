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

from app.ui.widgets.brasul_combo import BrasulComboBox


class FornecedoresWidget(QWidget):
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
        ht = QLabel("Auditoria por fornecedor")
        ht.setObjectName("moduleHeroTitle")
        hd = QLabel("Volume por obra, últimas compras e status de conformidade do fornecedor.")
        hd.setObjectName("moduleHeroDesc")
        hero.addWidget(ht)
        hero.addWidget(hd)
        root.addLayout(hero)

        filt_card = QFrame()
        filt_card.setObjectName("panelCard")
        top = QHBoxLayout(filt_card)
        top.setContentsMargins(16, 14, 16, 14)
        top.setSpacing(12)
        fl = QLabel("Fornecedor")
        fl.setObjectName("fieldLabel")
        self.cb = BrasulComboBox()
        btn = QPushButton("Analisar")
        btn.clicked.connect(self._analisar)
        top.addWidget(fl)
        top.addWidget(self.cb, 1)
        top.addWidget(btn)
        root.addWidget(filt_card)

        stats_card = QFrame()
        stats_card.setObjectName("panelCard")
        sl = QVBoxLayout(stats_card)
        sl.setContentsMargins(16, 12, 16, 12)
        self.lbl_stats = QLabel("Total: R$ 0,00 | Pedidos: 0 | Obras: 0 | Última compra: -")
        self.lbl_stats.setObjectName("muted")
        self.lbl_stats.setWordWrap(True)
        sl.addWidget(self.lbl_stats)
        root.addWidget(stats_card)

        tbl_card = QFrame()
        tbl_card.setObjectName("panelCard")
        tbl_l = QVBoxLayout(tbl_card)
        tbl_l.setContentsMargins(12, 12, 12, 12)
        self.tbl = QTableWidget(0, 6)
        self.tbl.setHorizontalHeaderLabels(["Pedido", "Data", "Obra", "Empresa", "Valor", "Status"])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setShowGrid(False)
        self.tbl.setFocusPolicy(Qt.NoFocus)
        self.tbl.horizontalHeader().setStretchLastSection(False)
        self.tbl.setColumnWidth(0, 72)
        self.tbl.setColumnWidth(1, 92)
        self.tbl.setColumnWidth(2, 208)
        self.tbl.setColumnWidth(3, 92)
        self.tbl.setColumnWidth(4, 104)
        self.tbl.setColumnWidth(5, 96)
        tbl_l.addWidget(self.tbl)
        root.addWidget(tbl_card, 1)

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
            f"Obras: {res.get('obras', 0)} | Última compra: {res.get('ultima_compra', '-')}"
        )
        rows = res.get("rows") or []
        self.tbl.setUpdatesEnabled(False)
        try:
            self.tbl.setRowCount(0)
            for i, r in enumerate(rows):
                self.tbl.insertRow(i)
                self.tbl.setRowHeight(i, 32)
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
        finally:
            self.tbl.setUpdatesEnabled(True)

    def _fmt(self, v):
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
