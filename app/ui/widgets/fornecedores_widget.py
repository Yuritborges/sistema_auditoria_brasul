from datetime import date, datetime
from typing import List, Optional

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
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

from app.ui.consulta_readonly import configurar_tabela_consulta, item_consulta
from app.ui.widgets.brasul_combo import BrasulComboBox
from app.ui.widgets.brasul_date_edit import BrasulDateEdit

_PLACEHOLDER_FORN = "Selecione um fornecedor..."


class FornecedoresWidget(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self._dados = []
        self._rows_base: List[dict] = []
        self._pending_filtro_restore = None
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
        self.cb.setEditable(False)
        btn = QPushButton("Analisar")
        btn.clicked.connect(self._analisar)
        top.addWidget(fl)
        top.addWidget(self.cb, 1)
        top.addWidget(btn)
        root.addWidget(filt_card)

        self.dash_card = QFrame()
        self.dash_card.setObjectName("panelCard")
        self.dash_card.setEnabled(False)
        dash_l = QVBoxLayout(self.dash_card)
        dash_l.setContentsMargins(16, 14, 16, 14)
        dash_l.setSpacing(10)
        dash_title = QLabel("Dashboard — filtros sobre os pedidos deste fornecedor")
        dash_title.setObjectName("fieldLabel")
        dash_l.addWidget(dash_title)
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        def _fl(text):
            lb = QLabel(text)
            lb.setObjectName("fieldLabel")
            return lb

        today = QDate.currentDate()
        jan1 = QDate(today.year(), 1, 1)
        self.dt_ini = BrasulDateEdit()
        self.dt_ini.setDisplayFormat("dd/MM/yyyy")
        self.dt_ini.setDate(jan1)
        self.dt_ini.setMaximumDate(today)
        self.dt_fim = BrasulDateEdit()
        self.dt_fim.setDisplayFormat("dd/MM/yyyy")
        self.dt_fim.setDate(today)
        self.dt_fim.setMaximumDate(today)
        self.dt_ini.dateChanged.connect(self._limitar_periodo)
        self.dt_fim.dateChanged.connect(self._limitar_periodo)

        self.cb_obra = BrasulComboBox()
        self.cb_obra.setEditable(False)
        self.ed_pedido = QLineEdit()
        self.ed_pedido.setPlaceholderText("Nº do pedido (contém)…")
        self.ed_empresa = QLineEdit()
        self.ed_empresa.setPlaceholderText("Empresa faturadora (contém)…")

        btn_f = QPushButton("Aplicar filtros")
        btn_f.clicked.connect(self._aplicar_filtros_dashboard)

        grid.addWidget(_fl("Período"), 0, 0)
        period_row = QHBoxLayout()
        period_row.setSpacing(10)
        period_row.addWidget(self.dt_ini, 1)
        lbl_ate = QLabel("até")
        lbl_ate.setObjectName("fieldLabel")
        period_row.addWidget(lbl_ate)
        period_row.addWidget(self.dt_fim, 1)
        period_wrap = QWidget()
        period_wrap.setLayout(period_row)
        grid.addWidget(period_wrap, 0, 1, 1, 3)

        grid.addWidget(_fl("Obra"), 1, 0)
        grid.addWidget(self.cb_obra, 1, 1)
        grid.addWidget(_fl("Pedido"), 1, 2)
        grid.addWidget(self.ed_pedido, 1, 3)
        grid.addWidget(_fl("Empresa"), 2, 0)
        grid.addWidget(self.ed_empresa, 2, 1)
        grid.addWidget(btn_f, 2, 3)
        dash_l.addLayout(grid)
        root.addWidget(self.dash_card)

        kpi_card = QFrame()
        kpi_card.setObjectName("panelCard")
        kpis = QHBoxLayout(kpi_card)
        kpis.setContentsMargins(16, 12, 16, 12)
        self.lbl_kpi_total = QLabel("Total (filtro): R$ 0,00")
        self.lbl_kpi_total.setObjectName("emphasisStat")
        self.lbl_kpi_qtd = QLabel("Pedidos: 0")
        self.lbl_kpi_qtd.setObjectName("muted")
        self.lbl_kpi_media = QLabel("Ticket médio: R$ 0,00")
        self.lbl_kpi_media.setObjectName("muted")
        self.lbl_kpi_obras = QLabel("Obras (filtro): 0")
        self.lbl_kpi_obras.setObjectName("muted")
        kpis.addWidget(self.lbl_kpi_total)
        kpis.addSpacing(20)
        kpis.addWidget(self.lbl_kpi_qtd)
        kpis.addSpacing(20)
        kpis.addWidget(self.lbl_kpi_media)
        kpis.addSpacing(20)
        kpis.addWidget(self.lbl_kpi_obras)
        kpis.addStretch()
        root.addWidget(kpi_card)

        stats_card = QFrame()
        stats_card.setObjectName("panelCard")
        sl = QVBoxLayout(stats_card)
        sl.setContentsMargins(16, 12, 16, 12)
        self.lbl_stats = QLabel("Selecione um fornecedor e clique em Analisar.")
        self.lbl_stats.setObjectName("muted")
        self.lbl_stats.setWordWrap(True)
        sl.addWidget(self.lbl_stats)
        self.lbl_base_ref = QLabel("")
        self.lbl_base_ref.setObjectName("muted")
        self.lbl_base_ref.setWordWrap(True)
        sl.addWidget(self.lbl_base_ref)
        root.addWidget(stats_card)

        split = QHBoxLayout()
        split.setSpacing(12)

        tbl_card = QFrame()
        tbl_card.setObjectName("panelCard")
        tbl_l = QVBoxLayout(tbl_card)
        tbl_l.setContentsMargins(12, 12, 12, 12)
        ht_tbl = QLabel("Pedidos")
        ht_tbl.setObjectName("fieldLabel")
        tbl_l.addWidget(ht_tbl)
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
        configurar_tabela_consulta(self.tbl)
        tbl_l.addWidget(self.tbl)
        split.addWidget(tbl_card, 3)

        resumo_card = QFrame()
        resumo_card.setObjectName("panelCard")
        resumo_l = QVBoxLayout(resumo_card)
        resumo_l.setContentsMargins(12, 12, 12, 12)
        ht_r = QLabel("Gasto por obra (filtro)")
        ht_r.setObjectName("fieldLabel")
        resumo_l.addWidget(ht_r)
        self.tbl_obra = QTableWidget(0, 3)
        self.tbl_obra.setHorizontalHeaderLabels(["Obra", "Pedidos", "Total"])
        self.tbl_obra.verticalHeader().setVisible(False)
        self.tbl_obra.setAlternatingRowColors(True)
        self.tbl_obra.setShowGrid(False)
        self.tbl_obra.setFocusPolicy(Qt.NoFocus)
        self.tbl_obra.horizontalHeader().setStretchLastSection(True)
        self.tbl_obra.setColumnWidth(0, 180)
        self.tbl_obra.setColumnWidth(1, 72)
        configurar_tabela_consulta(self.tbl_obra)
        resumo_l.addWidget(self.tbl_obra)
        split.addWidget(resumo_card, 2)

        root.addLayout(split, 1)

    def set_data(self, dados):
        forn_atual = (self.cb.currentText() or "").strip()
        ok_forn = bool(forn_atual and forn_atual != _PLACEHOLDER_FORN)

        pending = None
        if ok_forn:
            pending = {
                "obra": (self.cb_obra.currentText() or "").strip() or "TODAS",
                "pedido": self.ed_pedido.text().strip(),
                "empresa": self.ed_empresa.text().strip(),
                "d_ini": self.dt_ini.date(),
                "d_fim": self.dt_fim.date(),
            }

        self._dados = dados
        fornecedores = sorted(
            {(d.get("fornecedor_nome") or "").strip() for d in dados if (d.get("fornecedor_nome") or "").strip()}
        )
        self.cb.clear()
        self.cb.addItem(_PLACEHOLDER_FORN)
        self.cb.addItems(fornecedores)

        if not ok_forn:
            self._limpar_analise()
            return

        idx = -1
        for i in range(self.cb.count()):
            if self.cb.itemText(i).strip().upper() == forn_atual.upper():
                idx = i
                break
        if idx < 0:
            self._limpar_analise()
            return

        self.cb.setCurrentIndex(idx)
        self._pending_filtro_restore = pending
        self._analisar()

    def _limpar_analise(self):
        self._pending_filtro_restore = None
        self._rows_base = []
        self.dash_card.setEnabled(False)
        self.cb_obra.blockSignals(True)
        self.cb_obra.clear()
        self.cb_obra.addItem("TODAS")
        self.cb_obra.blockSignals(False)
        self.ed_pedido.clear()
        self.ed_empresa.clear()
        today = QDate.currentDate()
        jan1 = QDate(today.year(), 1, 1)
        self.dt_ini.blockSignals(True)
        self.dt_fim.blockSignals(True)
        self.dt_ini.setDate(jan1)
        self.dt_fim.setDate(today)
        self.dt_ini.blockSignals(False)
        self.dt_fim.blockSignals(False)
        self._limitar_periodo()
        self.lbl_stats.setText("Selecione um fornecedor e clique em Analisar.")
        self.lbl_base_ref.setText("")
        self._atualizar_kpis_filtrado(0, 0, 0, 0)
        self.tbl.setRowCount(0)
        self.tbl_obra.setRowCount(0)

    def _analisar(self):
        fornecedor = self.cb.currentText()
        if not fornecedor or fornecedor == _PLACEHOLDER_FORN:
            self._limpar_analise()
            return

        pending = self._pending_filtro_restore
        self._pending_filtro_restore = None

        res = self.service.fornecedor_auditoria(self._dados, fornecedor)
        self._rows_base = list(res.get("rows") or [])

        if pending:
            self.dt_ini.blockSignals(True)
            self.dt_fim.blockSignals(True)
            self.dt_ini.setDate(pending["d_ini"])
            self.dt_fim.setDate(pending["d_fim"])
            self.dt_ini.blockSignals(False)
            self.dt_fim.blockSignals(False)
            self._limitar_periodo()
            self.ed_pedido.setText(pending["pedido"])
            self.ed_empresa.setText(pending["empresa"])
            obra_pref = pending["obra"]
        else:
            self._default_period_from_rows()
            self.ed_pedido.clear()
            self.ed_empresa.clear()
            obra_pref = "TODAS"

        self._popular_obra_combo(obra_pref)
        self.dash_card.setEnabled(True)
        self._aplicar_filtros_dashboard()

    def _popular_obra_combo(self, obra_preferida: str):
        self.cb_obra.blockSignals(True)
        self.cb_obra.clear()
        self.cb_obra.addItem("TODAS")
        obras = sorted(
            {(p.get("obra_nome") or "").strip() for p in self._rows_base if (p.get("obra_nome") or "").strip()}
        )
        self.cb_obra.addItems(obras)
        pref = (obra_preferida or "").strip() or "TODAS"
        idx = self.cb_obra.findText(pref, Qt.MatchFixedString | Qt.MatchCaseSensitive)
        if idx < 0:
            idx = self.cb_obra.findText(pref, Qt.MatchFixedString | Qt.MatchCaseInsensitive)
        if idx < 0:
            idx = 0
        self.cb_obra.setCurrentIndex(idx)
        self.cb_obra.blockSignals(False)

    def _default_period_from_rows(self):
        today = QDate.currentDate()
        datas = [d for p in self._rows_base if (d := self._pedido_data(p)) is not None]
        if not datas:
            self.dt_ini.blockSignals(True)
            self.dt_fim.blockSignals(True)
            self.dt_ini.setDate(QDate(today.year(), 1, 1))
            self.dt_fim.setDate(today)
            self.dt_ini.blockSignals(False)
            self.dt_fim.blockSignals(False)
            self._limitar_periodo()
            return
        d_min, d_max = min(datas), max(datas)
        q_min = QDate(d_min.year, d_min.month, d_min.day)
        q_max = QDate(d_max.year, d_max.month, d_max.day)
        self.dt_ini.blockSignals(True)
        self.dt_fim.blockSignals(True)
        self.dt_ini.setDate(q_min)
        self.dt_fim.setDate(min(q_max, today))
        self.dt_ini.blockSignals(False)
        self.dt_fim.blockSignals(False)
        self._limitar_periodo()

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

    @staticmethod
    def _valor_pedido(p) -> float:
        return float(p.get("_valor_total_float", p.get("valor_total") or 0) or 0)

    def _filtrar_rows(self) -> List[dict]:
        if not self._rows_base:
            return []
        d0 = self._qdate_to_date(self.dt_ini.date())
        d1 = self._qdate_to_date(self.dt_fim.date())
        obra_f = (self.cb_obra.currentText() or "").strip()
        ped_f = (self.ed_pedido.text() or "").strip().upper()
        emp_f = (self.ed_empresa.text() or "").strip().upper()

        out = []
        for p in self._rows_base:
            pd = self._pedido_data(p)
            if pd is not None:
                if pd < d0 or pd > d1:
                    continue
            else:
                continue

            on = (p.get("obra_nome") or "").strip()
            if obra_f and obra_f != "TODAS" and on.upper() != obra_f.upper():
                continue

            num = str(p.get("numero") or "").strip().upper()
            if ped_f and ped_f not in num:
                continue

            emp = (p.get("empresa_faturadora") or "").strip().upper()
            if emp_f and emp_f not in emp:
                continue

            out.append(p)
        return out

    def _aplicar_filtros_dashboard(self):
        if not self._rows_base:
            self._atualizar_kpis_filtrado(0, 0, 0, 0)
            self.lbl_stats.setText("Nenhum pedido localizado para este fornecedor.")
            self.lbl_base_ref.setText("")
            self.tbl.setRowCount(0)
            self.tbl_obra.setRowCount(0)
            return

        rows = self._filtrar_rows()
        total_base = sum(self._valor_pedido(p) for p in self._rows_base)
        q_base = len(self._rows_base)
        obras_base = len({(r.get("obra_nome") or "").strip() for r in self._rows_base if (r.get("obra_nome") or "").strip()})
        ultima_base = self._rows_base[0].get("data_pedido") if self._rows_base else "-"

        total_f = sum(self._valor_pedido(p) for p in rows)
        q_f = len(rows)
        obras_f = len({(r.get("obra_nome") or "").strip() for r in rows if (r.get("obra_nome") or "").strip()})
        media_f = (total_f / q_f) if q_f else 0.0

        self._atualizar_kpis_filtrado(total_f, q_f, media_f, obras_f)

        self.lbl_base_ref.setText(
            f"Referência base (todos os pedidos do fornecedor): {self._fmt(total_base)} | "
            f"{q_base} pedido(s) | {obras_base} obra(s) | Última compra: {ultima_base}"
        )

        ultima_f = rows[0].get("data_pedido") if rows else "-"
        primeira_f = rows[-1].get("data_pedido") if rows else "-"
        self.lbl_stats.setText(
            f"No período e filtros atuais: {self._fmt(total_f)} | Pedidos: {q_f} | Obras: {obras_f} | "
            f"Mais recente: {ultima_f} | Mais antiga: {primeira_f}"
        )

        self._preencher_tabela_pedidos(rows)
        self._preencher_resumo_obra(rows)

    def _atualizar_kpis_filtrado(self, total: float, qtd: int, media: float, obras: int):
        self.lbl_kpi_total.setText(f"Total (filtro): {self._fmt(total)}")
        self.lbl_kpi_qtd.setText(f"Pedidos: {qtd}")
        self.lbl_kpi_media.setText(f"Ticket médio: {self._fmt(media)}")
        self.lbl_kpi_obras.setText(f"Obras (filtro): {obras}")

    def _preencher_tabela_pedidos(self, rows: List[dict]):
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
                    it = item_consulta(v)
                    if c in (0, 1, 4, 5):
                        it.setTextAlignment(Qt.AlignCenter)
                    self.tbl.setItem(i, c, it)
        finally:
            self.tbl.setUpdatesEnabled(True)

    def _preencher_resumo_obra(self, rows: List[dict]):
        agg: dict[str, tuple[int, float]] = {}
        for p in rows:
            o = (p.get("obra_nome") or "").strip() or "SEM OBRA"
            q, v = agg.get(o, (0, 0.0))
            agg[o] = (q + 1, v + self._valor_pedido(p))
        items = sorted(agg.items(), key=lambda x: x[1][1], reverse=True)
        self.tbl_obra.setUpdatesEnabled(False)
        try:
            self.tbl_obra.setRowCount(0)
            for i, (obra, (qtd, tot)) in enumerate(items):
                self.tbl_obra.insertRow(i)
                self.tbl_obra.setRowHeight(i, 28)
                self.tbl_obra.setItem(i, 0, item_consulta(obra))
                iq = item_consulta(str(qtd))
                iq.setTextAlignment(Qt.AlignCenter)
                self.tbl_obra.setItem(i, 1, iq)
                iv = item_consulta(self._fmt(tot))
                iv.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tbl_obra.setItem(i, 2, iv)
        finally:
            self.tbl_obra.setUpdatesEnabled(True)

    def _fmt(self, v):
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
