import os
from datetime import datetime

from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget


class RelatoriosWidget(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self._dados = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        title = QLabel("Relatorios")
        title.setObjectName("sectionTitle")
        root.addWidget(title)
        subtitle = QLabel("Exportacoes prioritarias (CSV compativel com Excel)")
        subtitle.setObjectName("muted")
        root.addWidget(subtitle)
        row = QHBoxLayout()
        for txt, fn in [
            ("Geral por obra", self._exportar_obras),
            ("Por fornecedor", self._exportar_fornecedores),
            ("Mensal", self._exportar_mensal),
            ("Curva ABC", self._exportar_abc),
        ]:
            b = QPushButton(txt)
            b.setObjectName("secondaryButton")
            b.clicked.connect(fn)
            row.addWidget(b)
        root.addLayout(row)
        self.lbl = QLabel("Escolha um relatorio para exportar.")
        root.addWidget(self.lbl)
        root.addStretch()

    def set_data(self, dados):
        self._dados = dados

    def _pick_path(self, sug):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar relatorio", sug, "CSV (*.csv)")
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

    def _save(self, nome, colunas, linhas):
        sugestao = os.path.join(os.getcwd(), f"{nome}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        path = self._pick_path(sugestao)
        if not path:
            return
        try:
            self.service.exportar_csv(path, colunas, linhas)
            self.lbl.setText(f"Arquivo gerado: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao gerar relatorio.\n\n{e}")
