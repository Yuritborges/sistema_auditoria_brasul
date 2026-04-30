from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class AuditoriaWidget(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        title = QLabel("Historico de Alteracoes")
        title.setObjectName("sectionTitle")
        root.addWidget(title)
        btn = QPushButton("Atualizar historico")
        btn.setObjectName("secondaryButton")
        btn.clicked.connect(self.refresh)
        root.addWidget(btn)
        self.tbl = QTableWidget(0, 8)
        self.tbl.setHorizontalHeaderLabels(["Data/Hora", "Usuario", "Entidade", "ID", "Acao", "Campo", "Anterior", "Novo"])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.horizontalHeader().setStretchLastSection(False)
        self.tbl.setColumnWidth(0, 130)
        self.tbl.setColumnWidth(1, 90)
        self.tbl.setColumnWidth(2, 110)
        self.tbl.setColumnWidth(3, 90)
        self.tbl.setColumnWidth(4, 90)
        self.tbl.setColumnWidth(5, 120)
        self.tbl.setColumnWidth(6, 170)
        self.tbl.setColumnWidth(7, 170)
        root.addWidget(self.tbl, 1)

    def set_data(self, _dados):
        self.refresh()

    def refresh(self):
        logs = self.service.listar_logs(limit=1000)
        self.tbl.setRowCount(0)
        for i, l in enumerate(logs):
            self.tbl.insertRow(i)
            self.tbl.setRowHeight(i, 26)
            vals = [
                l.get("data_hora", ""),
                l.get("usuario", ""),
                l.get("entidade", ""),
                l.get("entidade_id", ""),
                l.get("acao", ""),
                l.get("campo", ""),
                l.get("valor_anterior", ""),
                l.get("valor_novo", ""),
            ]
            for c, v in enumerate(vals):
                self.tbl.setItem(i, c, QTableWidgetItem(str(v)))
