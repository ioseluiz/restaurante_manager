# [FILE: app/views/modulos/costo_platos.py]
"""
Módulo Costo de Platos — cuánto cuesta producir cada plato y a qué precio venderlo.

Pestañas:
  1. Costo por plato: ingredientes + acompañamientos + bebida + empaque + indirectos,
     precio de venta vs precio sugerido (canal Local / Llevar-PedidosYa). Doble clic = desglose.
  2. Recetas de costeo: platos y componentes (chimichurri, salsas…) con su receta por
     porción o por tanda, sub-recetas y acompañamientos/empaque.
  3. Parámetros: % de ganancia, base de indirectos, fuente del costo de insumos.

La vista no calcula: todo sale de CosteoController.
"""

import csv
import datetime
import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.controllers.costeo_controller import CosteoController
from app.utils.importar_costeo_excel import importar
from app.views.widgets import SearchableComboBox

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
         "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

CATEGORIAS = [
    ("combo", "Combos"), ("orden_pollo", "Órdenes de pollo"), ("promo", "Promos"),
    ("plato", "Platos del día"), ("sopa", "Sopas"), ("acompanamiento", "Acompañamientos"),
    ("complemento", "Complementos"), ("bebida", "Bebidas"), ("desayuno", "Desayuno"),
]
_CAT_NOMBRE = dict(CATEGORIAS)

_RED = QColor("#c0392b")
_GREEN = QColor("#1e8449")
_GRAY = QColor("#7f8c8d")


def _money(v):
    return "—" if v is None else f"$ {v:,.2f}"


def _money4(v):
    return f"$ {v:,.4f}"


class _NumItem(QTableWidgetItem):
    """Celda con texto formateado que ordena por su valor numérico."""

    def __init__(self, valor, texto=None):
        super().__init__(texto if texto is not None else ("" if valor is None else f"{valor}"))
        self._v = valor
        self.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def __lt__(self, other):
        a = self._v if self._v is not None else float("-inf")
        b = getattr(other, "_v", None)
        b = b if b is not None else float("-inf")
        return a < b


def _tabla(columnas, stretch_col=None):
    t = QTableWidget()
    t.setColumnCount(len(columnas))
    t.setHorizontalHeaderLabels(columnas)
    t.setSelectionBehavior(QTableWidget.SelectRows)
    t.setSelectionMode(QTableWidget.SingleSelection)
    t.setEditTriggers(QTableWidget.NoEditTriggers)
    t.setAlternatingRowColors(True)
    t.verticalHeader().setVisible(False)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    if stretch_col is not None:
        t.horizontalHeader().setSectionResizeMode(stretch_col, QHeaderView.Stretch)
    return t


def _combo_unidades(db, texto_vacio):
    cmb = QComboBox()
    cmb.addItem(texto_vacio, None)
    for uid, nombre, abrev in db.fetch_all(
        "SELECT id, nombre, abreviatura FROM unidades_medida ORDER BY nombre"
    ):
        cmb.addItem(f"{abrev} ({nombre})", uid)
    return cmb


