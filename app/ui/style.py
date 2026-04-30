APP_STYLESHEET = """
QWidget {
    background: #f3f5f8;
    color: #1f2937;
    font-family: Segoe UI;
    font-size: 12px;
}
QFrame#menu, QFrame#topbar, QFrame#panelCard {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
}
QLabel#pageTitle {
    font-size: 22px;
    font-weight: 800;
    color: #111827;
}
QLabel#pageSubtitle {
    font-size: 11px;
    color: #6b7280;
}
QLabel#sectionTitle {
    font-size: 13px;
    font-weight: 800;
    color: #374151;
}
QLabel#muted {
    color: #6b7280;
}
QListWidget {
    background: #ffffff;
    border: none;
}
QListWidget::item {
    padding: 8px 10px;
    border-radius: 8px;
}
QListWidget::item:selected {
    background: #fdecea;
    color: #b91c1c;
    font-weight: 700;
}
QPushButton {
    background: #c0392b;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    min-height: 32px;
    padding: 0 12px;
    font-weight: 700;
}
QPushButton:hover {
    background: #a93226;
}
QPushButton#tablePdfButton {
    min-height: 22px;
    max-height: 24px;
    padding: 0 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
}
QPushButton#secondaryButton {
    background: #ffffff;
    color: #1f2937;
    border: 1px solid #d7dde5;
}
QPushButton#secondaryButton:hover {
    background: #f3f4f6;
}
QLineEdit, QComboBox {
    background: #ffffff;
    border: 1px solid #d7dde5;
    border-radius: 8px;
    padding: 6px 8px;
    min-height: 30px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1.5px solid #c0392b;
}
QTableWidget {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    gridline-color: #edf1f4;
    alternate-background-color: #fafbfc;
    selection-background-color: #fdecea;
    selection-color: #1f2937;
}
QHeaderView::section {
    background: #1f2f46;
    color: #ffffff;
    border: none;
    padding: 9px 7px;
    font-size: 11px;
    font-weight: 800;
}
QProgressBar {
    background: #eef2f6;
    border: 1px solid #d7dde5;
    border-radius: 6px;
    min-height: 14px;
}
QProgressBar::chunk {
    background: #c0392b;
    border-radius: 5px;
}
"""
