import logging
import os
from datetime import datetime

from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.user_messages import erro_generico


class RelatoriosWidget(QWidget):
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
        hero.setSpacing(4)
        ht = QLabel("Relatórios")
        ht.setObjectName("moduleHeroTitle")
        hd = QLabel("Exportações em CSV (compatível com Excel) para análises externas.")
        hd.setObjectName("moduleHeroDesc")
        hero.addWidget(ht)
        hero.addWidget(hd)
        root.addLayout(hero)

        card = QFrame()
        card.setObjectName("panelCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)
        subtitle = QLabel("Escolha o tipo de consolidado")
        subtitle.setObjectName("sectionTitle")
        lay.addWidget(subtitle)
        grid = QGridLayout()
        grid.setSpacing(12)
        actions = [
            ("Geral por obra", self._exportar_obras),
            ("Por fornecedor", self._exportar_fornecedores),
            ("Mensal", self._exportar_mensal),
            ("Curva ABC", self._exportar_abc),
            ("Relatório mensal PDF", self._exportar_mensal_pdf),
        ]
        for i, (txt, fn) in enumerate(actions):
            b = QPushButton(txt)
            b.setObjectName("secondaryButton")
            b.clicked.connect(fn)
            grid.addWidget(b, i // 2, i % 2)
        lay.addLayout(grid)
        self.lbl = QLabel("Escolha um relatório para exportar.")
        self.lbl.setObjectName("muted")
        self.lbl.setWordWrap(True)
        lay.addWidget(self.lbl)
        root.addWidget(card)
        root.addStretch()

    def set_data(self, dados):
        self._dados = dados

    def _pick_path(self, sug):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar relatório", sug, "CSV (*.csv)")
        return path

    def _pick_pdf_path(self, sug):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar relatório mensal", sug, "PDF (*.pdf)")
        return path

    def _exportar_obras(self):
        agg = self.service.dashboard_summary(self._dados)["top_obras"]
        linhas = [{"obra": a, "valor_total": b} for a, b in agg]
        self._save("relatorio_obras", ["obra", "valor_total"], linhas)

    def _exportar_fornecedores(self):
        agg = self.service.dashboard_summary(self._dados)["top_fornecedores"]
        linhas = [{"fornecedor": a, "valor_total": b} for a, b in agg]
        self._save("relatorio_fornecedores", ["fornecedor", "valor_total"], linhas)

    def _exportar_mensal(self):
        mensal = self.service.dashboard_summary(self._dados)["mensal"]
        linhas = [{"mes": k, "valor_total": v} for k, v in mensal.items()]
        self._save("relatorio_mensal", ["mes", "valor_total"], linhas)

    def _exportar_abc(self):
        itens = self.service.dashboard_summary(self._dados)["top_itens"]
        total = sum(v for _, v in itens) or 1
        acum = 0.0
        linhas = []
        for item, qtd in itens:
            perc = (qtd / total) * 100
            acum += perc
            cls = "A" if acum <= 80 else ("B" if acum <= 95 else "C")
            linhas.append({"item": item, "qtd": qtd, "perc": round(perc, 2), "classe": cls})
        self._save("relatorio_curva_abc", ["item", "qtd", "perc", "classe"], linhas)

    def _exportar_mensal_pdf(self):
        sugestao = os.path.join(os.getcwd(), f"relatorio_mensal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        path = self._pick_pdf_path(sugestao)
        if not path:
            return
        try:
            self.service.gerar_relatorio_mensal_pdf(path, "01/01/2026", datetime.now().strftime("%d/%m/%Y"), self._dados)
            self.lbl.setText(f"PDF gerado: {path}")
        except Exception:
            logging.getLogger(__name__).exception("Falha ao gerar PDF mensal")
            QMessageBox.critical(self, "Erro", erro_generico("gerar o relatório mensal"))

    def _save(self, nome, colunas, linhas):
        sugestao = os.path.join(os.getcwd(), f"{nome}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        path = self._pick_path(sugestao)
        if not path:
            return
        try:
            self.service.exportar_csv(path, colunas, linhas)
            self.lbl.setText(f"Arquivo gerado: {path}")
        except Exception:
            logging.getLogger(__name__).exception("Falha ao gerar relatório")
            QMessageBox.critical(self, "Erro", erro_generico("gerar o relatório"))
