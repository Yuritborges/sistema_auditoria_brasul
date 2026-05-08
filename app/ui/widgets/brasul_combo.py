"""QComboBox com lista suspensa legível no Windows (Fusion + QSS global com QWidget transparente).

O app usa QWidget { background: transparent } para cartões; o popup do combo é uma janela
à parte e herdava transparência → fundo preto nativo. Forçamos paleta + QSS na árvore do popup.
"""

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPalette, QPolygon
from PySide6.QtWidgets import QComboBox, QCompleter, QWidget


def _popup_stylesheet():
    return """
    QWidget {
        background-color: #ffffff;
        color: #0f172a;
    }
    QAbstractItemView {
        background-color: #ffffff;
        color: #0f172a;
        alternate-background-color: #ffffff;
        outline: none;
        border: 1px solid #93c5fd;
    }
    QAbstractItemView::item {
        min-height: 28px;
        padding: 6px 10px;
        border-radius: 6px;
        border: 1px solid transparent;
        margin: 2px 4px;
    }
    QAbstractItemView::item:hover {
        background-color: #f8fafc;
        border: 1px solid #bfdbfe;
    }
    QAbstractItemView::item:selected {
        background-color: #eff6ff;
        color: #0f172a;
        border: 1px solid #3b82f6;
    }
    QAbstractScrollArea {
        background-color: #ffffff;
        border: none;
    }
    QWidget#brasulComboViewport {
        background-color: #ffffff;
    }
    QScrollBar:vertical {
        background: #e8edf3;
        width: 14px;
        margin: 0;
        border: none;
        border-radius: 7px;
    }
    QScrollBar::handle:vertical {
        background: #94a3b8;
        border-radius: 7px;
        min-height: 32px;
        margin: 3px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
        width: 0;
    }
    """


def _opaque_palette():
    pal = QPalette()
    white = QColor("#ffffff")
    text = QColor("#0f172a")
    pal.setColor(QPalette.ColorRole.Window, white)
    pal.setColor(QPalette.ColorRole.Base, white)
    pal.setColor(QPalette.ColorRole.Button, white)
    pal.setColor(QPalette.ColorRole.Text, text)
    pal.setColor(QPalette.ColorRole.WindowText, text)
    return pal


def _paint_popup_branch(root: QWidget):
    pal = _opaque_palette()
    stack = [root]
    seen = set()
    while stack:
        w = stack.pop()
        if id(w) in seen:
            continue
        seen.add(id(w))
        w.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        w.setAutoFillBackground(True)
        w.setPalette(pal)
        for c in w.children():
            if isinstance(c, QWidget):
                stack.append(c)


class BrasulComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.setDuplicatesEnabled(False)
        self.setMaxVisibleItems(20)

        comp = QCompleter(self.model(), self)
        comp.setCaseSensitivity(Qt.CaseInsensitive)
        comp.setFilterMode(Qt.MatchContains)
        comp.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setCompleter(comp)

        le = self.lineEdit()
        if le is not None:
            le.setClearButtonEnabled(False)
            le.setTextMargins(0, 0, 18, 0)
            le.returnPressed.connect(self._normalize_typed_value)

    def _normalize_typed_value(self):
        txt = (self.currentText() or "").strip()
        if not txt:
            return
        idx = self.findText(txt, Qt.MatchFixedString | Qt.MatchCaseSensitive)
        if idx < 0:
            idx = self.findText(txt, Qt.MatchFixedString | Qt.MatchCaseInsensitive)
        if idx < 0:
            idx = self.findText(txt, Qt.MatchStartsWith | Qt.MatchCaseInsensitive)
        if idx < 0:
            idx = self.findText(txt, Qt.MatchContains | Qt.MatchCaseInsensitive)
        if idx >= 0 and idx != self.currentIndex():
            self.setCurrentIndex(idx)

    def showPopup(self):
        super().showPopup()
        self._polish_popup()
        QTimer.singleShot(0, self._polish_popup)

    def paintEvent(self, event):
        super().paintEvent(event)
        # Seta sempre visível à direita (independente de tema/QSS da máquina).
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#64748b"))
        right = self.rect().right() - 14
        cy = self.rect().center().y()
        tri = QPolygon(
            [
                QPoint(right - 4, cy - 2),
                QPoint(right + 4, cy - 2),
                QPoint(right, cy + 3),
            ]
        )
        painter.drawPolygon(tri)
        painter.end()

    def _polish_popup(self):
        view = self.view()
        if view is None:
            return
        vp = view.viewport()
        if vp is not None:
            vp.setObjectName("brasulComboViewport")
            vp.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            vp.setAutoFillBackground(True)
            vp.setPalette(_opaque_palette())

        view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        view.setAutoFillBackground(True)
        view.setPalette(_opaque_palette())
        view.setStyleSheet(_popup_stylesheet())

        win = view.window()
        if win is not None:
            win.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            win.setAutoFillBackground(True)
            win.setPalette(_opaque_palette())
            win.setStyleSheet(_popup_stylesheet())
            _paint_popup_branch(win)
