# [FILE: app/views/modulos/presupuestos.py]
import math
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QComboBox,
    QHeaderView,
    QMessageBox,
    QDialog,
    QSpinBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QAbstractItemView,
    QTextBrowser,
    QDoubleSpinBox,
)
from PyQt5.QtCore import Qt, QSize

# --- ESTILOS COMUNES PARA DIÁLOGOS ---
DIALOG_STYLES = """
    QDialog {
        background-color: #f0f2f5;
    }
    QLabel {
        color: #2c3e50;
        font-weight: bold;
    }
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
        background-color: #ffffff;
        color: #2c3e50;
        border: 1px solid #bdc3c7;
        padding: 5px;
        border-radius: 4px;
        min-height: 25px;
    }
    QComboBox QAbstractItemView {
        background-color: #ffffff;
        color: #2c3e50;
        selection-background-color: #3498db;
        selection-color: white;
    }
    QListWidget {
        background-color: #ffffff;
        color: #2c3e50;
        border: 1px solid #bdc3c7;
    }
    QTreeWidget {
        background-color: #ffffff;
        color: #2c3e50;
        border: 1px solid #bdc3c7;
    }
    QHeaderView::section {
        background-color: #ecf0f1;
        color: #2c3e50;
        padding: 5px;
        border: 1px solid #bdc3c7;
        font-weight: bold;
    }
"""


def recalcular_total_presupuesto(db, presupuesto_id):
    query = (
        "SELECT SUM(monto_estimado) FROM detalle_presupuestos WHERE presupuesto_id = ?"
    )
    total = db.fetch_one(query, (presupuesto_id,))
    total_val = total[0] if total and total[0] else 0.0
    db.execute_query(
        "UPDATE presupuestos SET monto_total = ? WHERE id = ?",
        (total_val, presupuesto_id),
    )
    return total_val


class PresupuestosView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Header ---
        header = QLabel("<h2>Gestión de Presupuestos</h2>")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # --- Botonera ---
        btn_layout = QHBoxLayout()

        btn_nuevo = QPushButton(" Nuevo Presupuesto")
        btn_nuevo.setStyleSheet(
            "background-color: #27ae60; color: white; padding: 8px; border-radius: 4px; font-weight: bold;"
        )
        btn_nuevo.clicked.connect(self.nuevo_presupuesto)

        btn_ver = QPushButton(" Ver / Editar Insumos")
        btn_ver.setStyleSheet(
            "background-color: #2980b9; color: white; padding: 8px; border-radius: 4px; font-weight: bold;"
        )
        btn_ver.clicked.connect(self.ver_presupuesto)

        btn_editar_gen = QPushButton(" Editar General")
        btn_editar_gen.setStyleSheet(
            "background-color: #f39c12; color: white; padding: 8px; border-radius: 4px; font-weight: bold;"
        )
        btn_editar_gen.clicked.connect(self.editar_general)

        btn_eliminar = QPushButton(" Eliminar")
        btn_eliminar.setStyleSheet(
            "background-color: #c0392b; color: white; padding: 8px; border-radius: 4px; font-weight: bold;"
        )
        btn_eliminar.clicked.connect(self.eliminar_presupuesto)

        btn_layout.addWidget(btn_nuevo)
        btn_layout.addWidget(btn_ver)
        btn_layout.addWidget(btn_editar_gen)
        btn_layout.addWidget(btn_eliminar)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # --- Tabla ---
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Número", "Mes", "Año", "Descripción", "Monto Total Estimado"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setStyleSheet(
            "background-color: white; color: #2c3e50; alternate-background-color: #f9f9f9;"
        )
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def cargar_datos(self):
        self.table.setRowCount(0)
        query = "SELECT id, numero, mes, anio, descripcion, monto_total FROM presupuestos ORDER BY id DESC"
        filas = self.db.fetch_all(query)

        for i, f in enumerate(filas):
            self.table.insertRow(i)
            item_num = QTableWidgetItem(str(f[1]))
            item_num.setData(Qt.UserRole, f[0])
            item_num.setTextAlignment(Qt.AlignCenter)

            self.table.setItem(i, 0, item_num)
            self.table.setItem(i, 1, QTableWidgetItem(str(f[2])))
            self.table.setItem(i, 2, QTableWidgetItem(str(f[3])))
            self.table.setItem(i, 3, QTableWidgetItem(f[4]))

            item_monto = QTableWidgetItem(f"${f[5]:,.2f}")
            item_monto.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 4, item_monto)

        self.table.resizeRowsToContents()

    def nuevo_presupuesto(self):
        dlg = CrearPresupuestoDialog(self.db, self)
        if dlg.exec_():
            self.cargar_datos()

    def ver_presupuesto(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, "Atención", "Debe seleccionar un presupuesto de la lista."
            )
            return

        presupuesto_id = self.table.item(row, 0).data(Qt.UserRole)
        numero = self.table.item(row, 0).text()
        mes = self.table.item(row, 1).text()
        anio = self.table.item(row, 2).text()
        desc = self.table.item(row, 3).text()
        monto = self.table.item(row, 4).text()

        dlg = VerPresupuestoDialog(
            self.db, presupuesto_id, numero, mes, anio, desc, monto, self
        )
        dlg.exec_()
        self.cargar_datos()

    def editar_general(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, "Atención", "Debe seleccionar un presupuesto de la lista."
            )
            return

        presupuesto_id = self.table.item(row, 0).data(Qt.UserRole)
        mes = self.table.item(row, 1).text()
        anio = self.table.item(row, 2).text()
        desc = self.table.item(row, 3).text()

        dlg = EditarGeneralDialog(self.db, presupuesto_id, mes, anio, desc, self)
        if dlg.exec_():
            self.cargar_datos()

    def eliminar_presupuesto(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, "Atención", "Debe seleccionar un presupuesto de la lista."
            )
            return

        presupuesto_id = self.table.item(row, 0).data(Qt.UserRole)
        numero = self.table.item(row, 0).text()

        resp = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de eliminar permanentemente el Presupuesto N° {numero}?\nEsta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if resp == QMessageBox.Yes:
            self.db.execute_query(
                "DELETE FROM presupuestos WHERE id = ?", (presupuesto_id,)
            )
            QMessageBox.information(
                self, "Éxito", "Presupuesto eliminado correctamente."
            )
            self.cargar_datos()


