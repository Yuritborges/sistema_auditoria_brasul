from PySide6.QtCore import QDate, QEvent, Qt
from PySide6.QtGui import QColor, QPalette, QWheelEvent
from PySide6.QtWidgets import (
    QCalendarWidget,
    QDateEdit,
    QDialog,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.brasul_combo import _criar_botao_seta


class BrasulDateEdit(QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setReadOnly(True)
        self._polish_calendar()
        self.installEventFilter(self)
        le = self.lineEdit()
        if le is not None:
            le.setCursor(Qt.PointingHandCursor)
            le.installEventFilter(self)

        self._btn_cal = _criar_botao_seta(self, "brasulDateDropBtn", self._open_calendar_dialog)
        self._reposicionar_botao_cal()

    def _reposicionar_botao_cal(self):
        if not hasattr(self, "_btn_cal"):
            return
        margem = 2
        h = max(self.height() - margem * 2, 24)
        self._btn_cal.setFixedSize(self._btn_cal.width(), h)
        self._btn_cal.move(max(0, self.width() - self._btn_cal.width() - margem), margem)
        self._btn_cal.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposicionar_botao_cal()

    def wheelEvent(self, event: QWheelEvent):
        # Scroll do mouse não deve alterar a data.
        event.ignore()

    def _polish_calendar(self):
        cal = self.calendarWidget()
        if cal is None:
            return

        pal = QPalette(cal.palette())
        pal.setColor(QPalette.Window, QColor("#ffffff"))
        pal.setColor(QPalette.Base, QColor("#ffffff"))
        pal.setColor(QPalette.Button, QColor("#f8fafc"))
        pal.setColor(QPalette.Text, QColor("#0f172a"))
        pal.setColor(QPalette.WindowText, QColor("#0f172a"))
        cal.setPalette(pal)
        cal.setAutoFillBackground(True)
        cal.setAttribute(Qt.WA_TranslucentBackground, False)
        cal.setAttribute(Qt.WA_StyledBackground, True)

        cal.setStyleSheet(
            """
            QCalendarWidget {
                background: #ffffff;
                color: #0f172a;
                border: 1px solid #dbe5f1;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background: #ffffff;
                border-bottom: 1px solid #dbe5f1;
            }
            QCalendarWidget QToolButton {
                background: #f8fafc;
                color: #0f172a;
                border: 1px solid #dbe5f1;
                border-radius: 6px;
                padding: 4px 8px;
            }
            QCalendarWidget QToolButton:hover {
                background: #eff6ff;
                border-color: #93c5fd;
            }
            QCalendarWidget QAbstractItemView:enabled {
                background: #ffffff;
                color: #0f172a;
                selection-background-color: #3b82f6;
                selection-color: #ffffff;
                alternate-background-color: #f8fafc;
                border: none;
            }
            """
        )

        win = cal.window()
        if isinstance(win, QWidget):
            win.setAttribute(Qt.WA_TranslucentBackground, False)
            win.setAttribute(Qt.WA_StyledBackground, True)
            win.setAutoFillBackground(True)
            win.setPalette(pal)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._open_calendar_dialog()
            event.accept()
            return
        super().mousePressEvent(event)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel:
            return True
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.LeftButton:
            if obj is self or obj is self.lineEdit():
                self._open_calendar_dialog()
                return True
        return super().eventFilter(obj, event)

    def _open_calendar_dialog(self):
        dlg = QDialog(self.window() or self)
        dlg.setWindowTitle("Selecionar data")
        dlg.setModal(True)
        dlg.setObjectName("calendarDialog")
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(10)

        cal = QCalendarWidget(dlg)
        atual = self.date() if self.date().isValid() else QDate.currentDate()
        cal.setSelectedDate(atual)
        mn = self.minimumDate()
        if mn.isValid():
            cal.setMinimumDate(mn)
        cap = self.maximumDate()
        cal.setMaximumDate(cap if cap.isValid() else QDate.currentDate())
        cal.setGridVisible(False)
        cal.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        cal.setStyleSheet(self.calendarWidget().styleSheet())
        lay.addWidget(cal)

        row = QHBoxLayout()
        btn_hoje = QPushButton("Hoje")
        btn_ano = QPushButton("Início do ano")
        row.addWidget(btn_hoje)
        row.addWidget(btn_ano)
        row.addStretch(1)
        btn_cancel = QPushButton("Cancelar")
        btn_ok = QPushButton("Aplicar")
        btn_ok.setObjectName("secondaryButton")
        row.addWidget(btn_cancel)
        row.addWidget(btn_ok)
        lay.addLayout(row)

        def _ir_hoje():
            hoje = QDate.currentDate()
            if cal.maximumDate().isValid() and hoje > cal.maximumDate():
                hoje = cal.maximumDate()
            if cal.minimumDate().isValid() and hoje < cal.minimumDate():
                hoje = cal.minimumDate()
            cal.setSelectedDate(hoje)
            cal.setCurrentPage(hoje.year(), hoje.month())

        def _ir_inicio_ano():
            hoje = QDate.currentDate()
            alvo = QDate(hoje.year(), 1, 1)
            if cal.minimumDate().isValid() and alvo < cal.minimumDate():
                alvo = cal.minimumDate()
            if cal.maximumDate().isValid() and alvo > cal.maximumDate():
                alvo = cal.maximumDate()
            cal.setSelectedDate(alvo)
            cal.setCurrentPage(alvo.year(), alvo.month())

        btn_hoje.clicked.connect(_ir_hoje)
        btn_ano.clicked.connect(_ir_inicio_ano)
        btn_cancel.clicked.connect(dlg.reject)
        cal.activated.connect(lambda _d: dlg.accept())
        btn_ok.clicked.connect(dlg.accept)

        if dlg.exec() == QDialog.Accepted:
            self.setDate(cal.selectedDate())
