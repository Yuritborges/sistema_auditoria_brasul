from datetime import date, datetime

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.ui.consulta_readonly import configurar_tabela_consulta
from app.ui.widgets.brasul_combo import (
    BrasulComboBox,
    garantir_combo_digitavel,
    itens_distintos_dos_pedidos,
    preencher_combo_filtro,
)
from app.ui.widgets.brasul_date_edit import BrasulDateEdit


class ItensWidget(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self._dados = []
        self._item_filtro_ativo = ""
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        hero = QVBoxLayout()
        hero.setSpacing(4)
        ht = QLabel("Auditoria por item / material")
        ht.setObjectName("moduleHeroTitle")
        hd = QLabel(
            "Mesmos filtros de Pedidos: comprador, obra, status, fornecedor, item e período. "
            "Veja quantidade e unidade por linha e o total comprado por obra."
        )
        hd.setObjectName("moduleHeroDesc")
        hd.setWordWrap(True)
        hero.addWidget(ht)
        hero.addWidget(hd)
        root.addLayout(hero)

        filtros_card = QFrame()
        filtros_card.setObjectName("panelCard")
        filtros = QGridLayout(filtros_card)
        filtros.setContentsMargins(16, 16, 16, 16)
        filtros.setHorizontalSpacing(12)
        filtros.setVerticalSpacing(10)

        self.cb_comprador = BrasulComboBox()
        self.cb_obra = BrasulComboBox()
        self.cb_status = BrasulComboBox()
        self.cb_status.addItems(["TODOS", "OK", "Sem PDF", "Sem comprador", "Crítico"])
        self.cb_forn = BrasulComboBox()
        self.cb_item = BrasulComboBox()
        for cb, ph in (
            (self.cb_comprador, "TODOS ou digite para buscar…"),
            (self.cb_obra, "TODAS ou digite para buscar…"),
            (self.cb_forn, "TODOS ou digite para buscar…"),
            (self.cb_item, "Item / material ou digite para buscar…"),
        ):
            garantir_combo_digitavel(cb)
            le = cb.lineEdit()
            if le is not None:
                le.setPlaceholderText(ph)

        filtros.setColumnStretch(0, 0)
        filtros.setColumnStretch(1, 1)
        filtros.setColumnStretch(2, 0)
        filtros.setColumnStretch(3, 1)

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
        self.dt_ini.dateChanged.connect(self.aplicar_filtros)
        self.dt_fim.dateChanged.connect(self.aplicar_filtros)

        def _fl(text):
            lb = QLabel(text)
            lb.setObjectName("fieldLabel")
            return lb

        filtros.addWidget(_fl("Comprador"), 0, 0)
        filtros.addWidget(self.cb_comprador, 0, 1)
        filtros.addWidget(_fl("Obra"), 0, 2)
        filtros.addWidget(self.cb_obra, 0, 3)
        filtros.addWidget(_fl("Status"), 1, 0)
        filtros.addWidget(self.cb_status, 1, 1)
        filtros.addWidget(_fl("Fornecedor"), 1, 2)
        filtros.addWidget(self.cb_forn, 1, 3)
        filtros.addWidget(_fl("Item"), 2, 0)
        filtros.addWidget(self.cb_item, 2, 1, 1, 3)
        filtros.addWidget(_fl("Período"), 3, 0)
        per = QHBoxLayout()
        per.setSpacing(8)
        per.addWidget(self.dt_ini, 1)
        lbl_ate = QLabel("até")
        lbl_ate.setObjectName("fieldLabel")
        per.addWidget(lbl_ate)
        per.addWidget(self.dt_fim, 1)
        per_w = QWidget()
        per_w.setLayout(per)
        filtros.addWidget(per_w, 3, 1, 1, 2)
        btn_filtrar = QPushButton("Filtrar")
        btn_filtrar.clicked.connect(self.aplicar_filtros)
        btn_pdf = QPushButton("Buscar PDFs")
        btn_pdf.setObjectName("secondaryButton")
        btn_pdf.clicked.connect(self.buscar_pdfs)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()
        btn_row.addWidget(btn_filtrar)
        btn_row.addWidget(btn_pdf)
        btn_w = QWidget()
        btn_w.setLayout(btn_row)
        filtros.addWidget(btn_w, 3, 3)
        root.addWidget(filtros_card)

        stats_card = QFrame()
        stats_card.setObjectName("panelCard")
        sl = QVBoxLayout(stats_card)
        sl.setContentsMargins(16, 12, 16, 12)
        sl.setSpacing(8)
        self.lbl_resumo = QLabel("Informe o item e clique em Filtrar.")
        self.lbl_resumo.setObjectName("muted")
        self.lbl_resumo.setWordWrap(True)
        sl.addWidget(self.lbl_resumo)
        self.lbl_stats = QLabel("")
        self.lbl_stats.setObjectName("muted")
        self.lbl_stats.setWordWrap(True)
        sl.addWidget(self.lbl_stats)
        self.lbl_totais_obra = QLabel("")
        self.lbl_totais_obra.setObjectName("moduleHeroDesc")
        self.lbl_totais_obra.setWordWrap(True)
        sl.addWidget(self.lbl_totais_obra)
        root.addWidget(stats_card)

        tbl_card = QFrame()
        tbl_card.setObjectName("panelCard")
        tbl_l = QVBoxLayout(tbl_card)
        tbl_l.setContentsMargins(12, 12, 12, 12)
        self.tbl = QTableWidget(0, 9)
        self.tbl.setHorizontalHeaderLabels(
            ["Item", "Obra", "Fornecedor", "Qtd", "Unid.", "Vlr unit.", "Valor item", "Data", "Pedido"]
        )
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setShowGrid(False)
        self.tbl.setFocusPolicy(Qt.NoFocus)
        self.tbl.horizontalHeader().setStretchLastSection(False)
        self.tbl.setColumnWidth(0, 220)
        self.tbl.setColumnWidth(1, 150)
        self.tbl.setColumnWidth(2, 140)
        self.tbl.setColumnWidth(3, 64)
        self.tbl.setColumnWidth(4, 48)
        self.tbl.setColumnWidth(5, 84)
        self.tbl.setColumnWidth(6, 92)
        self.tbl.setColumnWidth(7, 84)
        self.tbl.setColumnWidth(8, 64)
        configurar_tabela_consulta(self.tbl)
        tbl_l.addWidget(self.tbl)
        root.addWidget(tbl_card, 1)

    def set_data(self, dados):
        comprador_atual = (self.cb_comprador.currentText() or "").strip()
        obra_atual = (self.cb_obra.currentText() or "").strip()
        status_atual = (self.cb_status.currentText() or "").strip()
        fornecedor_atual = self.cb_forn.currentText()
        item_atual = self._item_filtro_ativo

        self._dados = list(dados)
        compradores = sorted({(d.get("comprador") or "").strip() for d in dados if (d.get("comprador") or "").strip()})
        obras = sorted({(d.get("obra_nome") or "").strip() for d in dados if (d.get("obra_nome") or "").strip()})
        preencher_combo_filtro(
            self.cb_comprador,
            compradores,
            comprador_atual or "TODOS",
            "TODOS ou digite para buscar…",
            opcao_todos="TODOS",
        )
        preencher_combo_filtro(
            self.cb_obra,
            obras,
            obra_atual or "TODAS",
            "TODAS ou digite para buscar…",
            opcao_todos="TODAS",
        )
        if status_atual:
            idx = self.cb_status.findText(status_atual, Qt.MatchFlag.MatchFixedString)
            if idx >= 0:
                self.cb_status.setCurrentIndex(idx)
        fornecedores = sorted(
            {(d.get("fornecedor_nome") or "").strip() for d in dados if (d.get("fornecedor_nome") or "").strip()}
        )
        preencher_combo_filtro(
            self.cb_forn,
            fornecedores,
            fornecedor_atual or "TODOS",
            "TODOS ou digite para buscar…",
            opcao_todos="TODOS",
        )
        preencher_combo_filtro(
            self.cb_item,
            itens_distintos_dos_pedidos(dados),
            item_atual,
            "Item / material ou digite para buscar…",
            iniciar_vazio=not item_atual,
        )
        self._atualizar_limites_calendario()
        if item_atual:
            self.aplicar_filtros()

    def _filtros_dict(self):
        d_ini = self._qdate_to_date(self.dt_ini.date())
        d_fim = self._qdate_to_date(self.dt_fim.date())
        if d_ini > d_fim:
            d_ini, d_fim = d_fim, d_ini
        item = self.cb_item.currentText().strip()
        self._item_filtro_ativo = item
        return {
            "comprador": self.cb_comprador.currentText(),
            "obra": self.cb_obra.currentText(),
            "status": self.cb_status.currentText(),
            "fornecedor": self.cb_forn.currentText(),
            "item": item,
            "data_ini": d_ini,
            "data_fim": d_fim,
        }

    def aplicar_filtros(self):
        filtros = self._filtros_dict()
        if not filtros.get("item"):
            self.lbl_resumo.setText("Informe o item/material no filtro e clique em Filtrar.")
            self.lbl_stats.setText("")
            self.lbl_totais_obra.setText("")
            self.tbl.setRowCount(0)
            return

        res = self.service.item_auditoria(self._dados, filtros)
        rows = res.get("rows") or []
        st = res.get("stats") or {}
        obra = filtros.get("obra") or "TODAS"

        self.lbl_resumo.setText(f"{len(rows)} linhas de item exibidas.")
        self.lbl_stats.setText(self._texto_stats(st))
        self.lbl_totais_obra.setText(self._texto_totais_obra(res, obra))

        self.tbl.setUpdatesEnabled(False)
        try:
            self.tbl.setRowCount(0)
            for i, r in enumerate(rows):
                self.tbl.insertRow(i)
                self.tbl.setRowHeight(i, 32)
                vals = [
                    r["item"],
                    r["obra"],
                    r["fornecedor"],
                    self._fmt_qtd(r.get("quantidade")),
                    r.get("unidade") or "—",
                    self._fmt(r.get("valor_unitario")),
                    self._fmt(r.get("valor")),
                    r.get("data") or "",
                    r.get("numero_pedido") or "",
                ]
                for c, v in enumerate(vals):
                    it = QTableWidgetItem(v)
                    if c in (3, 4, 5, 6, 7, 8):
                        it.setTextAlignment(Qt.AlignCenter)
                    self.tbl.setItem(i, c, it)
        finally:
            self.tbl.setUpdatesEnabled(True)

    def buscar_pdfs(self):
        filtros = self._filtros_dict()
        pedidos = self.service._filtrar_pedidos_item_auditoria(self._dados, filtros)
        if not pedidos:
            QMessageBox.information(self, "PDFs", "Nenhum pedido no filtro atual.")
            return
        ctx = {
            "comprador": filtros.get("comprador"),
            "obra": filtros.get("obra"),
            "fornecedor": filtros.get("fornecedor"),
            "item": filtros.get("item"),
        }
        total = self.service.buscar_pdfs_filtrados(pedidos, ctx)
        QMessageBox.information(self, "PDFs", f"PDFs encontrados para os filtros atuais: {total}")

    def _texto_stats(self, st):
        if not st:
            return "Nenhum registro para este filtro."
        return (
            f"Obras: {st.get('obras', 0)} | "
            f"Vlr unit. médio: {self._fmt(st.get('preco_medio_unit', 0))} | "
            f"Min unit.: {self._fmt(st.get('preco_min_unit', 0))} | "
            f"Max unit.: {self._fmt(st.get('preco_max_unit', 0))} | "
            f"Soma valores item: {self._fmt(st.get('valor_total_linhas', 0))} | "
            f"Menor vlr unit.: {st.get('fornecedor_mais_barato', '-')}"
        )

    def _texto_totais_obra(self, res, obra_filtro):
        obra_alvo = (obra_filtro or "").strip().upper()
        st = res.get("stats") or {}
        if obra_alvo and obra_alvo != "TODAS":
            partes = st.get("total_obra_filtrada") or []
            if not partes:
                return ""
            linhas = []
            for p in partes:
                un = p.get("unidade") or "—"
                tot = self._fmt_qtd(p.get("total"))
                linhas.append(f"<b>{p.get('obra')}</b>: {tot} {un}")
            return "Total na obra: " + " · ".join(linhas)
        totais = res.get("totais_obra") or []
        if not totais:
            return ""
        linhas = []
        for p in totais[:12]:
            un = p.get("unidade") or "—"
            tot = self._fmt_qtd(p.get("total"))
            linhas.append(f"{p.get('obra')}: {tot} {un}")
        txt = " · ".join(linhas)
        if len(totais) > 12:
            txt += f" … (+{len(totais) - 12} combinações obra/unidade)"
        return "Total comprado por obra: " + txt

    def _atualizar_limites_calendario(self):
        hoje = QDate.currentDate()
        mx = None
        for d in self._dados:
            dt = self.service._data_referencia_pedido(d)
            if dt == datetime.min:
                continue
            pd = dt.date()
            if mx is None or pd > mx:
                mx = pd
        if mx is not None:
            topo = QDate(mx.year, mx.month, mx.day)
            cap = topo if topo > hoje else hoje
        else:
            cap = hoje
        self.dt_ini.setMaximumDate(cap)
        self.dt_fim.setMaximumDate(cap)

    @staticmethod
    def _qdate_to_date(qd: QDate) -> date:
        return date(qd.year(), qd.month(), qd.day())

    def _fmt_qtd(self, v):
        n = float(v or 0)
        if abs(n - round(n)) < 0.0001:
            return f"{int(round(n)):,}".replace(",", ".")
        return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _fmt(self, v):
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
