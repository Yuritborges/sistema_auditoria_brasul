import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
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

from app.ui.consulta_readonly import configurar_tabela_consulta


class FiscalizacaoWidget(QWidget):
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
        t = QLabel("Fiscalização (Vistorias e RNC)")
        t.setObjectName("moduleHeroTitle")
        d = QLabel("Registre vistoria, abra RNCs e anexe evidências por caminho de arquivo.")
        d.setObjectName("moduleHeroDesc")
        hero.addWidget(t)
        hero.addWidget(d)
        root.addLayout(hero)

        form = QFrame(); form.setObjectName("panelCard")
        g = QGridLayout(form)
        g.setContentsMargins(16, 14, 16, 14)

        self.ed_obra = QLineEdit(); self.ed_obra.setPlaceholderText("Obra")
        self.ed_contrato = QLineEdit(); self.ed_contrato.setPlaceholderText("ID contrato (opcional)")
        self.ed_data = QLineEdit(); self.ed_data.setPlaceholderText("Data vistoria (dd/mm/aaaa)")
        self.ed_resp = QLineEdit(); self.ed_resp.setPlaceholderText("Responsável")
        self.ed_resumo = QLineEdit(); self.ed_resumo.setPlaceholderText("Resumo vistoria")

        self.ed_vistoria_id = QLineEdit(); self.ed_vistoria_id.setPlaceholderText("ID vistoria")
        self.ed_rnc_obra = QLineEdit(); self.ed_rnc_obra.setPlaceholderText("Obra RNC")
        self.ed_rnc_desc = QLineEdit(); self.ed_rnc_desc.setPlaceholderText("Descrição RNC")
        self.ed_rnc_prazo = QLineEdit(); self.ed_rnc_prazo.setPlaceholderText("Prazo solução (dd/mm/aaaa)")
        self.ed_rnc_acao = QLineEdit(); self.ed_rnc_acao.setPlaceholderText("Ação corretiva")

        self.ed_rnc_id = QLineEdit(); self.ed_rnc_id.setPlaceholderText("ID RNC p/ anexo")

        btn_v = QPushButton("Salvar vistoria")
        btn_v.clicked.connect(self._salvar_vistoria)
        btn_r = QPushButton("Abrir RNC")
        btn_r.setObjectName("secondaryButton")
        btn_r.clicked.connect(self._abrir_rnc)
        btn_a = QPushButton("Anexar arquivo na RNC")
        btn_a.setObjectName("secondaryButton")
        btn_a.clicked.connect(self._anexar)

        g.addWidget(QLabel("Obra"), 0, 0); g.addWidget(self.ed_obra, 0, 1)
        g.addWidget(QLabel("Contrato"), 0, 2); g.addWidget(self.ed_contrato, 0, 3)
        g.addWidget(QLabel("Data"), 1, 0); g.addWidget(self.ed_data, 1, 1)
        g.addWidget(QLabel("Responsável"), 1, 2); g.addWidget(self.ed_resp, 1, 3)
        g.addWidget(QLabel("Resumo"), 2, 0); g.addWidget(self.ed_resumo, 2, 1, 1, 2)
        g.addWidget(btn_v, 2, 3)

        g.addWidget(QLabel("Vistoria ID"), 3, 0); g.addWidget(self.ed_vistoria_id, 3, 1)
        g.addWidget(QLabel("Obra RNC"), 3, 2); g.addWidget(self.ed_rnc_obra, 3, 3)
        g.addWidget(QLabel("Descrição RNC"), 4, 0); g.addWidget(self.ed_rnc_desc, 4, 1, 1, 2)
        g.addWidget(btn_r, 4, 3)
        g.addWidget(QLabel("Prazo"), 5, 0); g.addWidget(self.ed_rnc_prazo, 5, 1)
        g.addWidget(QLabel("Ação"), 5, 2); g.addWidget(self.ed_rnc_acao, 5, 3)

        g.addWidget(QLabel("RNC ID"), 6, 0); g.addWidget(self.ed_rnc_id, 6, 1)
        g.addWidget(btn_a, 6, 3)

        root.addWidget(form)

        row = QGridLayout()

        v_card = QFrame(); v_card.setObjectName("panelCard")
        v_l = QVBoxLayout(v_card); v_l.setContentsMargins(12, 12, 12, 12)
        self.tbl_v = QTableWidget(0, 5)
        self.tbl_v.setHorizontalHeaderLabels(["ID", "Obra", "Data", "Resp.", "Status"])
        self.tbl_v.verticalHeader().setVisible(False)
        self.tbl_v.setAlternatingRowColors(True)
        self.tbl_v.setShowGrid(False)
        self.tbl_v.setFocusPolicy(Qt.NoFocus)
        self.tbl_v.setColumnWidth(0, 50)
        self.tbl_v.setColumnWidth(1, 160)
        self.tbl_v.setColumnWidth(2, 95)
        self.tbl_v.setColumnWidth(3, 120)
        self.tbl_v.setColumnWidth(4, 90)
        configurar_tabela_consulta(self.tbl_v)
        v_l.addWidget(self.tbl_v)

        r_card = QFrame(); r_card.setObjectName("panelCard")
        r_l = QVBoxLayout(r_card); r_l.setContentsMargins(12, 12, 12, 12)
        self.tbl_r = QTableWidget(0, 6)
        self.tbl_r.setHorizontalHeaderLabels(["ID", "Vistoria", "Obra", "Status", "Prazo", "Descrição"])
        self.tbl_r.verticalHeader().setVisible(False)
        self.tbl_r.setAlternatingRowColors(True)
        self.tbl_r.setShowGrid(False)
        self.tbl_r.setFocusPolicy(Qt.NoFocus)
        self.tbl_r.setColumnWidth(0, 50)
        self.tbl_r.setColumnWidth(1, 70)
        self.tbl_r.setColumnWidth(2, 140)
        self.tbl_r.setColumnWidth(3, 90)
        self.tbl_r.setColumnWidth(4, 95)
        self.tbl_r.setColumnWidth(5, 220)
        configurar_tabela_consulta(self.tbl_r)
        r_l.addWidget(self.tbl_r)

        a_card = QFrame(); a_card.setObjectName("panelCard")
        a_l = QVBoxLayout(a_card); a_l.setContentsMargins(12, 12, 12, 12)
        self.tbl_a = QTableWidget(0, 3)
        self.tbl_a.setHorizontalHeaderLabels(["RNC", "Tipo", "Arquivo"])
        self.tbl_a.verticalHeader().setVisible(False)
        self.tbl_a.setAlternatingRowColors(True)
        self.tbl_a.setShowGrid(False)
        self.tbl_a.setFocusPolicy(Qt.NoFocus)
        self.tbl_a.setColumnWidth(0, 50)
        self.tbl_a.setColumnWidth(1, 70)
        self.tbl_a.setColumnWidth(2, 300)
        configurar_tabela_consulta(self.tbl_a)
        a_l.addWidget(self.tbl_a)

        row.addWidget(v_card, 0, 0)
        row.addWidget(r_card, 0, 1)
        row.addWidget(a_card, 1, 0, 1, 2)
        root.addLayout(row, 1)

    def set_data(self, _dados):
        self._refresh()

    def _salvar_vistoria(self):
        try:
            cid = int((self.ed_contrato.text() or "0").strip()) if self.ed_contrato.text().strip() else None
            self.service.salvar_vistoria(
                self.ed_obra.text(),
                cid,
                self.ed_data.text(),
                self.ed_resp.text(),
                self.ed_resumo.text(),
                "ABERTA",
                self.usuario_getter(),
            )
            self._refresh()
        except Exception as e:
            QMessageBox.warning(self, "Fiscalização", f"Falha ao salvar vistoria.\n\n{e}")

    def _abrir_rnc(self):
        try:
            vistoria_id = int((self.ed_vistoria_id.text() or "0").strip())
            self.service.salvar_rnc(
                vistoria_id,
                self.ed_rnc_obra.text(),
                self.ed_rnc_desc.text(),
                self.ed_rnc_prazo.text(),
                self.ed_rnc_acao.text(),
                self.usuario_getter(),
            )
            self._refresh()
        except Exception as e:
            QMessageBox.warning(self, "RNC", f"Falha ao abrir RNC.\n\n{e}")

    def _anexar(self):
        try:
            rnc_id = int((self.ed_rnc_id.text() or "0").strip())
        except Exception:
            QMessageBox.warning(self, "RNC", "Informe o ID da RNC.")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar anexo RNC", os.getcwd(), "Arquivos (*.*)")
        if not path:
            return
        self.service.anexar_rnc(rnc_id, path, "FOTO", self.usuario_getter())
        self._refresh()

    def _refresh(self):
        vistorias = self.service.listar_vistorias()
        self.tbl_v.setRowCount(0)
        for i, v in enumerate(vistorias):
            self.tbl_v.insertRow(i)
            vals = [str(v.get("id") or ""), str(v.get("obra") or ""), str(v.get("data_vistoria") or ""), str(v.get("responsavel") or ""), str(v.get("status") or "")]
            for c, val in enumerate(vals):
                it = QTableWidgetItem(val)
                if c in (0, 2, 4):
                    it.setTextAlignment(Qt.AlignCenter)
                self.tbl_v.setItem(i, c, it)

        rncs = self.service.listar_rncs()
        self.tbl_r.setRowCount(0)
        for i, r in enumerate(rncs):
            self.tbl_r.insertRow(i)
            vals = [str(r.get("id") or ""), str(r.get("vistoria_id") or ""), str(r.get("obra") or ""), str(r.get("status") or ""), str(r.get("prazo_solucao") or ""), str(r.get("descricao") or "")]
            for c, val in enumerate(vals):
                it = QTableWidgetItem(val)
                if c in (0, 1, 3):
                    it.setTextAlignment(Qt.AlignCenter)
                self.tbl_r.setItem(i, c, it)

        anexos = self.service.listar_rnc_anexos()
        self.tbl_a.setRowCount(0)
        for i, a in enumerate(anexos):
            self.tbl_a.insertRow(i)
            vals = [str(a.get("rnc_id") or ""), str(a.get("tipo") or ""), str(a.get("caminho_arquivo") or "")]
            for c, val in enumerate(vals):
                it = QTableWidgetItem(val)
                if c in (0, 1):
                    it.setTextAlignment(Qt.AlignCenter)
                self.tbl_a.setItem(i, c, it)
