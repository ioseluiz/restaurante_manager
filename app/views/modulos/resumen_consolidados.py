from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QHeaderView,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QSizePolicy,
    QFrame,
    QComboBox,
    QSpinBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import csv
import datetime
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# ---------------------------------------------------------------------------
# Donut chart colors
# ---------------------------------------------------------------------------
_V_LABELS = ["Efectivo", "Yappy", "Pedidos Ya", "Clave", "Visa / MC"]
_V_COLORS = ["#c0392b", "#27ae60", "#f39c12", "#2980b9", "#8e44ad"]
_G_LABELS = ["Efectivo", "Cheques", "Yappy", "Tarjetas Créd."]
_G_COLORS = ["#e74c3c", "#3498db", "#2ecc71", "#9b59b6"]

_MESES_ES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
             "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]


class _DonutChart(FigureCanvas):
    def __init__(self, title, parent=None):
        self.fig = Figure(figsize=(3.8, 2.9), dpi=96, facecolor="white")
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self._title = title
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMaximumHeight(255)
        self.setMinimumHeight(200)
        self._draw_empty()

    def _draw_empty(self):
        self.ax.clear()
        self.ax.text(0.5, 0.5, "Sin datos este mes",
                     ha="center", va="center",
                     transform=self.ax.transAxes, color="#aaaaaa", fontsize=9)
        self.ax.axis("off")
        self.ax.set_title(self._title, fontsize=9.5, fontweight="bold",
                          color="#2c3e50", pad=6)
        self.fig.tight_layout()
        self.draw()

    def refresh(self, labels, values, colors):
        self.ax.clear()
        self.fig.set_facecolor("white")
        self.ax.set_facecolor("white")

        pairs = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
        if not pairs:
            self._draw_empty()
            return

        lbls, vals, cols = zip(*pairs)
        total = sum(vals)

        wedges, _, autopcts = self.ax.pie(
            vals,
            colors=cols,
            wedgeprops=dict(width=0.46, edgecolor="white", linewidth=2),
            startangle=90,
            autopct=lambda p: f"{p:.1f}%" if p >= 6 else "",
            pctdistance=0.75,
        )
        for ap in autopcts:
            ap.set_fontsize(7)
            ap.set_color("white")
            ap.set_fontweight("bold")

        self.ax.text(0, 0, f"${total:,.0f}",
                     ha="center", va="center",
                     fontsize=9, fontweight="bold", color="#2c3e50")

        legend_text = [f"{l}: ${v:,.0f}" for l, v in zip(lbls, vals)]
        self.ax.legend(
            wedges, legend_text,
            loc="lower center",
            bbox_to_anchor=(0.5, -0.30),
            fontsize=7.5,
            frameon=False,
            ncol=2,
            handlelength=0.9,
        )

        self.ax.set_title(self._title, fontsize=9.5, fontweight="bold",
                          color="#2c3e50", pad=6)
        self.fig.subplots_adjust(top=0.88, bottom=0.24, left=0.08, right=0.92)
        self.draw()


class NumericItem(QTableWidgetItem):
    """Permite ordenar columnas numéricas correctamente."""
    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            return super().__lt__(other)

