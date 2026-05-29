"""QComboBox com lista suspensa legível no Windows (Fusion + QSS global com QWidget transparente).

O app usa QWidget { background: transparent } para cartões; o popup do combo é uma janela
à parte e herdava transparência → fundo preto nativo. Forçamos paleta + QSS na árvore do popup.
"""

from PySide6.QtCore import QEvent, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFontMetrics, QPalette, QWheelEvent
from PySide6.QtWidgets import QApplication, QComboBox, QCompleter, QStyle, QToolButton, QWidget

_LARGURA_BOTAO_SETA = 34

_ESTILO_BOTAO_SETA = """
QToolButton#brasulComboDropBtn,
QToolButton#brasulDateDropBtn {
    border: none;
    border-left: 1px solid #e8e8e8;
    border-top-right-radius: 9px;
    border-bottom-right-radius: 9px;
    background: #fafafa;
    padding: 0 4px;
}
QToolButton#brasulComboDropBtn:hover,
QToolButton#brasulDateDropBtn:hover {
    background: #fdecec;
}
QToolButton#brasulComboDropBtn:pressed,
QToolButton#brasulDateDropBtn:pressed {
    background: #f5c6c6;
}
"""


def _icone_seta_padrao():
    app = QApplication.instance()
    if app is None:
        return None
    return app.style().standardIcon(QStyle.StandardPixmap.SP_ArrowDown)


def _criar_botao_seta(parent: QWidget, object_name: str, slot) -> QToolButton:
    btn = QToolButton(parent)
    btn.setObjectName(object_name)
    ic = _icone_seta_padrao()
    if ic is not None:
        btn.setIcon(ic)
    btn.setIconSize(QSize(12, 12))
    btn.setText("")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    btn.setFixedWidth(_LARGURA_BOTAO_SETA)
    btn.setStyleSheet(_ESTILO_BOTAO_SETA)
    btn.clicked.connect(slot)
    return btn


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


def garantir_combo_digitavel(combo: "BrasulComboBox") -> None:
    """Evita lineEdit somente leitura quando o combo está dentro de cartões/painéis."""
    combo.setEditable(True)
    le = combo.lineEdit()
    if le is None:
        return
    le.setReadOnly(False)
    le.setEnabled(True)
    le.setFocusPolicy(Qt.FocusPolicy.StrongFocus)


def preencher_combo_filtro(
    combo: "BrasulComboBox",
    valores: list[str],
    texto_atual: str = "",
    placeholder: str = "",
    opcao_todos: str = "",
    iniciar_vazio: bool = False,
) -> None:
    """Lista ordenada + digitação com completer; mantém texto livre se não houver item exato."""
    garantir_combo_digitavel(combo)
    combo.blockSignals(True)
    try:
        combo.clear()
        if opcao_todos:
            combo.addItem(opcao_todos)
        combo.addItems(valores)
        le = combo.lineEdit()
        if le is not None and placeholder:
            le.setPlaceholderText(placeholder)
        txt = (texto_atual or "").strip()
        if iniciar_vazio and not txt:
            combo.setCurrentIndex(-1)
            if le is not None:
                le.clear()
            return
        if txt:
            idx = combo.findText(txt, Qt.MatchFlag.MatchFixedString | Qt.MatchFlag.MatchCaseSensitive)
            if idx < 0:
                idx = combo.findText(txt, Qt.MatchFlag.MatchFixedString)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            else:
                combo.setEditText(txt)
        elif opcao_todos:
            combo.setCurrentIndex(0)
        elif le is not None:
            combo.setCurrentIndex(-1)
            le.clear()
    finally:
        combo.blockSignals(False)
    combo._reposicionar_botao_seta()


def itens_distintos_dos_pedidos(dados) -> list[str]:
    out = set()
    for d in dados or []:
        for part in str(d.get("itens_texto") or "").split("|"):
            t = part.strip()
            if t:
                out.add(t)
    return sorted(out, key=lambda s: s.upper())


