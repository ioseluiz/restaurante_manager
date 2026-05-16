import datetime

import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.ticker as mticker
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

_RED   = "#a20f22"
_ORANGE = "#d0741d"
_GREEN  = "#27ae60"
_BLUE   = "#2980b9"
_DARK   = "#2c3e50"
_GRAY   = "#7f8c8d"

_DIAS_ES   = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
_MESES_ES  = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
               "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
_MESES_ABR = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
               "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


# ---------------------------------------------------------------------------
# Embedded bar chart
# ---------------------------------------------------------------------------
class _BarChart(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 2.8), dpi=96, facecolor="white")
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._empty()

    def _empty(self):
        self.ax.clear()
        self.ax.set_facecolor("white")
        self.ax.text(0.5, 0.5, "Sin datos de ventas aún",
                     ha="center", va="center",
                     transform=self.ax.transAxes,
                     color=_GRAY, fontsize=11)
        self.fig.tight_layout(pad=1.0)
        self.draw()

    def refresh(self, labels, values):
        self.ax.clear()
        if not values or all(v == 0 for v in values):
            self._empty()
            return

        self.ax.set_facecolor("#fafafa")
        self.fig.set_facecolor("white")

        x = list(range(len(labels)))
        bars = self.ax.bar(x, values, color=_RED, width=0.55, zorder=2,
                           edgecolor="white", linewidth=0.5)

        max_val = max(values) if values else 1
        for bar, val in zip(bars, values):
            if val > 0:
                y_pos = bar.get_height() + max_val * 0.012
                self.ax.text(
                    bar.get_x() + bar.get_width() / 2, y_pos,
                    f"${val:,.0f}",
                    ha="center", va="bottom", fontsize=6.5, color=_DARK,
                )

        self.ax.set_xticks(x)
        self.ax.set_xticklabels(labels, fontsize=8)
        self.ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda v, _: f"${v:,.0f}")
        )
        self.ax.tick_params(axis="y", labelsize=7)
        for spine in ("top", "right"):
            self.ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"):
            self.ax.spines[spine].set_color("#e0e0e0")
        self.ax.yaxis.grid(True, color="#ebebeb", zorder=0)
        self.ax.set_axisbelow(True)
        self.fig.tight_layout(pad=1.2)
        self.draw()


