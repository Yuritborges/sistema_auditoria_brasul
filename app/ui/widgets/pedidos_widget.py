import os

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QComboBox,
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


class PedidosWidget(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self._dados = []
        self._filtrados = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        title = QLabel("Consulta de Pedidos")
        title.setObjectName("sectionTitle")
        root.addWidget(title)

        filtros_card = QFrame()
        filtros_card.setObjectName("panelCard")
        filtros = QGridLayout(filtros_card)
        filtros.setContentsMargins(10, 10, 10, 10)
        filtros.setHorizontalSpacing(8)
        filtros.setVerticalSpacing(8)
        self.cb_comprador = QComboBox()
        self.cb_obra = QComboBox()
        self.cb_status = QComboBox()
        self.cb_status.addItems(["TODOS", "OK", "Sem PDF", "Sem comprador", "Critico"])
        self.ed_item = QLineEdit()
        self.ed_item.setPlaceholderText("Item/material...")
        self.ed_forn = QLineEdit()
        self.ed_forn.setPlaceholderText("Fornecedor...")
        filtros.addWidget(QLabel("Comprador"), 0, 0)
        filtros.addWidget(self.cb_comprador, 0, 1)
        filtros.addWidget(QLabel("Obra"), 0, 2)
        filtros.addWidget(self.cb_obra, 0, 3)
        filtros.addWidget(QLabel("Status"), 0, 4)
        filtros.addWidget(self.cb_status, 0, 5)
        filtros.addWidget(QLabel("Fornecedor"), 1, 0)
        filtros.addWidget(self.ed_forn, 1, 1, 1, 2)
        filtros.addWidget(QLabel("Item"), 1, 3)
        filtros.addWidget(self.ed_item, 1, 4, 1, 2)
        btn_filtrar = QPushButton("Filtrar")
        btn_filtrar.clicked.connect(self.aplicar_filtros)
        btn_pdf = QPushButton("Buscar PDFs")
        btn_pdf.setObjectName("secondaryButton")
        btn_pdf.clicked.connect(self.buscar_pdfs)
        filtros.addWidget(btn_filtrar, 2, 4)
        filtros.addWidget(btn_pdf, 2, 5)
        root.addWidget(filtros_card)

        self.lbl_resumo = QLabel("0 pedidos exibidos")
        self.lbl_resumo.setObjectName("muted")
        root.addWidget(self.lbl_resumo)

        self.tbl = QTableWidget(0, 11)
        self.tbl.setHorizontalHeaderLabels(["Pedido", "Data", "Comprador", "Empresa", "Fornecedor", "Obra", "Valor", "Status", "Cond.", "Forma", "PDF"])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.horizontalHeader().setStretchLastSection(False)
        self.tbl.setColumnWidth(0, 70)
        self.tbl.setColumnWidth(1, 90)
        self.tbl.setColumnWidth(2, 95)
        self.tbl.setColumnWidth(3, 90)
        self.tbl.setColumnWidth(4, 170)
        self.tbl.setColumnWidth(5, 220)
        self.tbl.setColumnWidth(6, 100)
        self.tbl.setColumnWidth(7, 95)
        self.tbl.setColumnWidth(8, 80)
        self.tbl.setColumnWidth(9, 80)
        self.tbl.setColumnWidth(10, 64)
        root.addWidget(self.tbl, 1)

    def set_data(self, dados):
        self._dados = list(dados)
        compradores = sorted({(d.get("comprador") or "").strip() for d in dados if (d.get("comprador") or "").strip()})
        obras = sorted({(d.get("obra_nome") or "").strip() for d in dados if (d.get("obra_nome") or "").strip()})
        self.cb_comprador.clear()
        self.cb_obra.clear()
        self.cb_comprador.addItem("TODOS")
        self.cb_obra.addItem("TODAS")
        self.cb_comprador.addItems(compradores)
        self.cb_obra.addItems(obras)
        self.aplicar_filtros()

    def aplicar_filtros(self):
        comprador = self.cb_comprador.currentText().strip().upper()
        obra = self.cb_obra.currentText().strip().upper()
        status = self.cb_status.currentText().strip().upper()
        fornecedor = self.ed_forn.text().strip().upper()
        item = self.ed_item.text().strip().upper()
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
            self._filtrados.append(d)
        self._fill_table()
        self.lbl_resumo.setText(f"{len(self._filtrados)} pedidos exibidos")

    def buscar_pdfs(self):
        filtros = {
            "comprador": self.cb_comprador.currentText(),
            "obra": self.cb_obra.currentText(),
            "fornecedor": self.ed_forn.text(),
            "item": self.ed_item.text(),
        }
        total = self.service.buscar_pdfs_filtrados(self._filtrados, filtros)
        self._fill_table()
        QMessageBox.information(self, "PDFs", f"PDFs encontrados para os filtros atuais: {total}")

    def _fill_table(self):
        self.tbl.setRowCount(0)
        for i, d in enumerate(self._filtrados):
            self.tbl.insertRow(i)
            self.tbl.setRowHeight(i, 28)
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
                "Abrir" if d.get("pdf_rede") else "Sem PDF",
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if c in (0, 1, 2, 6, 7, 10):
                    it.setTextAlignment(Qt.AlignCenter)
                self.tbl.setItem(i, c, it)
            if d.get("pdf_rede"):
                btn = QPushButton("Abrir")
                btn.setObjectName("tablePdfButton")
                btn.clicked.connect(lambda _, p=d.get("pdf_rede"): self._abrir_pdf(p))
                self.tbl.setCellWidget(i, 10, btn)

    def _abrir_pdf(self, caminho):
        if not caminho or not os.path.exists(caminho):
            QMessageBox.warning(self, "PDF", "PDF nao encontrado.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(caminho))

    def _fmt(self, v):
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
