"""
Design system — visual Brasul: branco, vermelho institucional e destaque rosa claro.
Apenas apresentação (QSS); lógica e módulos permanecem iguais.
"""

APP_STYLESHEET = """
/* ---------- base ---------- */
QWidget {
    background: transparent;
    color: #1a1a1a;
    font-family: "Segoe UI", "SF Pro Display", system-ui, sans-serif;
    font-size: 13px;
}

QAbstractItemView {
    background-color: #ffffff;
    color: #1a1a1a;
    alternate-background-color: #fafafa;
    outline: none;
}

QWidget#contentHost {
    background: #ffffff;
}

/* ---------- sidebar ---------- */
QFrame#sidebar {
    background: #ffffff;
    border: none;
    border-right: 1px solid #e8e8e8;
}
QFrame#sidebar QLabel#sidebarBrand {
    font-size: 15px;
    font-weight: 800;
    color: #1a1a1a;
}
QFrame#sidebar QLabel#sidebarTagline {
    font-size: 11px;
    color: #9b1c1c;
    font-weight: 800;
    letter-spacing: 0.14em;
}
QLabel#sidebarLogo {
    padding: 2px 6px 12px 6px;
    background: transparent;
    border: none;
}
QLabel#topbarLogo {
    padding: 2px 12px 2px 2px;
    background: transparent;
    border: none;
}

QFrame#sidebar QLabel#sidebarSectionTitle {
    font-size: 10px;
    font-weight: 800;
    color: #64748b;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 8px 4px 4px 8px;
}

QListWidget#navMenu {
    background: transparent;
    border: none;
    outline: none;
    padding: 4px 0;
}
QListWidget#navMenu::item {
    color: #334155;
    padding: 11px 14px 11px 18px;
    margin: 2px 8px;
    border-radius: 8px;
    border: 1px solid transparent;
    border-left: 4px solid transparent;
}
QListWidget#navMenu::item:hover {
    background: #fafafa;
    color: #1a1a1a;
    border: 1px solid #eeeeee;
    border-left: 4px solid #e8e8e8;
}
QListWidget#navMenu::item:selected {
    background: #fdecec;
    color: #7f1d1d;
    font-weight: 700;
    border: 1px solid #f5c6c6;
    border-left: 4px solid #9b1c1c;
}

QPushButton#sidebarActionButton {
    background-color: #fdecec;
    color: #7f1d1d;
    border: 1px solid #f5c6c6;
    border-radius: 10px;
    min-height: 38px;
    padding: 0 14px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton#sidebarActionButton:hover {
    background-color: #fcd9d9;
    border-color: #e8a8a8;
    color: #6f1414;
}
QPushButton#sidebarActionButton:pressed {
    background-color: #f5c6c6;
}

/* ---------- topbar ---------- */
QFrame#topbar {
    background: #ffffff;
    border: 1px solid #e8e8e8;
    border-radius: 12px;
}
QFrame#topbarMeta {
    background: #fafafa;
    border: 1px solid #e8e8e8;
    border-radius: 10px;
}
QLabel#topbarMetaLine {
    color: #475569;
    font-size: 11px;
    font-weight: 500;
}
QLabel#pageTitle {
    font-size: 20px;
    font-weight: 800;
    color: #1a1a1a;
    letter-spacing: -0.02em;
}
QLabel#pageSubtitle {
    font-size: 12px;
    color: #64748b;
    font-weight: 500;
}
QLabel#muted {
    color: #64748b;
    font-size: 12px;
}
QLabel#emphasisStat {
    font-weight: 800;
    font-size: 15px;
    color: #1a1a1a;
}

/* ---------- titulos / cartoes ---------- */
QLabel#sectionTitle {
    font-size: 13px;
    font-weight: 800;
    color: #1a1a1a;
}
QLabel#moduleHeroTitle {
    font-size: 17px;
    font-weight: 800;
    color: #1a1a1a;
}
QLabel#moduleHeroDesc {
    font-size: 12px;
    color: #64748b;
}

QLabel#demoBanner {
    background: #fffbeb;
    color: #92400e;
    border: 1px solid #fcd34d;
    border-radius: 10px;
    padding: 10px 14px;
    font-weight: 600;
}
QFrame#panelCard {
    background: #ffffff;
    border: 1px solid #e8e8e8;
    border-radius: 12px;
}

QDialog#obraDetailDialog {
    background: #f4f5f7;
}
QDialog#loginDialog {
    background: #ececec;
}
QFrame#loginCard {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 14px;
}

QMessageBox {
    background: #ffffff;
}
QMessageBox QLabel {
    color: #1a1a1a;
    font-size: 13px;
}
QMessageBox QPushButton {
    min-width: 86px;
}
QMessageBox QWidget,
QMessageBox QFrame {
    background: #ffffff;
    color: #1a1a1a;
}

QMenu {
    background: #ffffff;
    color: #1a1a1a;
    border: 1px solid #e8e8e8;
    border-radius: 10px;
    padding: 6px;
}
QMenu::item {
    background: transparent;
    padding: 9px 22px 9px 12px;
    border-radius: 8px;
    margin: 2px 4px;
}
QMenu::item:selected {
    background: #fdecec;
    color: #7f1d1d;
    border: 1px solid #f5c6c6;
}
QToolTip {
    background: #ffffff;
    color: #1a1a1a;
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    padding: 8px 10px;
}

QLabel#loginLogo {
    padding-top: 2px;
    padding-bottom: 4px;
}
QLabel#loginTitle {
    font-size: 32px;
    font-weight: 800;
    color: #1a1a1a;
}
QLabel#loginHint {
    color: #64748b;
    font-size: 12px;
    font-weight: 500;
}
QLabel#loginError {
    color: #9b1c1c;
    font-size: 13px;
    font-weight: 700;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 8px;
    padding: 10px 12px;
    min-height: 20px;
}
QPushButton#userTileButton {
    background: #ffffff;
    color: #1a1a1a;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    min-height: 42px;
    text-align: left;
    padding: 0 14px;
    font-weight: 700;
}
QPushButton#userTileButton:hover {
    background: #fdecec;
    border-color: #f5c6c6;
    color: #7f1d1d;
}
QLabel#dialogHeroTitle {
    font-size: 22px;
    font-weight: 800;
    color: #1a1a1a;
}

QLabel#chipOk {
    background: #ecfdf5;
    color: #047857;
    border: 1px solid #a7f3d0;
    border-radius: 999px;
    padding: 5px 12px;
    font-weight: 700;
    font-size: 11px;
}
QLabel#chipWarn {
    background: #fffbeb;
    color: #b45309;
    border: 1px solid #fde68a;
    border-radius: 999px;
    padding: 5px 12px;
    font-weight: 700;
    font-size: 11px;
}
QLabel#chipBad {
    background: #fef2f2;
    color: #9b1c1c;
    border: 1px solid #fecaca;
    border-radius: 999px;
    padding: 5px 12px;
    font-weight: 700;
    font-size: 11px;
}

/* KPI cards (dashboard) */
QFrame#kpiCard {
    background: #ffffff;
    border: 1px solid #e8e8e8;
    border-radius: 12px;
}
QLabel#kpiIcon {
    background: #9b1c1c;
    color: #ffffff;
    border-radius: 22px;
    font-size: 15px;
    font-weight: 800;
    min-width: 44px;
    max-width: 44px;
    min-height: 44px;
    max-height: 44px;
}
QFrame#kpiCard QLabel#kpiTitle {
    font-size: 10px;
    font-weight: 700;
    color: #64748b;
    letter-spacing: 0.05em;
}
QFrame#kpiCard QLabel#kpiValue {
    font-size: 20px;
    font-weight: 800;
    color: #1a1a1a;
    letter-spacing: -0.02em;
}

QFrame#panelCard QLabel#kpiTitle {
    font-size: 11px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
}
QFrame#panelCard QLabel#kpiValue {
    font-size: 22px;
    font-weight: 800;
    color: #1a1a1a;
}

QFrame#panelCard QTableWidget {
    border: none;
    border-radius: 8px;
    background: #ffffff;
}

QFrame#kpiStrip {
    background: transparent;
    border: none;
}

/* ---------- botoes ---------- */
QPushButton {
    background-color: #9b1c1c;
    color: #ffffff;
    border: none;
    border-radius: 10px;
    min-height: 36px;
    padding: 0 18px;
    font-weight: 700;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #851818;
}
QPushButton:pressed {
    background-color: #6f1414;
}
QPushButton#secondaryButton {
    background-color: #ffffff;
    color: #334155;
    border: 1px solid #d1d5db;
}
QPushButton#secondaryButton:hover {
    background-color: #fafafa;
    border-color: #9ca3af;
}
QPushButton#ghostButton {
    background-color: #ffffff;
    color: #334155;
    border: 1px solid #d1d5db;
}
QPushButton#ghostButton:hover {
    background-color: #fafafa;
}
QPushButton#tablePdfButton {
    min-height: 26px;
    max-height: 28px;
    padding: 0 10px;
    border-radius: 8px;
    font-size: 11px;
    font-weight: 700;
}

/* ---------- campos ---------- */
QLineEdit, QDateEdit {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    padding: 8px 12px;
    min-height: 34px;
    selection-background-color: #fcd9d9;
    selection-color: #1a1a1a;
}
QComboBox {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    padding: 6px 34px 6px 10px;
    min-height: 34px;
    selection-background-color: #fcd9d9;
    selection-color: #1a1a1a;
}
QComboBox QLineEdit {
    border: none;
    background: transparent;
    padding: 2px 4px;
    margin: 0;
    min-height: 22px;
}
QLineEdit:focus, QDateEdit:focus {
    border: 2px solid #9b1c1c;
    padding: 7px 11px;
}
QComboBox:focus {
    border: 2px solid #9b1c1c;
    padding: 5px 33px 5px 9px;
}
QComboBox QLineEdit:focus {
    border: none;
    padding: 2px 4px;
}
QDateEdit::drop-down {
    width: 0;
    border: none;
}
QDateEdit::down-arrow {
    image: none;
    width: 0;
    height: 0;
}

QCalendarWidget {
    background: #ffffff;
    color: #1a1a1a;
}
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background: #ffffff;
    border: 1px solid #e8e8e8;
}
QCalendarWidget QToolButton {
    background: #ffffff;
    color: #1a1a1a;
    border: 1px solid #e8e8e8;
    border-radius: 6px;
}
QCalendarWidget QToolButton:hover {
    background: #fdecec;
    border-color: #f5c6c6;
}
QCalendarWidget QAbstractItemView:enabled {
    background: #ffffff;
    color: #1a1a1a;
    selection-background-color: #9b1c1c;
    selection-color: #ffffff;
    alternate-background-color: #fafafa;
    border: 1px solid #e8e8e8;
}

QComboBox::drop-down {
    width: 0;
    border: none;
}
QComboBox::down-arrow {
    image: none;
    width: 0;
    height: 0;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #1a1a1a;
    border: 1px solid #e8e8e8;
    selection-background-color: #fdecec;
    selection-color: #7f1d1d;
    padding: 4px;
    outline: none;
}
QComboBox QAbstractItemView::item {
    min-height: 28px;
    padding: 8px 14px;
    border-radius: 6px;
    margin: 2px 4px;
}
QComboBox QAbstractItemView::item:hover {
    background: #fafafa;
}
QComboBox QAbstractItemView::item:selected {
    background: #fdecec;
    color: #7f1d1d;
    border: 1px solid #f5c6c6;
}

QLabel#fieldLabel {
    font-size: 11px;
    font-weight: 700;
    color: #475569;
}

QCheckBox::indicator:checked {
    background: #9b1c1c;
    border-color: #9b1c1c;
}

/* ---------- tabelas ---------- */
QTableWidget {
    background: #ffffff;
    color: #334155;
    border: 1px solid #e8e8e8;
    border-radius: 10px;
    gridline-color: #f0f0f0;
    alternate-background-color: #fafafa;
    selection-background-color: #fdecec;
    selection-color: #7f1d1d;
}
QTableWidget::item:selected {
    background-color: #fdecec;
    color: #7f1d1d;
}

QHeaderView::section {
    background: #9b1c1c;
    color: #ffffff;
    border: none;
    border-right: 1px solid #851818;
    padding: 10px 10px;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
QHeaderView::section:last {
    border-right: none;
}

/* ---------- progresso (evolução mensal) ---------- */
QProgressBar {
    background: #eeeeee;
    border: none;
    border-radius: 6px;
    min-height: 12px;
    max-height: 12px;
}
QProgressBar::chunk {
    background: #9b1c1c;
    border-radius: 6px;
}

QLabel#monthTick {
    font-size: 11px;
    font-weight: 800;
    color: #475569;
    min-width: 32px;
}
QLabel#monthVal {
    font-size: 11px;
    font-weight: 600;
    color: #1a1a1a;
    min-width: 100px;
}

/* ---------- scroll ---------- */
QScrollBar:vertical {
    background: #f0f0f0;
    width: 14px;
    border: none;
    border-radius: 7px;
}
QScrollBar::handle:vertical {
    background: #b0b0b0;
    border-radius: 7px;
    min-height: 40px;
    margin: 2px 3px;
}
QScrollBar::handle:vertical:hover {
    background: #888888;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
    background: transparent;
}

QScrollBar:horizontal {
    background: #f0f0f0;
    height: 14px;
    border-radius: 7px;
}
QScrollBar::handle:horizontal {
    background: #b0b0b0;
    border-radius: 7px;
    min-width: 40px;
    margin: 3px 2px;
}

QLabel#emptyStateTitle {
    font-size: 18px;
    font-weight: 800;
    color: #1a1a1a;
}
QLabel#emptyStateBody {
    font-size: 13px;
    color: #64748b;
}

/* Botão seta dos combos */
QToolButton#brasulComboDropBtn,
QToolButton#brasulDateDropBtn {
    border: none;
    border-left: 1px solid #e8e8e8;
    border-top-right-radius: 9px;
    border-bottom-right-radius: 9px;
    background: #fafafa;
}
QToolButton#brasulComboDropBtn:hover,
QToolButton#brasulDateDropBtn:hover {
    background: #fdecec;
}
"""
