import datetime
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QDateEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QSizePolicy, QScrollArea,
)
from PyQt5.QtCore import Qt, QDate, QSize
from PyQt5.QtGui import QColor

_RED   = "#a20f22"
_DARK  = "#2c3e50"
_GRAY  = "#f5f5f5"

_COLORS = [
    "#e74c3c", "#2980b9", "#27ae60", "#f39c12",
    "#8e44ad", "#16a085", "#d35400", "#2c3e50",
    "#c0392b", "#1abc9c",
]


class _LineChart(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(8, 3.8), dpi=96, facecolor="white")
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(280)
        self._draw_empty()

    def _draw_empty(self):
        self.ax.clear()
        self.ax.text(
            0.5, 0.5, "Seleccione filtros y presione «Actualizar Gráfico»",
            ha="center", va="center",
            transform=self.ax.transAxes,
            color="#aaaaaa", fontsize=10,
        )
        self.ax.axis("off")
        self.fig.tight_layout()
        self.draw()

    def refresh(self, series):
        """
        series: list of dicts
          { "label": str, "dates": [date, ...], "prices": [float, ...], "color": str }
        """
        self.ax.clear()
        self.fig.set_facecolor("white")
        self.ax.set_facecolor("#fafafa")

        if not series:
            self._draw_empty()
            return

        for s in series:
            dates = s["dates"]
            prices = s["prices"]
            color = s["color"]
            label = s["label"]
            if len(dates) == 1:
                self.ax.scatter(dates, prices, color=color, zorder=5, s=50)
                self.ax.annotate(
                    f"${prices[0]:,.2f}",
                    (dates[0], prices[0]),
                    textcoords="offset points", xytext=(4, 4),
                    fontsize=7, color=color,
                )
            else:
                self.ax.plot(dates, prices, marker="o", markersize=5,
                             linewidth=1.8, color=color, label=label)
                for d, p in zip(dates, prices):
                    self.ax.annotate(
                        f"${p:,.2f}", (d, p),
                        textcoords="offset points", xytext=(3, 5),
                        fontsize=6.5, color=color,
                    )

        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%y"))
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.fig.autofmt_xdate(rotation=35, ha="right")

        self.ax.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, _: f"${x:,.2f}")
        )
        self.ax.tick_params(labelsize=7.5)
        self.ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.6)
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)

        if len(series) > 1 or (len(series) == 1 and len(series[0]["dates"]) > 1):
            self.ax.legend(
                loc="upper left",
                fontsize=7.5,
                framealpha=0.85,
                ncol=min(3, len(series)),
            )

        self.ax.set_title("Evolución de Precios", fontsize=10,
                          fontweight="bold", color=_DARK, pad=8)
        self.fig.tight_layout()
        self.draw()


