"""Impede que o scroll do mouse altere combos, datas e spinboxes acidentalmente."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QTimeEdit,
)


class NoWheelOnValueEditorsFilter(QObject):
    """Filtro global: wheel não muda valor; popup aberto do combo ainda pode rolar a lista."""

    def eventFilter(self, obj, event):
        if event.type() != QEvent.Type.Wheel:
            return False
        if isinstance(obj, QComboBox):
            view = obj.view()
            if view is not None and view.isVisible():
                return False
            return True
        if isinstance(obj, (QAbstractSpinBox, QDateEdit, QDateTimeEdit, QTimeEdit)):
            return True
        return False
