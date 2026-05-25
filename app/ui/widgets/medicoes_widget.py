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
from app.ui.widgets.brasul_combo import BrasulComboBox, garantir_combo_digitavel, preencher_combo_filtro


class MedicoesWidget(QWidget):
    def __init__(self, service, usuario_getter):
        super().__init__()
        self.service = service
        self.usuario_getter = usuario_getter
        self._contratos = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        hero = QVBoxLayout()
        ht = QLabel("Medições físico-financeiras")
        ht.setObjectName("moduleHeroTitle")
        hd = QLabel(
            "Registre medições por contrato. Os pedidos consolidados aparecem em Obras/Pedidos; "
            "cadastre o contrato em Contratos antes de medir."
        )
        hd.setObjectName("moduleHeroDesc")
        hero.addWidget(ht)
        hero.addWidget(hd)
        root.addLayout(hero)

        form = QFrame()
        form.setObjectName("panelCard")
        g = QGridLayout(form)
        g.setContentsMargins(16, 14, 16, 14)

        self.cb_contrato = BrasulComboBox()
        garantir_combo_digitavel(self.cb_contrato)
        le = self.cb_contrato.lineEdit()
        if le is not None:
            le.setPlaceholderText("Selecione ou digite ID do contrato…")
        self.cb_contrato.currentTextChanged.connect(self._ao_escolher_contrato)

        self.ed_obra = QLineEdit()
        self.ed_obra.setPlaceholderText("Obra (preenchida pelo contrato)")
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

        g.addWidget(QLabel("Contrato"), 0, 0)
        g.addWidget(self.cb_contrato, 0, 1, 1, 3)
        g.addWidget(QLabel("Obra"), 1, 0)
        g.addWidget(self.ed_obra, 1, 1, 1, 3)
        g.addWidget(QLabel("Competência"), 2, 0)
        g.addWidget(self.ed_comp, 2, 1)
        g.addWidget(QLabel("% físico"), 2, 2)
        g.addWidget(self.ed_fis, 2, 3)
        g.addWidget(QLabel("Valor medido"), 3, 0)
        g.addWidget(self.ed_val, 3, 1)
        g.addWidget(QLabel("Responsável"), 3, 2)
        g.addWidget(self.ed_resp, 3, 3)
        g.addWidget(QLabel("Obs"), 4, 0)
        g.addWidget(self.ed_obs, 4, 1, 1, 2)
        g.addWidget(btn, 4, 3)

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
        configurar_tabela_consulta(self.tbl)
        cl.addWidget(self.tbl)
        root.addWidget(card, 1)

        self._preencher_contratos()

    def _rotulos_contratos(self):
        self._contratos = self.service.listar_contratos()
        rotulos = []
        for c in self._contratos:
            cid = int(c.get("id") or 0)
            num = (c.get("numero") or "").strip()
            obra = (c.get("obra") or "").strip()
            rotulos.append(f"{cid} — {num} — {obra}" if obra else f"{cid} — {num}")
        return rotulos

    def _preencher_contratos(self):
        atual = self.cb_contrato.currentText()
        preencher_combo_filtro(
            self.cb_contrato,
            self._rotulos_contratos(),
            atual,
            "Contrato cadastrado…",
        )

    def _contrato_id_do_texto(self, texto: str) -> int:
        t = (texto or "").strip()
        if not t:
            return 0
        parte = t.split("—", 1)[0].strip()
        try:
            return int(parte)
        except ValueError:
            for c in self._contratos:
                rotulo = f"{c.get('id')} — {c.get('numero')}"
                if t.startswith(str(c.get("id"))) or t == rotulo:
                    return int(c.get("id") or 0)
        return 0

    def _ao_escolher_contrato(self, texto: str):
        cid = self._contrato_id_do_texto(texto)
        for c in self._contratos:
            if int(c.get("id") or 0) == cid:
                self.ed_obra.setText((c.get("obra") or "").strip())
                return

    def set_data(self, _dados):
        self._preencher_contratos()
        self._refresh()

    def _salvar(self):
        try:
            contrato_id = self._contrato_id_do_texto(self.cb_contrato.currentText())
            if contrato_id <= 0:
                raise ValueError("Selecione um contrato válido (cadastre em Contratos).")
            perc = float((self.ed_fis.text() or "0").replace(",", "."))
            val = float((self.ed_val.text() or "0").replace(".", "").replace(",", "."))
        except ValueError as e:
            QMessageBox.warning(self, "Medição", str(e))
            return
        try:
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
            QMessageBox.information(self, "Medição", "Medição registrada.")
            self._refresh()
        except Exception:
            logging.getLogger(__name__).exception("Falha ao salvar medição")
            QMessageBox.critical(self, "Erro", erro_salvar("a medição"))

    def _refresh(self):
        rows = self.service.resumo_fisico_financeiro()
        self.tbl.setRowCount(len(rows))
        for i, r in enumerate(rows):
            vals = [
                str(r.get("contrato_id") or ""),
                str(r.get("obra") or ""),
                str(r.get("competencia") or ""),
                f"{float(r.get('percentual_fisico') or 0):.1f}",
                f"{float(r.get('percentual_financeiro') or 0):.1f}",
                f"{float(r.get('gap_fisico_financeiro') or 0):.1f}",
                f"R$ {float(r.get('valor_medido') or 0):,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", "."),
                f"R$ {float(r.get('valor_contrato') or 0):,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", "."),
                str(r.get("responsavel") or ""),
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if c != 1:
                    it.setTextAlignment(Qt.AlignCenter)
                self.tbl.setItem(i, c, it)
