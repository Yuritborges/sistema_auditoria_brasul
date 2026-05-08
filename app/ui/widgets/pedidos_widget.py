import os
from datetime import date, datetime

from PySide6.QtCore import QDate, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.brasul_combo import BrasulComboBox
from app.ui.widgets.brasul_date_edit import BrasulDateEdit

PAGE_CHUNK = 300


class PedidosWidget(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self._dados = []
        self._filtrados = []
        self._visible_rows = PAGE_CHUNK
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        hero = QVBoxLayout()
        hero.setSpacing(4)
        ht = QLabel("Consulta de pedidos")
        ht.setObjectName("moduleHeroTitle")
        hd = QLabel(
            "Filtre por comprador, obra, status. A varredura completa na pasta de pedidos fica em “Buscar PDFs”."
        )
        hd.setObjectName("moduleHeroDesc")
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
        self.cb_status.addItems(["TODOS", "OK", "Sem PDF", "Sem comprador", "Critico"])
        self.ed_item = QLineEdit()
        self.ed_item.setPlaceholderText("Item / material…")
        self.ed_forn = QLineEdit()
        self.ed_forn.setPlaceholderText("Fornecedor…")
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

        def _fl(text):
            lb = QLabel(text)
            lb.setObjectName("fieldLabel")
            return lb

        filtros.addWidget(_fl("Comprador"), 0, 0)
        filtros.addWidget(self.cb_comprador, 0, 1)
        filtros.addWidget(_fl("Obra"), 0, 2)
        filtros.addWidget(self.cb_obra, 0, 3)
        filtros.addWidget(_fl("Status"), 0, 4)
        filtros.addWidget(self.cb_status, 0, 5)
        filtros.addWidget(_fl("Fornecedor"), 1, 0)
        filtros.addWidget(self.ed_forn, 1, 1, 1, 2)
        filtros.addWidget(_fl("Item"), 1, 3)
        filtros.addWidget(self.ed_item, 1, 4, 1, 2)
        filtros.addWidget(_fl("Período"), 2, 0)
        per = QHBoxLayout()
        per.setSpacing(8)
        per.addWidget(self.dt_ini, 1)
        per.addWidget(QLabel("até"))
        per.addWidget(self.dt_fim, 1)
        per_w = QWidget()
        per_w.setLayout(per)
        filtros.addWidget(per_w, 2, 1, 1, 3)
        btn_filtrar = QPushButton("Filtrar")
        btn_filtrar.clicked.connect(self.aplicar_filtros)
        btn_pdf = QPushButton("Buscar PDFs")
        btn_pdf.setObjectName("secondaryButton")
        btn_pdf.clicked.connect(self.buscar_pdfs)
        filtros.addWidget(btn_filtrar, 2, 4)
        filtros.addWidget(btn_pdf, 2, 5)
        root.addWidget(filtros_card)

        row_resumo = QHBoxLayout()
        row_resumo.setSpacing(12)
        self.lbl_resumo = QLabel("0 pedidos exibidos")
        self.lbl_resumo.setObjectName("muted")
        row_resumo.addWidget(self.lbl_resumo, 1)
        self.btn_mais = QPushButton(f"Carregar mais (+{PAGE_CHUNK})")
        self.btn_mais.setObjectName("secondaryButton")
        self.btn_mais.clicked.connect(self._carregar_mais_linhas)
        self.btn_mais.setVisible(False)
        row_resumo.addWidget(self.btn_mais, 0, Qt.AlignRight)
        root.addLayout(row_resumo)

        tbl_card = QFrame()
        tbl_card.setObjectName("panelCard")
        tbl_l = QVBoxLayout(tbl_card)
        tbl_l.setContentsMargins(12, 12, 12, 12)
        self.tbl = QTableWidget(0, 11)
        self.tbl.setHorizontalHeaderLabels(
            ["Pedido", "Data", "Comprador", "Empresa", "Fornecedor", "Obra", "Valor", "Status", "Cond.", "Forma", "PDF"]
        )
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setShowGrid(False)
        self.tbl.setFocusPolicy(Qt.NoFocus)
        self.tbl.horizontalHeader().setStretchLastSection(False)
        self.tbl.setColumnWidth(0, 72)
        self.tbl.setColumnWidth(1, 92)
        self.tbl.setColumnWidth(2, 100)
        self.tbl.setColumnWidth(3, 92)
        self.tbl.setColumnWidth(4, 170)
        self.tbl.setColumnWidth(5, 220)
        self.tbl.setColumnWidth(6, 104)
        self.tbl.setColumnWidth(7, 100)
        self.tbl.setColumnWidth(8, 82)
        self.tbl.setColumnWidth(9, 82)
        self.tbl.setColumnWidth(10, 72)
        tbl_l.addWidget(self.tbl)
        root.addWidget(tbl_card, 1)

        self.tbl.cellClicked.connect(self._on_pdf_cell_clicked)

    def set_data(self, dados):
        comprador_atual = (self.cb_comprador.currentText() or "").strip()
        obra_atual = (self.cb_obra.currentText() or "").strip()
        status_atual = (self.cb_status.currentText() or "").strip()
        fornecedor_atual = self.ed_forn.text()
        item_atual = self.ed_item.text()

        self._dados = list(dados)
        compradores = sorted({(d.get("comprador") or "").strip() for d in dados if (d.get("comprador") or "").strip()})
        obras = sorted({(d.get("obra_nome") or "").strip() for d in dados if (d.get("obra_nome") or "").strip()})
        self.cb_comprador.clear()
        self.cb_obra.clear()
        self.cb_comprador.addItem("TODOS")
        self.cb_obra.addItem("TODAS")
        self.cb_comprador.addItems(compradores)
        self.cb_obra.addItems(obras)

        if comprador_atual:
            idx = self.cb_comprador.findText(comprador_atual, Qt.MatchFixedString | Qt.MatchCaseInsensitive)
            if idx >= 0:
                self.cb_comprador.setCurrentIndex(idx)
            else:
                self.cb_comprador.setEditText(comprador_atual)
        if obra_atual:
            idx = self.cb_obra.findText(obra_atual, Qt.MatchFixedString | Qt.MatchCaseInsensitive)
            if idx >= 0:
                self.cb_obra.setCurrentIndex(idx)
            else:
                self.cb_obra.setEditText(obra_atual)
        if status_atual:
            idx = self.cb_status.findText(status_atual, Qt.MatchFixedString | Qt.MatchCaseInsensitive)
            if idx >= 0:
                self.cb_status.setCurrentIndex(idx)

        self.ed_forn.setText(fornecedor_atual)
        self.ed_item.setText(item_atual)
        self.aplicar_filtros()

    def _carregar_mais_linhas(self):
        self._visible_rows = min(len(self._filtrados), self._visible_rows + PAGE_CHUNK)
        self._fill_table()
        self._atualizar_texto_resumo()

    def aplicar_filtros(self):
        comprador = self.cb_comprador.currentText().strip().upper()
        obra = self.cb_obra.currentText().strip().upper()
        status = self.cb_status.currentText().strip().upper()
        fornecedor = self.ed_forn.text().strip().upper()
        item = self.ed_item.text().strip().upper()
        d_ini = self._qdate_to_date(self.dt_ini.date())
        d_fim = self._qdate_to_date(self.dt_fim.date())
        if d_ini > d_fim:
            d_ini, d_fim = d_fim, d_ini
        self._filtrados = []
        for d in self._dados:
            if comprador != "TODOS" and comprador != (d.get("comprador") or "").strip().upper():
                continue
            if obra != "TODAS" and obra != (d.get("obra_nome") or "").strip().upper():
                continue
            if status != "TODOS" and status != (d.get("status_auditoria") or "").strip().upper():
                continue
            if fornecedor and fornecedor not in (d.get("fornecedor_nome") or "").upper():
                continue
            if item and item not in (d.get("itens_texto") or "").upper():
                continue
            pd = self._pedido_data(d)
            if pd is not None and (pd < d_ini or pd > d_fim):
                continue
            self._filtrados.append(d)
        self._visible_rows = min(PAGE_CHUNK, len(self._filtrados)) if self._filtrados else 0
        self._fill_table()
        self._atualizar_texto_resumo()

    def _atualizar_texto_resumo(self):
        total = len(self._filtrados)
        shown = min(self._visible_rows, total)
        if total > shown:
            self.lbl_resumo.setText(f"{shown} de {total} pedidos no filtro — carregue mais linhas abaixo ou refine o filtro.")
        else:
            self.lbl_resumo.setText(f"{total} pedidos exibidos.")
        self.btn_mais.setVisible(total > shown)

    def buscar_pdfs(self):
        filtros = {
            "comprador": self.cb_comprador.currentText(),
            "obra": self.cb_obra.currentText(),
            "fornecedor": self.ed_forn.text(),
            "item": self.ed_item.text(),
        }
        total = self.service.buscar_pdfs_filtrados(self._filtrados, filtros)
        self._fill_table()
        self._atualizar_texto_resumo()
        QMessageBox.information(self, "PDFs", f"PDFs encontrados para os filtros atuais: {total}")

    def _fill_table(self):
        self.tbl.setUpdatesEnabled(False)
        try:
            self.tbl.clearContents()
            self.tbl.setRowCount(0)
            chunk = self._filtrados[: self._visible_rows]
            for i, d in enumerate(chunk):
                self.tbl.insertRow(i)
                self.tbl.setRowHeight(i, 32)
                path_pdf = (d.get("pdf_rede") or "").strip()
                vals = [
                    str(d.get("numero") or ""),
                    str(d.get("data_pedido") or ""),
                    str(d.get("comprador") or "SEM COMPRADOR"),
                    str(d.get("empresa_faturadora") or ""),
                    str(d.get("fornecedor_nome") or ""),
                    str(d.get("obra_nome") or ""),
                    self._fmt(d.get("valor_total")),
                    str(d.get("status_auditoria") or ""),
                    str(d.get("condicao_pagamento") or ""),
                    str(d.get("forma_pagamento") or ""),
                    "Abrir PDF" if path_pdf else "Sem PDF",
                ]
                for c, v in enumerate(vals):
                    it = QTableWidgetItem(v)
                    if c in (0, 1, 2, 6, 7, 10):
                        it.setTextAlignment(Qt.AlignCenter)
                    self.tbl.setItem(i, c, it)
                it_pdf = self.tbl.item(i, 10)
                if it_pdf and path_pdf:
                    it_pdf.setData(Qt.ItemDataRole.UserRole, path_pdf)
                    it_pdf.setToolTip(path_pdf)
        finally:
            self.tbl.setUpdatesEnabled(True)

    def _on_pdf_cell_clicked(self, row, col):
        if col != 10:
            return
        it = self.tbl.item(row, 10)
        if not it:
            return
        path = it.data(Qt.ItemDataRole.UserRole)
        if path:
            self._abrir_pdf(path)

    def _abrir_pdf(self, caminho):
        if not caminho or not os.path.exists(caminho):
            QMessageBox.warning(self, "PDF", "PDF não encontrado.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(caminho))

    def _fmt(self, v):
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    def _qdate_to_date(qd: QDate) -> date:
        return date(qd.year(), qd.month(), qd.day())

    @staticmethod
    def _pedido_data(p):
        dt = p.get("_data_ord")
        if isinstance(dt, datetime):
            return dt.date()
        txt = (p.get("data_pedido") or "").strip()
        for fmt in ("%d/%m/%Y", "%d/%m/%y"):
            try:
                return datetime.strptime(txt, fmt).date()
            except Exception:
                pass
        return None
