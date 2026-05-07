from PySide6.QtCore import Qt
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


class ContratosWidget(QWidget):
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
        hero.setSpacing(4)
        t = QLabel("Contratos e aditivos")
        t.setObjectName("moduleHeroTitle")
        d = QLabel("Cadastro contratual base para medição, conciliação e fiscalização.")
        d.setObjectName("moduleHeroDesc")
        hero.addWidget(t)
        hero.addWidget(d)
        root.addLayout(hero)

        form_card = QFrame()
        form_card.setObjectName("panelCard")
        f = QGridLayout(form_card)
        f.setContentsMargins(16, 14, 16, 14)
        f.setHorizontalSpacing(12)
        f.setVerticalSpacing(10)

        self.ed_num = QLineEdit()
        self.ed_num.setPlaceholderText("Número contrato")
        self.ed_obra = QLineEdit()
        self.ed_obra.setPlaceholderText("Obra")
        self.ed_obj = QLineEdit()
        self.ed_obj.setPlaceholderText("Objeto")
        self.ed_val = QLineEdit()
        self.ed_val.setPlaceholderText("Valor global")
        self.ed_ini = QLineEdit()
        self.ed_ini.setPlaceholderText("Início (dd/mm/aaaa)")
        self.ed_fim = QLineEdit()
        self.ed_fim.setPlaceholderText("Fim (dd/mm/aaaa)")

        self.ed_ad_tipo = QLineEdit()
        self.ed_ad_tipo.setPlaceholderText("Tipo aditivo")
        self.ed_ad_desc = QLineEdit()
        self.ed_ad_desc.setPlaceholderText("Descrição aditivo")
        self.ed_ad_val = QLineEdit()
        self.ed_ad_val.setPlaceholderText("Valor aditivo")
        self.ed_ad_prazo = QLineEdit()
        self.ed_ad_prazo.setPlaceholderText("Prazo dias")
        self.ed_ad_data = QLineEdit()
        self.ed_ad_data.setPlaceholderText("Data aditivo (dd/mm/aaaa)")

        btn_salvar = QPushButton("Salvar contrato")
        btn_salvar.clicked.connect(self._salvar_contrato)
        btn_del = QPushButton("Remover contrato")
        btn_del.setObjectName("secondaryButton")
        btn_del.clicked.connect(self._remover)
        btn_ad = QPushButton("Registrar aditivo")
        btn_ad.setObjectName("secondaryButton")
        btn_ad.clicked.connect(self._salvar_aditivo)

        f.addWidget(QLabel("Contrato"), 0, 0)
        f.addWidget(self.ed_num, 0, 1)
        f.addWidget(QLabel("Obra"), 0, 2)
        f.addWidget(self.ed_obra, 0, 3)
        f.addWidget(QLabel("Objeto"), 1, 0)
        f.addWidget(self.ed_obj, 1, 1, 1, 3)
        f.addWidget(QLabel("Valor"), 2, 0)
        f.addWidget(self.ed_val, 2, 1)
        f.addWidget(QLabel("Início"), 2, 2)
        f.addWidget(self.ed_ini, 2, 3)
        f.addWidget(QLabel("Fim"), 3, 0)
        f.addWidget(self.ed_fim, 3, 1)
        f.addWidget(btn_salvar, 3, 2)
        f.addWidget(btn_del, 3, 3)

        f.addWidget(QLabel("Aditivo tipo"), 4, 0)
        f.addWidget(self.ed_ad_tipo, 4, 1)
        f.addWidget(QLabel("Descrição"), 4, 2)
        f.addWidget(self.ed_ad_desc, 4, 3)
        f.addWidget(QLabel("Valor"), 5, 0)
        f.addWidget(self.ed_ad_val, 5, 1)
        f.addWidget(QLabel("Prazo dias"), 5, 2)
        f.addWidget(self.ed_ad_prazo, 5, 3)
        f.addWidget(QLabel("Data aditivo"), 6, 0)
        f.addWidget(self.ed_ad_data, 6, 1)
        f.addWidget(btn_ad, 6, 3)

        root.addWidget(form_card)

        row = QHBoxLayout()
        row.setSpacing(10)

        c_card = QFrame()
        c_card.setObjectName("panelCard")
        c_l = QVBoxLayout(c_card)
        c_l.setContentsMargins(12, 12, 12, 12)
        self.tbl = QTableWidget(0, 7)
        self.tbl.setHorizontalHeaderLabels(["ID", "Número", "Obra", "Objeto", "Valor", "Atualizado", "Status"])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setShowGrid(False)
        self.tbl.setFocusPolicy(Qt.ClickFocus)
        self.tbl.setColumnWidth(0, 50)
        self.tbl.setColumnWidth(1, 110)
        self.tbl.setColumnWidth(2, 170)
        self.tbl.setColumnWidth(3, 220)
        self.tbl.setColumnWidth(4, 100)
        self.tbl.setColumnWidth(5, 110)
        self.tbl.setColumnWidth(6, 90)
        c_l.addWidget(self.tbl)

        a_card = QFrame()
        a_card.setObjectName("panelCard")
        a_l = QVBoxLayout(a_card)
        a_l.setContentsMargins(12, 12, 12, 12)
        self.tbl_ad = QTableWidget(0, 6)
        self.tbl_ad.setHorizontalHeaderLabels(["Contrato ID", "Tipo", "Descrição", "Valor", "Prazo", "Data"])
        self.tbl_ad.verticalHeader().setVisible(False)
        self.tbl_ad.setAlternatingRowColors(True)
        self.tbl_ad.setShowGrid(False)
        self.tbl_ad.setFocusPolicy(Qt.NoFocus)
        self.tbl_ad.setColumnWidth(0, 90)
        self.tbl_ad.setColumnWidth(1, 90)
        self.tbl_ad.setColumnWidth(2, 180)
        self.tbl_ad.setColumnWidth(3, 90)
        self.tbl_ad.setColumnWidth(4, 70)
        self.tbl_ad.setColumnWidth(5, 90)
        a_l.addWidget(self.tbl_ad)

        row.addWidget(c_card, 3)
        row.addWidget(a_card, 2)
        root.addLayout(row, 1)

    def set_data(self, _dados):
        self._refresh()

    def _selected_contract_id(self):
        r = self.tbl.currentRow()
        if r < 0:
            return 0
        it = self.tbl.item(r, 0)
        if not it:
            return 0
        try:
            return int(it.text())
        except Exception:
            return 0

    def _salvar_contrato(self):
        try:
            val = float((self.ed_val.text() or "0").replace(".", "").replace(",", "."))
            self.service.salvar_contrato(
                self.ed_num.text(),
                self.ed_obra.text(),
                self.ed_obj.text(),
                val,
                self.ed_ini.text(),
                self.ed_fim.text(),
                self.usuario_getter(),
            )
            self._refresh()
        except Exception as e:
            QMessageBox.warning(self, "Contrato", f"Falha ao salvar contrato.\n\n{e}")

    def _remover(self):
        cid = self._selected_contract_id()
        if not cid:
            QMessageBox.warning(self, "Contrato", "Selecione um contrato.")
            return
        self.service.remover_contrato(cid, self.usuario_getter())
        self._refresh()

    def _salvar_aditivo(self):
        cid = self._selected_contract_id()
        if not cid:
            QMessageBox.warning(self, "Aditivo", "Selecione um contrato na tabela.")
            return
        try:
            valor = float((self.ed_ad_val.text() or "0").replace(".", "").replace(",", "."))
            prazo = int((self.ed_ad_prazo.text() or "0").strip())
            self.service.salvar_aditivo(
                cid,
                self.ed_ad_tipo.text(),
                self.ed_ad_desc.text(),
                valor,
                prazo,
                self.ed_ad_data.text(),
                self.usuario_getter(),
            )
            self._refresh()
        except Exception as e:
            QMessageBox.warning(self, "Aditivo", f"Falha ao salvar aditivo.\n\n{e}")

    def _refresh(self):
        contratos = self.service.listar_contratos()
        self.tbl.setRowCount(0)
        for i, c in enumerate(contratos):
            self.tbl.insertRow(i)
            self.tbl.setRowHeight(i, 30)
            vals = [
                str(c.get("id") or ""),
                str(c.get("numero") or ""),
                str(c.get("obra") or ""),
                str(c.get("objeto") or ""),
                self._fmt(c.get("valor_global")),
                self._fmt(c.get("valor_atualizado")),
                str(c.get("status") or ""),
            ]
            for col, val in enumerate(vals):
                it = QTableWidgetItem(val)
                if col in (0, 4, 5):
                    it.setTextAlignment(Qt.AlignCenter)
                self.tbl.setItem(i, col, it)

        aditivos = self.service.listar_aditivos()
        self.tbl_ad.setRowCount(0)
        for i, ad in enumerate(aditivos):
            self.tbl_ad.insertRow(i)
            vals = [
                str(ad.get("contrato_id") or ""),
                str(ad.get("tipo") or ""),
                str(ad.get("descricao") or ""),
                self._fmt(ad.get("valor")),
                str(ad.get("prazo_dias") or ""),
                str(ad.get("data_aditivo") or ""),
            ]
            for col, val in enumerate(vals):
                it = QTableWidgetItem(val)
                if col in (0, 3, 4):
                    it.setTextAlignment(Qt.AlignCenter)
                self.tbl_ad.setItem(i, col, it)

    def _fmt(self, v):
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
