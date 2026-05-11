from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from app.ui.consulta_readonly import configurar_tabela_consulta, item_consulta
from app.ui.widgets.obra_detail_dialog import ObraDetailDialog


class DashboardWidget(QWidget):
    """Emite o nome da obra para o shell abrir o módulo Obras (atalho a partir do painel)."""

    abrir_modulo_obras = Signal(str)

    def __init__(self, service):
        super().__init__()
        self.service = service
        self._dados = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        hero = QVBoxLayout()
        hero.setSpacing(4)
        ht = QLabel("Dashboard executivo")
        ht.setObjectName("moduleHeroTitle")
        hd = QLabel("Indicadores consolidados de pedidos, fornecedores e evolução mensal.")
        hd.setObjectName("moduleHeroDesc")
        hero.addWidget(ht)
        hero.addWidget(hd)
        root.addLayout(hero)

        cards = QGridLayout()
        cards.setHorizontalSpacing(12)
        cards.setVerticalSpacing(12)
        self.lbl_mes = self._kpi("Total gasto no mês", "R$ 0,00")
        self.lbl_ano = self._kpi("Total gasto no ano", "R$ 0,00")
        self.lbl_pend = self._kpi("Pedidos pendentes", "0")
        self.lbl_sem_pdf = self._kpi("Pedidos sem PDF", "0")
        cards.addWidget(self.lbl_mes.parentWidget(), 0, 0)
        cards.addWidget(self.lbl_ano.parentWidget(), 0, 1)
        cards.addWidget(self.lbl_pend.parentWidget(), 0, 2)
        cards.addWidget(self.lbl_sem_pdf.parentWidget(), 0, 3)
        root.addLayout(cards)

        split = QHBoxLayout()
        split.setSpacing(12)
        self.tbl_top_obras = self._table(["Obra", "Valor"])
        self.tbl_top_forn = self._table(["Fornecedor", "Valor"])
        self.tbl_top_itens = self._table(["Item", "Qtd"])
        self.tbl_top_obras.setCursor(QCursor(Qt.PointingHandCursor))
        self.tbl_top_obras.cellClicked.connect(self._abrir_painel_obra)
        split.addWidget(
            self._table_card(
                "Top obras",
                self.tbl_top_obras,
                "Clique numa obra para ver detalhes, pedidos e fornecedores.",
            ),
            1,
        )
        split.addWidget(self._table_card("Top fornecedores", self.tbl_top_forn), 1)
        split.addWidget(self._table_card("Top itens", self.tbl_top_itens), 1)
        root.addLayout(split)

        mensal_wrap = QFrame()
        mensal_wrap.setObjectName("panelCard")
        m_layout = QVBoxLayout(mensal_wrap)
        m_layout.setContentsMargins(16, 16, 16, 16)
        m_layout.setSpacing(10)
        ttl = QLabel("Evolução mensal (valor)")
        ttl.setObjectName("sectionTitle")
        m_layout.addWidget(ttl)
        self.mensal_bars = []
        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(8)
        for i in range(12):
            row, col = divmod(i, 2)
            r = QHBoxLayout()
            r.setSpacing(12)
            lb = QLabel(f"{i + 1:02d}")
            lb.setObjectName("monthTick")
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setTextVisible(False)
            val = QLabel("R$ 0,00")
            val.setObjectName("monthVal")
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            r.addWidget(lb)
            r.addWidget(bar, 1)
            r.addWidget(val)
            grid.addLayout(r, row, col)
            self.mensal_bars.append((bar, val))
        m_layout.addLayout(grid)
        root.addWidget(mensal_wrap)

    def _abrir_painel_obra(self, row, _col):
        it = self.tbl_top_obras.item(row, 0)
        if not it:
            return
        obra = it.text().strip()
        if not obra:
            return
        dlg = ObraDetailDialog(self.service, self._dados, obra, self)
        dlg.navegar_obras.connect(self.abrir_modulo_obras.emit)
        dlg.exec()

    def _kpi(self, titulo, valor):
        card = QFrame()
        card.setObjectName("kpiCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(6)
        t = QLabel(titulo)
        t.setObjectName("kpiTitle")
        lbl = QLabel(valor)
        lbl.setObjectName("kpiValue")
        lay.addWidget(t)
        lay.addWidget(lbl)
        setattr(lbl, "_card", card)
        return lbl

    def _table(self, headers):
        tbl = QTableWidget(0, len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.setSelectionBehavior(QTableWidget.SelectRows)
        tbl.setSelectionMode(QTableWidget.SingleSelection)
        tbl.setAlternatingRowColors(True)
        tbl.horizontalHeader().setStretchLastSection(True)
        tbl.setShowGrid(False)
        tbl.setFocusPolicy(Qt.StrongFocus)
        configurar_tabela_consulta(tbl)
        return tbl

    def _table_card(self, title, table, hint=None):
        card = QFrame()
        card.setObjectName("panelCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)
        ttl = QLabel(title)
        ttl.setObjectName("sectionTitle")
        lay.addWidget(ttl)
        if hint:
            h = QLabel(hint)
            h.setObjectName("muted")
            h.setWordWrap(True)
            lay.addWidget(h)
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
            tbl.setRowHeight(i, 30)
            tbl.setItem(i, 0, item_consulta(str(a)))
            txt = self._fmt(b) if money else str(b)
            it = item_consulta(txt)
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            tbl.setItem(i, 1, it)

    def _fmt(self, v):
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
