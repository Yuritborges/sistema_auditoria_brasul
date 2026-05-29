from datetime import date, datetime
from typing import Optional

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
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
    solicitantes_distintos_dos_pedidos,
)
from app.services.cadastros_rede import nomes_obras_cadastro
from app.ui.widgets.brasul_date_edit import BrasulDateEdit

PAGE_CHUNK = 300


class ObrasWidget(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self._dados = []
        self._filtrados = []
        self._visible_rows = PAGE_CHUNK
        self._item_filtro_ativo = ""
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
        self.cb_fornecedor = BrasulComboBox()
        self.cb_item = BrasulComboBox()
        self.cb_comprador = BrasulComboBox()
        self.cb_solicitante = BrasulComboBox()
        for cb, ph in (
            (self.cb_obra, "TODAS ou digite para buscar obra…"),
            (self.cb_fornecedor, "Fornecedor ou digite para buscar…"),
            (self.cb_item, "Material / item ou digite para buscar…"),
            (self.cb_comprador, "Comprador ou digite para buscar…"),
            (self.cb_solicitante, "Quem solicitou o material…"),
        ):
            garantir_combo_digitavel(cb)
            le = cb.lineEdit()
            if le is not None:
                le.setPlaceholderText(ph)

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
        self.dt_ini.dateChanged.connect(self._aplicar)
        self.dt_fim.dateChanged.connect(self._aplicar)

        for cb in (self.cb_obra, self.cb_fornecedor, self.cb_item, self.cb_comprador):
            cb.activated.connect(self._aplicar)
            le = cb.lineEdit()
            if le is not None:
                le.returnPressed.connect(self._aplicar)

        btn_limpar = QPushButton("Limpar")
        btn_limpar.setObjectName("secondaryButton")
        btn_limpar.setToolTip("Limpa fornecedor, item e comprador (mantém obra e período).")
        btn_limpar.clicked.connect(self._limpar_filtros_secundarios)

        btn = QPushButton("Aplicar filtros")
        btn.setToolTip("Atualiza a tabela com os filtros selecionados.")
        btn.clicked.connect(self._aplicar)

        def _fl(text):
            lb = QLabel(text)
            lb.setObjectName("fieldLabel")
            return lb

        filtros.addWidget(_fl("Obra"), 0, 0)
        filtros.addWidget(self.cb_obra, 0, 1)
        filtros.addWidget(_fl("Fornecedor"), 0, 2)
        filtros.addWidget(self.cb_fornecedor, 0, 3)
        filtros.addWidget(_fl("Item"), 1, 0)
        filtros.addWidget(self.cb_item, 1, 1)
        filtros.addWidget(_fl("Solicitante"), 1, 2)
        filtros.addWidget(self.cb_solicitante, 1, 3)
        filtros.addWidget(_fl("Comprador"), 2, 0)
        filtros.addWidget(self.cb_comprador, 2, 1, 1, 3)
        filtros.addWidget(_fl("Período"), 3, 0)
        period_row = QHBoxLayout()
        period_row.setSpacing(10)
        period_row.addWidget(self.dt_ini, 1)
        lbl_ate = QLabel("até")
        lbl_ate.setObjectName("fieldLabel")
        period_row.addWidget(lbl_ate)
        period_row.addWidget(self.dt_fim, 1)
        period_wrap = QWidget()
        period_wrap.setLayout(period_row)
        filtros.addWidget(period_wrap, 3, 1, 1, 2)
        acoes = QHBoxLayout()
        acoes.setSpacing(8)
        acoes.addWidget(btn_limpar)
        acoes.addWidget(btn)
        acoes_w = QWidget()
        acoes_w.setLayout(acoes)
        filtros.addWidget(acoes_w, 3, 3)
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
        configurar_tabela_consulta(self.tbl)
        tbl_l.addWidget(self.tbl)
        self.btn_mais = QPushButton("Carregar mais")
        self.btn_mais.setObjectName("secondaryButton")
        self.btn_mais.clicked.connect(self._carregar_mais)
        self.btn_mais.hide()
        tbl_l.addWidget(self.btn_mais)
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

    def _limpar_filtros_secundarios(self):
        self._item_filtro_ativo = ""
        for cb in (self.cb_fornecedor, self.cb_item, self.cb_comprador, self.cb_solicitante):
            le = cb.lineEdit()
            if le is not None:
                le.clear()
            cb.setCurrentIndex(-1)
        self._aplicar()

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

    def _pedido_data(self, p) -> Optional[date]:
        ref = self.service._data_referencia_pedido(p)
        if ref == datetime.min:
            return None
        return ref.date()

    def set_data(self, dados):
        obra_atual = (self.cb_obra.currentText() or "").strip()
        fornecedor_atual = self.cb_fornecedor.currentText()
        item_atual = self._item_filtro_ativo
        comprador_atual = self.cb_comprador.currentText()
        solicitante_atual = (self.cb_solicitante.currentText() or "").strip()
        dt_ini_atual = self.dt_ini.date()
        dt_fim_atual = self.dt_fim.date()

        self._dados = dados
        obras_set = {(d.get("obra_nome") or "").strip() for d in dados if (d.get("obra_nome") or "").strip()}
        obras_set.update(nomes_obras_cadastro())
        obras = sorted(obras_set, key=lambda s: s.upper())

        preencher_combo_filtro(
            self.cb_obra,
            ["TODAS", *obras],
            obra_atual or "TODAS",
            "TODAS ou digite para buscar obra…",
        )
        fornecedores = sorted(
            {(d.get("fornecedor_nome") or "").strip() for d in dados if (d.get("fornecedor_nome") or "").strip()}
        )
        compradores = sorted(
            {(d.get("comprador") or "").strip() for d in dados if (d.get("comprador") or "").strip()}
        )
        itens = itens_distintos_dos_pedidos(dados)
        preencher_combo_filtro(
            self.cb_fornecedor,
            fornecedores,
            fornecedor_atual,
            "Fornecedor ou digite para buscar…",
        )
        preencher_combo_filtro(
            self.cb_item,
            itens,
            item_atual,
            "Material / item ou digite para buscar…",
            iniciar_vazio=not item_atual,
        )
        preencher_combo_filtro(
            self.cb_comprador,
            compradores,
            comprador_atual,
            "Comprador ou digite para buscar…",
        )
        preencher_combo_filtro(
            self.cb_solicitante,
            solicitantes_distintos_dos_pedidos(dados),
            solicitante_atual or "",
            "Quem solicitou o material…",
            iniciar_vazio=not solicitante_atual,
        )
        self.dt_ini.setDate(dt_ini_atual)
        self.dt_fim.setDate(dt_fim_atual)
        self._limitar_periodo()
        self._aplicar()

    def _aplicar(self):
        obra = self.cb_obra.currentText().strip().upper()
        fornecedor = self.cb_fornecedor.currentText().strip().upper()
        item = self.cb_item.currentText().strip()
        self._item_filtro_ativo = item
        item = item.upper()
        comprador = self.cb_comprador.currentText().strip().upper()
        solicitante = self.cb_solicitante.currentText().strip().upper()
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
            if solicitante and solicitante not in (
                d.get("material_solicitado_por") or ""
            ).strip().upper():
                continue
            pd = self._pedido_data(d)
            if pd is None:
                continue
            if pd < d_ini or pd > d_fim:
                continue
            filtrados.append(d)
        self._filtrados = filtrados
        self._visible_rows = PAGE_CHUNK
        if obra != "TODAS":
            det = self.service.obra_details(filtrados, obra)
            titulo_obra = obra
        else:
            total = sum(
                p.get("_valor_total_float", float(p.get("valor_total") or 0)) for p in filtrados
            )
            det = {"valor_total": total, "qtd_pedidos": len(filtrados)}
            titulo_obra = "todas as obras (filtro)"
        self.lbl_total.setText(f"Valor total ({titulo_obra}): {self._fmt(det.get('valor_total', 0))}")
        self.lbl_qtd.setText(f"Pedidos: {len(filtrados)}")
        self._render_tabela()

    def _carregar_mais(self):
        self._visible_rows += PAGE_CHUNK
        self._render_tabela()

    def _render_tabela(self):
        visiveis = self._filtrados[: self._visible_rows]
        restante = len(self._filtrados) - len(visiveis)
        self.btn_mais.setVisible(restante > 0)
        if restante > 0:
            self.btn_mais.setText(f"Carregar mais ({restante} restantes)")
        self.tbl.setUpdatesEnabled(False)
        try:
            self.tbl.setRowCount(0)
            for i, p in enumerate(visiveis):
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