class GraficoPreciosView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self._init_ui()
        self._cargar_categorias()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        # ── Title ──────────────────────────────────────────────────────────────
        lbl = QLabel("Análisis de Precios de Insumos")
        lbl.setStyleSheet(f"font-size:17px; font-weight:bold; color:{_RED};")
        root.addWidget(lbl)

        # ── Filter bar ─────────────────────────────────────────────────────────
        filter_frame = QFrame()
        filter_frame.setStyleSheet(
            "background:#f9f9f9; border:1px solid #e0e0e0; border-radius:6px;"
        )
        filter_lay = QHBoxLayout(filter_frame)
        filter_lay.setContentsMargins(12, 8, 12, 8)
        filter_lay.setSpacing(10)

        filter_lay.addWidget(QLabel("Categoría:"))
        self.cmb_categoria = QComboBox()
        self.cmb_categoria.setMinimumWidth(160)
        self.cmb_categoria.currentIndexChanged.connect(self._on_categoria_changed)
        filter_lay.addWidget(self.cmb_categoria)

        filter_lay.addWidget(QLabel("Insumo:"))
        self.cmb_insumo = QComboBox()
        self.cmb_insumo.setMinimumWidth(200)
        filter_lay.addWidget(self.cmb_insumo)

        filter_lay.addWidget(QLabel("Desde:"))
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDate(QDate.currentDate().addMonths(-6))
        self.date_desde.setDisplayFormat("dd/MM/yyyy")
        filter_lay.addWidget(self.date_desde)

        filter_lay.addWidget(QLabel("Hasta:"))
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(QDate.currentDate())
        self.date_hasta.setDisplayFormat("dd/MM/yyyy")
        filter_lay.addWidget(self.date_hasta)

        btn_actualizar = QPushButton("Actualizar Gráfico")
        btn_actualizar.setProperty("class", "btn-primary")
        btn_actualizar.setStyleSheet(
            f"background:{_RED}; color:white; padding:6px 14px;"
            "border:none; border-radius:4px; font-weight:bold;"
        )
        btn_actualizar.clicked.connect(self._actualizar)
        filter_lay.addWidget(btn_actualizar)
        filter_lay.addStretch()
        root.addWidget(filter_frame)

        # ── Chart ──────────────────────────────────────────────────────────────
        self.chart = _LineChart(self)
        root.addWidget(self.chart, 3)

        # ── Detail table ───────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#e0e0e0;")
        root.addWidget(sep)

        lbl_det = QLabel("Detalle de Registros")
        lbl_det.setStyleSheet(f"font-size:12px; font-weight:bold; color:{_DARK};")
        root.addWidget(lbl_det)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Insumo", "Presentación", "Proveedor",
            "Fecha", "Precio Compra", "Costo Unit.",
        ])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setMaximumHeight(220)
        root.addWidget(self.table, 2)

    def _cargar_categorias(self):
        self.cmb_categoria.blockSignals(True)
        self.cmb_categoria.clear()
        self.cmb_categoria.addItem("— Todas las categorías —", None)
        rows = self.db.fetch_all(
            "SELECT id, nombre FROM categorias_insumos ORDER BY nombre", ()
        )
        for cat_id, nombre in rows:
            self.cmb_categoria.addItem(nombre, cat_id)
        self.cmb_categoria.blockSignals(False)
        self._cargar_insumos(None)

    def _cargar_insumos(self, categoria_id):
        self.cmb_insumo.blockSignals(True)
        self.cmb_insumo.clear()
        self.cmb_insumo.addItem("— Todos los insumos —", None)
        if categoria_id is None:
            rows = self.db.fetch_all(
                "SELECT id, nombre FROM insumos ORDER BY nombre", ()
            )
        else:
            rows = self.db.fetch_all(
                "SELECT id, nombre FROM insumos WHERE categoria_id=? ORDER BY nombre",
                (categoria_id,),
            )
        for ins_id, nombre in rows:
            self.cmb_insumo.addItem(nombre, ins_id)
        self.cmb_insumo.blockSignals(False)

    def _on_categoria_changed(self):
        cat_id = self.cmb_categoria.currentData()
        self._cargar_insumos(cat_id)

    def cargar_datos(self):
        pass

    def _actualizar(self):
        cat_id   = self.cmb_categoria.currentData()
        ins_id   = self.cmb_insumo.currentData()
        fecha_desde = self.date_desde.date().toString("yyyy-MM-dd")
        fecha_hasta = self.date_hasta.date().toString("yyyy-MM-dd")

        params = [fecha_desde, fecha_hasta]
        where_extra = ""
        if cat_id is not None:
            where_extra += " AND ci.id = ?"
            params.append(cat_id)
        if ins_id is not None:
            where_extra += " AND i.id = ?"
            params.append(ins_id)

        rows = self.db.fetch_all(
            f"""
            SELECT i.nombre, pc.nombre, COALESCE(pv.nombre, '—'),
                   h.fecha_registro, h.precio_compra, h.costo_unitario_calculado
            FROM historial_precios_presentacion h
            JOIN presentaciones_compra pc ON pc.id = h.presentacion_id
            JOIN insumos i ON i.id = pc.insumo_id
            LEFT JOIN proveedores pv ON pv.id = h.proveedor_id
            LEFT JOIN categorias_insumos ci ON ci.id = i.categoria_id
            WHERE h.fecha_registro BETWEEN ? AND ?
            {where_extra}
            ORDER BY i.nombre, pc.nombre, h.fecha_registro ASC
            """,
            tuple(params),
        )

        self._poblar_tabla(rows)

        series_map = {}
        for insumo, pres, proveedor, fecha_str, precio, costo in rows:
            key = f"{insumo} — {pres}"
            if key not in series_map:
                series_map[key] = {"dates": [], "prices": []}
            try:
                d = datetime.date.fromisoformat(str(fecha_str))
                series_map[key]["dates"].append(d)
                series_map[key]["prices"].append(float(precio))
            except (ValueError, TypeError):
                pass

        series = []
        for idx, (label, data) in enumerate(series_map.items()):
            if data["dates"]:
                series.append({
                    "label": label,
                    "dates": data["dates"],
                    "prices": data["prices"],
                    "color": _COLORS[idx % len(_COLORS)],
                })

        self.chart.refresh(series)

    def _poblar_tabla(self, rows):
        self.table.setRowCount(len(rows))
        for r, (insumo, pres, proveedor, fecha, precio, costo) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(str(insumo)))
            self.table.setItem(r, 1, QTableWidgetItem(str(pres)))
            self.table.setItem(r, 2, QTableWidgetItem(str(proveedor)))
            self.table.setItem(r, 3, QTableWidgetItem(str(fecha or "")))
            self.table.setItem(r, 4, QTableWidgetItem(f"$ {float(precio):,.2f}"))
            self.table.setItem(r, 5, QTableWidgetItem(f"$ {float(costo):,.4f}"))