# --- DIÁLOGOS DE EDICIÓN ---


class EditarGeneralDialog(QDialog):
    def __init__(self, db, p_id, mes, anio, desc, parent=None):
        super().__init__(parent)
        self.db = db
        self.p_id = p_id
        self.setWindowTitle("Editar Datos Generales")
        self.resize(400, 200)
        self.setStyleSheet(DIALOG_STYLES)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Mes:"))
        self.cmb_mes = QComboBox()
        self.cmb_mes.addItems([str(i) for i in range(1, 13)])
        self.cmb_mes.setCurrentText(mes)
        layout.addWidget(self.cmb_mes)

        layout.addWidget(QLabel("Año:"))
        self.spin_anio = QSpinBox()
        self.spin_anio.setRange(2020, 2100)
        self.spin_anio.setValue(int(anio))
        layout.addWidget(self.spin_anio)

        layout.addWidget(QLabel("Descripción:"))
        self.txt_desc = QLineEdit(desc)
        layout.addWidget(self.txt_desc)

        btn_layout = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btn_guardar = QPushButton("Guardar Cambios")
        btn_guardar.setStyleSheet(
            "background-color: #27ae60; color: white; font-weight: bold;"
        )
        btn_guardar.clicked.connect(self.guardar)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_guardar)
        layout.addLayout(btn_layout)

    def guardar(self):
        m = self.cmb_mes.currentText()
        a = self.spin_anio.value()
        d = self.txt_desc.text().strip()
        self.db.execute_query(
            "UPDATE presupuestos SET mes=?, anio=?, descripcion=? WHERE id=?",
            (m, a, d, self.p_id),
        )
        self.accept()


class EditarInsumoDialog(QDialog):
    def __init__(self, db, detalle_id, nombre, cant, monto, unidad, parent=None):
        super().__init__(parent)
        self.db = db
        self.detalle_id = detalle_id
        self.setWindowTitle(f"Edición Manual: {nombre}")
        self.resize(400, 250)
        self.setStyleSheet(DIALOG_STYLES)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>Modificando Insumo:</b> {nombre}"))

        layout.addWidget(QLabel(f"Cantidad a Comprar ({unidad}):"))
        self.spin_cant = QDoubleSpinBox()
        self.spin_cant.setRange(0, 9999999.99)
        self.spin_cant.setValue(cant)
        layout.addWidget(self.spin_cant)

        layout.addWidget(QLabel("Monto Estimado Total ($):"))
        self.spin_monto = QDoubleSpinBox()
        self.spin_monto.setRange(0, 9999999.99)
        self.spin_monto.setValue(monto)
        layout.addWidget(self.spin_monto)

        lbl_info = QLabel(
            "<i>Nota: Al guardar, se reemplazará el cálculo automático de esta línea.</i>"
        )
        lbl_info.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(lbl_info)

        btn_layout = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btn_guardar = QPushButton("Aplicar Cambios")
        btn_guardar.setStyleSheet(
            "background-color: #f39c12; color: white; font-weight: bold;"
        )
        btn_guardar.clicked.connect(self.guardar)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_guardar)
        layout.addLayout(btn_layout)

    def guardar(self):
        c = self.spin_cant.value()
        m = self.spin_monto.value()
        det = "<h3 style='color:#e67e22;'>Editado Manualmente</h3><p>Los valores de esta línea fueron modificados por el usuario, sobreescribiendo el cálculo automático original.</p>"

        self.db.execute_query(
            "UPDATE detalle_presupuestos SET cantidad_requerida=?, monto_estimado=?, detalle_calculo=? WHERE id=?",
            (c, m, det, self.detalle_id),
        )
        self.accept()


