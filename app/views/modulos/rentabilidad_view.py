# [FILE: app/views/modulos/rentabilidad_view.py]
"""
Módulo de Rentabilidad — Estado de Resultados (P&L) mensual y anual.

Tres pestañas:
  1. Estado de Resultados: P&L vertical del mes elegido (Ventas − Costo de Ventas
     − Gastos = Utilidad Neta) con % sobre ventas, costo real vs teórico (merma) y
     variación vs mes anterior / vs año anterior. Tarjetas KPI y export CSV.
  2. Desglose de Gastos: gastos por categoría del mes (tabla + donut) y compras
     itemizadas por categoría de insumo (referencia, no sumada).
  3. Comparativo Anual: 12 meses × métricas + total, con gráfico de utilidad neta.
"""

import csv
import datetime

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QHeaderView,
    QPushButton,
    QComboBox,
    QSpinBox,
    QFrame,
    QFileDialog,
    QMessageBox,
    QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from app.controllers.rentabilidad_controller import (
    RentabilidadController,
    ETIQUETAS_GASTOS,
    ETIQUETAS_COGS,
    GASTO_OP_COLS,
    COGS_COLS,
)
from app.views.modulos.resumen_consolidados import _DonutChart, NumericItem
from app.views.dashboard import _BarChart, _make_card, _MESES_ES, _MESES_ABR

_RED = "#a20f22"
_GREEN = "#2ecc71"
_RED_NEG = "#e74c3c"
_ORANGE = "#d0741d"
_BLUE = "#2980b9"
_DARK = "#2c3e50"
_GRAY = "#7f8c8d"

# Paleta de gastos para el donut (orden = GASTO_OP_COLS + canales)
_GASTO_KEYS = GASTO_OP_COLS + ["cheques", "yappy", "tarjetas"]
_GASTO_COLORS = [
    "#c0392b", "#e67e22", "#f1c40f", "#16a085", "#2980b9",
    "#8e44ad", "#7f8c8d", "#95a5a6", "#2c3e50", "#27ae60", "#9b59b6",
]


def _money(v):
    return f"$ {v:,.2f}"


def _pct_str(v):
    return f"{v:.1f}%"


