"""
Design system da interface — paleta slate + acento vermelho Brasul (ações)
+ azul refinado para listas/menus/seleção (borda #3b82f6, fundo #eff6ff).
"""

APP_STYLESHEET = """
/* ---------- base ---------- */
QWidget {
    background: transparent;
    color: #0f172a;
    font-family: "Segoe UI", "SF Pro Display", system-ui, sans-serif;
    font-size: 13px;
}

/* Views base (tabelas não recebem ::item aqui — evita margens em toda a grade). */
QAbstractItemView {
    background-color: #ffffff;
    color: #0f172a;
    alternate-background-color: #ffffff;
    outline: none;
}

/* Area principal (stack + fundo ao lado da sidebar) */
QWidget#contentHost {
    background: #ffffff;
}

/* ---------- sidebar ---------- */
QFrame#sidebar {
    background: #ffffff;
    border: none;
    border-right: 1px solid #e2e8f0;
    border-radius: 0px;
}
QFrame#sidebar QLabel#sidebarBrand {
    font-size: 15px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: 0.02em;
}
QFrame#sidebar QLabel#sidebarTagline {
    font-size: 11px;
    color: #334155;
    font-weight: 500;
}
QLabel#sidebarLogo {
    padding: 2px 6px 14px 6px;
}
QLabel#topbarLogo {
    padding: 2px 12px 2px 2px;
}

QFrame#sidebar QLabel#sectionTitle {
    font-size: 10px;
    font-weight: 800;
    color: #334155;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding-left: 4px;
}

QListWidget#navMenu {
    background: transparent;
    border: none;
    outline: none;
    padding: 4px 0;
}
QListWidget#navMenu::item {
    color: #1e293b;
    padding: 11px 14px;
    margin: 2px 10px;
    border-radius: 10px;
    border: 1px solid transparent;
}
QListWidget#navMenu::item:hover {
    background: #f8fafc;
    color: #0f172a;
    border: 1px solid #e2e8f0;
}
QListWidget#navMenu::item:selected {
    background: #eff6ff;
    color: #1e3a8a;
    font-weight: 700;
    border: 1px solid #93c5fd;
}

/* ---------- topbar (area de conteudo) ---------- */
QFrame#topbar {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
}
QLabel#pageTitle {
    font-size: 20px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.02em;
}
QLabel#pageSubtitle {
    font-size: 12px;
    color: #334155;
    font-weight: 500;
}
QLabel#muted {
    color: #334155;
    font-size: 12px;
}
QLabel#emphasisStat {
    font-weight: 800;
    font-size: 15px;
    color: #0f172a;
}

/* ---------- titulos de modulo / cartoes ---------- */
QLabel#sectionTitle {
    font-size: 13px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.01em;
}
QLabel#moduleHeroTitle {
    font-size: 17px;
    font-weight: 800;
    color: #0f172a;
}
QLabel#moduleHeroDesc {
    font-size: 12px;
    color: #334155;
}

QFrame#panelCard {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
}

QDialog#obraDetailDialog {
    background: #f1f5f9;
}
QDialog#loginDialog {
    background: #e5e7eb;
}
QFrame#loginCard {
    background: #f8fafc;
    border: 1px solid #d1d5db;
    border-radius: 14px;
}
/* Mensagens/alertas legíveis em qualquer tema */
QMessageBox {
    background: #ffffff;
}
QMessageBox QLabel {
    color: #0f172a;
    font-size: 13px;
}
QMessageBox QPushButton {
    min-width: 86px;
}
QMessageBox QWidget,
QMessageBox QFrame {
    background: #ffffff;
    color: #0f172a;
}

/* Menus contextuais — borda azul suave */
QMenu {
    background: #ffffff;
    color: #0f172a;
    border: 1px solid #93c5fd;
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
    background: #eff6ff;
    color: #0f172a;
    border: 1px solid #3b82f6;
}
QToolTip {
    background: #ffffff;
    color: #0f172a;
    border: 1px solid #bfdbfe;
    border-radius: 8px;
    padding: 8px 10px;
}
QLabel#loginLogo {
    padding-top: 2px;
    padding-bottom: 4px;
}
QLabel#loginTitle {
    font-size: 38px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.03em;
}
QLabel#loginHint {
    color: #334155;
    font-size: 12px;
    font-weight: 500;
    padding: 2px 2px 0 2px;
}
QLabel#loginError {
    color: #b91c1c;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 2px 2px 2px;
}
QPushButton#userTileButton {
    background: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    min-height: 42px;
    text-align: left;
    padding: 0 14px;
    font-weight: 700;
}
QPushButton#userTileButton:hover {
    background: #f8fafc;
    border-color: #94a3b8;
}
QLabel#dialogHeroTitle {
    font-size: 22px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.02em;
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
    color: #b91c1c;
    border: 1px solid #fecaca;
    border-radius: 999px;
    padding: 5px 12px;
    font-weight: 700;
    font-size: 11px;
}

QFrame#kpiCard {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    border-top: 3px solid #c0392b;
}
QFrame#kpiCard QLabel#kpiTitle {
    font-size: 10px;
    font-weight: 700;
    color: #334155;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
QFrame#kpiCard QLabel#kpiValue {
    font-size: 18px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.02em;
}

QFrame#panelCard QLabel#kpiTitle {
    font-size: 11px;
    font-weight: 700;
    color: #334155;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
QFrame#panelCard QLabel#kpiValue {
    font-size: 22px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.02em;
}

QFrame#panelCard QTableWidget {
    border: none;
    border-radius: 10px;
    background: #ffffff;
}

/* KPI strip no dashboard */
QFrame#kpiStrip {
    background: transparent;
    border: none;
}

/* ---------- botoes ---------- */
QPushButton {
    background-color: #c0392b;
    color: #ffffff;
    border: none;
    border-radius: 10px;
    min-height: 36px;
    padding: 0 18px;
    font-weight: 700;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #a93226;
}
QPushButton:pressed {
    background-color: #922b21;
}
QPushButton#secondaryButton {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #cbd5e1;
}
QPushButton#secondaryButton:hover {
    background-color: #f8fafc;
    border-color: #94a3b8;
}
QPushButton#ghostButton {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #cbd5e1;
}
QPushButton#ghostButton:hover {
    background-color: #f8fafc;
    border-color: #94a3b8;
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
QLineEdit, QComboBox, QDateEdit {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    padding: 8px 12px;
    min-height: 34px;
    selection-background-color: #bfdbfe;
    selection-color: #0f172a;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
    border: 2px solid #3b82f6;
    padding: 7px 11px;
}
QDateEdit::drop-down {
    border: none;
    width: 26px;
}
QDateEdit::down-arrow {
    width: 10px;
    height: 10px;
}
/* Calendário popup do QDateEdit (evita barra/preenchimento preto no Windows). */
QCalendarWidget {
    background: #ffffff;
    color: #0f172a;
}
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background: #ffffff;
    border: 1px solid #dbe5f1;
    border-bottom: none;
}
QCalendarWidget QToolButton {
    background: #ffffff;
    color: #0f172a;
    border: 1px solid #dbe5f1;
    border-radius: 6px;
    padding: 4px 8px;
}
QCalendarWidget QToolButton:hover {
    background: #f8fafc;
    border-color: #bfdbfe;
}
QCalendarWidget QMenu {
    background: #ffffff;
    color: #0f172a;
    border: 1px solid #bfdbfe;
}
QCalendarWidget QSpinBox {
    background: #ffffff;
    color: #0f172a;
    border: 1px solid #dbe5f1;
    border-radius: 6px;
    padding: 2px 6px;
}
QCalendarWidget QAbstractItemView:enabled {
    background: #ffffff;
    color: #0f172a;
    selection-background-color: #eff6ff;
    selection-color: #0f172a;
    alternate-background-color: #f8fafc;
    border: 1px solid #dbe5f1;
}
QComboBox::drop-down {
    border: none;
    width: 28px;
}
/* Popup do combo — lista branca, moldura azul clara; itens com borda na seleção */
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #93c5fd;
    border-radius: 0px;
    selection-background-color: #eff6ff;
    selection-color: #0f172a;
    padding: 4px;
    outline: none;
    min-width: 120px;
}
QComboBox QAbstractItemView::item {
    min-height: 28px;
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid transparent;
    margin: 2px 4px;
}
QComboBox QAbstractItemView::item:hover {
    background: #f8fafc;
    color: #0f172a;
    border: 1px solid #bfdbfe;
}
QComboBox QAbstractItemView::item:selected {
    background: #eff6ff;
    color: #0f172a;
    border: 1px solid #3b82f6;
}
QComboBox QListView {
    background-color: #ffffff;
    color: #0f172a;
    outline: none;
}

QLabel#fieldLabel {
    font-size: 11px;
    font-weight: 700;
    color: #334155;
}

QCheckBox {
    spacing: 8px;
    color: #1e293b;
    font-weight: 600;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #cbd5e1;
    background: #ffffff;
}
QCheckBox::indicator:checked {
    background: #c0392b;
    border-color: #c0392b;
}

/* ---------- tabelas ---------- */
QTableWidget {
    background: #ffffff;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    gridline-color: #f1f5f9;
    alternate-background-color: #f8fafc;
    selection-background-color: #dbeafe;
    selection-color: #0f172a;
}
QTableWidget::item:selected,
QTableWidget::item:selected:!active,
QTableWidget::item:selected:active {
    background-color: #dbeafe;
    color: #0f172a;
}

/* Combo dentro da grade de usuários */
QTableWidget QComboBox {
    min-height: 30px;
    padding: 4px 10px;
    border-radius: 8px;
}
QHeaderView::section {
    background: #c0392b;
    color: #ffffff;
    border: none;
    border-right: 1px solid #a93226;
    border-bottom: 2px solid #922b21;
    padding: 10px 10px;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
QHeaderView::section:last {
    border-right: none;
}

/* ---------- progresso ---------- */
QProgressBar {
    background: #e2e8f0;
    border: none;
    border-radius: 8px;
    min-height: 10px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #c0392b, stop:1 #e74c3c);
    border-radius: 8px;
}

QLabel#monthTick {
    font-size: 11px;
    font-weight: 700;
    color: #334155;
    min-width: 22px;
}
QLabel#monthVal {
    font-size: 11px;
    font-weight: 600;
    color: #0f172a;
    min-width: 88px;
}

/* ---------- scroll (legível: trilho + thumb largos, contraste alto) ---------- */
QScrollBar:vertical {
    background: #e8edf3;
    width: 16px;
    margin: 0;
    border: none;
    border-radius: 8px;
}
QScrollBar::handle:vertical {
    background: #64748b;
    border: none;
    border-radius: 8px;
    min-height: 48px;
    margin: 3px 4px 3px 4px;
}
QScrollBar::handle:vertical:hover {
    background: #475569;
}
QScrollBar::handle:vertical:pressed {
    background: #334155;
}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: #e8edf3;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
    width: 0px;
    border: none;
    background: transparent;
}

QScrollBar:horizontal {
    background: #e8edf3;
    height: 16px;
    margin: 0;
    border: none;
    border-radius: 8px;
}
QScrollBar::handle:horizontal {
    background: #64748b;
    border: none;
    border-radius: 8px;
    min-width: 48px;
    margin: 4px 3px 4px 3px;
}
QScrollBar::handle:horizontal:hover {
    background: #475569;
}
QScrollBar::handle:horizontal:pressed {
    background: #334155;
}
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: #e8edf3;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
    height: 0px;
    border: none;
    background: transparent;
}

/* Scroll dentro de painéis brancos: trilho não “some” no fundo */
QFrame#panelCard QScrollBar:vertical,
QDialog QScrollBar:vertical {
    background: #dce3ec;
}
QFrame#panelCard QScrollBar::add-page:vertical,
QFrame#panelCard QScrollBar::sub-page:vertical,
QDialog QScrollBar::add-page:vertical,
QDialog QScrollBar::sub-page:vertical {
    background: #dce3ec;
}

/* ---------- placeholder / estados vazios ---------- */
QLabel#emptyStateTitle {
    font-size: 18px;
    font-weight: 800;
    color: #0f172a;
}
QLabel#emptyStateBody {
    font-size: 13px;
    color: #334155;
}
"""