class ResumenConsolidadosView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        hoy = datetime.date.today()
        _DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        dia_nombre = _DIAS_ES[hoy.weekday()]
        mes_nombre_hoy = _MESES_ES[hoy.month - 1]

        # --- HEADER ---
        header_layout = QHBoxLayout()
        title = QLabel("<h2>Resumen General Mensual</h2>")
        header_layout.addWidget(title)

        lbl_fecha = QLabel(f"Hoy: {dia_nombre}, {hoy.day} de {mes_nombre_hoy} de {hoy.year}")
        lbl_fecha.setStyleSheet("color: #2c3e50; font-size: 13px; font-weight: bold;")
        header_layout.addWidget(lbl_fecha)

        header_layout.addStretch()

        btn_exportar = QPushButton("📄 Exportar CSV")
        btn_exportar.setCursor(Qt.PointingHandCursor)
        btn_exportar.clicked.connect(self.exportar_csv)
        header_layout.addWidget(btn_exportar)

        btn_refresh = QPushButton("Actualizar Datos")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setProperty("class", "btn-primary")
        btn_refresh.clicked.connect(self.cargar_datos)
        header_layout.addWidget(btn_refresh)

        layout.addLayout(header_layout)

        info = QLabel("Vista consolidada de todos los ingresos (Ventas) y los gastos/pagos realizados por mes.")
        info.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info)

        # --- FILTER CONTROLS FOR DONUTS ---
        filter_frame = QFrame()
        filter_frame.setStyleSheet(
            "QFrame { background: #f9f9f9; border-radius: 6px; border: 1px solid #e0e0e0; }"
        )
        filter_row = QHBoxLayout(filter_frame)
        filter_row.setContentsMargins(12, 8, 12, 8)
        filter_row.setSpacing(10)

        lbl_filtro = QLabel("Período del gráfico:")
        lbl_filtro.setStyleSheet("font-weight: bold; border: none; background: transparent;")
        filter_row.addWidget(lbl_filtro)

        self.cmb_mes = QComboBox()
        for m in _MESES_ES:
            self.cmb_mes.addItem(m)
        self.cmb_mes.setCurrentIndex(hoy.month - 1)
        self.cmb_mes.setFixedWidth(130)
        filter_row.addWidget(self.cmb_mes)

        self.spn_anio = QSpinBox()
        self.spn_anio.setRange(2020, hoy.year + 1)
        self.spn_anio.setValue(hoy.year)
        self.spn_anio.setFixedWidth(75)
        filter_row.addWidget(self.spn_anio)

        btn_mes_actual = QPushButton("Mes Actual")
        btn_mes_actual.setCursor(Qt.PointingHandCursor)
        btn_mes_actual.clicked.connect(self._reset_filtro)
        filter_row.addWidget(btn_mes_actual)

        filter_row.addStretch()
        layout.addWidget(filter_frame)

        # --- DONUT CHARTS ---
        donut_frame = QFrame()
        donut_frame.setStyleSheet(
            "QFrame { background: white; border-radius: 8px; border: 1px solid #f0e0e2; }"
        )
        donut_row = QHBoxLayout(donut_frame)
        donut_row.setContentsMargins(12, 10, 12, 10)
        donut_row.setSpacing(16)

        mes_nombre = _MESES_ES[hoy.month - 1]
        self.donut_ventas = _DonutChart(f"Ventas por método de cobro — {mes_nombre} {hoy.year}")
        self.donut_gastos = _DonutChart(f"Gastos por método de pago — {mes_nombre} {hoy.year}")

        donut_row.addWidget(self.donut_ventas)
        donut_row.addWidget(self.donut_gastos)
        layout.addWidget(donut_frame)

        self.cmb_mes.currentIndexChanged.connect(self._on_filtro_changed)
        self.spn_anio.valueChanged.connect(self._on_filtro_changed)

        # --- TABLA ---
        self.table = QTableWidget()
        
        self.columnas = [
            "Mes / Año", 
            "Total Ventas (+)", 
            "Efectivo (-)", 
            "Cheques (-)", 
            "Yappy (-)", 
            "Tarjetas (-)", 
            "Total Gastos (-)", 
            "Balance General"
        ]
        
        self.table.setColumnCount(len(self.columnas))
        self.table.setHorizontalHeaderLabels(self.columnas)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
            
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        
        layout.addWidget(self.table)
        self.setLayout(layout)

    def exportar_csv(self):
        from app.views.modulos.export_utils import exportar_tabla_por_mes
        exportar_tabla_por_mes(self, self.table, "resumen_consolidados.csv", 0)

    def cargar_datos(self):
        self.table.setSortingEnabled(False)
        
        # Diccionario para agrupar por mes: { 'YYYY-MM': { 'ventas': 0, 'efectivo': 0, ... } }
        datos_mensuales = {}
        
        def inicializar_mes(mes):
            if mes not in datos_mensuales:
                datos_mensuales[mes] = {
                    'ventas': 0.0,
                    'efectivo': 0.0,
                    'cheques': 0.0,
                    'yappy': 0.0,
                    'tarjetas': 0.0
                }

        # 1. Obtener Ventas (Diario de Ventas)
        self.db.cursor.execute("""
            SELECT strftime('%Y-%m', fecha) as mes, SUM(total_ventas) 
            FROM diario_ventas GROUP BY mes
        """)
        for row in self.db.cursor.fetchall():
            mes = row[0]
            if not mes: continue
            inicializar_mes(mes)
            datos_mensuales[mes]['ventas'] += float(row[1] or 0.0)

        # 2. Obtener Gastos en Efectivo
        self.db.cursor.execute("""
            SELECT strftime('%Y-%m', fecha) as mes, SUM(total) 
            FROM pagos_efectivo GROUP BY mes
        """)
        for row in self.db.cursor.fetchall():
            mes = row[0]
            if not mes: continue
            inicializar_mes(mes)
            datos_mensuales[mes]['efectivo'] += float(row[1] or 0.0)

        # 3. Obtener Gastos por Cheque (monto)
        self.db.cursor.execute("""
            SELECT strftime('%Y-%m', fecha) as mes, SUM(monto) 
            FROM chequera GROUP BY mes
        """)
        for row in self.db.cursor.fetchall():
            mes = row[0]
            if not mes: continue
            inicializar_mes(mes)
            datos_mensuales[mes]['cheques'] += float(row[1] or 0.0)

        # 4. Obtener Gastos por Yappy (monto)
        self.db.cursor.execute("""
            SELECT strftime('%Y-%m', fecha) as mes, SUM(monto) 
            FROM transacciones_yappy GROUP BY mes
        """)
        for row in self.db.cursor.fetchall():
            mes = row[0]
            if not mes: continue
            inicializar_mes(mes)
            datos_mensuales[mes]['yappy'] += float(row[1] or 0.0)

        # 5. Obtener Gastos por Tarjeta (Solo tipo COMPRA, es decir, pagos realizados a terceros)
        self.db.cursor.execute("""
            SELECT strftime('%Y-%m', fecha) as mes, SUM(monto) 
            FROM transacciones_tarjeta 
            WHERE tipo_transaccion = 'COMPRA'
            GROUP BY mes
        """)
        for row in self.db.cursor.fetchall():
            mes = row[0]
            if not mes: continue
            inicializar_mes(mes)
            datos_mensuales[mes]['tarjetas'] += float(row[1] or 0.0)

        # Llenar la tabla
        self.table.setRowCount(0)
        
        # Ordenar meses de más reciente a más antiguo
        meses_ordenados = sorted(datos_mensuales.keys(), reverse=True)
        
        for r_idx, mes in enumerate(meses_ordenados):
            data = datos_mensuales[mes]
            ventas = data['ventas']
            efectivo = data['efectivo']
            cheques = data['cheques']
            yappy = data['yappy']
            tarjetas = data['tarjetas']
            
            total_gastos = efectivo + cheques + yappy + tarjetas
            balance = ventas - total_gastos
            
            self.table.insertRow(r_idx)
            
            # Mes / Año
            self.table.setItem(r_idx, 0, QTableWidgetItem(mes))
            
            # Ventas (+)
            it_ventas = NumericItem(f"{ventas:.2f}")
            it_ventas.setForeground(QColor("#2ecc71")) # Verde
            self.table.setItem(r_idx, 1, it_ventas)
            
            # Efectivo (-)
            self.table.setItem(r_idx, 2, NumericItem(f"{efectivo:.2f}"))
            
            # Cheques (-)
            self.table.setItem(r_idx, 3, NumericItem(f"{cheques:.2f}"))
            
            # Yappy (-)
            self.table.setItem(r_idx, 4, NumericItem(f"{yappy:.2f}"))
            
            # Tarjetas (-)
            self.table.setItem(r_idx, 5, NumericItem(f"{tarjetas:.2f}"))
            
            # Total Gastos (-)
            it_gastos = NumericItem(f"{total_gastos:.2f}")
            it_gastos.setForeground(QColor("#e74c3c")) # Rojo
            font = it_gastos.font()
            font.setBold(True)
            it_gastos.setFont(font)
            self.table.setItem(r_idx, 6, it_gastos)
            
            # Balance
            it_balance = NumericItem(f"{balance:.2f}")
            font_bal = it_balance.font()
            font_bal.setBold(True)
            it_balance.setFont(font_bal)
            if balance > 0:
                it_balance.setForeground(QColor("#2ecc71")) # Verde (Ganancia)
            elif balance < 0:
                it_balance.setForeground(QColor("#e74c3c")) # Rojo (Pérdida)
                
            self.table.setItem(r_idx, 7, it_balance)

        self.table.setSortingEnabled(True)

        # Refresh donuts using current filter selection
        self._actualizar_donuts(self.spn_anio.value(), self.cmb_mes.currentIndex() + 1)

    def _reset_filtro(self):
        hoy = datetime.date.today()
        self.cmb_mes.blockSignals(True)
        self.spn_anio.blockSignals(True)
        self.cmb_mes.setCurrentIndex(hoy.month - 1)
        self.spn_anio.setValue(hoy.year)
        self.cmb_mes.blockSignals(False)
        self.spn_anio.blockSignals(False)
        self._actualizar_donuts(hoy.year, hoy.month)

    def _on_filtro_changed(self):
        self._actualizar_donuts(self.spn_anio.value(), self.cmb_mes.currentIndex() + 1)

    def _actualizar_donuts(self, year: int, month: int):
        mes_key = f"{year:04d}-{month:02d}"
        mes_nombre = _MESES_ES[month - 1]
        self.donut_ventas._title = f"Ventas por método de cobro — {mes_nombre} {year}"
        self.donut_gastos._title = f"Gastos por método de pago — {mes_nombre} {year}"

        cur = self.db.cursor

        cur.execute("""
            SELECT COALESCE(SUM(yappy), 0),
                   COALESCE(SUM(pedidos_ya), 0),
                   COALESCE(SUM(clave), 0),
                   COALESCE(SUM(visa_mastercard), 0),
                   COALESCE(SUM(total_ventas), 0),
                   COALESCE(SUM(efectivo), 0)
            FROM diario_ventas
            WHERE strftime('%Y-%m', fecha) = ?
        """, (mes_key,))
        rv = cur.fetchone() or (0, 0, 0, 0, 0, 0)
        yappy_v, pedidos_v, clave_v, visa_v, total_v, efectivo_v = (float(x) for x in rv)
        self.donut_ventas.refresh(
            _V_LABELS,
            [efectivo_v, yappy_v, pedidos_v, clave_v, visa_v],
            _V_COLORS,
        )

        cur.execute("SELECT COALESCE(SUM(total), 0) FROM pagos_efectivo WHERE strftime('%Y-%m', fecha) = ?", (mes_key,))
        ef_g = float((cur.fetchone() or (0,))[0])

        cur.execute("SELECT COALESCE(SUM(monto), 0) FROM chequera WHERE strftime('%Y-%m', fecha) = ?", (mes_key,))
        ch_g = float((cur.fetchone() or (0,))[0])

        cur.execute("SELECT COALESCE(SUM(monto), 0) FROM transacciones_yappy WHERE strftime('%Y-%m', fecha) = ?", (mes_key,))
        ya_g = float((cur.fetchone() or (0,))[0])

        cur.execute("""
            SELECT COALESCE(SUM(monto), 0) FROM transacciones_tarjeta
            WHERE tipo_transaccion = 'COMPRA' AND strftime('%Y-%m', fecha) = ?
        """, (mes_key,))
        tc_g = float((cur.fetchone() or (0,))[0])

        self.donut_gastos.refresh(
            _G_LABELS,
            [ef_g, ch_g, ya_g, tc_g],
            _G_COLORS,
        )