class RentabilidadView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.ctrl = RentabilidadController(db_manager)
        self._init_ui()
        self.cargar_datos()

    # ==================================================================
    # UI
    # ==================================================================
    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        # --- Encabezado con selector de período ---
        header = QHBoxLayout()
        title = QLabel("<h2>Análisis de Rentabilidad</h2>")
        header.addWidget(title)
        header.addStretch()

        header.addWidget(self._lbl("Mes:"))
        self.cmb_mes = QComboBox()
        for m in _MESES_ES:
            self.cmb_mes.addItem(m)
        hoy = datetime.date.today()
        self.cmb_mes.setCurrentIndex(hoy.month - 1)
        self.cmb_mes.setFixedWidth(130)
        header.addWidget(self.cmb_mes)

        header.addWidget(self._lbl("Año:"))
        self.spn_anio = QSpinBox()
        self.spn_anio.setRange(2020, hoy.year + 1)
        self.spn_anio.setValue(hoy.year)
        self.spn_anio.setFixedWidth(80)
        header.addWidget(self.spn_anio)

        btn_actual = QPushButton("Mes Actual")
        btn_actual.setCursor(Qt.PointingHandCursor)
        btn_actual.clicked.connect(self._reset_periodo)
        header.addWidget(btn_actual)

        btn_refresh = QPushButton("Actualizar")
        btn_refresh.setProperty("class", "btn-primary")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self.cargar_datos)
        header.addWidget(btn_refresh)

        root.addLayout(header)

        # --- Pestañas ---
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_tab_pyl(), "Estado de Resultados")
        self.tabs.addTab(self._build_tab_desglose(), "Desglose de Gastos")
        self.tabs.addTab(self._build_tab_anual(), "Comparativo Anual")
        root.addWidget(self.tabs)

        # Señales
        self.cmb_mes.currentIndexChanged.connect(self.cargar_datos)
        self.spn_anio.valueChanged.connect(self.cargar_datos)
        self.tabs.currentChanged.connect(lambda _: self.cargar_datos())

    def _lbl(self, text):
        l = QLabel(text)
        l.setStyleSheet("font-weight: bold; color: #2c3e50;")
        return l

    # ---------------- Tab 1: P&L ----------------
    def _build_tab_pyl(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 10, 6, 6)
        lay.setSpacing(12)

        # KPIs
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        self.card_ventas = _make_card("Ventas Netas", _BLUE, "mes seleccionado")
        self.card_bruta = _make_card("Utilidad Bruta", _ORANGE, "ventas − costo")
        self.card_neta = _make_card("Utilidad Neta", _GREEN, "resultado del mes")
        self.card_margen = _make_card("Margen Neto", _RED, "utilidad / ventas")
        for c in (self.card_ventas, self.card_bruta, self.card_neta, self.card_margen):
            kpi_row.addWidget(c)
        lay.addLayout(kpi_row)

        # Botón export
        bar = QHBoxLayout()
        self.lbl_periodo_pyl = QLabel("")
        self.lbl_periodo_pyl.setStyleSheet("color: #7f8c8d; font-style: italic;")
        bar.addWidget(self.lbl_periodo_pyl)
        bar.addStretch()
        btn_exp = QPushButton("📄 Exportar CSV")
        btn_exp.setCursor(Qt.PointingHandCursor)
        btn_exp.clicked.connect(lambda: self._exportar_tabla(self.tbl_pyl, "estado_resultados.csv"))
        bar.addWidget(btn_exp)
        lay.addLayout(bar)

        # Tabla del estado de resultados
        self.tbl_pyl = QTableWidget()
        cols = ["Concepto", "Monto", "% Ventas", "Δ Mes Anterior", "Δ Año Anterior"]
        self.tbl_pyl.setColumnCount(len(cols))
        self.tbl_pyl.setHorizontalHeaderLabels(cols)
        h = self.tbl_pyl.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, len(cols)):
            h.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.tbl_pyl.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_pyl.setSelectionMode(QTableWidget.NoSelection)
        self.tbl_pyl.verticalHeader().setVisible(False)
        lay.addWidget(self.tbl_pyl)
        return w

    # ---------------- Tab 2: Desglose ----------------
    def _build_tab_desglose(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 10, 6, 6)
        lay.setSpacing(12)

        top = QHBoxLayout()
        top.setSpacing(14)

        # Donut de gastos
        donut_frame = QFrame()
        donut_frame.setStyleSheet(
            "QFrame { background: white; border-radius: 8px; border: 1px solid #f0e0e2; }"
        )
        dl = QVBoxLayout(donut_frame)
        dl.setContentsMargins(10, 8, 10, 8)
        self.donut_gastos = _DonutChart("Gastos Operativos por categoría")
        dl.addWidget(self.donut_gastos)
        top.addWidget(donut_frame, stretch=2)

        # Tabla de gastos por categoría
        gastos_frame = QFrame()
        gl = QVBoxLayout(gastos_frame)
        gl.setContentsMargins(0, 0, 0, 0)
        gl.addWidget(self._section_label("Gastos del mes por categoría"))
        self.tbl_gastos = QTableWidget()
        self.tbl_gastos.setColumnCount(3)
        self.tbl_gastos.setHorizontalHeaderLabels(["Categoría", "Monto", "% Ventas"])
        self.tbl_gastos.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_gastos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_gastos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl_gastos.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_gastos.verticalHeader().setVisible(False)
        gl.addWidget(self.tbl_gastos)
        top.addWidget(gastos_frame, stretch=3)
        lay.addLayout(top)

        # Compras por categoría (referencia)
        lay.addWidget(self._section_label(
            "Compras registradas por categoría de insumo  (referencia — no se suma al P&L)"
        ))
        self.tbl_compras = QTableWidget()
        self.tbl_compras.setColumnCount(2)
        self.tbl_compras.setHorizontalHeaderLabels(["Categoría de Insumo", "Total Compras"])
        self.tbl_compras.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_compras.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_compras.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_compras.verticalHeader().setVisible(False)
        self.tbl_compras.setMaximumHeight(200)
        lay.addWidget(self.tbl_compras)
        return w

    # ---------------- Tab 3: Comparativo anual ----------------
    def _build_tab_anual(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 10, 6, 6)
        lay.setSpacing(12)

        bar = QHBoxLayout()
        self.lbl_anual = QLabel("")
        self.lbl_anual.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px;")
        bar.addWidget(self.lbl_anual)
        bar.addStretch()
        btn_exp = QPushButton("📄 Exportar CSV")
        btn_exp.setCursor(Qt.PointingHandCursor)
        btn_exp.clicked.connect(lambda: self._exportar_tabla(self.tbl_anual, "comparativo_anual.csv"))
        bar.addWidget(btn_exp)
        lay.addLayout(bar)

        # Tabla: filas = métricas, columnas = meses + total
        self.tbl_anual = QTableWidget()
        headers = ["Concepto"] + _MESES_ABR + ["TOTAL"]
        self.tbl_anual.setColumnCount(len(headers))
        self.tbl_anual.setHorizontalHeaderLabels(headers)
        self.tbl_anual.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, len(headers)):
            self.tbl_anual.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.tbl_anual.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_anual.setSelectionMode(QTableWidget.NoSelection)
        self.tbl_anual.verticalHeader().setVisible(False)
        self.tbl_anual.setMaximumHeight(230)
        lay.addWidget(self.tbl_anual)

        # Gráfico de utilidad neta mensual
        chart_frame = QFrame()
        chart_frame.setStyleSheet("QFrame { background: white; border-radius: 8px; }")
        cl = QVBoxLayout(chart_frame)
        cl.setContentsMargins(10, 8, 10, 8)
        cl.addWidget(self._section_label("Utilidad Neta mensual"))
        self.bar_anual = _BarChart()
        cl.addWidget(self.bar_anual)
        lay.addWidget(chart_frame)
        return w

    def _section_label(self, text):
        l = QLabel(text)
        l.setStyleSheet("font-size: 12px; font-weight: bold; color: #2c3e50; margin-top: 4px;")
        return l

    # ==================================================================
    # Carga de datos
    # ==================================================================
    @property
    def anio(self):
        return self.spn_anio.value()

    @property
    def mes(self):
        return self.cmb_mes.currentIndex() + 1

    def cargar_datos(self):
        idx = self.tabs.currentIndex()
        if idx == 0:
            self._refresh_pyl()
        elif idx == 1:
            self._refresh_desglose()
        elif idx == 2:
            self._refresh_anual()

    def _reset_periodo(self):
        hoy = datetime.date.today()
        self.cmb_mes.blockSignals(True)
        self.spn_anio.blockSignals(True)
        self.cmb_mes.setCurrentIndex(hoy.month - 1)
        self.spn_anio.setValue(hoy.year)
        self.cmb_mes.blockSignals(False)
        self.spn_anio.blockSignals(False)
        self.cargar_datos()

    # ------------------ P&L ------------------
    def _refresh_pyl(self):
        d = self.ctrl.deltas(self.anio, self.mes)
        pyl = d["actual"]
        self.lbl_periodo_pyl.setText(
            f"Estado de Resultados — {_MESES_ES[self.mes - 1]} {self.anio}"
        )

        # KPIs
        self.card_ventas.lbl_value.setText(_money(pyl["ventas"]))
        self.card_bruta.lbl_value.setText(_money(pyl["utilidad_bruta"]))
        self.card_neta.lbl_value.setText(_money(pyl["utilidad_neta"]))
        self.card_margen.lbl_value.setText(_pct_str(pyl["margen_neto"]))
        # color utilidad neta
        neta_color = _GREEN if pyl["utilidad_neta"] >= 0 else _RED_NEG
        self.card_neta.lbl_value.setStyleSheet(
            f"color: {neta_color}; font-size: 22px; font-weight: bold;"
        )

        rows = self._construir_filas_pyl(pyl, d)
        self.tbl_pyl.setRowCount(0)
        for r, fila in enumerate(rows):
            self.tbl_pyl.insertRow(r)
            self._pintar_fila_pyl(r, fila)

    def _construir_filas_pyl(self, pyl, d):
        """Cada fila: (concepto, monto|None, pct|None, delta_ma|None, delta_aa|None, estilo)."""
        p = pyl["pct"]
        dma = d["vs_mes_anterior"]
        daa = d["vs_anio_anterior"]
        filas = []

        # Ventas
        filas.append(("VENTAS NETAS", pyl["ventas"], p["ventas"],
                      dma["ventas"], daa["ventas"], "header"))

        # Costo de ventas
        filas.append(("COSTO DE VENTAS", None, None, None, None, "section"))
        for c in COGS_COLS:
            filas.append(("   " + ETIQUETAS_COGS[c], pyl["cogs_desglose"][c],
                          p[c], None, None, "detail"))
        filas.append(("   Costo de Ventas (Real)", pyl["costo_real"],
                      p["costo_real"], None, None, "subtotal"))
        if pyl["costo_teorico"] is not None:
            filas.append(("   Costo Teórico (Recetas)", pyl["costo_teorico"],
                          p.get("costo_teorico"), None, None, "detail"))
            filas.append(("   Merma / Desviación", pyl["merma"],
                          p.get("merma"), None, None, "merma"))
        else:
            filas.append(("   Costo Teórico (Recetas)", None, None, None, None, "sin_dato"))

        # Utilidad bruta
        filas.append(("UTILIDAD BRUTA", pyl["utilidad_bruta"], p["utilidad_bruta"],
                      dma["utilidad_bruta"], daa["utilidad_bruta"], "header"))

        # Gastos operativos
        filas.append(("GASTOS OPERATIVOS", None, None, None, None, "section"))
        for k in _GASTO_KEYS:
            filas.append(("   " + ETIQUETAS_GASTOS[k], pyl["gastos"][k],
                          p[k], None, None, "detail"))
        filas.append(("   Total Gastos Operativos", pyl["total_gastos"],
                      p["total_gastos"], None, None, "subtotal"))

        # Utilidad neta
        filas.append(("UTILIDAD NETA", pyl["utilidad_neta"], p["utilidad_neta"],
                      dma["utilidad_neta"], daa["utilidad_neta"], "total"))
        return filas

    def _pintar_fila_pyl(self, r, fila):
        concepto, monto, pct, dma, daa, estilo = fila

        it_concepto = QTableWidgetItem(concepto)
        it_monto = QTableWidgetItem("—" if monto is None else _money(monto))
        it_monto.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        it_pct = QTableWidgetItem("" if pct is None else _pct_str(pct))
        it_pct.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        it_dma = QTableWidgetItem(self._fmt_delta(dma))
        it_dma.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        it_daa = QTableWidgetItem(self._fmt_delta(daa))
        it_daa.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

        items = [it_concepto, it_monto, it_pct, it_dma, it_daa]

        # Estilos por tipo de fila
        def bold(it):
            f = it.font(); f.setBold(True); it.setFont(f)

        if estilo in ("header", "total", "subtotal", "section"):
            for it in items:
                bold(it)
        if estilo == "total":
            color = _GREEN if (monto is not None and monto >= 0) else _RED_NEG
            for it in items:
                it.setForeground(QColor(color))
                it.setBackground(QColor("#f7f7f7"))
        elif estilo == "header":
            for it in items:
                it.setForeground(QColor(_DARK))
                it.setBackground(QColor("#eef3f8"))
        elif estilo == "subtotal":
            for it in items:
                it.setForeground(QColor(_DARK))
        elif estilo == "section":
            for it in items:
                it.setForeground(QColor(_GRAY))
        elif estilo == "merma":
            # merma positiva = costo real por encima del teórico → alerta
            color = _RED_NEG if (monto is not None and monto > 0) else _GREEN
            it_monto.setForeground(QColor(color))
        elif estilo == "sin_dato":
            for it in items:
                it.setForeground(QColor("#aaaaaa"))
            it_monto.setText("Sin datos")

        # Colorear deltas
        self._color_delta(it_dma, dma)
        self._color_delta(it_daa, daa)

        for col, it in enumerate(items):
            self.tbl_pyl.setItem(r, col, it)

    def _fmt_delta(self, delta):
        if not delta:
            return ""
        abs_d = delta["abs"]
        pct_d = delta["pct"]
        signo = "▲" if abs_d > 0 else ("▼" if abs_d < 0 else "—")
        return f"{signo} {_money(abs(abs_d))} ({pct_d:+.1f}%)"

    def _color_delta(self, item, delta):
        if not delta:
            return
        if delta["abs"] > 0:
            item.setForeground(QColor(_GREEN))
        elif delta["abs"] < 0:
            item.setForeground(QColor(_RED_NEG))

    # ------------------ Desglose ------------------
    def _refresh_desglose(self):
        pyl = self.ctrl.pyl_mensual(self.anio, self.mes)
        ventas = pyl["ventas"]

        # Donut
        labels = [ETIQUETAS_GASTOS[k] for k in _GASTO_KEYS]
        values = [pyl["gastos"][k] for k in _GASTO_KEYS]
        self.donut_gastos._title = f"Gastos — {_MESES_ES[self.mes - 1]} {self.anio}"
        self.donut_gastos.refresh(labels, values, _GASTO_COLORS)

        # Tabla gastos
        self.tbl_gastos.setRowCount(0)
        r = 0
        for k in _GASTO_KEYS:
            monto = pyl["gastos"][k]
            self.tbl_gastos.insertRow(r)
            self.tbl_gastos.setItem(r, 0, QTableWidgetItem(ETIQUETAS_GASTOS[k]))
            it_m = NumericItem(f"{monto:.2f}")
            it_m.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_gastos.setItem(r, 1, it_m)
            it_p = QTableWidgetItem(_pct_str(pyl["pct"][k]))
            it_p.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_gastos.setItem(r, 2, it_p)
            r += 1
        # Fila total
        self.tbl_gastos.insertRow(r)
        it_t = QTableWidgetItem("TOTAL GASTOS")
        f = it_t.font(); f.setBold(True); it_t.setFont(f)
        self.tbl_gastos.setItem(r, 0, it_t)
        it_tm = QTableWidgetItem(f"{pyl['total_gastos']:.2f}")
        it_tm.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        f = it_tm.font(); f.setBold(True); it_tm.setFont(f)
        it_tm.setForeground(QColor(_RED_NEG))
        self.tbl_gastos.setItem(r, 1, it_tm)
        it_tp = QTableWidgetItem(_pct_str(pyl["pct"]["total_gastos"]))
        it_tp.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        f = it_tp.font(); f.setBold(True); it_tp.setFont(f)
        self.tbl_gastos.setItem(r, 2, it_tp)

        # Compras por categoría (referencia)
        compras = self.ctrl.compras_por_categoria_mes(self.anio, self.mes)
        self.tbl_compras.setRowCount(0)
        for rr, (categoria, total) in enumerate(compras):
            self.tbl_compras.insertRow(rr)
            self.tbl_compras.setItem(rr, 0, QTableWidgetItem(str(categoria)))
            it = NumericItem(f"{float(total or 0):.2f}")
            it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_compras.setItem(rr, 1, it)

    # ------------------ Anual ------------------
    def _refresh_anual(self):
        anio = self.anio
        self.lbl_anual.setText(f"Comparativo Anual — {anio}")
        matriz = self.ctrl.matriz_anual(anio)  # 12 meses + total

        # Filas = métricas
        metricas = [
            ("Ventas Netas", "ventas", "money"),
            ("Costo de Ventas", "costo_real", "money"),
            ("Utilidad Bruta", "utilidad_bruta", "money"),
            ("Gastos Operativos", "total_gastos", "money"),
            ("Utilidad Neta", "utilidad_neta", "money"),
            ("Margen Neto", "margen_neto", "pct"),
        ]
        self.tbl_anual.setRowCount(0)
        for r, (label, key, tipo) in enumerate(metricas):
            self.tbl_anual.insertRow(r)
            it_lbl = QTableWidgetItem(label)
            f = it_lbl.font(); f.setBold(True); it_lbl.setFont(f)
            self.tbl_anual.setItem(r, 0, it_lbl)
            for col, fila in enumerate(matriz, start=1):
                val = fila[key]
                txt = _pct_str(val) if tipo == "pct" else f"{val:,.0f}"
                it = QTableWidgetItem(txt)
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if key == "utilidad_neta":
                    it.setForeground(QColor(_GREEN if val >= 0 else _RED_NEG))
                if col == len(matriz):  # columna total
                    f = it.font(); f.setBold(True); it.setFont(f)
                    it.setBackground(QColor("#f7f7f7"))
                self.tbl_anual.setItem(r, col, it)

        # Gráfico de utilidad neta por mes (sin la fila total)
        labels = [_MESES_ABR[i] for i in range(12)]
        values = [matriz[i]["utilidad_neta"] for i in range(12)]
        self.bar_anual.refresh(labels, values)

    # ==================================================================
    # Export CSV genérico de una tabla
    # ==================================================================
    def _exportar_tabla(self, table, nombre_default):
        fileName, _ = QFileDialog.getSaveFileName(
            self, "Exportar a CSV", nombre_default, "CSV Files (*.csv);;All Files (*)"
        )
        if not fileName:
            return
        try:
            with open(fileName, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                headers = [
                    table.horizontalHeaderItem(c).text()
                    for c in range(table.columnCount())
                ]
                writer.writerow(headers)
                for row in range(table.rowCount()):
                    row_data = []
                    for col in range(table.columnCount()):
                        item = table.item(row, col)
                        row_data.append(item.text() if item is not None else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Éxito", "Datos exportados correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar: {e}")