class AgregarInsumoManualDialog(QDialog):
    def __init__(self, db, presupuesto_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.presupuesto_id = presupuesto_id
        self.setWindowTitle("Agregar Insumo Manualmente")
        self.resize(450, 400)
        self.setStyleSheet(DIALOG_STYLES)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Categoría (Puede escribir una nueva):"))
        self.cmb_cat = QComboBox()
        self.cmb_cat.setEditable(True)
        cats = self.db.fetch_all("SELECT DISTINCT nombre FROM categorias_insumos")
        self.cmb_cat.addItems([c[0] for c in cats])
        layout.addWidget(self.cmb_cat)

        layout.addWidget(QLabel("Insumo / Artículo:"))
        self.txt_insumo = QLineEdit()
        layout.addWidget(self.txt_insumo)

        layout.addWidget(QLabel("Unidad (Ej. Empaque, Kg, Lbs):"))
        self.txt_unidad = QLineEdit()
        layout.addWidget(self.txt_unidad)

        layout.addWidget(QLabel("Cantidad a Comprar:"))
        self.spin_cant = QDoubleSpinBox()
        self.spin_cant.setRange(0, 9999999.99)
        layout.addWidget(self.spin_cant)

        layout.addWidget(QLabel("Monto Estimado Total ($):"))
        self.spin_monto = QDoubleSpinBox()
        self.spin_monto.setRange(0, 9999999.99)
        layout.addWidget(self.spin_monto)

        btn_layout = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btn_guardar = QPushButton("Agregar al Presupuesto")
        btn_guardar.setStyleSheet(
            "background-color: #27ae60; color: white; font-weight: bold;"
        )
        btn_guardar.clicked.connect(self.guardar)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_guardar)
        layout.addLayout(btn_layout)

    def guardar(self):
        cat = self.cmb_cat.currentText().strip()
        ins = self.txt_insumo.text().strip()
        uni = self.txt_unidad.text().strip()
        c = self.spin_cant.value()
        m = self.spin_monto.value()

        if not cat or not ins or not uni:
            QMessageBox.warning(
                self, "Error", "Debe completar Categoría, Insumo y Unidad."
            )
            return

        det = "<h3 style='color:#27ae60;'>Insumo Agregado Manualmente</h3><p>Este artículo no proviene del cálculo automático, fue agregado manualmente al presupuesto por el usuario.</p>"

        query = """
            INSERT INTO detalle_presupuestos (presupuesto_id, categoria_nombre, insumo_nombre, unidad_nombre, cantidad_requerida, monto_estimado, items_menu, detalle_calculo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(
            query, (self.presupuesto_id, cat, ins, uni, c, m, "Agregado Extra", det)
        )
        self.accept()


# --- DIÁLOGOS DE CREACIÓN Y VISTA DE DETALLE ---


class CrearPresupuestoDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("Crear Nuevo Presupuesto")
        self.resize(700, 550)
        self.setStyleSheet(DIALOG_STYLES)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        gb_gen = QWidget()
        hl_gen = QHBoxLayout(gb_gen)
        hl_gen.setContentsMargins(0, 0, 0, 0)

        hl_gen.addWidget(QLabel("Mes:"))
        self.cmb_mes = QComboBox()
        self.cmb_mes.addItems([str(i) for i in range(1, 13)])
        self.cmb_mes.setFixedWidth(80)
        hl_gen.addWidget(self.cmb_mes)

        hl_gen.addWidget(QLabel("Año:"))
        self.spin_anio = QSpinBox()
        self.spin_anio.setRange(2020, 2100)
        self.spin_anio.setValue(2025)
        self.spin_anio.setFixedWidth(100)
        hl_gen.addWidget(self.spin_anio)

        hl_gen.addStretch()
        layout.addWidget(gb_gen)

        h_layout2 = QVBoxLayout()
        h_layout2.setSpacing(5)
        h_layout2.addWidget(QLabel("Descripción (Opcional):"))
        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Ej: Presupuesto T1 2025 - Temporada Alta")
        h_layout2.addWidget(self.txt_desc)
        layout.addLayout(h_layout2)

        lbl_rep = QLabel("Seleccione los reportes de venta base para el cálculo:")
        lbl_rep.setStyleSheet("margin-top: 10px;")
        layout.addWidget(lbl_rep)

        self.list_reportes = QListWidget()
        self.cargar_reportes()
        layout.addWidget(self.list_reportes)

        btn_layout = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("padding: 8px;")
        btn_cancelar.clicked.connect(self.reject)

        btn_guardar = QPushButton(" Calcular y Generar Presupuesto")
        btn_guardar.setStyleSheet(
            "background-color: #27ae60; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px;"
        )
        btn_guardar.clicked.connect(self.generar_presupuesto)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_guardar)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def cargar_reportes(self):
        query = "SELECT id, fecha_inicio_periodo, fecha_fin_periodo FROM reportes_ventas ORDER BY id DESC"
        reportes = self.db.fetch_all(query)
        for r in reportes:
            item = QListWidgetItem(f"Reporte ID: {r[0]} | Periodo: {r[1]} al {r[2]}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, r[0])
            self.list_reportes.addItem(item)

    def generar_presupuesto(self):
        mes = int(self.cmb_mes.currentText())
        anio = self.spin_anio.value()
        desc = self.txt_desc.text().strip()

        reportes_ids = []
        for i in range(self.list_reportes.count()):
            item = self.list_reportes.item(i)
            if item.checkState() == Qt.Checked:
                reportes_ids.append(str(item.data(Qt.UserRole)))

        if not reportes_ids:
            QMessageBox.warning(
                self,
                "Error",
                "Debe seleccionar al menos un reporte para basar el cálculo.",
            )
            return

        try:
            placeholders = ",".join(["?"] * len(reportes_ids))
            query_ventas = f"""
                SELECT reporte_id, codigo_producto, LOWER(dia_semana), SUM(cantidad) as cant
                FROM detalle_reportes_ventas 
                WHERE reporte_id IN ({placeholders})
                GROUP BY reporte_id, codigo_producto, LOWER(dia_semana)
            """
            ventas_data = self.db.fetch_all(query_ventas, tuple(reportes_ids))

            dias_validos = {
                "lunes",
                "martes",
                "miercoles",
                "miércoles",
                "jueves",
                "viernes",
                "sabado",
                "sábado",
                "domingo",
                "lun",
                "mar",
                "mie",
                "jue",
                "vie",
                "sab",
                "dom",
            }

            ventas_por_producto = {}
            for row in ventas_data:
                rep_id, cod, dia, cant = row
                dia_str = str(dia).strip().lower()

                if dia_str not in dias_validos:
                    continue

                if cod not in ventas_por_producto:
                    ventas_por_producto[cod] = {}
                if dia_str not in ventas_por_producto[cod]:
                    ventas_por_producto[cod][dia_str] = []

                ventas_por_producto[cod][dia_str].append(cant)

            ventas_detalle_mensual = {}
            SEMANAS_POR_MES = 4.0
            total_reportes = len(reportes_ids)

            for cod, dias in ventas_por_producto.items():
                detalle_dias = {}
                total_venta_semanal_promedio = 0
                for dia, cants in dias.items():
                    prom_dia = sum(cants) / total_reportes
                    detalle_dias[dia] = prom_dia
                    total_venta_semanal_promedio += prom_dia

                ventas_detalle_mensual[cod] = {
                    "dias": detalle_dias,
                    "total_mensual": total_venta_semanal_promedio * SEMANAS_POR_MES,
                }

            insumos_calc = {}

            for cod, info_ventas in ventas_detalle_mensual.items():
                ventas_totales = info_ventas["total_mensual"]
                if ventas_totales <= 0:
                    continue

                query_recetas = """
                    SELECT r.insumo_id, i.nombre, i.factor_calculo, c.nombre as categoria, 
                           r.cantidad_necesaria, m.nombre as menu_nombre, u.abreviatura
                    FROM recetas r
                    JOIN menu_items m ON r.menu_item_id = m.id
                    JOIN insumos i ON r.insumo_id = i.id
                    LEFT JOIN categorias_insumos c ON i.categoria_id = c.id
                    LEFT JOIN unidades_medida u ON i.unidad_base_id = u.id
                    WHERE m.codigo = ?
                """
                recetas = self.db.fetch_all(query_recetas, (cod,))

                for rec in recetas:
                    ins_id, ins_nom, factor, cat_nom, cant_nec, menu_nom, abrev_uni = (
                        rec
                    )
                    factor = factor if factor else 1.0
                    cat_nom = cat_nom if cat_nom else "Sin Categoría"
                    abrev_uni = abrev_uni if abrev_uni else "Und."

                    cant_amplificada = (ventas_totales * cant_nec) * factor

                    if ins_id not in insumos_calc:
                        insumos_calc[ins_id] = {
                            "nombre": ins_nom,
                            "categoria": cat_nom,
                            "unidad_base": abrev_uni,
                            "factor": factor,
                            "qty_base_total": 0.0,
                            "items_menu": {},
                        }

                    insumos_calc[ins_id]["qty_base_total"] += cant_amplificada

                    if menu_nom not in insumos_calc[ins_id]["items_menu"]:
                        insumos_calc[ins_id]["items_menu"][menu_nom] = {
                            "ventas_dias": info_ventas["dias"],
                            "ventas_mensual": ventas_totales,
                            "receta_cant": cant_nec,
                            "total_plato": 0.0,
                        }

                    insumos_calc[ins_id]["items_menu"][menu_nom]["total_plato"] += (
                        cant_amplificada
                    )

            monto_total_presupuesto = 0.0
            detalles_db = []

            for ins_id, data in insumos_calc.items():
                abrev_base = data["unidad_base"]
                factor_val = data["factor"]

                query_pres = "SELECT cantidad_contenido, precio_compra, nombre FROM presentaciones_compra WHERE insumo_id = ? ORDER BY id ASC LIMIT 1"
                pres = self.db.fetch_one(query_pres, (ins_id,))

                cant_compra_exacta = 0.0
                cant_compra_final = 0.0  # Redondeada
                costo_insumo_final = 0.0
                unidad_nombre_final = ""

                det_html = f"<div style='font-family: Arial, sans-serif;'>"
                det_html += f"<h3 style='color:#2c3e50; border-bottom: 2px solid #bdc3c7; padding-bottom: 5px;'>Detalle de Cálculo: {data['nombre']}</h3>"

                det_html += f"<table width='100%' style='margin-bottom: 15px;'><tr>"
                det_html += (
                    f"<td width='50%'><b>Unidad Base Recetas:</b> {abrev_base}</td>"
                )
                det_html += f"<td width='50%'><b>Factor de Insumo (Merma):</b> {factor_val:.2f}</td>"
                det_html += f"</tr></table>"

                if pres and pres[0] > 0:
                    cant_contenido, precio_pres, nombre_pres = pres

                    cant_compra_exacta = data["qty_base_total"] / cant_contenido
                    # Redondeo hacia arriba a número entero
                    cant_compra_final = math.ceil(cant_compra_exacta)
                    costo_insumo_final = cant_compra_final * precio_pres
                    unidad_nombre_final = nombre_pres

                    det_html += f"<div style='background-color: #e8f8f5; padding: 10px; border-radius: 4px; border: 1px solid #1abc9c; margin-bottom: 15px;'>"
                    det_html += f"<b>Presentación de Compra:</b> {nombre_pres}<br>"
                    det_html += f"<b>Contenido:</b> {cant_contenido} {abrev_base}<br>"
                    det_html += f"<b>Precio:</b> ${precio_pres:,.2f}"
                    det_html += f"</div>"
                else:
                    query_fallback = "SELECT costo_unitario FROM insumos WHERE id = ?"
                    ins_data = self.db.fetch_one(query_fallback, (ins_id,))
                    precio_uni = ins_data[0] if ins_data and ins_data[0] else 0.0

                    cant_compra_exacta = data["qty_base_total"]
                    # Redondeo hacia arriba a número entero
                    cant_compra_final = math.ceil(cant_compra_exacta)
                    costo_insumo_final = cant_compra_final * precio_uni
                    unidad_nombre_final = abrev_base

                    det_html += f"<div style='background-color: #fcf3cf; padding: 10px; border-radius: 4px; border: 1px solid #f1c40f; margin-bottom: 15px;'>"
                    det_html += f"<i>No tiene presentación de compra asignada. Se calcula sobre unidad base.</i><br>"
                    det_html += f"<b>Precio Unitario (Base):</b> ${precio_uni:,.2f}"
                    det_html += f"</div>"

                monto_total_presupuesto += costo_insumo_final

                det_html += "<h4 style='color:#2980b9;'>1. Requerimiento por Platos de Menú</h4>"
                factor_str = (
                    f" x {factor_val:.2f} (Factor)" if factor_val != 1.0 else ""
                )

                for m_nom, m_info in data["items_menu"].items():
                    dias_format = " | ".join(
                        [
                            f"{d[:3].capitalize()}: {v:.1f}"
                            for d, v in m_info["ventas_dias"].items()
                        ]
                    )

                    det_html += f"<div style='margin-bottom: 10px; padding: 10px; border-left: 4px solid #3498db; background-color: #f8f9fa; border-radius: 0 4px 4px 0;'>"
                    det_html += (
                        f"<b style='color:#2c3e50; font-size: 14px;'>{m_nom}</b><br>"
                    )

                    det_html += f"<table width='100%' style='font-size: 12px; margin-top: 5px; color: #555;'>"
                    det_html += f"<tr><td width='35%'><b>Ventas Diario (Promedio):</b></td><td>[{dias_format}]</td></tr>"
                    det_html += f"<tr><td><b>Ventas Mensual Proyectado:</b></td><td>{m_info['ventas_mensual']:.2f} platos vendidos</td></tr>"
                    det_html += f"<tr><td><b>Requerido en Receta:</b></td><td>{m_info['receta_cant']:.4f} {abrev_base} por plato</td></tr>"
                    det_html += f"</table>"

                    det_html += f"<div style='margin-top: 6px; padding-top: 6px; border-top: 1px dashed #ccc; font-family: monospace; font-size: 13px;'>"
                    det_html += f"Fórmula: {m_info['ventas_mensual']:.2f} platos x {m_info['receta_cant']:.4f} {abrev_base}{factor_str} = <b style='color: #c0392b;'>{m_info['total_plato']:.2f} {abrev_base}</b>"
                    det_html += f"</div></div>"

                det_html += f"<h4 style='color:#27ae60; margin-top: 20px;'>2. Conversión a Compras y Costo Final</h4>"
                det_html += f"<ul style='font-size: 14px; background-color: #ecf0f1; padding: 15px 15px 15px 35px; border-radius: 5px;'>"
                det_html += f"<li style='margin-bottom: 5px;'><b>Total Base Requerido (Suma Platos):</b> {data['qty_base_total']:.2f} {abrev_base}</li>"
                det_html += f"<li style='margin-bottom: 5px;'><b>Cantidad Exacta de Compra:</b> {cant_compra_exacta:.2f} {unidad_nombre_final}</li>"
                det_html += f"<li style='margin-bottom: 5px; color: #c0392b;'><b>Cantidad a Comprar (Redondeada):</b> <span style='background-color:#f1c40f; padding: 2px 5px; border-radius: 3px; font-weight: bold; color: #2c3e50;'>{int(cant_compra_final)} {unidad_nombre_final}</span></li>"
                det_html += (
                    f"<li><b>Costo Estimado:</b> ${costo_insumo_final:,.2f}</li>"
                )
                det_html += f"</ul></div>"

                items_str = "\n".join(
                    [
                        f"• {k} ({v['total_plato']:.2f})"
                        for k, v in data["items_menu"].items()
                    ]
                )

                detalles_db.append(
                    (
                        data["categoria"],
                        data["nombre"],
                        unidad_nombre_final,
                        cant_compra_final,
                        costo_insumo_final,
                        items_str,
                        det_html,
                    )
                )

            num_query = "SELECT COUNT(*) FROM presupuestos"
            count_res = self.db.fetch_one(num_query)
            count = count_res[0] if count_res else 0
            nuevo_num = count + 1

            query_pres_insert = "INSERT INTO presupuestos (numero, mes, anio, descripcion, monto_total) VALUES (?,?,?,?,?)"
            self.db.execute_query(
                query_pres_insert, (nuevo_num, mes, anio, desc, monto_total_presupuesto)
            )
            presupuesto_id = self.db.cursor.lastrowid

            for rid in reportes_ids:
                self.db.execute_query(
                    "INSERT INTO presupuesto_reportes (presupuesto_id, reporte_id) VALUES (?,?)",
                    (presupuesto_id, int(rid)),
                )

            query_det_insert = """
                INSERT INTO detalle_presupuestos 
                (presupuesto_id, categoria_nombre, insumo_nombre, unidad_nombre, cantidad_requerida, monto_estimado, items_menu, detalle_calculo) 
                VALUES (?,?,?,?,?,?,?,?)
            """
            for det in detalles_db:
                self.db.execute_query(query_det_insert, (presupuesto_id, *det))

            QMessageBox.information(
                self,
                "Éxito",
                f"Presupuesto N°{nuevo_num} generado correctamente.\nMonto Total Estimado: ${monto_total_presupuesto:,.2f}",
            )
            self.accept()

        except Exception as e:
            import traceback

            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Error",
                f"Ha ocurrido un error al calcular el presupuesto:\n{str(e)}",
            )


class DetalleCalculoDialog(QDialog):
    def __init__(self, html_content, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detalle del Cálculo")
        self.resize(650, 550)
        self.setStyleSheet(DIALOG_STYLES)

        layout = QVBoxLayout(self)
        self.browser = QTextBrowser()
        self.browser.setHtml(html_content)
        self.browser.setStyleSheet(
            "background-color: white; color: #2c3e50; border: 1px solid #bdc3c7; border-radius: 4px; padding: 15px;"
        )
        layout.addWidget(self.browser)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setStyleSheet(
            "background-color: #bdc3c7; color: #2c3e50; font-weight: bold; padding: 8px 15px; border-radius: 4px;"
        )
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignCenter)


class VerPresupuestoDialog(QDialog):
    def __init__(
        self, db_manager, presupuesto_id, numero, mes, anio, desc, monto, parent=None
    ):
        super().__init__(parent)
        self.db = db_manager
        self.presupuesto_id = presupuesto_id
        self.numero = numero
        self.mes = mes
        self.anio = anio
        self.desc = desc
        self.setWindowTitle(f"Detalle Presupuesto N° {numero}")
        self.resize(1150, 700)
        self.setStyleSheet(DIALOG_STYLES)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.lbl_head = QLabel()
        layout.addWidget(self.lbl_head)

        btn_agregar_insumo = QPushButton(" + Agregar Insumo Manual Extra")
        btn_agregar_insumo.setStyleSheet(
            "background-color: #27ae60; color: white; padding: 6px; border-radius: 4px; font-weight: bold;"
        )
        btn_agregar_insumo.clicked.connect(self.agregar_insumo_manual)
        layout.addWidget(btn_agregar_insumo, alignment=Qt.AlignRight)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(
            [
                "Insumo / Categoría",
                "Cantidad a Comprar",
                "Monto Estimado",
                "Desglose por Platos",
                "Acciones",
            ]
        )
        self.tree.setColumnWidth(0, 250)
        self.tree.setColumnWidth(1, 150)
        self.tree.setColumnWidth(2, 120)
        self.tree.setColumnWidth(3, 300)
        self.tree.setColumnWidth(4, 220)
        self.tree.setAlternatingRowColors(True)

        self.tree.setWordWrap(True)
        layout.addWidget(self.tree)

        self.cargar_detalles()

        btn_cerrar = QPushButton("Cerrar Vista")
        btn_cerrar.setStyleSheet(
            "background-color: #bdc3c7; color: #2c3e50; font-weight: bold; padding: 8px 15px; border-radius: 4px;"
        )
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignRight)

        self.setLayout(layout)

    def actualizar_encabezado(self):
        query = "SELECT monto_total FROM presupuestos WHERE id = ?"
        total = self.db.fetch_one(query, (self.presupuesto_id,))
        monto_actual = total[0] if total and total[0] else 0.0

        html = f"""
            <div style='background-color: #ecf0f1; padding: 15px; border-radius: 5px; border: 1px solid #bdc3c7;'>
                <h3 style='margin:0; color: #2c3e50;'>Presupuesto N° {self.numero}</h3>
                <p style='margin: 5px 0; color: #34495e;'><b>Periodo:</b> {self.mes}/{self.anio} &nbsp;|&nbsp; <b>Total Estimado:</b> <span style='color: #c0392b; font-size: 16px;'>${monto_actual:,.2f}</span></p>
                <p style='margin: 0; color: #7f8c8d; font-style: italic;'>{self.desc}</p>
            </div>
        """
        self.lbl_head.setText(html)

    def cargar_detalles(self):
        self.tree.clear()
        self.actualizar_encabezado()

        query = """
            SELECT id, categoria_nombre, insumo_nombre, unidad_nombre, cantidad_requerida, monto_estimado, items_menu, detalle_calculo 
            FROM detalle_presupuestos 
            WHERE presupuesto_id = ? 
            ORDER BY categoria_nombre, insumo_nombre
        """
        detalles = self.db.fetch_all(query, (self.presupuesto_id,))

        agrupado = {}
        for d in detalles:
            det_id, cat_nom, ins_nom, uni_nom, cant, monto, items, det_calc = d

            if cat_nom not in agrupado:
                agrupado[cat_nom] = {"items": [], "total_monto": 0}

            agrupado[cat_nom]["items"].append(d)
            agrupado[cat_nom]["total_monto"] += monto

        for cat, data in agrupado.items():
            cat_item = QTreeWidgetItem(self.tree)
            cat_item.setText(0, cat.upper())
            cat_item.setText(2, f"${data['total_monto']:,.2f}")

            for i in range(5):
                cat_item.setBackground(i, Qt.darkGray)
                cat_item.setForeground(i, Qt.white)
                font = cat_item.font(i)
                font.setBold(True)
                cat_item.setFont(i, font)

            for d in data["items"]:
                det_id, cat_nom, ins_nom, uni_nom, cant, monto, items, det_calc = d

                hijo = QTreeWidgetItem(cat_item)
                hijo.setText(0, ins_nom)
                # Formateo a número entero para la visualización en la tabla
                hijo.setText(1, f"{int(cant)}  {uni_nom}")
                hijo.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
                hijo.setText(2, f"${monto:,.2f}")
                hijo.setTextAlignment(2, Qt.AlignRight | Qt.AlignVCenter)
                hijo.setText(3, items)
                hijo.setToolTip(3, items)

                widget_acciones = QWidget()
                layout_acciones = QHBoxLayout(widget_acciones)
                layout_acciones.setContentsMargins(0, 0, 0, 0)
                layout_acciones.setSpacing(5)

                btn_detalle = QPushButton("Detalle")
                btn_detalle.setStyleSheet(
                    "background-color: #3498db; color: white; border-radius: 3px; padding: 4px; font-weight: bold; font-size: 11px;"
                )
                btn_detalle.setCursor(Qt.PointingHandCursor)
                btn_detalle.clicked.connect(
                    lambda checked, html=det_calc: self.mostrar_calculo(html)
                )

                btn_editar = QPushButton("Editar")
                btn_editar.setStyleSheet(
                    "background-color: #f39c12; color: white; border-radius: 3px; padding: 4px; font-weight: bold; font-size: 11px;"
                )
                btn_editar.setCursor(Qt.PointingHandCursor)
                btn_editar.clicked.connect(
                    lambda checked, d_id=det_id, nom=ins_nom, c=cant, m=monto, uni=uni_nom: (
                        self.editar_insumo(d_id, nom, c, m, uni)
                    )
                )

                btn_borrar = QPushButton(" X ")
                btn_borrar.setStyleSheet(
                    "background-color: #c0392b; color: white; border-radius: 3px; padding: 4px; font-weight: bold; font-size: 11px;"
                )
                btn_borrar.setCursor(Qt.PointingHandCursor)
                btn_borrar.clicked.connect(
                    lambda checked, d_id=det_id, nom=ins_nom: self.eliminar_insumo(
                        d_id, nom
                    )
                )

                layout_acciones.addWidget(btn_detalle)
                layout_acciones.addWidget(btn_editar)
                layout_acciones.addWidget(btn_borrar)

                self.tree.setItemWidget(hijo, 4, widget_acciones)

        self.tree.expandAll()

    def mostrar_calculo(self, html_content):
        if not html_content:
            QMessageBox.information(
                self,
                "Información",
                "El detalle de cálculo no está disponible para este registro.",
            )
            return
        dlg = DetalleCalculoDialog(html_content, self)
        dlg.exec_()

    def editar_insumo(self, det_id, nombre, cant, monto, unidad):
        dlg = EditarInsumoDialog(self.db, det_id, nombre, cant, monto, unidad, self)
        if dlg.exec_():
            recalcular_total_presupuesto(self.db, self.presupuesto_id)
            self.cargar_detalles()

    def eliminar_insumo(self, det_id, nombre):
        resp = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Seguro que desea remover '{nombre}' de este presupuesto?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            self.db.execute_query(
                "DELETE FROM detalle_presupuestos WHERE id = ?", (det_id,)
            )
            recalcular_total_presupuesto(self.db, self.presupuesto_id)
            self.cargar_detalles()

    def agregar_insumo_manual(self):
        dlg = AgregarInsumoManualDialog(self.db, self.presupuesto_id, self)
        if dlg.exec_():
            recalcular_total_presupuesto(self.db, self.presupuesto_id)
            self.cargar_detalles()
