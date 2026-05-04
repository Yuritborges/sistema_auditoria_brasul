from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.ui.style import APP_STYLESHEET


class ObraDetailDialog(QDialog):
    """Painel rico com resumo da obra, conformidade, fornecedores e pedidos."""

    navegar_obras = Signal(str)

    def __init__(self, service, dados, obra_nome, parent=None):
        super().__init__(parent)
        self.service = service
        self._dados = dados
        self._obra = (obra_nome or "").strip()
        self.setObjectName("obraDetailDialog")
        self.setWindowTitle("Detalhe da obra")
        self.setModal(True)
        self.setMinimumSize(760, 560)
        self.resize(880, 620)
        self.setStyleSheet(APP_STYLESHEET)
        self._build()

    def _build(self):
        resumo = self.service.obra_resumo_executivo(self._dados, self._obra)
        nome = resumo.get("obra_nome_exibicao") or self._obra
        pedidos = sorted(
            resumo.get("pedidos") or [],
            key=lambda p: self.service._chave_ordenacao(p),
            reverse=True,
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 16)
        root.setSpacing(14)

        head = QVBoxLayout()
        head.setSpacing(6)
        title = QLabel(nome)
        title.setObjectName("dialogHeroTitle")
        title.setWordWrap(True)
        sub = QLabel("Visão consolidada de gastos, conformidade e fornecedores nesta obra.")
        sub.setObjectName("moduleHeroDesc")
        head.addWidget(title)
        head.addWidget(sub)
        root.addLayout(head)

        chips = QHBoxLayout()
        chips.setSpacing(8)
        for label, key, st in [
            ("OK", "OK", "chipOk"),
            ("Sem PDF", "Sem PDF", "chipWarn"),
            ("Sem comprador", "Sem comprador", "chipWarn"),
            ("Crítico", "Critico", "chipBad"),
        ]:
            n = resumo.get("by_status", {}).get(key, 0)
            lb = QLabel(f"{label}: {n}")
            lb.setObjectName(st)
            chips.addWidget(lb)
        chips.addStretch()
        root.addLayout(chips)

        strip = QHBoxLayout()
        strip.setSpacing(12)
        strip.addWidget(self._mini_kpi("Valor total", self._fmt(resumo.get("valor_total", 0))))
        strip.addWidget(self._mini_kpi("Pedidos", str(resumo.get("qtd_pedidos", 0))))
        strip.addWidget(self._mini_kpi("Sem PDF", str(resumo.get("sem_pdf_n", 0))))
        strip.addWidget(self._mini_kpi("Sem comprador", str(resumo.get("sem_comprador_n", 0))))
        root.addLayout(strip)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        inner = QWidget()
        inner_l = QVBoxLayout(inner)
        inner_l.setContentsMargins(0, 0, 8, 0)
        inner_l.setSpacing(14)

        mensal = resumo.get("mensal") or {}
        max_v = max(mensal.values()) if mensal else 0
        if max_v <= 0:
            max_v = 1.0

        mes_card = QFrame()
        mes_card.setObjectName("panelCard")
        ml = QVBoxLayout(mes_card)
        ml.setContentsMargins(14, 12, 14, 12)
        ml.setSpacing(8)
        mt = QLabel("Evolução mensal nesta obra")
        mt.setObjectName("sectionTitle")
        ml.addWidget(mt)
        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(6)
        for i in range(12):
            row, col = divmod(i, 2)
            r = QHBoxLayout()
            r.setSpacing(10)
            lb = QLabel(f"{i + 1:02d}")
            lb.setObjectName("monthTick")
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setTextVisible(False)
            v = mensal.get(i + 1, 0)
            bar.setValue(int((v / max_v) * 100))
            val = QLabel(self._fmt(v))
            val.setObjectName("monthVal")
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            r.addWidget(lb)
            r.addWidget(bar, 1)
            r.addWidget(val)
            grid.addLayout(r, row, col)
        ml.addLayout(grid)
        inner_l.addWidget(mes_card)

        forn_card = QFrame()
        forn_card.setObjectName("panelCard")
        fl = QVBoxLayout(forn_card)
        fl.setContentsMargins(12, 12, 12, 12)
        fl.setSpacing(8)
        ft = QLabel("Fornecedores com maior volume (nesta obra)")
        ft.setObjectName("sectionTitle")
        fl.addWidget(ft)
        tforn = QTableWidget(0, 2)
        tforn.setHorizontalHeaderLabels(["Fornecedor", "Valor"])
        tforn.verticalHeader().setVisible(False)
        tforn.setAlternatingRowColors(True)
        tforn.setShowGrid(False)
        tforn.setFocusPolicy(Qt.NoFocus)
        tforn.horizontalHeader().setStretchLastSection(True)
        tforn.setMaximumHeight(220)
        for i, (fn, val) in enumerate(resumo.get("top_fornecedores") or []):
            tforn.insertRow(i)
            tforn.setRowHeight(i, 28)
            tforn.setItem(i, 0, QTableWidgetItem(fn))
            it = QTableWidgetItem(self._fmt(val))
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            tforn.setItem(i, 1, it)
        fl.addWidget(tforn)
        inner_l.addWidget(forn_card)

        ped_card = QFrame()
        ped_card.setObjectName("panelCard")
        pl = QVBoxLayout(ped_card)
        pl.setContentsMargins(12, 12, 12, 12)
        pl.setSpacing(8)
        pt = QLabel("Pedidos vinculados")
        pt.setObjectName("sectionTitle")
        pl.addWidget(pt)
        tbl = QTableWidget(0, 6)
        tbl.setHorizontalHeaderLabels(["Pedido", "Data", "Fornecedor", "Empresa", "Valor", "Status"])
        tbl.verticalHeader().setVisible(False)
        tbl.setAlternatingRowColors(True)
        tbl.setShowGrid(False)
        tbl.setFocusPolicy(Qt.NoFocus)
        tbl.horizontalHeader().setStretchLastSection(True)
        tbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        for i, p in enumerate(pedidos[:500]):
            tbl.insertRow(i)
            tbl.setRowHeight(i, 28)
            vals = [
                str(p.get("numero") or ""),
                str(p.get("data_pedido") or ""),
                str(p.get("fornecedor_nome") or ""),
                str(p.get("empresa_faturadora") or ""),
                self._fmt(p.get("valor_total")),
                str(p.get("status_auditoria") or ""),
            ]
            for c, x in enumerate(vals):
                it = QTableWidgetItem(x)
                if c in (0, 1, 4, 5):
                    it.setTextAlignment(Qt.AlignCenter)
                tbl.setItem(i, c, it)
        pl.addWidget(tbl)
        inner_l.addWidget(ped_card)

        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

        actions = QHBoxLayout()
        actions.addStretch()
        btn_fechar = QPushButton("Fechar")
        btn_fechar.setObjectName("secondaryButton")
        btn_fechar.clicked.connect(self.reject)
        btn_obras = QPushButton("Abrir em Obras")
        btn_obras.clicked.connect(self._emit_ir_obras)
        actions.addWidget(btn_fechar)
        actions.addWidget(btn_obras)
        root.addLayout(actions)

    def _emit_ir_obras(self):
        self.navegar_obras.emit(self._obra)
        self.accept()

    def _mini_kpi(self, titulo, valor):
        fr = QFrame()
        fr.setObjectName("kpiCard")
        lay = QVBoxLayout(fr)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(4)
        t = QLabel(titulo)
        t.setObjectName("kpiTitle")
        v = QLabel(valor)
        v.setObjectName("kpiValue")
        lay.addWidget(t)
        lay.addWidget(v)
        return fr

    def _fmt(self, v):
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