def solicitantes_distintos_dos_pedidos(dados):
    """Nomes em «Material solicitado por» para filtro na auditoria."""
    out = set()
    for d in dados:
        t = (d.get("material_solicitado_por") or "").strip()
        if t:
            out.add(t)
    return sorted(out, key=lambda s: s.upper())


class BrasulComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.setDuplicatesEnabled(False)
        self.setMaxVisibleItems(25)
        self.setMinimumContentsLength(10)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.setMinimumWidth(150)

        comp = QCompleter(self.model(), self)
        comp.setCaseSensitivity(Qt.CaseInsensitive)
        comp.setFilterMode(Qt.MatchFlag.MatchContains)
        comp.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setCompleter(comp)

        le = self.lineEdit()
        if le is not None:
            le.setClearButtonEnabled(False)
            le.setTextMargins(4, 0, _LARGURA_BOTAO_SETA + 6, 0)
            le.returnPressed.connect(self._normalize_typed_value)
            le.installEventFilter(self)

        self._btn_seta = _criar_botao_seta(self, "brasulComboDropBtn", self._abrir_lista)
        self._reposicionar_botao_seta()

        self.activated.connect(self._ao_selecionar_item)

    def _reposicionar_botao_seta(self):
        if not hasattr(self, "_btn_seta"):
            return
        margem = 2
        h = max(self.height() - margem * 2, 24)
        self._btn_seta.setFixedSize(self._btn_seta.width(), h)
        self._btn_seta.move(max(0, self.width() - self._btn_seta.width() - margem), margem)
        self._btn_seta.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposicionar_botao_seta()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._reposicionar_botao_seta)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Wheel:
            return True
        return super().eventFilter(watched, event)

    def _ao_selecionar_item(self, index: int):
        le = self.lineEdit()
        if le is not None and 0 <= index < self.count():
            le.setText(self.itemText(index))

    def _abrir_lista(self):
        if self.count() <= 0:
            return
        le = self.lineEdit()
        texto_livre = (le.text() if le else "").strip()
        idx_antes = self.currentIndex()

        self.setFocus(Qt.FocusReason.MouseFocusReason)
        # Qt no Windows às vezes não abre popup com índice -1.
        if idx_antes < 0 and self.count() > 0:
            self.blockSignals(True)
            self.setCurrentIndex(0)
            self.blockSignals(False)

        super().showPopup()

        if idx_antes < 0:
            self.blockSignals(True)
            self.setCurrentIndex(-1)
            if le is not None:
                le.setText(texto_livre)
            self.blockSignals(False)

    def wheelEvent(self, event: QWheelEvent):
        event.ignore()

    def _normalize_typed_value(self):
        txt = (self.currentText() or "").strip()
        if not txt:
            return
        idx = self.findText(txt, Qt.MatchFlag.MatchFixedString | Qt.MatchFlag.MatchCaseSensitive)
        if idx < 0:
            idx = self.findText(txt, Qt.MatchFlag.MatchFixedString)
        if idx < 0:
            idx = self.findText(txt, Qt.MatchFlag.MatchStartsWith)
        if idx < 0:
            idx = self.findText(txt, Qt.MatchFlag.MatchContains)
        if idx >= 0 and idx != self.currentIndex():
            self.setCurrentIndex(idx)

    def _largura_popup(self) -> int:
        fm = QFontMetrics(self.font())
        largura = max(self.width(), 220)
        for i in range(self.count()):
            largura = max(largura, fm.horizontalAdvance(self.itemText(i)) + 56)
        return min(largura, 560)

    def showPopup(self):
        if self.count() <= 0:
            return
        super().showPopup()
        self._polish_popup()
        QTimer.singleShot(0, self._polish_popup)

    def _ajustar_largura_popup(self):
        view = self.view()
        if view is None:
            return
        largura = self._largura_popup()
        view.setTextElideMode(Qt.TextElideMode.ElideNone)
        view.setMinimumWidth(largura)
        win = view.window()
        if win is not None:
            win.setMinimumWidth(largura)

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
        self._ajustar_largura_popup()
