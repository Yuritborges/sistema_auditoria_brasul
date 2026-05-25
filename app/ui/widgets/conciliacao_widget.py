from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import logging

from app.ui.consulta_readonly import configurar_tabela_consulta
from app.ui.user_messages import erro_salvar


class ConciliacaoWidget(QWidget):
    def __init__(self, service, usuario_getter):
        super().__init__()
        self.service = service
        self.usuario_getter = usuario_getter
        self._dados = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        hero = QVBoxLayout()
        t = QLabel("Conciliação NF x Pedido x Medição")
        t.setObjectName("moduleHeroTitle")
        d = QLabel("Registre notas fiscais e identifique divergências automaticamente.")
        d.setObjectName("moduleHeroDesc")
        hero.addWidget(t)
        hero.addWidget(d)
        root.addLayout(hero)

        form = QFrame()
        form.setObjectName("panelCard")
        g = QGridLayout(form)
        g.setContentsMargins(16, 14, 16, 14)

        self.ed_nf = QLineEdit(); self.ed_nf.setPlaceholderText("Nº NF")
        self.ed_pedido = QLineEdit(); self.ed_pedido.setPlaceholderText("Pedido")
        self.ed_contrato = QLineEdit(); self.ed_contrato.setPlaceholderText("ID contrato")
        self.ed_obra = QLineEdit(); self.ed_obra.setPlaceholderText("Obra")
        self.ed_forn = QLineEdit(); self.ed_forn.setPlaceholderText("Fornecedor")
        self.ed_valor = QLineEdit(); self.ed_valor.setPlaceholderText("Valor")
        self.ed_data = QLineEdit(); self.ed_data.setPlaceholderText("Data emissão (dd/mm/aaaa)")
        self.ed_status = QLineEdit(); self.ed_status.setPlaceholderText("Status (ABERTA/RESOLVIDA)")
        self.ed_just = QLineEdit(); self.ed_just.setPlaceholderText("Justificativa")

        btn_save = QPushButton("Salvar NF")
        btn_save.clicked.connect(self._salvar_nf)
        btn_run = QPushButton("Rodar conciliação")
        btn_run.setObjectName("secondaryButton")
        btn_run.clicked.connect(self._refresh)

        g.addWidget(QLabel("NF"), 0, 0); g.addWidget(self.ed_nf, 0, 1)
        g.addWidget(QLabel("Pedido"), 0, 2); g.addWidget(self.ed_pedido, 0, 3)
        g.addWidget(QLabel("Contrato"), 1, 0); g.addWidget(self.ed_contrato, 1, 1)
        g.addWidget(QLabel("Obra"), 1, 2); g.addWidget(self.ed_obra, 1, 3)
        g.addWidget(QLabel("Fornecedor"), 2, 0); g.addWidget(self.ed_forn, 2, 1)
        g.addWidget(QLabel("Valor"), 2, 2); g.addWidget(self.ed_valor, 2, 3)
        g.addWidget(QLabel("Data"), 3, 0); g.addWidget(self.ed_data, 3, 1)
        g.addWidget(QLabel("Status"), 3, 2); g.addWidget(self.ed_status, 3, 3)
        g.addWidget(QLabel("Justificativa"), 4, 0); g.addWidget(self.ed_just, 4, 1, 1, 2)
        g.addWidget(btn_save, 4, 3)
        g.addWidget(btn_run, 5, 3)

        root.addWidget(form)

        card = QFrame()
        card.setObjectName("panelCard")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 12, 12, 12)
        self.tbl = QTableWidget(0, 8)
        self.tbl.setHorizontalHeaderLabels(["NF", "Pedido", "Fornecedor", "Valor", "Status", "Flags", "Contrato", "Data"])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setShowGrid(False)
        self.tbl.setFocusPolicy(Qt.NoFocus)
        self.tbl.setColumnWidth(0, 90)
        self.tbl.setColumnWidth(1, 90)
        self.tbl.setColumnWidth(2, 160)
        self.tbl.setColumnWidth(3, 100)
        self.tbl.setColumnWidth(4, 95)
        self.tbl.setColumnWidth(5, 260)
        self.tbl.setColumnWidth(6, 70)
        self.tbl.setColumnWidth(7, 100)
        configurar_tabela_consulta(self.tbl)
        cl.addWidget(self.tbl)
        root.addWidget(card, 1)

    def set_data(self, dados):
        self._dados = dados
        self._refresh()

    def _salvar_nf(self):
        try:
            cid = int((self.ed_contrato.text() or "0").strip()) if self.ed_contrato.text().strip() else None
            val = float((self.ed_valor.text() or "0").replace(".", "").replace(",", "."))
            status = (self.ed_status.text() or "ABERTA").strip().upper()
            self.service.salvar_nota_fiscal(
                self.ed_nf.text(),
                self.ed_pedido.text(),
                cid,
                self.ed_obra.text(),
                self.ed_forn.text(),
                val,
                self.ed_data.text(),
                status,
                self.ed_just.text(),
                self.usuario_getter(),
            )
            self._refresh()
        except Exception:
            logging.getLogger(__name__).exception("Falha ao salvar NF")
            QMessageBox.warning(self, "Conciliação", erro_salvar("a nota fiscal"))

    def _refresh(self):
        rows = self.service.conciliar_nf_pedidos_medicoes(self._dados)
        self.tbl.setRowCount(0)
        for i, r in enumerate(rows):
            self.tbl.insertRow(i)
            flags = ", ".join(r.get("flags") or []) or "-"
            vals = [
                str(r.get("numero_nf") or ""),
                str(r.get("pedido_numero") or ""),
                str(r.get("fornecedor") or ""),
                self._fmt(r.get("valor")),
                str(r.get("status") or ""),
                flags,
                str(r.get("contrato_id") or ""),
                str(r.get("data_emissao") or ""),
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if c in (0, 1, 3, 4, 6):
                    it.setTextAlignment(Qt.AlignCenter)
                self.tbl.setItem(i, c, it)

    def _fmt(self, v):
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
