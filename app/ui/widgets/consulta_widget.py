import os
from collections import defaultdict
from datetime import datetime

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QFont, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QCompleter,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
    QTabWidget,
)

from app.config import ASSETS_DIR, LOGOS_DIR
from app.services.auditoria_service import AuditoriaService

LOGO_PATHS = [
    os.path.join(LOGOS_DIR, "logo_brasul.png"),
    os.path.join(LOGOS_DIR, "brasul.png"),
    os.path.join(ASSETS_DIR, "logo_brasul.png"),
]

MESES_PT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


class ConsultaPatraoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.service = AuditoriaService()
        self._dados = []
        self._filtrados = []
        self._build()
        self.recarregar()

    def _build(self):
        self.setStyleSheet(
            """
            QWidget { background: #f3f5f8; color: #1f2937; font-size: 12px; font-family: Segoe UI; }
            QFrame#headerCard { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #ffffff,stop:1 #fff7f5); border:1px solid #eadfdd; border-radius:22px; }
            QFrame#sectionCard { background:#ffffff; border:1px solid #e7eaee; border-radius:18px; }
            QFrame#summaryCard,QFrame#miniPanel { background:#ffffff; border:1px solid #e7eaee; border-radius:16px; }
            QLabel#pageTitle { font-size: 30px; font-weight: 800; color: #192434; }
            QLabel#pageSubtitle { font-size: 12px; color: #6b7280; }
            QLabel#sourceInfo { font-size: 11px; color: #4b5563; font-weight: 700; }
            QLabel#badgeOnlyRead { background:#fdecea; color:#c0392b; border-radius:10px; padding:7px 12px; font-size:11px; font-weight:800; }
            QLabel#sectionTitle,QLabel#miniTitle { font-size:13px; font-weight:800; color:#374151; }
            QLabel#fieldLabel { font-size:11px; font-weight:700; color:#6b7280; }
            QLabel#summaryTitle { font-size:11px; color:#6b7280; font-weight:700; }
            QLabel#summaryValue { font-size:24px; font-weight:800; color:#111827; }
            QLabel#summaryHint { font-size:11px; color:#c0392b; font-weight:700; }
            QLabel#miniMuted { font-size:11px; color:#6b7280; }
            QLineEdit,QComboBox { background:#ffffff; border:1px solid #d7dde5; border-radius:10px; padding:8px 10px; min-height:38px; color:#1f2937; }
            QLineEdit:focus,QComboBox:focus { border:1.5px solid #c0392b; background:#fffefe; }
            QPushButton { background:#c0392b; color:white; border:none; border-radius:10px; padding:8px 14px; min-height:38px; font-weight:800; }
            QPushButton:hover { background:#a93226; }
            QPushButton#secondaryButton { background:#ffffff; color:#1f2937; border:1px solid #d7dde5; }
            QPushButton#secondaryButton:hover { background:#f3f4f6; }
            QPushButton#pdfButton { background:#ffffff; color:#1f2937; border:1px solid #d7dde5; border-radius:8px; padding:4px 10px; min-height:30px; font-weight:700; }
            QPushButton#pdfButtonDisabled { background:#eef2f6; color:#8a96a3; border:1px solid #d7dde5; border-radius:8px; padding:4px 10px; min-height:30px; font-weight:700; }
            QTableWidget { background:#ffffff; border:1px solid #e7eaee; border-radius:14px; gridline-color:#edf1f4; alternate-background-color:#fafbfc; selection-background-color:#fdecea; selection-color:#1f2937; }
            QHeaderView::section { background:#1f2f46; color:#ffffff; border:none; padding:11px 8px; font-size:11px; font-weight:800; }
            QProgressBar { background:#eef2f6; border:1px solid #d7dde5; border-radius:7px; min-height:18px; }
            QProgressBar::chunk { background:#c0392b; border-radius:6px; }
            QTabWidget::pane { border: 1px solid #e7eaee; border-radius: 12px; background: #ffffff; }
            QTabBar::tab { background: #eef2f6; color: #374151; border: 1px solid #d7dde5; padding: 8px 14px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 4px; }
            QTabBar::tab:selected { background: #ffffff; color: #111827; font-weight: 800; }
            QLabel#focusHint { font-size: 11px; color: #6b7280; font-weight: 700; }
            QFrame#filtersCard { background: #ffffff; border: 1px solid #e7eaee; border-radius: 16px; }
            """
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)
        root.addWidget(self._build_header())
        root.addWidget(self._build_workspace(), 1)

    def _build_workspace(self):
        wrapper = QSplitter(Qt.Horizontal)
        wrapper.setChildrenCollapsible(True)

        filters_panel = self._build_filters()
        self.filters_panel = filters_panel
        self.filters_panel.setMinimumWidth(300)
        self.filters_panel.setMaximumWidth(420)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        right_layout.addLayout(self._build_summary())
        right_layout.addWidget(self._build_main_panel(), 1)

        wrapper.addWidget(filters_panel)
        wrapper.addWidget(right)
        wrapper.setStretchFactor(0, 0)
        wrapper.setStretchFactor(1, 1)
        wrapper.setSizes([340, 1500])
        self.workspace_splitter = wrapper
        return wrapper

    def _build_header(self):
        card = QFrame()
        card.setObjectName("headerCard")
        self._apply_shadow(card)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        logo_wrap = QFrame()
        logo_wrap.setStyleSheet("QFrame { background:#ffffff; border:1px solid #ececec; border-radius:14px; }")
        logo_wrap.setFixedSize(120, 76)
        lw = QVBoxLayout(logo_wrap)
        lw.setContentsMargins(10, 10, 10, 10)
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        pix = self._load_logo()
        if pix:
            logo_label.setPixmap(pix.scaled(96, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo_label.setText("BRASUL")
            logo_label.setStyleSheet("background:#c0392b; color:white; border-radius:10px; font-size:22px; font-weight:800;")
        lw.addWidget(logo_label)
        layout.addWidget(logo_wrap)

        text_box = QVBoxLayout()
        lbl_title = QLabel("Painel de Auditoria de Obras")
        lbl_title.setObjectName("pageTitle")
        lbl_subtitle = QLabel("Conformidade de pedidos, documentos e valores por obra")
        lbl_subtitle.setObjectName("pageSubtitle")
        self.lbl_source = QLabel("Fonte de dados: carregando...")
        self.lbl_source.setObjectName("sourceInfo")
        lbl_badge = QLabel("Somente leitura")
        lbl_badge.setObjectName("badgeOnlyRead")
        lbl_badge.setFixedWidth(140)
        lbl_badge.setAlignment(Qt.AlignCenter)
        text_box.addWidget(lbl_title)
        text_box.addWidget(lbl_subtitle)
        text_box.addWidget(self.lbl_source)
        text_box.addWidget(lbl_badge)
        layout.addLayout(text_box)
        layout.addStretch()
        self.btn_toggle_filtros = QPushButton("Ocultar filtros")
        self.btn_toggle_filtros.setObjectName("secondaryButton")
        self.btn_toggle_filtros.clicked.connect(self._toggle_filtros)
        layout.addWidget(self.btn_toggle_filtros)

        self.btn_recarregar = QPushButton("Recarregar")
        self.btn_recarregar.clicked.connect(self.recarregar)
        layout.addWidget(self.btn_recarregar)
        return card

    def _build_filters(self):
        card = QFrame()
        card.setObjectName("filtersCard")
        self._apply_shadow(card)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        title = QLabel("Filtros de Auditoria")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.cb_comprador = QComboBox()
        self.cb_empresa = QComboBox()
        self.cb_status = QComboBox()
        self.cb_status.addItems(["TODOS", "OK", "Sem PDF", "Sem comprador", "Critico"])
        self.cb_obra = QComboBox()
        self.cb_obra.setEditable(True)
        self.cb_fornecedor = QComboBox()
        self.cb_fornecedor.setEditable(True)
        for cb in (self.cb_obra, self.cb_fornecedor):
            comp = QCompleter()
            comp.setCaseSensitivity(Qt.CaseInsensitive)
            comp.setFilterMode(Qt.MatchContains)
            cb.setCompleter(comp)
            cb.setInsertPolicy(QComboBox.NoInsert)
        self.ed_item = QLineEdit()
        self.ed_item.setPlaceholderText("Descrição do item / material...")
        self.ed_numero = QLineEdit()
        self.ed_numero.setPlaceholderText("Número do pedido...")
        self.ed_data_ini = QLineEdit()
        self.ed_data_ini.setPlaceholderText("Data inicial (dd/mm/aaaa)")
        self.ed_data_fim = QLineEdit()
        self.ed_data_fim.setPlaceholderText("Data final (dd/mm/aaaa)")

        for field in (
            self._field("Comprador", self.cb_comprador),
            self._field("Empresa", self.cb_empresa),
            self._field("Status Auditoria", self.cb_status),
            self._field("Obra", self.cb_obra),
            self._field("Fornecedor", self.cb_fornecedor),
            self._field("Pedido", self.ed_numero),
            self._field("Data Inicial", self.ed_data_ini),
            self._field("Data Final", self.ed_data_fim),
            self._field("Item / Material", self.ed_item),
        ):
            layout.addWidget(field)

        btns = QHBoxLayout()
        btn_filtrar = QPushButton("Filtrar")
        btn_filtrar.clicked.connect(self.aplicar_filtros)
        btn_buscar_pdf = QPushButton("Buscar PDFs")
        btn_buscar_pdf.setObjectName("secondaryButton")
        btn_buscar_pdf.clicked.connect(self.buscar_pdfs_filtrados)
        btn_limpar = QPushButton("Limpar")
        btn_limpar.setObjectName("secondaryButton")
        btn_limpar.clicked.connect(self.limpar_filtros)
        btns.addWidget(btn_filtrar, 1)
        btns.addWidget(btn_buscar_pdf, 1)
        btns.addWidget(btn_limpar, 1)
        layout.addLayout(btns)
        layout.addStretch()
        return card

    def _build_summary(self):
        row = QHBoxLayout()
        row.setSpacing(12)
        self.card_total = self._summary_card("Pedidos", "0", "Total encontrado")
        self.card_valor = self._summary_card("Valor Total", "R$ 0,00", "Valor consolidado")
        self.card_ticket = self._summary_card("Ticket Medio", "R$ 0,00", "Media por pedido")
        self.card_critico = self._summary_card("Pendencias", "0", "Sem PDF ou sem comprador")
        self.card_conformidade = self._summary_card("Conformidade", "0%", "Pedidos com status OK")
        for card in (self.card_total, self.card_valor, self.card_ticket, self.card_critico, self.card_conformidade):
            row.addWidget(card)
        return row

    def _build_main_panel(self):
        card = QFrame()
        card.setObjectName("sectionCard")
        self._apply_shadow(card)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        title_row = QHBoxLayout()
        title = QLabel("Pedidos Auditados")
        title.setObjectName("sectionTitle")
        title_row.addWidget(title)
        title_row.addStretch()
        self.btn_aba_obras = QPushButton("Abrir aba de Obras")
        self.btn_aba_obras.setObjectName("secondaryButton")
        self.btn_aba_obras.clicked.connect(self._abrir_aba_obras)
        self.btn_foco = QPushButton("Modo foco")
        self.btn_foco.setObjectName("secondaryButton")
        self.btn_foco.clicked.connect(self._ativar_foco_tabela)
        self.btn_restaurar = QPushButton("Ver dashboard")
        self.btn_restaurar.setObjectName("secondaryButton")
        self.btn_restaurar.clicked.connect(self._restaurar_layout)
        self.lbl_focus_hint = QLabel("Dica: use Modo foco para enxergar tudo da tabela.")
        self.lbl_focus_hint.setObjectName("focusHint")
        title_row.addWidget(self.lbl_focus_hint)
        title_row.addWidget(self.btn_foco)
        title_row.addWidget(self.btn_restaurar)
        title_row.addWidget(self.btn_aba_obras)
        layout.addLayout(title_row)
        splitter = QSplitter(Qt.Horizontal)
        table_panel = self._build_analysis_tabs()
        side_panel = self._build_side_panel()
        self._side_panel = side_panel
        self._splitter = splitter
        splitter.addWidget(table_panel)
        splitter.addWidget(side_panel)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)
        splitter.setChildrenCollapsible(True)
        splitter.setSizes([1450, 330])
        layout.addWidget(splitter, 1)
        return card

    def _build_analysis_tabs(self):
        panel = QFrame()
        panel.setObjectName("miniPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        self.tabs_analise = QTabWidget()
        self.tabs_analise.addTab(self._build_table_panel(), "Pedidos")
        self.tabs_analise.addTab(self._build_item_table_panel(), "Itens")
        layout.addWidget(self.tabs_analise)
        return panel

    def _build_table_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        self.tbl = QTableWidget(0, 11)
        self.tbl.setHorizontalHeaderLabels(
            ["Pedido", "Comprador", "Data", "Empresa", "Fornecedor", "Obra", "Cond. Pgto", "Forma", "Valor", "Status", "PDF"]
        )
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tbl.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tbl.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tbl.horizontalHeader().setStretchLastSection(True)
        widths = [80, 95, 90, 95, 160, 260, 85, 90, 110, 105, 80]
        for idx, w in enumerate(widths):
            self.tbl.setColumnWidth(idx, w)
        layout.addWidget(self.tbl)
        return panel

    def _build_item_table_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        self.tbl_itens = QTableWidget(0, 4)
        self.tbl_itens.setHorizontalHeaderLabels(["Item", "Ocorrencias", "Obras", "Fornecedores"])
        self.tbl_itens.verticalHeader().setVisible(False)
        self.tbl_itens.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_itens.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_itens.setAlternatingRowColors(True)
        self.tbl_itens.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tbl_itens.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tbl_itens.horizontalHeader().setStretchLastSection(True)
        self.tbl_itens.setColumnWidth(0, 430)
        self.tbl_itens.setColumnWidth(1, 100)
        self.tbl_itens.setColumnWidth(2, 90)
        self.tbl_itens.setColumnWidth(3, 120)
        layout.addWidget(self.tbl_itens)
        return panel

    def _build_side_panel(self):
        outer = QFrame()
        outer.setObjectName("miniPanel")
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer.setMinimumWidth(320)
        outer.setMaximumWidth(520)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        self.box_top_obras = self._mini_panel("Top 5 Obras por Valor")
        self.top_obras_layout = self.box_top_obras.layout()
        self.box_empresas = self._mini_panel("Gastos por Empresa")
        self.empresas_layout = self.box_empresas.layout()
        self.box_status = self._mini_panel("Status de Auditoria")
        self.status_layout = self.box_status.layout()
        self.box_fornecedores = self._mini_panel("Top Fornecedores por Valor")
        self.fornecedores_layout = self.box_fornecedores.layout()
        self.box_itens = self._mini_panel("Top Itens por Ocorrencia")
        self.itens_layout = self.box_itens.layout()
        self.box_mensal = self._mini_panel("Evolucao Mensal de Pedidos")
        self.mensal_layout = self.box_mensal.layout()
        for box in (
            self.box_top_obras,
            self.box_empresas,
            self.box_status,
            self.box_fornecedores,
            self.box_itens,
            self.box_mensal,
        ):
            layout.addWidget(box)
        layout.addStretch()
        scroll.setWidget(container)
        outer_layout.addWidget(scroll)
        return outer

    def _mini_panel(self, title_text):
        card = QFrame()
        card.setObjectName("miniPanel")
        v = QVBoxLayout(card)
        v.setContentsMargins(12, 12, 12, 12)
        title = QLabel(title_text)
        title.setObjectName("miniTitle")
        v.addWidget(title)
        return card

    def _field(self, label_text, widget):
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        layout.addWidget(label)
        layout.addWidget(widget)
        return wrapper

    def _summary_card(self, title, value, hint):
        card = QFrame()
        card.setObjectName("summaryCard")
        self._apply_shadow(card)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        lbl_title = QLabel(title)
        lbl_title.setObjectName("summaryTitle")
        lbl_value = QLabel(value)
        lbl_value.setObjectName("summaryValue")
        lbl_hint = QLabel(hint)
        lbl_hint.setObjectName("summaryHint")
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        layout.addWidget(lbl_hint)
        layout.addStretch()
        card._valor_label = lbl_value
        return card

    def _apply_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 18))
        widget.setGraphicsEffect(shadow)

    def _load_logo(self):
        for path in LOGO_PATHS:
            if os.path.exists(path):
                return QPixmap(path)
        return None

    def recarregar(self):
        try:
            self._dados, origem = self.service.carregar()
            self.lbl_source.setText(f"Fonte de dados: {origem}")
            self._filtrados = list(self._dados)
            self._popular_filtros_combo()
            self._atualizar_tela()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao recarregar dados.\n\n{e}")

    def buscar_pdfs_filtrados(self):
        filtros = {
            "comprador": self.cb_comprador.currentText(),
            "obra": self.cb_obra.currentText(),
            "fornecedor": self.cb_fornecedor.currentText(),
            "item": self.ed_item.text(),
        }
        try:
            total = self.service.buscar_pdfs_filtrados(self._filtrados, filtros)
            self._atualizar_tela()
            QMessageBox.information(
                self,
                "Busca de PDFs concluida",
                f"PDFs encontrados para o filtro atual: {total}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao buscar PDFs filtrados.\n\n{e}")

    def _popular_filtros_combo(self):
        compradores = sorted({(i.get("comprador") or "").strip() for i in self._dados if (i.get("comprador") or "").strip()})
        empresas = sorted({(i.get("empresa_faturadora") or "").strip() for i in self._dados if (i.get("empresa_faturadora") or "").strip()})
        obras = sorted({(i.get("obra_nome") or "").strip() for i in self._dados if (i.get("obra_nome") or "").strip()})
        fornecedores = sorted({(i.get("fornecedor_nome") or "").strip() for i in self._dados if (i.get("fornecedor_nome") or "").strip()})

        self.cb_comprador.clear()
        self.cb_empresa.clear()
        self.cb_obra.clear()
        self.cb_fornecedor.clear()

        self.cb_comprador.addItems(["TODOS"] + compradores + ["SEM COMPRADOR"])
        self.cb_empresa.addItems(["TODAS"] + empresas)
        self.cb_obra.addItems(["TODAS"] + obras)
        self.cb_fornecedor.addItems(["TODOS"] + fornecedores)

        if self.cb_obra.completer():
            self.cb_obra.completer().setModel(self.cb_obra.model())
        if self.cb_fornecedor.completer():
            self.cb_fornecedor.completer().setModel(self.cb_fornecedor.model())

    def aplicar_filtros(self):
        comprador = self.cb_comprador.currentText().strip().upper()
        empresa = self.cb_empresa.currentText().strip().upper()
        status = self.cb_status.currentText().strip().upper()
        obra = self.cb_obra.currentText().strip().upper()
        fornecedor = self.cb_fornecedor.currentText().strip().upper()
        numero = self.ed_numero.text().strip().upper()
        item_busca = self.ed_item.text().strip().upper()
        data_ini = self.ed_data_ini.text().strip()
        data_fim = self.ed_data_fim.text().strip()
        dados = []
        for item in self._dados:
            comp_item = (item.get("comprador") or "").strip().upper() or "SEM COMPRADOR"
            stat_item = (item.get("status_auditoria") or "").strip().upper()
            if comprador != "TODOS" and comp_item != comprador:
                continue
            if empresa != "TODAS" and (item.get("empresa_faturadora") or "").strip().upper() != empresa:
                continue
            if status != "TODOS" and stat_item != status:
                continue
            if obra and obra != "TODAS" and obra not in (item.get("obra_nome") or "").upper():
                continue
            if fornecedor and fornecedor != "TODOS" and fornecedor not in (item.get("fornecedor_nome") or "").upper():
                continue
            if numero and numero not in str(item.get("numero") or "").upper():
                continue
            if item_busca and item_busca not in (item.get("itens_texto") or "").upper():
                continue
            if not self._data_no_intervalo(item.get("data_pedido", ""), data_ini, data_fim):
                continue
            dados.append(item)
        self._filtrados = dados
        self._atualizar_tela()

    def limpar_filtros(self):
        for cb in (self.cb_comprador, self.cb_empresa, self.cb_status, self.cb_obra, self.cb_fornecedor):
            cb.setCurrentIndex(0)
        self.ed_numero.clear()
        self.ed_item.clear()
        self.ed_data_ini.clear()
        self.ed_data_fim.clear()
        self._filtrados = list(self._dados)
        self._atualizar_tela()

    def _atualizar_tela(self):
        self._preencher_tabela()
        self._preencher_tabela_itens()
        self._atualizar_cards()
        self._atualizar_painel_lateral()

    def _data_no_intervalo(self, data_texto, data_ini, data_fim):
        base = self._parse_data(data_texto)
        if base is None:
            return True
        if data_ini:
            d_ini = self._parse_data(data_ini)
            if d_ini and base < d_ini:
                return False
        if data_fim:
            d_fim = self._parse_data(data_fim)
            if d_fim and base > d_fim:
                return False
        return True

    def _parse_data(self, texto):
        for fmt in ("%d/%m/%Y", "%d/%m/%y"):
            try:
                return datetime.strptime(texto, fmt)
            except Exception:
                pass
        return None

    def _preencher_tabela(self):
        self.tbl.setRowCount(0)
        for row_idx, item in enumerate(self._filtrados):
            self.tbl.insertRow(row_idx)
            self.tbl.setRowHeight(row_idx, 40)
            comprador = str(item.get("comprador") or "").strip() or "SEM COMPRADOR"
            self._set_item(row_idx, 0, str(item.get("numero") or ""))
            self._set_item(row_idx, 1, comprador)
            self._set_item(row_idx, 2, str(item.get("data_pedido") or ""))
            self._set_item(row_idx, 3, str(item.get("empresa_faturadora") or ""))
            self._set_item(row_idx, 4, str(item.get("fornecedor_nome") or ""))
            self._set_item(row_idx, 5, str(item.get("obra_nome") or ""))
            self._set_item(row_idx, 6, str(item.get("condicao_pagamento") or ""))
            self._set_item(row_idx, 7, str(item.get("forma_pagamento") or ""))
            self._set_item(row_idx, 8, self._fmt_moeda(item.get("valor_total")))
            self._set_item(row_idx, 9, str(item.get("status_auditoria") or ""))
            path = item.get("pdf_rede", "") or ""
            if path and os.path.exists(path):
                btn_pdf = QPushButton("Abrir")
                btn_pdf.setObjectName("pdfButton")
                btn_pdf.clicked.connect(lambda _, p=path: self._abrir_pdf(p))
            else:
                btn_pdf = QPushButton("Sem PDF")
                btn_pdf.setObjectName("pdfButtonDisabled")
                btn_pdf.setEnabled(False)
            self.tbl.setCellWidget(row_idx, 10, btn_pdf)

    def _preencher_tabela_itens(self):
        agregados = {}
        for pedido in self._filtrados:
            itens = pedido.get("itens_lista") or []
            obra = (pedido.get("obra_nome") or "SEM OBRA").strip() or "SEM OBRA"
            forn = (pedido.get("fornecedor_nome") or "SEM FORNECEDOR").strip() or "SEM FORNECEDOR"
            for item in itens:
                if item not in agregados:
                    agregados[item] = {"qtd": 0, "obras": set(), "fornecedores": set()}
                agregados[item]["qtd"] += 1
                agregados[item]["obras"].add(obra)
                agregados[item]["fornecedores"].add(forn)

        ranking = sorted(agregados.items(), key=lambda x: x[1]["qtd"], reverse=True)
        self.tbl_itens.setRowCount(0)
        for row_idx, (nome_item, dados) in enumerate(ranking):
            self.tbl_itens.insertRow(row_idx)
            self.tbl_itens.setRowHeight(row_idx, 34)
            self.tbl_itens.setItem(row_idx, 0, QTableWidgetItem(nome_item))
            for col_idx, valor in enumerate(
                [str(dados["qtd"]), str(len(dados["obras"])), str(len(dados["fornecedores"]))], start=1
            ):
                it = QTableWidgetItem(valor)
                it.setTextAlignment(Qt.AlignCenter)
                self.tbl_itens.setItem(row_idx, col_idx, it)

    def _abrir_aba_obras(self):
        nome_aba = "Obras"
        idx_existente = self._index_aba_por_nome(nome_aba)
        if idx_existente >= 0:
            self.tabs_analise.removeTab(idx_existente)

        tabela = QTableWidget(0, 7)
        tabela.setHorizontalHeaderLabels(
            ["Obra", "Pedidos", "Valor Total", "Ticket Medio", "Pendencias", "Conformidade", "Fornecedores"]
        )
        tabela.verticalHeader().setVisible(False)
        tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tabela.setAlternatingRowColors(True)
        tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        tabela.setColumnWidth(0, 280)
        tabela.setColumnWidth(1, 80)
        tabela.setColumnWidth(2, 130)
        tabela.setColumnWidth(3, 120)
        tabela.setColumnWidth(4, 95)
        tabela.setColumnWidth(5, 110)
        tabela.setColumnWidth(6, 100)

        por_obra = {}
        for pedido in self._filtrados:
            obra = (pedido.get("obra_nome") or "SEM OBRA").strip() or "SEM OBRA"
            if obra not in por_obra:
                por_obra[obra] = {
                    "pedidos": 0,
                    "valor": 0.0,
                    "pendencias": 0,
                    "fornecedores": set(),
                }
            por_obra[obra]["pedidos"] += 1
            por_obra[obra]["valor"] += float(pedido.get("valor_total") or 0)
            if pedido.get("status_auditoria") != "OK":
                por_obra[obra]["pendencias"] += 1
            por_obra[obra]["fornecedores"].add((pedido.get("fornecedor_nome") or "SEM FORNECEDOR").strip() or "SEM FORNECEDOR")

        ranking = sorted(por_obra.items(), key=lambda x: x[1]["valor"], reverse=True)
        for row_idx, (obra, dados) in enumerate(ranking):
            tabela.insertRow(row_idx)
            tabela.setRowHeight(row_idx, 34)
            pedidos = dados["pedidos"]
            valor = dados["valor"]
            pendencias = dados["pendencias"]
            conformidade = ((pedidos - pendencias) / pedidos * 100) if pedidos > 0 else 0
            ticket = valor / pedidos if pedidos > 0 else 0

            tabela.setItem(row_idx, 0, QTableWidgetItem(obra))
            for col, texto in [
                (1, str(pedidos)),
                (2, self._fmt_moeda(valor)),
                (3, self._fmt_moeda(ticket)),
                (4, str(pendencias)),
                (5, f"{conformidade:.1f}%"),
                (6, str(len(dados["fornecedores"]))),
            ]:
                it = QTableWidgetItem(texto)
                it.setTextAlignment(Qt.AlignCenter)
                if col == 4 and pendencias > 0:
                    it.setForeground(QColor("#c0392b"))
                    f = QFont()
                    f.setBold(True)
                    it.setFont(f)
                tabela.setItem(row_idx, col, it)

        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(8, 8, 8, 8)
        info = QLabel("Visao consolidada por obra baseada nos filtros atuais.")
        info.setObjectName("miniMuted")
        c_layout.addWidget(info)
        c_layout.addWidget(tabela)

        idx_novo = self.tabs_analise.addTab(container, nome_aba)
        self.tabs_analise.setCurrentIndex(idx_novo)

    def _index_aba_por_nome(self, nome):
        for i in range(self.tabs_analise.count()):
            if self.tabs_analise.tabText(i) == nome:
                return i
        return -1

    def _ativar_foco_tabela(self):
        self._side_panel.setMaximumWidth(0)
        self._side_panel.setMinimumWidth(0)
        self._splitter.setSizes([9999, 0])
        self.lbl_focus_hint.setText("Modo foco ativo: tabela expandida.")

    def _restaurar_layout(self):
        self._side_panel.setMinimumWidth(320)
        self._side_panel.setMaximumWidth(520)
        self._splitter.setSizes([1450, 330])
        self.lbl_focus_hint.setText("Dica: use Modo foco para enxergar tudo da tabela.")

    def _toggle_filtros(self):
        if self.filters_panel.maximumWidth() == 0:
            self.filters_panel.setMinimumWidth(300)
            self.filters_panel.setMaximumWidth(420)
            self.workspace_splitter.setSizes([340, 1500])
            self.btn_toggle_filtros.setText("Ocultar filtros")
        else:
            self.filters_panel.setMinimumWidth(0)
            self.filters_panel.setMaximumWidth(0)
            self.workspace_splitter.setSizes([0, 1900])
            self.btn_toggle_filtros.setText("Mostrar filtros")

    def _set_item(self, row, col, texto):
        it = QTableWidgetItem(texto)
        if col in (0, 1, 2, 3, 6, 7, 8, 9):
            it.setTextAlignment(Qt.AlignCenter)
        if col == 8:
            it.setForeground(QColor("#0b6e3d"))
            f = QFont()
            f.setBold(True)
            it.setFont(f)
        if col == 9 and texto in ("Sem PDF", "Sem comprador", "Critico"):
            it.setForeground(QColor("#c0392b"))
            f = QFont()
            f.setBold(True)
            it.setFont(f)
        self.tbl.setItem(row, col, it)

    def _atualizar_cards(self):
        total = len(self._filtrados)
        total_valor = sum(float(i.get("valor_total") or 0) for i in self._filtrados)
        pendencias = sum(1 for i in self._filtrados if i.get("status_auditoria") != "OK")
        ticket = (total_valor / total) if total > 0 else 0
        conformidade = ((total - pendencias) / total * 100) if total > 0 else 0
        self.card_total._valor_label.setText(str(total))
        self.card_valor._valor_label.setText(self._fmt_moeda(total_valor))
        self.card_ticket._valor_label.setText(self._fmt_moeda(ticket))
        self.card_critico._valor_label.setText(str(pendencias))
        self.card_conformidade._valor_label.setText(f"{conformidade:.1f}%")

    def _atualizar_painel_lateral(self):
        self._clear_layout_keep_title(self.top_obras_layout)
        self._clear_layout_keep_title(self.empresas_layout)
        self._clear_layout_keep_title(self.status_layout)
        self._clear_layout_keep_title(self.fornecedores_layout)
        self._clear_layout_keep_title(self.itens_layout)
        self._clear_layout_keep_title(self.mensal_layout)

        obras = defaultdict(float)
        empresas = defaultdict(float)
        status = defaultdict(int)
        fornecedores = defaultdict(float)
        itens = defaultdict(int)
        mensal = {m: 0 for m in range(1, 13)}

        for item in self._filtrados:
            obras[(item.get("obra_nome") or "SEM OBRA").strip() or "SEM OBRA"] += float(item.get("valor_total") or 0)
            empresas[(item.get("empresa_faturadora") or "SEM EMPRESA").strip() or "SEM EMPRESA"] += float(item.get("valor_total") or 0)
            status[(item.get("status_auditoria") or "Sem status")] += 1
            fornecedores[(item.get("fornecedor_nome") or "SEM FORNECEDOR").strip() or "SEM FORNECEDOR"] += float(item.get("valor_total") or 0)
            for desc in item.get("itens_lista") or []:
                itens[desc] += 1
            dt = self._parse_data(item.get("data_pedido") or "")
            if dt:
                mensal[dt.month] += 1

        self._render_barras(self.top_obras_layout, sorted(obras.items(), key=lambda x: x[1], reverse=True)[:5], moeda=True)
        self._render_barras(self.empresas_layout, sorted(empresas.items(), key=lambda x: x[1], reverse=True), moeda=True)
        self._render_barras(self.status_layout, sorted(status.items(), key=lambda x: x[1], reverse=True), inteiro=True)
        self._render_barras(self.fornecedores_layout, sorted(fornecedores.items(), key=lambda x: x[1], reverse=True)[:7], moeda=True)
        self._render_barras(self.itens_layout, sorted(itens.items(), key=lambda x: x[1], reverse=True)[:10], inteiro=True)
        self._render_barras(self.mensal_layout, [(MESES_PT[m - 1], mensal[m]) for m in range(1, 13)], inteiro=True)

    def _render_barras(self, layout, dados, moeda=False, inteiro=False):
        if not dados:
            layout.addWidget(self._label_muted("Sem dados para exibir."))
            return
        maximo = max(v for _, v in dados)
        if maximo == 0:
            maximo = 1
        for nome, valor in dados:
            layout.addWidget(self._bar_row(nome, valor, maximo, moeda=moeda, inteiro=inteiro))

    def _bar_row(self, nome, valor, maximo, moeda=False, inteiro=False):
        w = QWidget()
        h = QVBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(4)
        topo = QHBoxLayout()
        lbl_nome = QLabel(nome)
        lbl_nome.setObjectName("miniMuted")
        lbl_nome.setWordWrap(True)
        if moeda:
            texto_valor = self._fmt_moeda(valor)
        elif inteiro:
            texto_valor = str(int(valor))
        else:
            texto_valor = str(valor)
        lbl_valor = QLabel(texto_valor)
        lbl_valor.setStyleSheet("font-size:11px; font-weight:700; color:#1f2937;")
        topo.addWidget(lbl_nome, 1)
        topo.addWidget(lbl_valor)
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(int((float(valor) / float(maximo)) * 100) if maximo > 0 else 0)
        bar.setTextVisible(False)
        h.addLayout(topo)
        h.addWidget(bar)
        return w

    def _label_muted(self, texto):
        lbl = QLabel(texto)
        lbl.setObjectName("miniMuted")
        return lbl

    def _clear_layout_keep_title(self, layout):
        while layout.count() > 1:
            item = layout.takeAt(1)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _abrir_pdf(self, caminho_pdf):
        if not caminho_pdf or not os.path.exists(caminho_pdf):
            QMessageBox.warning(self, "PDF não encontrado", f"Arquivo não localizado:\n\n{caminho_pdf}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(caminho_pdf))

    def _fmt_moeda(self, valor):
        try:
            return f"R$ {float(valor or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            return "R$ 0,00"
