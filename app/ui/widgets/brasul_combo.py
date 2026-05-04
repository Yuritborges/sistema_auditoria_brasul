"""QComboBox com lista suspensa legível no Windows (Fusion + QSS global com QWidget transparente).

O app usa QWidget { background: transparent } para cartões; o popup do combo é uma janela
à parte e herdava transparência → fundo preto nativo. Forçamos paleta + QSS na árvore do popup.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QComboBox, QWidget


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
    def showPopup(self):
        super().showPopup()
        self._polish_popup()
        QTimer.singleShot(0, self._polish_popup)

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