# ======================================================================
# Vista principal
# ======================================================================
class CostoPlatosView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.ctrl = CosteoController(db_manager)
        self._filas = []  # dicts de costo_plato de la tabla actual (para exportar)
        self._init_ui()

    # ------------------------------------------------------------------ UI
    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(QLabel("<h2>Costo de Platos</h2>"))
        header.addStretch()
        header.addWidget(QLabel("Mes:"))
        self.cmb_mes = QComboBox()
        self.cmb_mes.addItems(MESES)
        hoy = datetime.date.today()
        self.cmb_mes.setCurrentIndex(hoy.month - 1)
        header.addWidget(self.cmb_mes)
        header.addWidget(QLabel("Año:"))
        self.spn_anio = QSpinBox()
        self.spn_anio.setRange(2020, hoy.year + 1)
        self.spn_anio.setValue(hoy.year)
        header.addWidget(self.spn_anio)
        header.addWidget(QLabel("Canal:"))
        self.cmb_canal = QComboBox()
        self.cmb_canal.addItem("Local (30% ganancia)", "LOCAL")
        self.cmb_canal.addItem("Llevar / PedidosYa", "LLEVAR")
        header.addWidget(self.cmb_canal)
        btn = QPushButton("Actualizar")
        btn.setProperty("class", "btn-primary")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.cargar_datos)
        header.addWidget(btn)
        root.addLayout(header)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_tab_costos(), "Costo por plato")
        self.tabs.addTab(self._build_tab_recetas(), "Recetas de costeo")
        self.tabs.addTab(self._build_tab_parametros(), "Parámetros")
        root.addWidget(self.tabs)

        self.tabs.currentChanged.connect(self._refrescar_tab)
        self.cmb_mes.currentIndexChanged.connect(self.cargar_datos)
        self.spn_anio.valueChanged.connect(self.cargar_datos)
        self.cmb_canal.currentIndexChanged.connect(self.cargar_datos)

    # ---------------------------------------------------- Tab 1: costo por plato
    def _build_tab_costos(self):
        w = QWidget()
        lay = QVBoxLayout(w)

        self.lbl_pool = QLabel()
        self.lbl_pool.setWordWrap(True)
        self.lbl_pool.setStyleSheet("padding:6px; background:#ecf0f1; border-radius:4px; color:#2c3e50;")
        lay.addWidget(self.lbl_pool)

        filtros = QHBoxLayout()
        self.txt_filtro = QLineEdit()
        self.txt_filtro.setPlaceholderText("Filtrar por código o nombre…")
        self.txt_filtro.textChanged.connect(self._aplicar_filtro_costos)
        self.cmb_cat = QComboBox()
        self.cmb_cat.addItem("Todas las categorías", None)
        for k, v in CATEGORIAS:
            self.cmb_cat.addItem(v, k)
        self.cmb_cat.currentIndexChanged.connect(self._aplicar_filtro_costos)
        self.chk_indirectos = QCheckBox("Incluir indirectos")
        self.chk_indirectos.setChecked(True)
        self.chk_indirectos.stateChanged.connect(self.cargar_datos)
        self.chk_solo_receta = QCheckBox("Solo con receta")
        self.chk_solo_receta.stateChanged.connect(self._aplicar_filtro_costos)
        filtros.addWidget(self.txt_filtro, 1)
        filtros.addWidget(self.cmb_cat)
        filtros.addWidget(self.chk_indirectos)
        filtros.addWidget(self.chk_solo_receta)
        lay.addLayout(filtros)

        self.tbl_costos = _tabla(
            ["Categoría", "Código", "Plato", "Ingredientes", "Acomp.", "Bebida", "Empaque",
             "Indirectos", "Costo total", "Precio venta", "Food cost %", "Margen $",
             "Precio sugerido", "Alertas"], stretch_col=2)
        self.tbl_costos.setSortingEnabled(True)
        self.tbl_costos.cellDoubleClicked.connect(lambda *_: self._ver_desglose())
        lay.addWidget(self.tbl_costos)

        acciones = QHBoxLayout()
        b_det = QPushButton("Ver desglose")
        b_det.setCursor(Qt.PointingHandCursor)
        b_det.clicked.connect(self._ver_desglose)
        b_exp = QPushButton("Exportar (Excel / CSV)")
        b_exp.setProperty("class", "btn-success")
        b_exp.setCursor(Qt.PointingHandCursor)
        b_exp.clicked.connect(self._exportar)
        self.lbl_resumen = QLabel()
        acciones.addWidget(b_det)
        acciones.addWidget(b_exp)
        acciones.addStretch()
        acciones.addWidget(self.lbl_resumen)
        lay.addLayout(acciones)
        return w

    def _periodo(self):
        return self.cmb_mes.currentIndex() + 1, self.spn_anio.value()

    def _cargar_costos(self):
        canal = self.cmb_canal.currentData()
        indirecto, texto = 0.0, ""
        try:
            pool = self.ctrl.pool_indirectos(*self._periodo())
            if self.chk_indirectos.isChecked():
                indirecto = pool["por_plato"]
            texto = (
                f"<b>Indirectos por plato: {_money(pool['por_plato'])}</b> = "
                f"(gastos fijos {_money(pool['total_gastos'])} + planilla {_money(pool['planilla'])}) "
                f"÷ {pool['platos']:,.0f} platos ({pool['fuente_platos']})."
            )
            if not pool["total"]:
                texto += " <span style='color:#c0392b'>Sin gastos ni planilla registrados en el mes.</span>"
        except Exception as e:  # datos de planilla/gastos incompletos no deben tumbar el módulo
            texto = f"<span style='color:#c0392b'>No se pudieron calcular los indirectos: {e}</span>"
        self.lbl_pool.setText(texto)

        self._filas = []
        t = self.tbl_costos
        t.setSortingEnabled(False)
        t.setRowCount(0)
        for (mid,) in self.ctrl.listar_platos():
            c = self.ctrl.costo_plato(mid, canal, indirecto)
            c["con_receta"] = "Sin receta" not in c["advertencias"]
            self._filas.append(c)
            r = t.rowCount()
            t.insertRow(r)
            t.setItem(r, 0, QTableWidgetItem(_CAT_NOMBRE.get(c["categoria"], c["categoria"] or "—")))
            t.setItem(r, 1, QTableWidgetItem(str(c["codigo"])))
            nombre = QTableWidgetItem(c["nombre"])
            nombre.setData(Qt.UserRole, mid)
            t.setItem(r, 2, nombre)
            for col, key in ((3, "ingredientes"), (4, "acompanamientos"), (5, "bebida"),
                             (6, "empaque"), (7, "indirecto"), (8, "total")):
                t.setItem(r, col, _NumItem(c[key], _money(c[key])))
            pv = _NumItem(c["precio_venta"], _money(c["precio_venta"]))
            sug = c["precio_sugerido"]
            if c["con_receta"] and sug is not None and c["precio_venta"]:
                pv.setForeground(_RED if c["precio_venta"] < sug else _GREEN)
            t.setItem(r, 9, pv)
            fc = c["food_cost_pct"]
            t.setItem(r, 10, _NumItem(fc, "—" if fc is None else f"{fc:.1f}%"))
            t.setItem(r, 11, _NumItem(c["margen"], _money(c["margen"])))
            t.setItem(r, 12, _NumItem(sug, _money(sug)))
            n_adv = len(c["advertencias"])
            adv = _NumItem(n_adv, f"⚠ {n_adv}" if n_adv else "")
            adv.setForeground(_RED)
            adv.setToolTip("\n".join(c["advertencias"]))
            t.setItem(r, 13, adv)
        t.setSortingEnabled(True)
        self._aplicar_filtro_costos()

    def _aplicar_filtro_costos(self):
        txt = self.txt_filtro.text().strip().lower()
        cat = self.cmb_cat.currentData()
        solo = self.chk_solo_receta.isChecked()
        visibles = con_alerta = 0
        for r in range(self.tbl_costos.rowCount()):
            mid = self.tbl_costos.item(r, 2).data(Qt.UserRole)
            c = next((f for f in self._filas if f["menu_item_id"] == mid), None)
            ok = c is not None
            if ok and txt:
                ok = txt in c["nombre"].lower() or txt in str(c["codigo"]).lower()
            if ok and cat:
                ok = c["categoria"] == cat
            if ok and solo:
                ok = c["con_receta"]
            self.tbl_costos.setRowHidden(r, not ok)
            if ok:
                visibles += 1
                con_alerta += bool(c["advertencias"])
        self.lbl_resumen.setText(f"{visibles} platos · {con_alerta} con alertas")

    def _plato_seleccionado(self):
        r = self.tbl_costos.currentRow()
        if r < 0:
            QMessageBox.information(self, "Costo de platos", "Seleccione un plato.")
            return None
        return self.tbl_costos.item(r, 2).data(Qt.UserRole)

    def _ver_desglose(self):
        mid = self._plato_seleccionado()
        if mid is None:
            return
        indirecto = 0.0
        c_prev = next((f for f in self._filas if f["menu_item_id"] == mid), None)
        if c_prev:
            indirecto = c_prev["indirecto"]
        c = self.ctrl.costo_plato(mid, self.cmb_canal.currentData(), indirecto)
        DesgloseDialog(c, self.ctrl.factor_por_porcion(mid), self).exec_()

    def _exportar(self):
        if not self._filas:
            QMessageBox.information(self, "Exportar", "No hay datos para exportar.")
            return
        mes, anio = self._periodo()
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar costo de platos", f"costo_platos_{anio}_{mes:02d}.xlsx",
            "Excel (*.xlsx);;CSV (*.csv)")
        if not ruta:
            return
        cab = ["Categoría", "Código", "Plato", "Ingredientes", "Acompañamientos", "Bebida",
               "Empaque", "Indirectos", "Costo total", "Precio venta", "Food cost %",
               "Margen $", "Precio sugerido", "Alertas"]
        filas = []
        for c in self._filas:
            filas.append([
                _CAT_NOMBRE.get(c["categoria"], c["categoria"] or ""), c["codigo"], c["nombre"],
                round(c["ingredientes"], 4), round(c["acompanamientos"], 4), round(c["bebida"], 4),
                round(c["empaque"], 4), round(c["indirecto"], 4), round(c["total"], 4),
                c["precio_venta"], None if c["food_cost_pct"] is None else round(c["food_cost_pct"], 2),
                None if c["margen"] is None else round(c["margen"], 4),
                None if c["precio_sugerido"] is None else round(c["precio_sugerido"], 4),
                "; ".join(c["advertencias"]),
            ])
        try:
            if ruta.lower().endswith(".csv"):
                with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f)
                    w.writerow(cab)
                    w.writerows(filas)
            else:
                from openpyxl import Workbook
                from openpyxl.styles import Font
                wb = Workbook()
                ws = wb.active
                ws.title = "Costo de platos"
                ws.append(cab)
                for cel in ws[1]:
                    cel.font = Font(bold=True)
                for fila in filas:
                    ws.append(fila)
                for col, ancho in zip("ABCDEFGHIJKLMN", (16, 10, 32, 13, 15, 10, 10, 11, 12, 12, 12, 11, 15, 50)):
                    ws.column_dimensions[col].width = ancho
                wb.save(ruta)
        except Exception as e:
            QMessageBox.critical(self, "Exportar", f"No se pudo guardar el archivo:\n{e}")
            return
        QMessageBox.information(self, "Exportar", f"Archivo guardado:\n{ruta}")

    # -------------------------------------------------- Tab 2: recetas de costeo
    def _build_tab_recetas(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        top = QHBoxLayout()
        self.txt_filtro_rec = QLineEdit()
        self.txt_filtro_rec.setPlaceholderText("Filtrar por código o nombre…")
        self.txt_filtro_rec.textChanged.connect(self._cargar_recetas)
        self.cmb_tipo_rec = QComboBox()
        self.cmb_tipo_rec.addItem("Platos y componentes", None)
        self.cmb_tipo_rec.addItem("Solo platos", 0)
        self.cmb_tipo_rec.addItem("Solo componentes", 1)
        self.cmb_tipo_rec.currentIndexChanged.connect(self._cargar_recetas)
        top.addWidget(self.txt_filtro_rec, 1)
        top.addWidget(self.cmb_tipo_rec)
        lay.addLayout(top)

        self.tbl_rec = _tabla(
            ["Código", "Nombre", "Tipo", "Categoría", "Ingredientes", "Sub-recetas",
             "Rendimiento", "Porción servida"], stretch_col=1)
        self.tbl_rec.setSortingEnabled(True)
        self.tbl_rec.cellDoubleClicked.connect(lambda *_: self._editar_receta())
        lay.addWidget(self.tbl_rec)

        acc = QHBoxLayout()
        b_edit = QPushButton("Editar receta / costeo")
        b_edit.setProperty("class", "btn-primary")
        b_edit.setCursor(Qt.PointingHandCursor)
        b_edit.clicked.connect(self._editar_receta)
        b_new = QPushButton("Nuevo componente")
        b_new.setProperty("class", "btn-success")
        b_new.setCursor(Qt.PointingHandCursor)
        b_new.clicked.connect(self._nuevo_componente)
        b_del = QPushButton("Eliminar componente")
        b_del.setProperty("class", "btn-danger")
        b_del.setCursor(Qt.PointingHandCursor)
        b_del.clicked.connect(self._eliminar_componente)
        b_imp = QPushButton("Importar desde Excel…")
        b_imp.setCursor(Qt.PointingHandCursor)
        b_imp.clicked.connect(self._importar_excel)
        acc.addWidget(b_edit)
        acc.addWidget(b_new)
        acc.addWidget(b_del)
        acc.addWidget(b_imp)
        acc.addStretch()
        lay.addLayout(acc)
        return w

    def _cargar_recetas(self):
        txt = self.txt_filtro_rec.text().strip().lower()
        tipo = self.cmb_tipo_rec.currentData()
        rows = self.db.fetch_all(
            """SELECT m.id, m.codigo, m.nombre, COALESCE(m.es_componente,0), m.categoria_costeo,
                      (SELECT COUNT(*) FROM recetas r WHERE r.menu_item_id = m.id),
                      (SELECT COUNT(*) FROM receta_componentes rc WHERE rc.menu_item_id = m.id),
                      m.rendimiento, m.porcion_servida, u.abreviatura
               FROM menu_items m LEFT JOIN unidades_medida u ON u.id = m.unidad_rendimiento_id
               ORDER BY m.nombre""")
        t = self.tbl_rec
        t.setSortingEnabled(False)
        t.setRowCount(0)
        for mid, cod, nom, es_comp, cat, n_ins, n_sub, rend, por, ab in rows:
            if tipo is not None and es_comp != tipo:
                continue
            if txt and txt not in str(nom).lower() and txt not in str(cod).lower():
                continue
            r = t.rowCount()
            t.insertRow(r)
            t.setItem(r, 0, QTableWidgetItem(str(cod)))
            item = QTableWidgetItem(nom)
            item.setData(Qt.UserRole, mid)
            t.setItem(r, 1, item)
            t.setItem(r, 2, QTableWidgetItem("Componente" if es_comp else "Plato"))
            t.setItem(r, 3, QTableWidgetItem(_CAT_NOMBRE.get(cat, cat or "—")))
            ing = _NumItem(n_ins, str(n_ins) if n_ins else "Sin receta")
            ing.setForeground(_GREEN if n_ins else _RED)
            t.setItem(r, 4, ing)
            t.setItem(r, 5, _NumItem(n_sub, str(n_sub)))
            u = f" {ab}" if ab else ""
            t.setItem(r, 6, _NumItem(rend, f"{rend:g}{u}" if rend else "por porción"))
            t.setItem(r, 7, _NumItem(por, f"{por:g}{u}" if por else "—"))
        t.setSortingEnabled(True)

    def _receta_seleccionada(self):
        r = self.tbl_rec.currentRow()
        if r < 0:
            QMessageBox.information(self, "Recetas de costeo", "Seleccione un plato o componente.")
            return None
        it = self.tbl_rec.item(r, 1)
        return it.data(Qt.UserRole), it.text(), self.tbl_rec.item(r, 2).text() == "Componente"

    def _editar_receta(self):
        sel = self._receta_seleccionada()
        if not sel:
            return
        RecetaCosteoDialog(self.db, self.ctrl, sel[0], sel[1], self).exec_()
        self.ctrl.limpiar_cache()
        self._cargar_recetas()

    def _importar_excel(self):
        ImportarExcelDialog(self.db, self).exec_()
        self.ctrl.limpiar_cache()
        self._cargar_recetas()

    def _nuevo_componente(self):
        dlg = NuevoComponenteDialog(self.db, self)
        if dlg.exec_() == QDialog.Accepted:
            self._cargar_recetas()
            RecetaCosteoDialog(self.db, self.ctrl, dlg.nuevo_id, dlg.nombre, self).exec_()
            self.ctrl.limpiar_cache()
            self._cargar_recetas()

    def _eliminar_componente(self):
        sel = self._receta_seleccionada()
        if not sel:
            return
        mid, nombre, es_comp = sel
        if not es_comp:
            QMessageBox.information(self, "Eliminar", "Solo se pueden eliminar componentes; "
                                    "los platos se gestionan en el módulo Menú.")
            return
        usos = self.db.fetch_one(
            "SELECT (SELECT COUNT(*) FROM receta_componentes WHERE componente_id = ?) + "
            "(SELECT COUNT(*) FROM plato_extras WHERE componente_id = ?)", (mid, mid))[0]
        if usos:
            QMessageBox.warning(self, "Eliminar", f"'{nombre}' se usa en {usos} receta(s)/extra(s). "
                                "Quítelo de ellas primero.")
            return
        if QMessageBox.question(self, "Eliminar", f"¿Eliminar el componente '{nombre}' y su receta?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        for sql in ("DELETE FROM recetas WHERE menu_item_id = ?",
                    "DELETE FROM receta_componentes WHERE menu_item_id = ?",
                    "DELETE FROM plato_extras WHERE menu_item_id = ?",
                    "DELETE FROM menu_items WHERE id = ? AND COALESCE(es_componente,0) = 1"):
            self.db.execute_query(sql, (mid,))
        self._cargar_recetas()

    # ------------------------------------------------------ Tab 3: parámetros
    def _build_tab_parametros(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        form = QFormLayout()
        self.sp_dias = QDoubleSpinBox()
        self.sp_dias.setRange(1, 31)
        self.sp_dias.setDecimals(0)
        self.sp_platos = QDoubleSpinBox()
        self.sp_platos.setRange(1, 100000)
        self.sp_platos.setDecimals(0)
        self.sp_pct_local = QDoubleSpinBox()
        self.sp_pct_local.setRange(0, 99)
        self.sp_pct_local.setSuffix(" %")
        self.sp_pct_llevar = QDoubleSpinBox()
        self.sp_pct_llevar.setRange(0, 99)
        self.sp_pct_llevar.setSuffix(" %")
        self.cmb_base = QComboBox()
        self.cmb_base.addItem("Gastos reales del mes (consolidados)", "REAL")
        self.cmb_base.addItem("Presupuesto del mes", "PRESUPUESTO")
        self.cmb_fuente = QComboBox()
        self.cmb_fuente.addItem("Precio vigente de la presentación de compra", "VIGENTE")
        self.cmb_fuente.addItem("Costo promedio ponderado del inventario", "PROMEDIO")
        form.addRow("Días del mes:", self.sp_dias)
        form.addRow("Platos por día (si no hay ventas del mes):", self.sp_platos)
        form.addRow("% de ganancia — Local:", self.sp_pct_local)
        form.addRow("% de ganancia — Llevar / PedidosYa:", self.sp_pct_llevar)
        form.addRow("Base de gastos indirectos:", self.cmb_base)
        form.addRow("Costo de los insumos:", self.cmb_fuente)
        lay.addLayout(form)

        b = QPushButton("Guardar parámetros")
        b.setProperty("class", "btn-primary")
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(self._guardar_parametros)
        lay.addWidget(b, alignment=Qt.AlignLeft)

        lay.addWidget(QLabel("<b>Indirectos del período seleccionado</b>"))
        self.tbl_pool = _tabla(["Concepto", "Monto"], stretch_col=0)
        lay.addWidget(self.tbl_pool)
        return w

    def _cargar_parametros(self):
        c = self.ctrl
        self.sp_dias.setValue(c.config_float("dias_mes", 30))
        self.sp_platos.setValue(c.config_float("platos_dia_default", 198))
        self.sp_pct_local.setValue(c.config_float("pct_ganancia_local", 30))
        self.sp_pct_llevar.setValue(c.config_float("pct_ganancia_pedidosya", 50))
        self.cmb_base.setCurrentIndex(max(0, self.cmb_base.findData(c.config("base_indirectos", "REAL"))))
        self.cmb_fuente.setCurrentIndex(max(0, self.cmb_fuente.findData(c.config("fuente_costo_insumo", "VIGENTE"))))
        self.cmb_canal.setItemText(0, f"Local ({self.sp_pct_local.value():g}% ganancia)")
        self.cmb_canal.setItemText(1, f"Llevar / PedidosYa ({self.sp_pct_llevar.value():g}% ganancia)")

        t = self.tbl_pool
        t.setRowCount(0)
        try:
            p = c.pool_indirectos(*self._periodo())
        except Exception as e:
            t.setRowCount(1)
            t.setItem(0, 0, QTableWidgetItem(f"Error: {e}"))
            return
        filas = [(k, v) for k, v in sorted(p["gastos"].items())]
        filas += [("PLANILLA", p["planilla"]), ("TOTAL indirectos", p["total"]),
                  (f"Platos vendidos ({p['fuente_platos']})", p["platos"]),
                  ("Indirecto por plato", p["por_plato"])]
        for k, v in filas:
            r = t.rowCount()
            t.insertRow(r)
            t.setItem(r, 0, QTableWidgetItem(str(k)))
            t.setItem(r, 1, _NumItem(v, f"{v:,.0f}" if k.startswith("Platos") else _money(v)))

    def _guardar_parametros(self):
        for clave, valor in [
            ("dias_mes", self.sp_dias.value()), ("platos_dia_default", self.sp_platos.value()),
            ("pct_ganancia_local", self.sp_pct_local.value()),
            ("pct_ganancia_pedidosya", self.sp_pct_llevar.value()),
            ("base_indirectos", self.cmb_base.currentData()),
            ("fuente_costo_insumo", self.cmb_fuente.currentData()),
        ]:
            self.db.execute_query(
                "INSERT INTO costeo_config (clave, valor) VALUES (?, ?) "
                "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor", (clave, str(valor)))
        self.ctrl.limpiar_cache()
        self.cargar_datos()
        QMessageBox.information(self, "Parámetros", "Parámetros guardados.")

    # --------------------------------------------------------------- refresco
    def cargar_datos(self, *_):
        self.ctrl.limpiar_cache()
        self._cargar_parametros()
        self._refrescar_tab(self.tabs.currentIndex())

    def _refrescar_tab(self, idx):
        if idx == 0:
            self._cargar_costos()
        elif idx == 1:
            self._cargar_recetas()
        else:
            self._cargar_parametros()


# ======================================================================
# Diálogos
# ======================================================================
class DesgloseDialog(QDialog):
    def __init__(self, c, factor, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Desglose de costo — {c['nombre']}")
        self.resize(760, 560)
        lay = QVBoxLayout(self)
        resumen = (
            f"<h3>{c['nombre']} <small style='color:#7f8c8d'>({c['codigo']})</small></h3>"
            f"Ingredientes {_money(c['ingredientes'])} · Acompañamientos {_money(c['acompanamientos'])} · "
            f"Bebida {_money(c['bebida'])} · Empaque {_money(c['empaque'])} · "
            f"Indirectos {_money(c['indirecto'])}<br>"
            f"<b>Costo total: {_money(c['total'])}</b> · Precio venta {_money(c['precio_venta'])} · "
            f"Precio sugerido {_money(c['precio_sugerido'])}")
        lbl = QLabel(resumen)
        lbl.setWordWrap(True)
        lay.addWidget(lbl)
        if abs(factor - 1.0) > 1e-9:
            lay.addWidget(QLabel(f"<i>Receta por tanda: los subtotales ya están prorrateados a una porción (× {factor:.4f}).</i>"))

        t = _tabla(["Tipo", "Concepto", "Cantidad", "Costo unitario", "Subtotal"], stretch_col=1)
        for ln in c["lineas"]:
            r = t.rowCount()
            t.insertRow(r)
            t.setItem(r, 0, QTableWidgetItem(ln["tipo"].capitalize()))
            t.setItem(r, 1, QTableWidgetItem(ln["nombre"]))
            t.setItem(r, 2, _NumItem(ln["cantidad"], f"{ln['cantidad']:g}"))
            cu = ln.get("costo_unitario")
            t.setItem(r, 3, _NumItem(cu, "" if cu is None else _money4(cu)))
            t.setItem(r, 4, _NumItem(ln["subtotal"], _money4(ln["subtotal"])))
        lay.addWidget(t)

        if c["advertencias"]:
            adv = QTextEdit()
            adv.setReadOnly(True)
            adv.setMaximumHeight(110)
            adv.setPlainText("Alertas:\n" + "\n".join(f"• {a}" for a in c["advertencias"]))
            lay.addWidget(adv)
        b = QPushButton("Cerrar")
        b.clicked.connect(self.accept)
        lay.addWidget(b, alignment=Qt.AlignRight)


class NuevoComponenteDialog(QDialog):
    """Alta de un componente (sub-receta, acompañamiento, empaque) que no se vende."""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.nuevo_id = None
        self.nombre = ""
        self.setWindowTitle("Nuevo componente")
        form = QFormLayout(self)
        self.txt_codigo = QLineEdit()
        self.txt_codigo.setPlaceholderText("Ej. #205")
        self.txt_nombre = QLineEdit()
        self.cmb_cat = QComboBox()
        for k, v in CATEGORIAS:
            self.cmb_cat.addItem(v, k)
        self.cmb_cat.setCurrentIndex(self.cmb_cat.findData("complemento"))
        form.addRow("Código:", self.txt_codigo)
        form.addRow("Nombre:", self.txt_nombre)
        form.addRow("Categoría:", self.cmb_cat)
        b = QPushButton("Crear")
        b.setProperty("class", "btn-success")
        b.clicked.connect(self._crear)
        form.addRow(b)

    def _crear(self):
        codigo, nombre = self.txt_codigo.text().strip(), self.txt_nombre.text().strip()
        if not codigo or not nombre:
            QMessageBox.warning(self, "Nuevo componente", "Código y nombre son obligatorios.")
            return
        if self.db.fetch_one("SELECT 1 FROM menu_items WHERE codigo = ?", (codigo,)):
            QMessageBox.warning(self, "Nuevo componente", f"Ya existe un ítem con el código '{codigo}'.")
            return
        cur = self.db.execute_query(
            "INSERT INTO menu_items (codigo, nombre, precio_venta, es_preparado, es_componente, categoria_costeo) "
            "VALUES (?, ?, 0, 1, 1, ?)", (codigo, nombre, self.cmb_cat.currentData()))
        self.nuevo_id, self.nombre = cur.lastrowid, nombre
        self.accept()


class RecetaCosteoDialog(QDialog):
    """Datos de costeo (categoría, rendimiento, porción) + ingredientes, sub-recetas y extras."""

    def __init__(self, db, ctrl, menu_item_id, nombre, parent=None):
        super().__init__(parent)
        self.db, self.ctrl, self.mid = db, ctrl, menu_item_id
        self.setWindowTitle(f"Receta de costeo — {nombre}")
        self.resize(860, 700)
        self._init_ui()
        self._cargar_datos_item()
        self._refrescar()

    # ------------------------------------------------------------------ UI
    def _init_ui(self):
        lay = QVBoxLayout(self)

        form = QFormLayout()
        self.cmb_cat = QComboBox()
        self.cmb_cat.addItem("(sin categoría)", None)
        for k, v in CATEGORIAS:
            self.cmb_cat.addItem(v, k)
        self.chk_comp = QCheckBox("Es componente (no se vende: salsa, sazonador, acompañamiento, empaque…)")
        self.sp_rend = QDoubleSpinBox()
        self.sp_rend.setRange(0, 9999999)
        self.sp_rend.setDecimals(3)
        self.sp_rend.setSpecialValueText("Receta por porción")
        self.cmb_u_rend = _combo_unidades(self.db, "(sin unidad)")
        self.sp_por = QDoubleSpinBox()
        self.sp_por.setRange(0, 9999999)
        self.sp_por.setDecimals(3)
        self.sp_por.setSpecialValueText("—")
        b_sum = QPushButton("Rendimiento = suma de ingredientes")
        b_sum.clicked.connect(self._rendimiento_suma)
        fila = QHBoxLayout()
        fila.addWidget(self.sp_rend)
        fila.addWidget(self.cmb_u_rend)
        fila.addWidget(b_sum)
        form.addRow("Categoría:", self.cmb_cat)
        form.addRow("", self.chk_comp)
        form.addRow("Rendimiento de la tanda:", fila)
        form.addRow("Porción servida (misma unidad):", self.sp_por)
        lay.addLayout(form)

        b_save = QPushButton("Guardar datos de costeo")
        b_save.setProperty("class", "btn-primary")
        b_save.clicked.connect(self._guardar_datos_item)
        lay.addWidget(b_save, alignment=Qt.AlignLeft)
        nota = QLabel(
            "<i>Si define rendimiento, las cantidades de los ingredientes son <b>por tanda</b> y el costo por "
            "porción = costo de la tanda × porción ÷ rendimiento (también lo usan Compras, Presupuestos y "
            "Rentabilidad). Sin rendimiento, las cantidades son por porción. "
            "Para un componente, el costo por unidad = costo de la tanda ÷ rendimiento.</i>")
        nota.setWordWrap(True)
        lay.addWidget(nota)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_ingredientes(), "Ingredientes")
        self.tabs.addTab(self._tab_subrecetas(), "Sub-recetas")
        self.tabs.addTab(self._tab_extras(), "Acompañamientos / bebida / empaque")
        lay.addWidget(self.tabs, 1)

        self.lbl_costo = QLabel()
        self.lbl_costo.setWordWrap(True)
        self.lbl_costo.setStyleSheet("padding:6px; background:#ecf0f1; border-radius:4px; color:#2c3e50;")
        lay.addWidget(self.lbl_costo)
        b = QPushButton("Cerrar")
        b.clicked.connect(self.accept)
        lay.addWidget(b, alignment=Qt.AlignRight)

    def _tab_ingredientes(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        fila = QHBoxLayout()
        self.cmb_insumo = SearchableComboBox(placeholder="Escriba para buscar insumo…")
        self.cmb_insumo.setMinimumWidth(260)
        for iid, nom, ab in self.db.fetch_all(
            "SELECT i.id, i.nombre, u.abreviatura FROM insumos i "
            "LEFT JOIN unidades_medida u ON u.id = i.unidad_base_id ORDER BY i.nombre"):
            self.cmb_insumo.addItem(f"{nom} ({ab or '?'})", userData=iid)
        self.sp_ins_cant = QDoubleSpinBox()
        self.sp_ins_cant.setRange(0, 9999999)
        self.sp_ins_cant.setDecimals(4)
        self.cmb_ins_unidad = _combo_unidades(self.db, "(unidad base del insumo)")
        b = QPushButton("Agregar / actualizar")
        b.setProperty("class", "btn-success")
        b.clicked.connect(self._agregar_insumo)
        for x in (QLabel("Insumo:"), self.cmb_insumo, QLabel("Cantidad:"), self.sp_ins_cant,
                  self.cmb_ins_unidad, b):
            fila.addWidget(x)
        lay.addLayout(fila)
        lay.addWidget(QLabel("<i>Si elige otra unidad se convierte a la unidad base del insumo al guardar.</i>"))
        self.tbl_ins = _tabla(["Insumo", "Cantidad (unidad base)", "Costo unitario", "Subtotal", ""], stretch_col=0)
        lay.addWidget(self.tbl_ins)
        return w

    def _tab_subrecetas(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        fila = QHBoxLayout()
        self.cmb_sub = SearchableComboBox(placeholder="Escriba para buscar componente…")
        self.cmb_sub.setMinimumWidth(260)
        self.sp_sub_cant = QDoubleSpinBox()
        self.sp_sub_cant.setRange(0, 9999999)
        self.sp_sub_cant.setDecimals(4)
        self.cmb_sub_unidad = _combo_unidades(self.db, "(unidad de rendimiento)")
        b = QPushButton("Agregar / actualizar")
        b.setProperty("class", "btn-success")
        b.clicked.connect(self._agregar_sub)
        for x in (QLabel("Componente:"), self.cmb_sub, QLabel("Cantidad:"), self.sp_sub_cant,
                  self.cmb_sub_unidad, b):
            fila.addWidget(x)
        lay.addLayout(fila)
        self.tbl_sub = _tabla(["Componente", "Cantidad", "Costo por unidad", "Subtotal", ""], stretch_col=0)
        lay.addWidget(self.tbl_sub)
        return w

    def _tab_extras(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        fila = QHBoxLayout()
        self.cmb_extra = SearchableComboBox(placeholder="Escriba para buscar…")
        self.cmb_extra.setMinimumWidth(240)
        self.sp_extra_cant = QDoubleSpinBox()
        self.sp_extra_cant.setRange(0, 999)
        self.sp_extra_cant.setDecimals(2)
        self.sp_extra_cant.setValue(1)
        self.cmb_extra_tipo = QComboBox()
        for k, v in (("ACOMPANAMIENTO", "Acompañamiento"), ("BEBIDA", "Bebida"), ("EMPAQUE", "Empaque")):
            self.cmb_extra_tipo.addItem(v, k)
        self.cmb_extra_canal = QComboBox()
        for k, v in (("AMBOS", "Local y llevar"), ("LOCAL", "Solo local"), ("LLEVAR", "Solo llevar")):
            self.cmb_extra_canal.addItem(v, k)
        b = QPushButton("Agregar")
        b.setProperty("class", "btn-success")
        b.clicked.connect(self._agregar_extra)
        for x in (self.cmb_extra, QLabel("Porciones:"), self.sp_extra_cant, self.cmb_extra_tipo,
                  self.cmb_extra_canal, b):
            fila.addWidget(x)
        lay.addLayout(fila)
        lay.addWidget(QLabel("<i>Se suman al costo del plato según el canal. Un mismo acompañamiento puede "
                             "repetirse cambiando las porciones (ej. 3 porciones de frijoles).</i>"))
        self.tbl_extra = _tabla(["Ítem", "Tipo", "Canal", "Porciones", "Costo", ""], stretch_col=0)
        lay.addWidget(self.tbl_extra)
        return w

    # ------------------------------------------------------- datos del ítem
    def _cargar_datos_item(self):
        r = self.db.fetch_one(
            "SELECT categoria_costeo, COALESCE(es_componente,0), rendimiento, unidad_rendimiento_id, "
            "porcion_servida FROM menu_items WHERE id = ?", (self.mid,))
        cat, es_comp, rend, u_rend, por = r
        self.cmb_cat.setCurrentIndex(max(0, self.cmb_cat.findData(cat)))
        self.chk_comp.setChecked(bool(es_comp))
        self.sp_rend.setValue(rend or 0)
        self.sp_por.setValue(por or 0)
        self.cmb_u_rend.setCurrentIndex(max(0, self.cmb_u_rend.findData(u_rend)))
        # candidatos para sub-recetas y extras: todo lo demás (componentes primero)
        otros = self.db.fetch_all(
            "SELECT id, nombre, COALESCE(es_componente,0) FROM menu_items WHERE id <> ? "
            "ORDER BY es_componente DESC, nombre", (self.mid,))
        for cmb in (self.cmb_sub, self.cmb_extra):
            cmb.clear()
            for oid, nom, comp in otros:
                cmb.addItem(f"{nom}{'' if comp else ' (plato)'}", userData=oid)

    def _guardar_datos_item(self):
        rend, por = self.sp_rend.value(), self.sp_por.value()
        if por > 0 and rend <= 0:
            QMessageBox.warning(self, "Costeo", "Para usar porción servida defina el rendimiento de la tanda.")
            return
        u = self.cmb_u_rend.currentData()
        self.db.execute_query(
            "UPDATE menu_items SET categoria_costeo=?, es_componente=?, rendimiento=?, unidad_rendimiento_id=?, "
            "porcion_servida=?, unidad_porcion_id=? WHERE id=?",
            (self.cmb_cat.currentData(), 1 if self.chk_comp.isChecked() else 0,
             rend or None, u if rend else None, por or None, u if por else None, self.mid))
        self._refrescar()

    def _rendimiento_suma(self):
        s = self.db.fetch_one("SELECT COALESCE(SUM(cantidad_necesaria),0) FROM recetas WHERE menu_item_id = ?",
                              (self.mid,))[0]
        self.sp_rend.setValue(s)

    # ---------------------------------------------------------- ingredientes
    def _agregar_insumo(self):
        iid = self.cmb_insumo.currentData()
        cant = self.sp_ins_cant.value()
        if iid is None:
            QMessageBox.warning(self, "Ingrediente", "Seleccione un insumo de la lista.")
            return
        if cant <= 0:
            QMessageBox.warning(self, "Ingrediente", "La cantidad debe ser mayor a 0.")
            return
        base_id = self.db.fetch_one("SELECT unidad_base_id FROM insumos WHERE id = ?", (iid,))[0]
        en_base = self.ctrl.convertir(cant, self.cmb_ins_unidad.currentData(), base_id)
        if en_base is None:
            QMessageBox.warning(self, "Ingrediente",
                                "No hay conversión entre esa unidad y la unidad base del insumo. "
                                "Use la unidad base o cargue la conversión.")
            return
        ex = self.db.fetch_one("SELECT id FROM recetas WHERE menu_item_id=? AND insumo_id=?", (self.mid, iid))
        if ex:
            self.db.execute_query("UPDATE recetas SET cantidad_necesaria=?, unidad_id=NULL WHERE id=?",
                                  (en_base, ex[0]))
        else:
            self.db.execute_query(
                "INSERT INTO recetas (menu_item_id, insumo_id, cantidad_necesaria) VALUES (?,?,?)",
                (self.mid, iid, en_base))
        self.sp_ins_cant.setValue(0)
        self._refrescar()

    def _quitar(self, sql, pid):
        self.db.execute_query(sql, (pid,))
        self._refrescar()

    def _boton_quitar(self, tabla, fila, col, sql, pid):
        b = QPushButton("✕")
        b.setFixedWidth(34)
        b.setStyleSheet("background-color:#e74c3c; color:white; font-weight:bold;")
        b.clicked.connect(lambda: self._quitar(sql, pid))
        tabla.setCellWidget(fila, col, b)

    # ------------------------------------------------------------ sub-recetas
    def _crea_ciclo(self, componente_id):
        """True si agregar `componente_id` a este ítem crearía un ciclo (él ya depende de nosotros)."""
        visto, pila = set(), [componente_id]
        while pila:
            x = pila.pop()
            if x == self.mid:
                return True
            if x in visto:
                continue
            visto.add(x)
            pila += [r[0] for r in self.db.fetch_all(
                "SELECT componente_id FROM receta_componentes WHERE menu_item_id = ?", (x,))]
        return False

    def _agregar_sub(self):
        cid = self.cmb_sub.currentData()
        cant = self.sp_sub_cant.value()
        if cid is None or cant <= 0:
            QMessageBox.warning(self, "Sub-receta", "Seleccione un componente e indique una cantidad mayor a 0.")
            return
        if self._crea_ciclo(cid):
            QMessageBox.warning(self, "Sub-receta", "Esa sub-receta ya depende de este ítem: se crearía un ciclo.")
            return
        comp = self.ctrl._item(cid)
        u_comp = comp[7] if comp else None
        en_u = self.ctrl.convertir(cant, self.cmb_sub_unidad.currentData(), u_comp)
        if en_u is None:
            QMessageBox.warning(self, "Sub-receta", "No hay conversión entre esa unidad y la unidad de "
                                "rendimiento del componente. Use su misma unidad.")
            return
        # se guarda siempre en la unidad de rendimiento del componente (lo asume v_recetas_explotadas)
        self.db.execute_query(
            "INSERT INTO receta_componentes (menu_item_id, componente_id, cantidad, unidad_id) VALUES (?,?,?,?) "
            "ON CONFLICT(menu_item_id, componente_id) DO UPDATE SET cantidad=excluded.cantidad, "
            "unidad_id=excluded.unidad_id",
            (self.mid, cid, en_u, u_comp))
        self.sp_sub_cant.setValue(0)
        self._refrescar()

    # ----------------------------------------------------------------- extras
    def _agregar_extra(self):
        cid = self.cmb_extra.currentData()
        if cid is None or self.sp_extra_cant.value() <= 0:
            QMessageBox.warning(self, "Extras", "Seleccione un ítem e indique las porciones.")
            return
        self.db.execute_query(
            "INSERT INTO plato_extras (menu_item_id, componente_id, cantidad_porciones, tipo, canal) "
            "VALUES (?,?,?,?,?)",
            (self.mid, cid, self.sp_extra_cant.value(), self.cmb_extra_tipo.currentData(),
             self.cmb_extra_canal.currentData()))
        self._refrescar()

    # -------------------------------------------------------------- refresco
    def _refrescar(self):
        self.ctrl.limpiar_cache()
        c = self.ctrl

        t = self.tbl_ins
        t.setRowCount(0)
        for rid, iid, nom, cant, ab in self.db.fetch_all(
            "SELECT r.id, i.id, i.nombre, r.cantidad_necesaria, u.abreviatura FROM recetas r "
            "JOIN insumos i ON i.id = r.insumo_id LEFT JOIN unidades_medida u ON u.id = i.unidad_base_id "
            "WHERE r.menu_item_id = ? ORDER BY i.nombre", (self.mid,)):
            cu, sin = c.costo_unitario_insumo(iid)
            r = t.rowCount()
            t.insertRow(r)
            t.setItem(r, 0, QTableWidgetItem(nom))
            t.setItem(r, 1, _NumItem(cant, f"{cant:g} {ab or ''}"))
            it = _NumItem(cu, "SIN COSTO" if sin else _money4(cu))
            if sin:
                it.setForeground(_RED)
            t.setItem(r, 2, it)
            t.setItem(r, 3, _NumItem(cant * cu, _money4(cant * cu)))
            self._boton_quitar(t, r, 4, "DELETE FROM recetas WHERE id=?", rid)

        t = self.tbl_sub
        t.setRowCount(0)
        for rcid, cid, nom, cant, uid in self.db.fetch_all(
            "SELECT rc.id, rc.componente_id, m.nombre, rc.cantidad, rc.unidad_id FROM receta_componentes rc "
            "JOIN menu_items m ON m.id = rc.componente_id WHERE rc.menu_item_id = ? ORDER BY m.nombre",
            (self.mid,)):
            cu, adv = c.costo_por_unidad_componente(cid)
            comp = c._item(cid)
            en_u = c.convertir(cant, uid, comp[7]) if comp else cant
            en_u = cant if en_u is None else en_u
            r = t.rowCount()
            t.insertRow(r)
            t.setItem(r, 0, QTableWidgetItem(nom))
            t.setItem(r, 1, _NumItem(cant, f"{cant:g}"))
            it = _NumItem(cu, _money4(cu))
            if adv:
                it.setForeground(_RED)
                it.setToolTip("\n".join(adv))
            t.setItem(r, 2, it)
            t.setItem(r, 3, _NumItem(en_u * cu, _money4(en_u * cu)))
            self._boton_quitar(t, r, 4, "DELETE FROM receta_componentes WHERE id=?", rcid)

        t = self.tbl_extra
        t.setRowCount(0)
        for eid, cid, nom, por, tipo, canal in self.db.fetch_all(
            "SELECT e.id, e.componente_id, m.nombre, e.cantidad_porciones, e.tipo, e.canal FROM plato_extras e "
            "JOIN menu_items m ON m.id = e.componente_id WHERE e.menu_item_id = ? ORDER BY e.tipo, m.nombre",
            (self.mid,)):
            costo = c.costo_ingredientes(cid)["total"] * por
            r = t.rowCount()
            t.insertRow(r)
            t.setItem(r, 0, QTableWidgetItem(nom))
            t.setItem(r, 1, QTableWidgetItem(tipo.capitalize()))
            t.setItem(r, 2, QTableWidgetItem({"AMBOS": "Local y llevar", "LOCAL": "Solo local",
                                              "LLEVAR": "Solo llevar"}[canal]))
            t.setItem(r, 3, _NumItem(por, f"{por:g}"))
            t.setItem(r, 4, _NumItem(costo, _money4(costo)))
            self._boton_quitar(t, r, 5, "DELETE FROM plato_extras WHERE id=?", eid)

        tanda = c.costo_tanda(self.mid)
        porcion = c.costo_ingredientes(self.mid)
        it = c._item(self.mid)
        partes = [f"<b>Costo de la receta:</b> {_money(tanda['total'])}"]
        if it and it[6]:
            partes.append(f"<b>Costo por porción:</b> {_money(porcion['total'])}")
            partes.append(f"<b>Costo por unidad de rendimiento:</b> {_money4(tanda['total'] / it[6])}")
        adv = sorted(set(tanda["advertencias"]))
        if adv:
            partes.append("<span style='color:#c0392b'>⚠ " + " · ".join(adv) + "</span>")
        self.lbl_costo.setText("<br>".join(partes))


class ImportarExcelDialog(QDialog):
    """Importa recetas desde el Excel de costeo del cliente: primero simula y luego importa."""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Importar recetas desde Excel")
        self.resize(900, 640)
        lay = QVBoxLayout(self)
        fila = QHBoxLayout()
        self.txt_ruta = QLineEdit()
        self.txt_ruta.setPlaceholderText("Archivo «COSTEO DE PLATOS Y SUS INSUMOS.xlsx»…")
        b = QPushButton("Examinar…")
        b.clicked.connect(self._examinar)
        fila.addWidget(self.txt_ruta, 1)
        fila.addWidget(b)
        lay.addLayout(fila)

        self.chk_crear = QCheckBox("Crear los insumos que no existan (con la unidad y el costo que trae el Excel)")
        self.chk_costos = QCheckBox("Completar el costo de los insumos existentes que no tienen costo")
        self.chk_reemplazar = QCheckBox("Reemplazar las recetas que ya existen en la app (por defecto se omiten)")
        for c in (self.chk_crear, self.chk_costos, self.chk_reemplazar):
            lay.addWidget(c)
        lay.addWidget(QLabel(
            "<i>Recomendado: 1) Simular y revisar el reporte, 2) corregir el Excel o los nombres, 3) Importar. "
            "Una receta con insumos sin resolver nunca se importa a medias. Antes de importar se hace una copia "
            "de respaldo de la base de datos.</i>"))

        botones = QHBoxLayout()
        self.btn_sim = QPushButton("Simular (no guarda)")
        self.btn_sim.clicked.connect(lambda: self._ejecutar(True))
        self.btn_imp = QPushButton("Importar")
        self.btn_imp.setProperty("class", "btn-success")
        self.btn_imp.clicked.connect(lambda: self._ejecutar(False))
        self.btn_guardar = QPushButton("Guardar reporte…")
        self.btn_guardar.clicked.connect(self._guardar_reporte)
        for x in (self.btn_sim, self.btn_imp, self.btn_guardar):
            botones.addWidget(x)
        botones.addStretch()
        lay.addLayout(botones)

        self.txt_reporte = QTextEdit()
        self.txt_reporte.setReadOnly(True)
        self.txt_reporte.setStyleSheet("font-family: Consolas, monospace;")
        lay.addWidget(self.txt_reporte, 1)
        b_cerrar = QPushButton("Cerrar")
        b_cerrar.clicked.connect(self.accept)
        lay.addWidget(b_cerrar, alignment=Qt.AlignRight)

    def _examinar(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Excel de costeo", "", "Excel (*.xlsx *.xlsm)")
        if ruta:
            self.txt_ruta.setText(ruta)

    def _ejecutar(self, simular):
        ruta = self.txt_ruta.text().strip()
        if not ruta or not os.path.exists(ruta):
            QMessageBox.warning(self, "Importar", "Seleccione un archivo Excel válido.")
            return
        prefijo = ""
        if not simular:
            if QMessageBox.question(self, "Importar", "Se importarán las recetas a la base de datos. "
                                    "Se guardará antes una copia de respaldo. ¿Continuar?",
                                    QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
                return
            ok, destino = self.db.create_backup(os.path.dirname(self.db.db_path))
            if not ok:
                QMessageBox.critical(self, "Importar", f"No se pudo crear el respaldo; no se importó nada: {destino}")
                return
            prefijo = f"Respaldo creado: {destino}\n\n"
        try:
            res = importar(self.db, ruta, dry_run=simular, crear_insumos=self.chk_crear.isChecked(),
                           completar_costos=self.chk_costos.isChecked(), reemplazar=self.chk_reemplazar.isChecked())
        except Exception as e:
            QMessageBox.critical(self, "Importar", f"No se pudo leer/importar el archivo: {e}")
            return
        self.txt_reporte.setPlainText(prefijo + res.texto())

    def _guardar_reporte(self):
        texto = self.txt_reporte.toPlainText()
        if not texto:
            return
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar reporte", "reporte_importacion.txt", "Texto (*.txt)")
        if ruta:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(texto)
