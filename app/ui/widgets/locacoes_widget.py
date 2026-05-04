from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class LocacoesWidget(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        hero = QVBoxLayout()
        hero.setSpacing(4)
        ht = QLabel("Locações")
        ht.setObjectName("moduleHeroTitle")
        hd = QLabel("Reserva de estrutura para equipamentos, períodos e custos por obra.")
        hd.setObjectName("moduleHeroDesc")
        hero.addWidget(ht)
        hero.addWidget(hd)
        root.addLayout(hero)

        card = QFrame()
        card.setObjectName("panelCard")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(40, 48, 40, 48)
        inner.setSpacing(12)
        lbl = QLabel("Módulo em construção")
        lbl.setObjectName("emptyStateTitle")
        lbl.setAlignment(Qt.AlignCenter)
        sub = QLabel(
            "Próximos passos: equipamento, obra, fornecedor, início/fim, custo e status — alinhado ao fluxo de auditoria."
        )
        sub.setObjectName("emptyStateBody")
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)
        inner.addStretch()
        inner.addWidget(lbl)
        inner.addWidget(sub)
        inner.addStretch()
        root.addWidget(card, 1)
