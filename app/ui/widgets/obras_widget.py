from datetime import date, datetime
from typing import Optional

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.brasul_combo import BrasulComboBox


class ObrasWidget(QWidget):
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
        ht = QLabel("Consulta por obra")
        ht.setObjectName("moduleHeroTitle")
        hd = QLabel("Consolide pedidos da obra selecionada e refine por fornecedor, item ou comprador.")
        hd.setObjectName("moduleHeroDesc")
        hero.addWidget(ht)
        hero.addWidget(hd)
        root.addLayout(hero)

        card = QFrame()
        card.setObjectName("panelCard")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 16, 16, 16)
        filtros = QGridLayout()
        filtros.setHorizontalSpacing(12)
        filtros.setVerticalSpacing(10)
        self.cb_obra = BrasulComboBox()
        self.ed_fornecedor = QLineEdit()
        self.ed_fornecedor.setPlaceholderText("Fornecedor…")
        self.ed_item = QLineEdit()
        self.ed_item.setPlaceholderText("Material / item…")
        self.ed_comprador = QLineEdit()
        self.ed_comprador.setPlaceholderText("Comprador…")

        today = QDate.currentDate()
        jan1 = QDate(today.year(), 1, 1)
        self.dt_ini = QDateEdit()
        self.dt_ini.setCalendarPopup(True)
        self.dt_ini.setDisplayFormat("dd/MM/yyyy")
        self.dt_ini.setDate(jan1)
        self.dt_ini.setMaximumDate(today)
        self.dt_fim = QDateEdit()
        self.dt_fim.setCalendarPopup(True)
        self.dt_fim.setDisplayFormat("dd/MM/yyyy")
        self.dt_fim.setDate(today)
        self.dt_fim.setMaximumDate(today)
        self.dt_ini.dateChanged.connect(self._limitar_periodo)
        self.dt_fim.dateChanged.connect(self._limitar_periodo)

        btn = QPushButton("Aplicar")
        btn.clicked.connect(self._aplicar)

        def _fl(text):
            lb = QLabel(text)
            lb.setObjectName("fieldLabel")
            return lb

        filtros.addWidget(_fl("Obra"), 0, 0)
        filtros.addWidget(self.cb_obra, 0, 1)
        filtros.addWidget(_fl("Fornecedor"), 0, 2)
        filtros.addWidget(self.ed_fornecedor, 0, 3)
        filtros.addWidget(_fl("Item"), 1, 0)
        filtros.addWidget(self.ed_item, 1, 1)
        filtros.addWidget(_fl("Comprador"), 1, 2)
        filtros.addWidget(self.ed_comprador, 1, 3)
        filtros.addWidget(_fl("Período"), 2, 0)
        period_row = QHBoxLayout()
        period_row.setSpacing(10)
        period_row.addWidget(self.dt_ini, 1)
        lbl_ate = QLabel("até")
        lbl_ate.setObjectName("fieldLabel")
        period_row.addWidget(lbl_ate)
        period_row.addWidget(self.dt_fim, 1)
        period_wrap = QWidget()
        period_wrap.setLayout(period_row)
        filtros.addWidget(period_wrap, 2, 1, 1, 2)
        filtros.addWidget(btn, 2, 3)
        c_layout.addLayout(filtros)
        root.addWidget(card)

        kpi_card = QFrame()
        kpi_card.setObjectName("panelCard")
        kpis = QHBoxLayout(kpi_card)
        kpis.setContentsMargins(16, 12, 16, 12)
        self.lbl_total = QLabel("Valor total: R$ 0,00")
        self.lbl_total.setObjectName("emphasisStat")
        self.lbl_qtd = QLabel("Pedidos: 0")
        self.lbl_qtd.setObjectName("muted")
        kpis.addWidget(self.lbl_total)
        kpis.addSpacing(24)
        kpis.addWidget(self.lbl_qtd)
        kpis.addStretch()
        root.addWidget(kpi_card)

        tbl_card = QFrame()
        tbl_card.setObjectName("panelCard")
        tbl_l = QVBoxLayout(tbl_card)
        tbl_l.setContentsMargins(12, 12, 12, 12)
        self.tbl = QTableWidget(0, 8)
        self.tbl.setHorizontalHeaderLabels(["Pedido", "Data", "Fornecedor", "Comprador", "Empresa", "Valor", "Status", "PDF"])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setShowGrid(False)
        self.tbl.setFocusPolicy(Qt.NoFocus)
        self.tbl.horizontalHeader().setStretchLastSection(False)
        self.tbl.setColumnWidth(0, 72)
        self.tbl.setColumnWidth(1, 92)
        self.tbl.setColumnWidth(2, 168)
        self.tbl.setColumnWidth(3, 100)
        self.tbl.setColumnWidth(4, 92)
        self.tbl.setColumnWidth(5, 104)
        self.tbl.setColumnWidth(6, 100)
        self.tbl.setColumnWidth(7, 88)
        tbl_l.addWidget(self.tbl)
        root.addWidget(tbl_card, 1)

    def focus_obra(self, obra_nome: str):
        """Seleciona a obra no filtro e atualiza a grade (atalho a partir do dashboard)."""
        if not obra_nome or not self._dados:
            return
        alvo = obra_nome.strip().upper()
        for i in range(self.cb_obra.count()):
            if self.cb_obra.itemText(i).strip().upper() == alvo:
                self.cb_obra.setCurrentIndex(i)
                self._aplicar()
                return
        for i in range(self.cb_obra.count()):
            if alvo in self.cb_obra.itemText(i).upper():
                self.cb_obra.setCurrentIndex(i)
                self._aplicar()
                return

    def _limitar_periodo(self):
        today = QDate.currentDate()
        d0 = self.dt_ini.date()
        d1 = self.dt_fim.date()
        self.dt_ini.blockSignals(True)
        self.dt_fim.blockSignals(True)
        try:
            self.dt_ini.setMaximumDate(min(d1, today))
            self.dt_fim.setMinimumDate(d0)
            self.dt_fim.setMaximumDate(today)
            if d0 > d1:
                self.dt_fim.setDate(d0)
            elif d1 > today:
                self.dt_fim.setDate(today)
        finally:
            self.dt_ini.blockSignals(False)
            self.dt_fim.blockSignals(False)

    @staticmethod
    def _qdate_to_date(qd: QDate) -> date:
        return date(qd.year(), qd.month(), qd.day())

    @staticmethod
    def _pedido_data(p) -> Optional[date]:
        dt = p.get("_data_ord")
        if isinstance(dt, datetime):
            return dt.date()
        txt = (p.get("data_pedido") or "").strip()
        for fmt in ("%d/%m/%Y", "%d/%m/%y"):
            try:
                return datetime.strptime(txt, fmt).date()
            except ValueError:
                continue
        return None

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
        d_ini = self._qdate_to_date(self.dt_ini.date())
        d_fim = self._qdate_to_date(self.dt_fim.date())
        if d_ini > d_fim:
            d_ini, d_fim = d_fim, d_ini

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
            pd = self._pedido_data(d)
            if pd is not None and (pd < d_ini or pd > d_fim):
                continue
            filtrados.append(d)
        obra_ref = obra if obra != "TODAS" else (filtrados[0].get("obra_nome") if filtrados else "")
        det = self.service.obra_details(filtrados, obra_ref)
        self.lbl_total.setText(f"Valor total: {self._fmt(det.get('valor_total', 0))}")
        self.lbl_qtd.setText(f"Pedidos: {len(filtrados)}")
        self.tbl.setUpdatesEnabled(False)
        try:
            self.tbl.setRowCount(0)
            for i, p in enumerate(filtrados):
                self.tbl.insertRow(i)
                self.tbl.setRowHeight(i, 32)
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
        finally:
            self.tbl.setUpdatesEnabled(True)

    def _fmt(self, v):
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
