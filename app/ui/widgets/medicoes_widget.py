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


class MedicoesWidget(QWidget):
    def __init__(self, service, usuario_getter):
        super().__init__()
        self.service = service
        self.usuario_getter = usuario_getter
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        hero = QVBoxLayout()
        ht = QLabel("Medições físico-financeiras")
        ht.setObjectName("moduleHeroTitle")
        hd = QLabel("Registre medições por contrato e acompanhe gap físico x financeiro.")
        hd.setObjectName("moduleHeroDesc")
        hero.addWidget(ht)
        hero.addWidget(hd)
        root.addLayout(hero)

        form = QFrame()
        form.setObjectName("panelCard")
        g = QGridLayout(form)
        g.setContentsMargins(16, 14, 16, 14)

        self.ed_contrato = QLineEdit()
        self.ed_contrato.setPlaceholderText("ID contrato")
        self.ed_obra = QLineEdit()
        self.ed_obra.setPlaceholderText("Obra")
        self.ed_comp = QLineEdit()
        self.ed_comp.setPlaceholderText("Competência (aaaa-mm)")
        self.ed_fis = QLineEdit()
        self.ed_fis.setPlaceholderText("% físico")
        self.ed_val = QLineEdit()
        self.ed_val.setPlaceholderText("Valor medido")
        self.ed_resp = QLineEdit()
        self.ed_resp.setPlaceholderText("Responsável")
        self.ed_obs = QLineEdit()
        self.ed_obs.setPlaceholderText("Observações")

        btn = QPushButton("Salvar medição")
        btn.clicked.connect(self._salvar)

        g.addWidget(QLabel("Contrato ID"), 0, 0)
        g.addWidget(self.ed_contrato, 0, 1)
        g.addWidget(QLabel("Obra"), 0, 2)
        g.addWidget(self.ed_obra, 0, 3)
        g.addWidget(QLabel("Competência"), 1, 0)
        g.addWidget(self.ed_comp, 1, 1)
        g.addWidget(QLabel("% físico"), 1, 2)
        g.addWidget(self.ed_fis, 1, 3)
        g.addWidget(QLabel("Valor medido"), 2, 0)
        g.addWidget(self.ed_val, 2, 1)
        g.addWidget(QLabel("Responsável"), 2, 2)
        g.addWidget(self.ed_resp, 2, 3)
        g.addWidget(QLabel("Obs"), 3, 0)
        g.addWidget(self.ed_obs, 3, 1, 1, 2)
        g.addWidget(btn, 3, 3)

        root.addWidget(form)

        card = QFrame()
        card.setObjectName("panelCard")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 12, 12, 12)
        self.tbl = QTableWidget(0, 9)
        self.tbl.setHorizontalHeaderLabels([
            "Contrato",
            "Obra",
            "Competência",
            "% Físico",
            "% Financeiro",
            "Gap",
            "Valor medido",
            "Valor contrato",
            "Resp.",
        ])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setShowGrid(False)
        self.tbl.setFocusPolicy(Qt.NoFocus)
        self.tbl.setColumnWidth(0, 70)
        self.tbl.setColumnWidth(1, 160)
        self.tbl.setColumnWidth(2, 100)
        self.tbl.setColumnWidth(3, 90)
        self.tbl.setColumnWidth(4, 100)
        self.tbl.setColumnWidth(5, 70)
        self.tbl.setColumnWidth(6, 110)
        self.tbl.setColumnWidth(7, 110)
        self.tbl.setColumnWidth(8, 100)
        cl.addWidget(self.tbl)
        root.addWidget(card, 1)

    def set_data(self, _dados):
        self._refresh()

    def _salvar(self):
        try:
            contrato_id = int((self.ed_contrato.text() or "0").strip())
            perc = float((self.ed_fis.text() or "0").replace(",", "."))
            val = float((self.ed_val.text() or "0").replace(".", "").replace(",", "."))
            self.service.salvar_medicao(
                contrato_id,
                self.ed_obra.text(),
                self.ed_comp.text(),
                perc,
                val,
                self.ed_resp.text(),
                self.ed_obs.text(),
                self.usuario_getter(),
            )
            self._refresh()
        except Exception as e:
            QMessageBox.warning(self, "Medição", f"Falha ao salvar medição.\n\n{e}")

    def _refresh(self):
        rows = self.service.resumo_fisico_financeiro()
        self.tbl.setRowCount(0)
        for i, r in enumerate(rows):
            self.tbl.insertRow(i)
            vals = [
                str(r.get("contrato_id") or ""),
                str(r.get("obra") or ""),
                str(r.get("competencia") or ""),
                f"{float(r.get('percentual_fisico') or 0):.1f}%",
                f"{float(r.get('percentual_financeiro') or 0):.1f}%",
                f"{float(r.get('gap_fisico_financeiro') or 0):.1f}pp",
                self._fmt(r.get("valor_medido")),
                self._fmt(r.get("valor_contrato")),
                str(r.get("responsavel") or ""),
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if c in (0, 2, 3, 4, 5, 6, 7):
                    it.setTextAlignment(Qt.AlignCenter)
                self.tbl.setItem(i, c, it)

    def _fmt(self, v):
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