# ---------------------------------------------------------------------------
# Reusable KPI card
# ---------------------------------------------------------------------------
def _make_card(title, color, subtitle=""):
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background-color: white;
            border-radius: 10px;
            border-top: 4px solid {color};
        }}
        QLabel {{ border: none; }}
    """)
    frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    frame.setMinimumHeight(100)

    vl = QVBoxLayout(frame)
    vl.setContentsMargins(16, 12, 16, 12)
    vl.setSpacing(4)

    lbl_title = QLabel(title)
    lbl_title.setStyleSheet(f"color: {_GRAY}; font-size: 12px; font-weight: bold;")
    lbl_title.setAlignment(Qt.AlignLeft)

    lbl_value = QLabel("—")
    lbl_value.setStyleSheet(f"color: {_DARK}; font-size: 22px; font-weight: bold;")
    lbl_value.setAlignment(Qt.AlignLeft)

    vl.addWidget(lbl_title)
    vl.addWidget(lbl_value)

    if subtitle:
        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet(f"color: {_GRAY}; font-size: 10px;")
        vl.addWidget(lbl_sub)
        frame.lbl_sub = lbl_sub

    frame.lbl_value = lbl_value
    return frame


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class DashboardView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(18)

        # ── Date header ──────────────────────────────────────────────
        root.addWidget(self._build_date_header())

        # ── KPI cards ────────────────────────────────────────────────
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)

        self.card_inventario = _make_card("Valor del Inventario", _RED, "stock actual × costo")
        self.card_tomas      = _make_card("Tomas de Inventario", _ORANGE, "sesiones cerradas")
        self.card_ayer       = _make_card("Ventas Día Anterior", _GREEN, "diario de ventas")
        self.card_mes        = _make_card("Ventas del Mes", _BLUE, "mes en curso")

        for c in (self.card_inventario, self.card_tomas, self.card_ayer, self.card_mes):
            kpi_row.addWidget(c)
        root.addLayout(kpi_row)

        # ── Chart + tables row ───────────────────────────────────────
        content_row = QHBoxLayout()
        content_row.setSpacing(18)

        # Left: chart
        self._chart_source = "diario"

        chart_frame = self._make_section_frame()
        chart_vl = QVBoxLayout(chart_frame)
        chart_vl.setContentsMargins(14, 12, 14, 10)
        chart_vl.setSpacing(8)

        # Title + toggle row
        chart_header = QHBoxLayout()
        chart_header.setSpacing(10)

        self.lbl_chart = QLabel("Ventas Mensuales — Diario de Ventas")
        self.lbl_chart.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {_DARK};"
        )
        chart_header.addWidget(self.lbl_chart)
        chart_header.addStretch()

        # Segmented toggle
        _seg_base = (
            "QPushButton {{"
            "  border: 1px solid #ddd; padding: 3px 14px;"
            "  font-size: 11px; background: white; color: #555;"
            "  border-{side}-radius: 0px; border-top-{side2}-radius: 5px;"
            "  border-bottom-{side2}-radius: 5px;"
            "}}"
            "QPushButton:checked {{"
            "  background: {red}; color: white; border-color: {red};"
            "}}"
            "QPushButton:hover:!checked {{ background: #fff0f1; }}"
        )
        _seg_L = (
            f"QPushButton {{ border: 1px solid #ddd; border-right: none;"
            f"  border-radius: 0; border-top-left-radius: 5px;"
            f"  border-bottom-left-radius: 5px; padding: 3px 14px;"
            f"  font-size: 11px; background: white; color: #555; }}"
            f"QPushButton:checked {{ background: {_RED}; color: white; border-color: {_RED}; }}"
            f"QPushButton:hover:!checked {{ background: #fff0f1; }}"
        )
        _seg_R = (
            f"QPushButton {{ border: 1px solid #ddd;"
            f"  border-radius: 0; border-top-right-radius: 5px;"
            f"  border-bottom-right-radius: 5px; padding: 3px 14px;"
            f"  font-size: 11px; background: white; color: #555; }}"
            f"QPushButton:checked {{ background: {_RED}; color: white; border-color: {_RED}; }}"
            f"QPushButton:hover:!checked {{ background: #fff0f1; }}"
        )

        from PyQt5.QtWidgets import QPushButton
        self.btn_src_diario   = QPushButton("Diario de Ventas")
        self.btn_src_reportes = QPushButton("Reportes del POS")
        for btn in (self.btn_src_diario, self.btn_src_reportes):
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(26)
            btn.setProperty("skip-auto-icon", True)

        self.btn_src_diario.setStyleSheet(_seg_L)
        self.btn_src_reportes.setStyleSheet(_seg_R)
        self.btn_src_diario.setChecked(True)

        self.btn_src_diario.clicked.connect(
            lambda: self._set_chart_source("diario")
        )
        self.btn_src_reportes.clicked.connect(
            lambda: self._set_chart_source("reportes")
        )

        chart_header.addWidget(self.btn_src_diario)
        chart_header.addWidget(self.btn_src_reportes)

        chart_vl.addLayout(chart_header)

        self.bar_chart = _BarChart()
        chart_vl.addWidget(self.bar_chart)

        content_row.addWidget(chart_frame, stretch=3)

        # Right: tables stacked
        tables_col = QVBoxLayout()
        tables_col.setSpacing(14)

        self.tbl_stock   = self._build_table("Alerta de Stock — 5 más bajos",
                                             ["Insumo", "Stock"])
        self.tbl_platos  = self._build_table("Top 5 Platos Más Vendidos",
                                             ["Plato", "Cantidad"])
        tables_col.addWidget(self.tbl_stock["frame"])
        tables_col.addWidget(self.tbl_platos["frame"])

        right_frame = self._make_section_frame()
        right_frame.setLayout(tables_col)
        right_frame.layout().setContentsMargins(14, 12, 14, 12)

        content_row.addWidget(right_frame, stretch=2)
        root.addLayout(content_row)

        # Initial load
        self.cargar_datos()

    # ------------------------------------------------------------------
    # Helper builders
    # ------------------------------------------------------------------
    def _build_date_header(self):
        hoy = datetime.date.today()
        dia_nombre = _DIAS_ES[hoy.weekday()]
        mes_nombre = _MESES_ES[hoy.month - 1]

        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
            }
            QLabel { border: none; }
        """)
        hl = QHBoxLayout(frame)
        hl.setContentsMargins(20, 14, 20, 14)

        lbl_fecha = QLabel(f"{dia_nombre}, {hoy.day} de {mes_nombre} de {hoy.year}")
        lbl_fecha.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {_DARK};"
        )
        hl.addWidget(lbl_fecha)
        hl.addStretch()

        lbl_badge = QLabel(f"{mes_nombre.upper()}  {hoy.year}")
        lbl_badge.setStyleSheet(f"""
            background-color: {_RED};
            color: white;
            font-size: 12px;
            font-weight: bold;
            border-radius: 6px;
            padding: 4px 14px;
        """)
        hl.addWidget(lbl_badge)
        return frame

    def _make_section_frame(self):
        f = QFrame()
        f.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
            }
        """)
        return f

    def _build_table(self, title, headers):
        frame = QFrame()
        frame.setStyleSheet("QFrame { background: transparent; } QLabel { border: none; }")
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(6)

        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {_DARK};")
        vl.addWidget(lbl)

        tbl = QTableWidget(0, len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        if len(headers) > 1:
            tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.NoSelection)
        tbl.setAlternatingRowColors(True)
        tbl.verticalHeader().setVisible(False)
        tbl.setMaximumHeight(180)
        vl.addWidget(tbl)

        return {"frame": frame, "table": tbl}

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def cargar_datos(self):
        hoy = datetime.date.today()
        ayer_str = (hoy - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        mes_str  = hoy.strftime("%Y-%m")

        cur = self.db.cursor

        # --- Valor del inventario ---
        cur.execute(
            "SELECT COALESCE(SUM(stock_actual * costo_unitario), 0.0) FROM insumos"
        )
        valor_inv = cur.fetchone()[0] or 0.0
        self.card_inventario.lbl_value.setText(f"$ {valor_inv:,.2f}")

        # --- Tomas de inventario cerradas ---
        try:
            cur.execute(
                "SELECT COUNT(*) FROM conteos_inventario WHERE estado = 'CERRADO'"
            )
            tomas = cur.fetchone()[0] or 0
        except Exception:
            tomas = 0
        self.card_tomas.lbl_value.setText(str(tomas))

        # --- Ventas día anterior ---
        cur.execute(
            "SELECT COALESCE(SUM(total_ventas), 0.0) FROM diario_ventas WHERE fecha = ?",
            (ayer_str,),
        )
        ventas_ayer = cur.fetchone()[0] or 0.0
        self.card_ayer.lbl_value.setText(f"$ {ventas_ayer:,.2f}")
        self.card_ayer.lbl_sub.setText(
            f"Ayer — {_DIAS_ES[(hoy - datetime.timedelta(days=1)).weekday()]} {ayer_str}"
        )

        # --- Ventas del mes en curso ---
        cur.execute(
            "SELECT COALESCE(SUM(total_ventas), 0.0) FROM diario_ventas "
            "WHERE strftime('%Y-%m', fecha) = ?",
            (mes_str,),
        )
        ventas_mes = cur.fetchone()[0] or 0.0
        self.card_mes.lbl_value.setText(f"$ {ventas_mes:,.2f}")

        # --- Gráfico ---
        self._load_chart()

        # --- Stock más bajo ---
        cur.execute(
            "SELECT nombre, stock_actual FROM insumos ORDER BY stock_actual ASC LIMIT 5"
        )
        tbl_s = self.tbl_stock["table"]
        tbl_s.setRowCount(0)
        for r, (nombre, stock) in enumerate(cur.fetchall()):
            tbl_s.insertRow(r)
            tbl_s.setItem(r, 0, QTableWidgetItem(nombre))
            it = QTableWidgetItem(f"{stock:.2f}")
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if stock <= 0:
                it.setForeground(QColor(_RED))
            tbl_s.setItem(r, 1, it)

        # --- Top platos vendidos ---
        cur.execute(
            """
            SELECT m.nombre, SUM(d.cantidad) AS total_vendido
            FROM detalle_ventas_diarias d
            JOIN menu_items m ON d.menu_item_id = m.id
            GROUP BY m.id
            ORDER BY total_vendido DESC
            LIMIT 5
            """
        )
        tbl_p = self.tbl_platos["table"]
        tbl_p.setRowCount(0)
        for r, (nombre, cant) in enumerate(cur.fetchall()):
            tbl_p.insertRow(r)
            tbl_p.setItem(r, 0, QTableWidgetItem(nombre))
            it = QTableWidgetItem(f"{cant:.0f}")
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            tbl_p.setItem(r, 1, it)

    # ------------------------------------------------------------------
    # Chart source toggle
    # ------------------------------------------------------------------
    def _set_chart_source(self, source: str):
        self._chart_source = source
        self.btn_src_diario.setChecked(source == "diario")
        self.btn_src_reportes.setChecked(source == "reportes")
        titles = {
            "diario":   "Ventas Mensuales — Diario de Ventas",
            "reportes": "Ventas Mensuales — Reportes del POS",
        }
        self.lbl_chart.setText(titles[source])
        self._load_chart()

    # ------------------------------------------------------------------
    # Date parsing helper — handles any common format from POS CSV
    # ------------------------------------------------------------------
    _DATE_FMTS = (
        "%Y-%m-%d",   # ISO  2025-03-01
        "%d/%m/%Y",   # Latin  01/03/2025
        "%d-%m-%Y",   # 01-03-2025
        "%m/%d/%Y",   # US  03/01/2025
        "%Y/%m/%d",   # 2025/03/01
        "%d/%m/%y",   # 01/03/25
    )

    def _parse_mes(self, date_str: str):
        """Return 'YYYY-MM' from any common date string, or None."""
        s = date_str.strip()
        for fmt in self._DATE_FMTS:
            try:
                return datetime.datetime.strptime(s, fmt).strftime("%Y-%m")
            except ValueError:
                continue
        return None

    def _load_chart(self):
        cur = self.db.cursor

        if self._chart_source == "diario":
            cur.execute(
                """
                SELECT strftime('%Y-%m', fecha) AS mes, COALESCE(SUM(total_ventas), 0)
                FROM diario_ventas
                WHERE fecha IS NOT NULL
                GROUP BY mes ORDER BY mes ASC
                """
            )
            rows = cur.fetchall()
            # diario_ventas stores ISO dates → strftime is reliable
            data = {mes: float(val) for mes, val in rows if mes}

        else:
            # fecha_inicio_periodo may be stored in any format from the POS CSV.
            # Group by report id, fetch raw date, aggregate by month in Python.
            cur.execute(
                """
                SELECT rv.fecha_inicio_periodo, COALESCE(SUM(drv.total_venta), 0)
                FROM reportes_ventas rv
                JOIN detalle_reportes_ventas drv ON drv.reporte_id = rv.id
                WHERE rv.fecha_inicio_periodo IS NOT NULL
                  AND rv.fecha_inicio_periodo != ''
                GROUP BY rv.id
                ORDER BY rv.fecha_inicio_periodo ASC
                """
            )
            rows = cur.fetchall()
            data = {}
            for fecha_str, total in rows:
                mes = self._parse_mes(str(fecha_str))
                if mes:
                    data[mes] = data.get(mes, 0.0) + float(total)

        if not data:
            self.bar_chart.refresh([], [])
            return

        # Build a continuous month range: earliest data → current month
        today = datetime.date.today()
        earliest = min(data.keys())
        ey, em = map(int, earliest.split("-"))
        cy, cm = today.year, today.month

        labels, values = [], []
        y, m = ey, em
        while (y, m) <= (cy, cm):
            key = f"{y:04d}-{m:02d}"
            labels.append(f"{_MESES_ABR[m - 1]}\n'{y % 100:02d}")
            values.append(data.get(key, 0.0))
            m += 1
            if m > 12:
                m, y = 1, y + 1

        # Keep the last 18 months when the range is very long
        if len(labels) > 18:
            labels = labels[-18:]
            values = values[-18:]

        self.bar_chart.refresh(labels, values)
