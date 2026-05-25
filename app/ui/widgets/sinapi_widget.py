import logging
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
from app.ui.user_messages import erro_generico


class SinapiWidget(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self._dados = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        hero = QVBoxLayout()
        t = QLabel("SINAPI")
        t.setObjectName("moduleHeroTitle")
        d = QLabel("Importe a tabela mensal e compare variação dos itens dos pedidos.")
        d.setObjectName("moduleHeroDesc")
        hero.addWidget(t)
        hero.addWidget(d)
        root.addLayout(hero)

        form = QFrame(); form.setObjectName("panelCard")
        g = QGridLayout(form)
        g.setContentsMargins(16, 14, 16, 14)
        self.ed_comp = QLineEdit(); self.ed_comp.setPlaceholderText("Competência (aaaa-mm)")
        self.ed_uf = QLineEdit(); self.ed_uf.setText("SP")
        btn_import = QPushButton("Atualizar SINAPI (CSV)")
        btn_import.clicked.connect(self._importar)
        btn_comp = QPushButton("Comparar com pedidos")
        btn_comp.setObjectName("secondaryButton")
        btn_comp.clicked.connect(self._comparar)
        self.lbl_msg = QLabel("Aguardando importação.")
        self.lbl_msg.setObjectName("muted")

        g.addWidget(QLabel("Competência"), 0, 0); g.addWidget(self.ed_comp, 0, 1)
        g.addWidget(QLabel("UF"), 0, 2); g.addWidget(self.ed_uf, 0, 3)
        g.addWidget(btn_import, 1, 2)
        g.addWidget(btn_comp, 1, 3)
        g.addWidget(self.lbl_msg, 2, 0, 1, 4)
        root.addWidget(form)

        card = QFrame(); card.setObjectName("panelCard")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 12, 12, 12)
        self.tbl = QTableWidget(0, 7)
        self.tbl.setHorizontalHeaderLabels(["Pedido", "Item", "Código", "Preço item", "Preço SINAPI", "Variação %", "Alerta"])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setShowGrid(False)
        self.tbl.setFocusPolicy(Qt.NoFocus)
        self.tbl.setColumnWidth(0, 80)
        self.tbl.setColumnWidth(1, 260)
        self.tbl.setColumnWidth(2, 90)
        self.tbl.setColumnWidth(3, 110)
        self.tbl.setColumnWidth(4, 110)
        self.tbl.setColumnWidth(5, 95)
        self.tbl.setColumnWidth(6, 100)
        configurar_tabela_consulta(self.tbl)
        cl.addWidget(self.tbl)
        root.addWidget(card, 1)

    def set_data(self, dados):
        self._dados = dados

    def _importar(self):
        comp = self.ed_comp.text().strip()
        uf = (self.ed_uf.text() or "SP").strip().upper()
        if not comp:
            QMessageBox.warning(self, "SINAPI", "Informe a competência.")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar CSV SINAPI", os.getcwd(), "CSV (*.csv)")
        if not path:
            return
        try:
            total = self.service.importar_sinapi_csv(path, comp, uf)
            self.lbl_msg.setText(f"SINAPI atualizado: {total} itens importados para {comp}/{uf}.")
        except Exception:
            logging.getLogger(__name__).exception("Falha ao importar SINAPI")
            QMessageBox.critical(self, "SINAPI", erro_generico("importar o arquivo"))

    def _comparar(self):
        comp = self.ed_comp.text().strip()
        uf = (self.ed_uf.text() or "SP").strip().upper()
        rows = self.service.comparar_itens_com_sinapi(self._dados, comp, uf)
        self.tbl.setRowCount(0)
        for i, r in enumerate(rows):
            self.tbl.insertRow(i)
            vals = [
                str(r.get("pedido") or ""),
                str(r.get("item") or ""),
                str(r.get("codigo_sinapi") or ""),
                self._fmt(r.get("preco_item_estimado")),
                self._fmt(r.get("preco_sinapi")),
                f"{float(r.get('variacao_percentual') or 0):.1f}%",
                str(r.get("alerta") or ""),
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if c in (0, 2, 3, 4, 5, 6):
                    it.setTextAlignment(Qt.AlignCenter)
                self.tbl.setItem(i, c, it)
        self.lbl_msg.setText(f"Comparação concluída: {len(rows)} itens com código SINAPI encontrado.")

    def _fmt(self, v):
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
