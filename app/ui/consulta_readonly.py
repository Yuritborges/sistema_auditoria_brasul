"""Dados exibidos em telas de auditoria/consulta: não editáveis na UI (somente leitura)."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QTableWidget, QTableWidgetItem


def configurar_tabela_consulta(tbl: QTableWidget) -> None:
    """Impede edição inline, arrastar valores e similares em grades de consulta."""
    tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    tbl.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
    tbl.setDropIndicatorShown(False)


def item_consulta(text: str) -> QTableWidgetItem:
    """Célula de dados auditados — não editável."""
    it = QTableWidgetItem(text)
    it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return it
