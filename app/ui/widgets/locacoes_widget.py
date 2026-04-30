from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class LocacoesWidget(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        lbl = QLabel("Modulo de Locacoes em construcao")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size:24px;font-weight:800;color:#1f2937;")
        sub = QLabel(
            "Estrutura pronta para evoluir: equipamento, obra, fornecedor, inicio/fim, custo e status."
        )
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)
        sub.setStyleSheet("font-size:12px;color:#6b7280;")
        root.addStretch()
        root.addWidget(lbl)
        root.addWidget(sub)
        root.addStretch()
