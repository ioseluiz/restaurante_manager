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
    QTabWidget,
    QFormLayout,
    QCheckBox,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QFont

from app.utils.calculo_planilla import calcular_costo_empleado

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


def recalcular_total_planilla(db, presupuesto_id):
    """Suma el costo total (bruto + patronal) del bloque de planilla y lo
    guarda en presupuestos.monto_planilla. Independiente del bloque de compras."""
    total = db.fetch_one(
        "SELECT SUM(costo_total) FROM detalle_presupuesto_planilla WHERE presupuesto_id = ?",
        (presupuesto_id,),
    )
    total_val = total[0] if total and total[0] else 0.0
    db.execute_query(
        "UPDATE presupuestos SET monto_planilla = ? WHERE id = ?",
        (total_val, presupuesto_id),
    )
    return total_val


def recalcular_total_gastos(db, presupuesto_id):
    """Suma los gastos fijos del presupuesto y lo guarda en monto_gastos.
    Independiente de los bloques de compras y planilla."""
    total = db.fetch_one(
        "SELECT SUM(monto) FROM detalle_presupuesto_gastos WHERE presupuesto_id = ?",
        (presupuesto_id,),
    )
    total_val = total[0] if total and total[0] else 0.0
    db.execute_query(
        "UPDATE presupuestos SET monto_gastos = ? WHERE id = ?",
        (total_val, presupuesto_id),
    )
    return total_val


from app.utils.gastos_reales import (  # noqa: F401  (reexport)
    calcular_planilla_real_mes,
    ejecutado_gastos_mes,
)


class PresupuestosView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("<h2>Gestión de Presupuestos</h2>")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

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

        btn_control = QPushButton(" Control Presupuestal")
        btn_control.setStyleSheet(
            "background-color: #8e44ad; color: white; padding: 8px; border-radius: 4px; font-weight: bold;"
        )
        btn_control.clicked.connect(self.abrir_control_presupuesto)

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
        btn_layout.addWidget(btn_control)
        btn_layout.addWidget(btn_editar_gen)
        btn_layout.addWidget(btn_eliminar)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["Número", "Mes", "Año", "Descripción", "Compras", "Planilla", "Gastos", "Total General"]
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
        query = (
            "SELECT id, numero, mes, anio, descripcion, monto_total, "
            "COALESCE(monto_planilla, 0.0), COALESCE(monto_gastos, 0.0) "
            "FROM presupuestos ORDER BY id DESC"
        )
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

            monto_compras = f[5] if f[5] else 0.0
            monto_planilla = f[6] if f[6] else 0.0
            monto_gastos = f[7] if f[7] else 0.0
            total_general = monto_compras + monto_planilla + monto_gastos

            for col, val in [
                (4, monto_compras), (5, monto_planilla),
                (6, monto_gastos), (7, total_general),
            ]:
                it = QTableWidgetItem(f"${val:,.2f}")
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if col == 7:
                    font = it.font()
                    font.setBold(True)
                    it.setFont(font)
                self.table.setItem(i, col, it)

        self.table.resizeRowsToContents()

    def nuevo_presupuesto(self):
        dlg = CrearPresupuestoDialog(self.db, self)
        if dlg.exec_():
            if (
                getattr(dlg, "chk_incluir_planilla", None)
                and dlg.chk_incluir_planilla.isChecked()
                and dlg.nuevo_presupuesto_id
            ):
                copiar = CopiarPlanillaDialog(self.db, dlg.nuevo_presupuesto_id, self)
                if copiar.exec_():
                    recalcular_total_planilla(self.db, dlg.nuevo_presupuesto_id)
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

    def abrir_control_presupuesto(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, "Atención", "Debe seleccionar un presupuesto para ver su control."
            )
            return

        presupuesto_id = self.table.item(row, 0).data(Qt.UserRole)
        numero = self.table.item(row, 0).text()
        mes = self.table.item(row, 1).text()
        anio = self.table.item(row, 2).text()

        dlg = ControlPresupuestoDialog(self.db, presupuesto_id, numero, mes, anio, self)
        dlg.exec_()

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


class ControlPresupuestoDialog(QDialog):
    def __init__(self, db_manager, presupuesto_id, numero, mes, anio, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.presupuesto_id = presupuesto_id
        self.numero = numero
        self.mes = mes
        self.anio = anio

        self.setWindowTitle(f"Control de Presupuesto N° {numero} ({mes}/{anio})")
        self.resize(900, 600)
        self.setStyleSheet(DIALOG_STYLES)

        self.init_ui()
        self.cargar_datos_control()

    def init_ui(self):
        layout = QVBoxLayout(self)

        lbl_head = QLabel(f"<h3>Análisis y Control: Presupuesto N° {self.numero}</h3>")
        lbl_head.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_head)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(
            [
                "Categoría / Concepto",
                "Monto Presupuestado",
                "Monto Ejecutado (Real)",
                "Saldo (Diferencia)",
            ]
        )
        self.tree.setColumnWidth(0, 350)
        self.tree.setColumnWidth(1, 150)
        self.tree.setColumnWidth(2, 170)
        self.tree.setColumnWidth(3, 150)
        self.tree.setAlternatingRowColors(True)
        layout.addWidget(self.tree)

        self.lbl_resumen = QLabel("Cargando datos...")
        self.lbl_resumen.setStyleSheet(
            "font-size: 14px; padding: 10px; background-color: white; border: 1px solid #bdc3c7; border-radius: 4px;"
        )
        layout.addWidget(self.lbl_resumen)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setStyleSheet(
            "background-color: #bdc3c7; font-weight: bold; padding: 8px;"
        )
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignRight)

    def cargar_datos_control(self):
        self.tree.clear()

        query_pres = """
            SELECT categoria_nombre, insumo_nombre, monto_estimado 
            FROM detalle_presupuestos 
            WHERE presupuesto_id = ?
        """
        datos_presupuesto = self.db.fetch_all(query_pres, (self.presupuesto_id,))

        query_compras = """
            SELECT 
                COALESCE(cat.nombre, 'Sin Categoría') as categoria,
                i.nombre as insumo,
                SUM(dc.subtotal) as ejecutado
            FROM detalle_compras dc
            JOIN compras c ON dc.compra_id = c.id
            JOIN presentaciones_compra pc ON dc.presentacion_id = pc.id
            JOIN insumos i ON pc.insumo_id = i.id
            LEFT JOIN categorias_insumos cat ON i.categoria_id = cat.id
            WHERE c.presupuesto_id = ?
            GROUP BY cat.nombre, i.nombre
        """
        datos_compras = self.db.fetch_all(query_compras, (self.presupuesto_id,))

        diccionario = {}

        for d in datos_presupuesto:
            cat_nom = d[0] if d[0] else "Sin Categoría"
            ins_nom = d[1]
            monto_pres = d[2]

            if cat_nom not in diccionario:
                diccionario[cat_nom] = {}
            if ins_nom not in diccionario[cat_nom]:
                diccionario[cat_nom][ins_nom] = {"presupuestado": 0.0, "ejecutado": 0.0}

            diccionario[cat_nom][ins_nom]["presupuestado"] += monto_pres

        for c in datos_compras:
            cat_nom = c[0]
            ins_nom = c[1]
            monto_ejec = c[2]

            if cat_nom not in diccionario:
                diccionario[cat_nom] = {}
            if ins_nom not in diccionario[cat_nom]:
                diccionario[cat_nom][ins_nom] = {"presupuestado": 0.0, "ejecutado": 0.0}

            diccionario[cat_nom][ins_nom]["ejecutado"] += monto_ejec

        gran_total_presupuestado = 0.0
        gran_total_ejecutado = 0.0

        font_bold = QFont()
        font_bold.setBold(True)

        for cat in sorted(diccionario.keys()):
            cat_item = QTreeWidgetItem(self.tree)
            cat_item.setText(0, cat.upper())
            cat_item.setFont(0, font_bold)

            for i in range(4):
                cat_item.setBackground(i, Qt.lightGray)

            total_cat_pres = 0.0
            total_cat_ejec = 0.0

            for ins in sorted(diccionario[cat].keys()):
                valores = diccionario[cat][ins]
                m_pres = valores["presupuestado"]
                m_ejec = valores["ejecutado"]
                dif = m_pres - m_ejec

                total_cat_pres += m_pres
                total_cat_ejec += m_ejec

                hijo = QTreeWidgetItem(cat_item)
                hijo.setText(0, f"  {ins}")
                hijo.setText(1, f"${m_pres:,.2f}")
                hijo.setText(2, f"${m_ejec:,.2f}")

                if dif < 0:
                    hijo.setText(3, f"-${abs(dif):,.2f} (Excedido)")
                    hijo.setForeground(3, QColor("#c0392b"))
                else:
                    hijo.setText(3, f"${dif:,.2f}")
                    hijo.setForeground(3, QColor("#2980b9"))

            dif_cat = total_cat_pres - total_cat_ejec
            cat_item.setText(1, f"${total_cat_pres:,.2f}")
            cat_item.setText(2, f"${total_cat_ejec:,.2f}")
            if dif_cat < 0:
                cat_item.setText(3, f"-${abs(dif_cat):,.2f}")
                cat_item.setForeground(3, QColor("#c0392b"))
            else:
                cat_item.setText(3, f"${dif_cat:,.2f}")
                cat_item.setForeground(3, QColor("#2980b9"))

            gran_total_presupuestado += total_cat_pres
            gran_total_ejecutado += total_cat_ejec

        # Categorías adicionales: planilla y gastos fijos (bloques del presupuesto)
        p_pres, p_ejec = self._control_planilla(font_bold)
        gran_total_presupuestado += p_pres
        gran_total_ejecutado += p_ejec

        g_pres, g_ejec = self._control_gastos(font_bold)
        gran_total_presupuestado += g_pres
        gran_total_ejecutado += g_ejec

        self.tree.expandAll()

    def _fila_saldo(self, item, columna, dif):
        if dif < 0:
            item.setText(columna, f"-${abs(dif):,.2f} (Excedido)")
            item.setForeground(columna, QColor("#c0392b"))
        else:
            item.setText(columna, f"${dif:,.2f}")
            item.setForeground(columna, QColor("#2980b9"))

    def _control_planilla(self, font_bold):
        pres = self.db.fetch_one(
            "SELECT COALESCE(SUM(costo_total), 0) FROM detalle_presupuesto_planilla WHERE presupuesto_id = ?",
            (self.presupuesto_id,),
        )[0] or 0.0
        ejec = calcular_planilla_real_mes(self.db, self.mes, self.anio)
        if not pres and not ejec:
            return 0.0, 0.0

        cat_item = QTreeWidgetItem(self.tree)
        cat_item.setText(0, "PLANILLA")
        cat_item.setFont(0, font_bold)
        for i in range(4):
            cat_item.setBackground(i, Qt.lightGray)
        cat_item.setText(1, f"${pres:,.2f}")
        cat_item.setText(2, f"${ejec:,.2f}")
        self._fila_saldo(cat_item, 3, pres - ejec)

        hijo = QTreeWidgetItem(cat_item)
        hijo.setText(0, "  Planilla del mes (real)")
        hijo.setText(1, f"${pres:,.2f}")
        hijo.setText(2, f"${ejec:,.2f}")
        self._fila_saldo(hijo, 3, pres - ejec)
        return pres, ejec

    def _control_gastos(self, font_bold):
        pres_por_concepto = {}
        for concepto, monto in self.db.fetch_all(
            "SELECT concepto, SUM(monto) FROM detalle_presupuesto_gastos "
            "WHERE presupuesto_id = ? GROUP BY concepto",
            (self.presupuesto_id,),
        ):
            pres_por_concepto[concepto] = float(monto or 0)

        ejec_por_concepto = ejecutado_gastos_mes(self.db, self.mes, self.anio)

        conceptos = sorted(set(pres_por_concepto) | set(ejec_por_concepto))
        if not conceptos:
            return 0.0, 0.0

        cat_item = QTreeWidgetItem(self.tree)
        cat_item.setText(0, "GASTOS FIJOS")
        cat_item.setFont(0, font_bold)
        for i in range(4):
            cat_item.setBackground(i, Qt.lightGray)

        total_pres = 0.0
        total_ejec = 0.0
        for concepto in conceptos:
            m_pres = pres_por_concepto.get(concepto, 0.0)
            m_ejec = ejec_por_concepto.get(concepto, 0.0)
            total_pres += m_pres
            total_ejec += m_ejec

            hijo = QTreeWidgetItem(cat_item)
            hijo.setText(0, f"  {concepto}")
            hijo.setText(1, f"${m_pres:,.2f}")
            hijo.setText(2, f"${m_ejec:,.2f}")
            self._fila_saldo(hijo, 3, m_pres - m_ejec)

        cat_item.setText(1, f"${total_pres:,.2f}")
        cat_item.setText(2, f"${total_ejec:,.2f}")
        self._fila_saldo(cat_item, 3, total_pres - total_ejec)
        return total_pres, total_ejec

        dif_global = gran_total_presupuestado - gran_total_ejecutado
        color_saldo = "red" if dif_global < 0 else "blue"
        texto_saldo = (
            f"-${abs(dif_global):,.2f} (Alerta de Exceso)"
            if dif_global < 0
            else f"${dif_global:,.2f} (Dentro de Margen)"
        )

        html_res = f"""
            <b>Total Original Presupuestado:</b> ${gran_total_presupuestado:,.2f} &nbsp;&nbsp;|&nbsp;&nbsp; 
            <b>Total Real Ejecutado:</b> ${gran_total_ejecutado:,.2f} &nbsp;&nbsp;|&nbsp;&nbsp;
            <b>Saldo Global:</b> <span style='color:{color_saldo}; font-weight:bold;'>{texto_saldo}</span>
        """
        self.lbl_resumen.setText(html_res)


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


# --- NUEVO DIÁLOGO PARA AJUSTAR PORCENTAJE ---
class AjustarPorcentajeDialog(QDialog):
    def __init__(self, db, detalle_id, nombre, pct_actual, parent=None):
        super().__init__(parent)
        self.db = db
        self.detalle_id = detalle_id
        self.setWindowTitle(f"Ajustar Porcentaje: {nombre}")
        self.resize(350, 150)
        self.setStyleSheet(DIALOG_STYLES)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>Insumo:</b> {nombre}"))

        layout.addWidget(QLabel("Porcentaje Sugerido a Aplicar (%):"))
        self.spin_pct = QDoubleSpinBox()
        self.spin_pct.setRange(-100.0, 1000.0)
        self.spin_pct.setValue(pct_actual if pct_actual is not None else 0.0)
        layout.addWidget(self.spin_pct)

        btn_layout = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        btn_guardar = QPushButton("Guardar y Recalcular")
        btn_guardar.setStyleSheet(
            "background-color: #9b59b6; color: white; font-weight: bold;"
        )
        btn_guardar.clicked.connect(self.guardar)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_guardar)
        layout.addLayout(btn_layout)

    def guardar(self):
        self.db.execute_query(
            "UPDATE detalle_presupuestos SET porcentaje_usado=? WHERE id=?",
            (self.spin_pct.value(), self.detalle_id),
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
            INSERT INTO detalle_presupuestos (presupuesto_id, categoria_nombre, insumo_nombre, unidad_nombre, cantidad_requerida, monto_estimado, items_menu, detalle_calculo, porcentaje_usado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(
            query,
            (self.presupuesto_id, cat, ins, uni, c, m, "Agregado Extra", det, 0.0),
        )
        self.accept()


class CrearPresupuestoDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.nuevo_presupuesto_id = None
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

        self.chk_incluir_planilla = QCheckBox(
            "Incluir planilla base (se elegirá el período tras crear el presupuesto)"
        )
        layout.addWidget(self.chk_incluir_planilla)

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

            # --- MODIFICADO: Calculamos el promedio del porcentaje_sugerido de los reportes ---
            query_pct = f"SELECT AVG(porcentaje_sugerido) FROM reportes_ventas WHERE id IN ({placeholders})"
            avg_pct_row = self.db.fetch_one(query_pct, tuple(reportes_ids))
            avg_pct = float(avg_pct_row[0]) if avg_pct_row and avg_pct_row[0] else 0.0

            query_ventas = f"""
                SELECT reporte_id, codigo_producto, LOWER(dia_semana), SUM(promedio_medida) as cant
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

                # --- MODIFICADO: Ya no buscamos factor_calculo de insumos, sino aplicamos pct global del reporte ---
                query_recetas = """
                    SELECT r.insumo_id, i.nombre, c.nombre as categoria, 
                           r.cantidad_necesaria AS cantidad_necesaria, m.nombre as menu_nombre, u.abreviatura
                    FROM v_recetas_explotadas r
                    JOIN menu_items m ON r.menu_item_id = m.id
                    JOIN insumos i ON r.insumo_id = i.id
                    LEFT JOIN categorias_insumos c ON i.categoria_id = c.id
                    LEFT JOIN unidades_medida u ON i.unidad_base_id = u.id
                    WHERE m.codigo = ?
                """
                recetas = self.db.fetch_all(query_recetas, (cod,))

                for rec in recetas:
                    ins_id, ins_nom, cat_nom, cant_nec, menu_nom, abrev_uni = rec
                    cat_nom = cat_nom if cat_nom else "Sin Categoría"
                    abrev_uni = abrev_uni if abrev_uni else "Und."

                    pct_usado = avg_pct
                    factor_val = 1.0 + (pct_usado / 100.0)

                    cant_amplificada = (ventas_totales * cant_nec) * factor_val

                    if ins_id not in insumos_calc:
                        insumos_calc[ins_id] = {
                            "nombre": ins_nom,
                            "categoria": cat_nom,
                            "unidad_base": abrev_uni,
                            "pct_usado": pct_usado,
                            "factor": factor_val,
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
                pct_val = data["pct_usado"]

                query_pres = "SELECT cantidad_contenido, precio_compra, nombre FROM presentaciones_compra WHERE insumo_id = ? ORDER BY id ASC LIMIT 1"
                pres = self.db.fetch_one(query_pres, (ins_id,))

                cant_compra_exacta = 0.0
                cant_compra_final = 0.0
                costo_insumo_final = 0.0
                unidad_nombre_final = ""

                det_html = f"<div style='font-family: Arial, sans-serif;'>"
                det_html += f"<h3 style='color:#2c3e50; border-bottom: 2px solid #bdc3c7; padding-bottom: 5px;'>Detalle de Cálculo: {data['nombre']}</h3>"

                det_html += f"<table width='100%' style='margin-bottom: 15px;'><tr>"
                det_html += (
                    f"<td width='50%'><b>Unidad Base Recetas:</b> {abrev_base}</td>"
                )
                det_html += f"<td width='50%'><b>Porcentaje Sugerido Aplicado:</b> {pct_val:.2f}% (Factor: {factor_val:.2f})</td>"
                det_html += f"</tr></table>"

                if pres and pres[0] > 0:
                    cant_contenido, precio_pres, nombre_pres = pres

                    cant_compra_exacta = data["qty_base_total"] / cant_contenido
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
                        data["pct_usado"],
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
            self.nuevo_presupuesto_id = presupuesto_id

            for rid in reportes_ids:
                self.db.execute_query(
                    "INSERT INTO presupuesto_reportes (presupuesto_id, reporte_id) VALUES (?,?)",
                    (presupuesto_id, int(rid)),
                )

            query_det_insert = """
                INSERT INTO detalle_presupuestos 
                (presupuesto_id, categoria_nombre, insumo_nombre, unidad_nombre, cantidad_requerida, monto_estimado, items_menu, detalle_calculo, porcentaje_usado) 
                VALUES (?,?,?,?,?,?,?,?,?)
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
        self.resize(1200, 700)
        self.setStyleSheet(DIALOG_STYLES)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.lbl_head = QLabel()
        layout.addWidget(self.lbl_head)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # ---------------- Tab COMPRAS (bloque existente) ----------------
        tab_compras = QWidget()
        lay_compras = QVBoxLayout(tab_compras)
        lay_compras.setContentsMargins(0, 10, 0, 0)
        lay_compras.setSpacing(10)

        btn_layout_top = QHBoxLayout()

        btn_recalcular = QPushButton(" 🔄 Recalcular con Precios Actuales")
        btn_recalcular.setStyleSheet(
            "background-color: #8e44ad; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold;"
        )
        btn_recalcular.clicked.connect(self.recalcular_automatico)

        btn_agregar_insumo = QPushButton(" + Agregar Insumo Manual Extra")
        btn_agregar_insumo.setStyleSheet(
            "background-color: #27ae60; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold;"
        )
        btn_agregar_insumo.clicked.connect(self.agregar_insumo_manual)

        btn_layout_top.addWidget(btn_recalcular)
        btn_layout_top.addStretch()
        btn_layout_top.addWidget(btn_agregar_insumo)

        lay_compras.addLayout(btn_layout_top)

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
        self.tree.setColumnWidth(1, 140)
        self.tree.setColumnWidth(2, 120)
        self.tree.setColumnWidth(3, 270)
        self.tree.setColumnWidth(4, 310)
        self.tree.setAlternatingRowColors(True)
        self.tree.setWordWrap(True)
        lay_compras.addWidget(self.tree)

        self.tabs.addTab(tab_compras, "🧾 Compras")

        # ---------------- Tab PLANILLA (bloque nuevo) ----------------
        tab_planilla = QWidget()
        self._init_planilla_tab(tab_planilla)
        self.tabs.addTab(tab_planilla, "👥 Planilla")

        self.cargar_detalles()
        self.cargar_planilla()

        btn_cerrar = QPushButton("Cerrar Vista")
        btn_cerrar.setStyleSheet(
            "background-color: #bdc3c7; color: #2c3e50; font-weight: bold; padding: 8px 15px; border-radius: 4px;"
        )
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignRight)

        self.setLayout(layout)

    def _init_planilla_tab(self, contenedor):
        lay = QVBoxLayout(contenedor)
        lay.setContentsMargins(0, 10, 0, 0)
        lay.setSpacing(10)

        btn_bar = QHBoxLayout()

        btn_copiar = QPushButton(" 📋 Copiar planilla de período…")
        btn_copiar.setStyleSheet(
            "background-color: #2980b9; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold;"
        )
        btn_copiar.clicked.connect(self.copiar_planilla_periodo)

        btn_agregar_emp = QPushButton(" + Agregar empleado manual")
        btn_agregar_emp.setStyleSheet(
            "background-color: #27ae60; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold;"
        )
        btn_agregar_emp.clicked.connect(self.agregar_empleado_planilla)

        btn_bar.addWidget(btn_copiar)
        btn_bar.addStretch()
        btn_bar.addWidget(btn_agregar_emp)
        lay.addLayout(btn_bar)

        self.tabla_planilla = QTableWidget()
        self.tabla_planilla.setColumnCount(9)
        self.tabla_planilla.setHorizontalHeaderLabels(
            [
                "Empleado",
                "Puesto",
                "Sucursal",
                "Salario Bruto",
                "Deducc. Colab.",
                "Costo Patronal",
                "Provisiones",
                "Costo Total",
                "Acciones",
            ]
        )
        self.tabla_planilla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_planilla.horizontalHeader().setSectionResizeMode(
            8, QHeaderView.ResizeToContents
        )
        self.tabla_planilla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_planilla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_planilla.setAlternatingRowColors(True)
        self.tabla_planilla.setStyleSheet(
            "background-color: white; color: #2c3e50; alternate-background-color: #f9f9f9;"
        )
        lay.addWidget(self.tabla_planilla)

        self.lbl_total_planilla = QLabel()
        self.lbl_total_planilla.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lay.addWidget(self.lbl_total_planilla)

    def actualizar_encabezado(self):
        row = self.db.fetch_one(
            "SELECT monto_total, COALESCE(monto_planilla, 0.0), COALESCE(monto_gastos, 0.0) "
            "FROM presupuestos WHERE id = ?",
            (self.presupuesto_id,),
        )
        monto_compras = row[0] if row and row[0] else 0.0
        monto_planilla = row[1] if row and row[1] else 0.0
        monto_gastos = row[2] if row and row[2] else 0.0
        total_general = monto_compras + monto_planilla + monto_gastos

        html = f"""
            <div style='background-color: #ecf0f1; padding: 15px; border-radius: 5px; border: 1px solid #bdc3c7;'>
                <h3 style='margin:0; color: #2c3e50;'>Presupuesto N° {self.numero}</h3>
                <p style='margin: 5px 0; color: #34495e;'>
                    <b>Periodo:</b> {self.mes}/{self.anio}
                    &nbsp;|&nbsp; <b>Compras:</b> <span style='color: #c0392b;'>${monto_compras:,.2f}</span>
                    &nbsp;|&nbsp; <b>Planilla:</b> <span style='color: #2980b9;'>${monto_planilla:,.2f}</span>
                    &nbsp;|&nbsp; <b>Gastos fijos:</b> <span style='color: #d35400;'>${monto_gastos:,.2f}</span>
                    &nbsp;|&nbsp; <b>Total General:</b> <span style='color: #16a085; font-size: 16px;'>${total_general:,.2f}</span>
                </p>
                <p style='margin: 0; color: #7f8c8d; font-style: italic;'>{self.desc}</p>
            </div>
        """
        self.lbl_head.setText(html)

    def cargar_detalles(self):
        self.tree.clear()
        self.actualizar_encabezado()

        query = """
            SELECT id, categoria_nombre, insumo_nombre, unidad_nombre, cantidad_requerida, monto_estimado, items_menu, detalle_calculo, porcentaje_usado
            FROM detalle_presupuestos 
            WHERE presupuesto_id = ? 
            ORDER BY categoria_nombre, insumo_nombre
        """
        detalles = self.db.fetch_all(query, (self.presupuesto_id,))

        agrupado = {}
        for d in detalles:
            (
                det_id,
                cat_nom,
                ins_nom,
                uni_nom,
                cant,
                monto,
                items,
                det_calc,
                pct_usado,
            ) = d
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
                (
                    det_id,
                    cat_nom,
                    ins_nom,
                    uni_nom,
                    cant,
                    monto,
                    items,
                    det_calc,
                    pct_usado,
                ) = d

                hijo = QTreeWidgetItem(cat_item)
                hijo.setText(0, ins_nom)
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

                _btn_style = (
                    "QPushButton{{background-color:{bg};color:white;border-radius:3px;"
                    "padding:5px 10px;font-weight:bold;font-size:11px;border:none;}}"
                    "QPushButton:hover{{background-color:{hov};}}"
                    "QPushButton:pressed{{background-color:{prs};}}"
                )

                btn_detalle = QPushButton("Detalle")
                btn_detalle.setProperty("skip-auto-icon", True)
                btn_detalle.setStyleSheet(_btn_style.format(bg="#3498db", hov="#2176ae", prs="#1a5f8a"))
                btn_detalle.setCursor(Qt.PointingHandCursor)
                btn_detalle.setMinimumWidth(68)
                btn_detalle.clicked.connect(
                    lambda checked, html=det_calc: self.mostrar_calculo(html)
                )

                btn_porcentaje = QPushButton("Ajustar %")
                btn_porcentaje.setProperty("skip-auto-icon", True)
                btn_porcentaje.setStyleSheet(_btn_style.format(bg="#9b59b6", hov="#7d3c98", prs="#6c3483"))
                btn_porcentaje.setCursor(Qt.PointingHandCursor)
                btn_porcentaje.setMinimumWidth(78)
                btn_porcentaje.clicked.connect(
                    lambda checked, d_id=det_id, nom=ins_nom, pct=pct_usado: (
                        self.abrir_ajuste_porcentaje(d_id, nom, pct)
                    )
                )

                btn_editar = QPushButton("Editar")
                btn_editar.setProperty("skip-auto-icon", True)
                btn_editar.setStyleSheet(_btn_style.format(bg="#f39c12", hov="#c87f0a", prs="#9a6008"))
                btn_editar.setCursor(Qt.PointingHandCursor)
                btn_editar.setMinimumWidth(60)
                btn_editar.clicked.connect(
                    lambda checked, d_id=det_id, nom=ins_nom, c=cant, m=monto, uni=uni_nom: (
                        self.editar_insumo(d_id, nom, c, m, uni)
                    )
                )

                btn_borrar = QPushButton("Borrar")
                btn_borrar.setProperty("skip-auto-icon", True)
                btn_borrar.setStyleSheet(_btn_style.format(bg="#c0392b", hov="#96281b", prs="#6e1c13"))
                btn_borrar.setCursor(Qt.PointingHandCursor)
                btn_borrar.setMinimumWidth(60)
                btn_borrar.clicked.connect(
                    lambda checked, d_id=det_id, nom=ins_nom: self.eliminar_insumo(
                        d_id, nom
                    )
                )

                layout_acciones.addWidget(btn_detalle)
                layout_acciones.addWidget(btn_porcentaje)
                layout_acciones.addWidget(btn_editar)
                layout_acciones.addWidget(btn_borrar)

                self.tree.setItemWidget(hijo, 4, widget_acciones)

        self._agregar_categoria_planilla()
        self._agregar_categoria_gastos()

        self.tree.expandAll()

    def _agregar_categoria_planilla(self):
        """Muestra la planilla como una categoría más dentro del árbol del
        presupuesto (junto a las categorías de insumos), con el monto del mes
        y cada empleado como sub-fila editable."""
        empleados = self.db.fetch_all(
            """SELECT id, empleado_nombre, puesto, sucursal_nombre, costo_total
               FROM detalle_presupuesto_planilla
               WHERE presupuesto_id = ?
               ORDER BY empleado_nombre""",
            (self.presupuesto_id,),
        )
        total_planilla = sum(float(e[4] or 0) for e in empleados)

        cat_item = QTreeWidgetItem(self.tree)
        cat_item.setText(0, "PLANILLA (PLANIFICADA)")
        cat_item.setText(2, f"${total_planilla:,.2f}")
        for i in range(5):
            cat_item.setBackground(i, QColor("#2980b9"))
            cat_item.setForeground(i, Qt.white)
            font = cat_item.font(i)
            font.setBold(True)
            cat_item.setFont(i, font)

        # Botones a nivel de categoría: copiar de período / agregar empleado
        cat_widget = QWidget()
        cat_lay = QHBoxLayout(cat_widget)
        cat_lay.setContentsMargins(0, 0, 0, 0)
        cat_lay.setSpacing(5)
        _cat_btn = (
            "QPushButton{{background-color:{bg};color:white;border-radius:3px;"
            "padding:4px 9px;font-weight:bold;font-size:11px;border:none;}}"
            "QPushButton:hover{{background-color:{hov};}}"
        )
        btn_copiar = QPushButton("Copiar de período")
        btn_copiar.setProperty("skip-auto-icon", True)
        btn_copiar.setStyleSheet(_cat_btn.format(bg="#2471a3", hov="#1b4f72"))
        btn_copiar.setCursor(Qt.PointingHandCursor)
        btn_copiar.clicked.connect(self.copiar_planilla_periodo)
        btn_add = QPushButton("+ Empleado")
        btn_add.setProperty("skip-auto-icon", True)
        btn_add.setStyleSheet(_cat_btn.format(bg="#27ae60", hov="#1e8449"))
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(self.agregar_empleado_planilla)
        cat_lay.addWidget(btn_copiar)
        cat_lay.addWidget(btn_add)
        self.tree.setItemWidget(cat_item, 4, cat_widget)

        if not empleados:
            vacio = QTreeWidgetItem(cat_item)
            vacio.setText(0, "Sin planilla planificada")
            vacio.setText(3, "Use “Copiar de período” o “+ Empleado”.")
            vacio.setForeground(0, QColor("#7f8c8d"))
            return

        for (det_id, nombre, puesto, sucursal, costo_total) in empleados:
            hijo = QTreeWidgetItem(cat_item)
            hijo.setText(0, nombre or "—")
            hijo.setText(2, f"${float(costo_total or 0):,.2f}")
            hijo.setTextAlignment(2, Qt.AlignRight | Qt.AlignVCenter)
            desglose = " · ".join([x for x in [puesto, sucursal] if x and x != "—"])
            hijo.setText(3, desglose)

            widget = QWidget()
            hl = QHBoxLayout(widget)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.setSpacing(5)
            _btn = (
                "QPushButton{{background-color:{bg};color:white;border-radius:3px;"
                "padding:5px 10px;font-weight:bold;font-size:11px;border:none;}}"
                "QPushButton:hover{{background-color:{hov};}}"
            )
            btn_e = QPushButton("Editar")
            btn_e.setProperty("skip-auto-icon", True)
            btn_e.setStyleSheet(_btn.format(bg="#f39c12", hov="#c87f0a"))
            btn_e.setCursor(Qt.PointingHandCursor)
            btn_e.clicked.connect(
                lambda checked, d_id=det_id: self.editar_empleado_planilla(d_id)
            )
            btn_b = QPushButton("Borrar")
            btn_b.setProperty("skip-auto-icon", True)
            btn_b.setStyleSheet(_btn.format(bg="#c0392b", hov="#96281b"))
            btn_b.setCursor(Qt.PointingHandCursor)
            btn_b.clicked.connect(
                lambda checked, d_id=det_id, nom=nombre: self.eliminar_empleado_planilla(d_id, nom)
            )
            hl.addWidget(btn_e)
            hl.addWidget(btn_b)
            self.tree.setItemWidget(hijo, 4, widget)

    def _agregar_categoria_gastos(self):
        """Muestra los gastos fijos (alquiler, luz, agua, otros) como una
        categoría más dentro del árbol del presupuesto."""
        gastos = self.db.fetch_all(
            """SELECT id, concepto, monto
               FROM detalle_presupuesto_gastos
               WHERE presupuesto_id = ?
               ORDER BY concepto""",
            (self.presupuesto_id,),
        )
        total_gastos = sum(float(g[2] or 0) for g in gastos)

        cat_item = QTreeWidgetItem(self.tree)
        cat_item.setText(0, "GASTOS FIJOS")
        cat_item.setText(2, f"${total_gastos:,.2f}")
        for i in range(5):
            cat_item.setBackground(i, QColor("#d35400"))
            cat_item.setForeground(i, Qt.white)
            font = cat_item.font(i)
            font.setBold(True)
            cat_item.setFont(i, font)

        cat_widget = QWidget()
        cat_lay = QHBoxLayout(cat_widget)
        cat_lay.setContentsMargins(0, 0, 0, 0)
        cat_lay.setSpacing(5)
        _cat_btn = (
            "QPushButton{{background-color:{bg};color:white;border-radius:3px;"
            "padding:4px 9px;font-weight:bold;font-size:11px;border:none;}}"
            "QPushButton:hover{{background-color:{hov};}}"
        )
        btn_copiar = QPushButton("Copiar del anterior")
        btn_copiar.setProperty("skip-auto-icon", True)
        btn_copiar.setStyleSheet(_cat_btn.format(bg="#ba4a00", hov="#873600"))
        btn_copiar.setCursor(Qt.PointingHandCursor)
        btn_copiar.clicked.connect(self.copiar_gastos_anterior)
        btn_add = QPushButton("+ Gasto")
        btn_add.setProperty("skip-auto-icon", True)
        btn_add.setStyleSheet(_cat_btn.format(bg="#27ae60", hov="#1e8449"))
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(self.agregar_gasto)
        cat_lay.addWidget(btn_copiar)
        cat_lay.addWidget(btn_add)
        self.tree.setItemWidget(cat_item, 4, cat_widget)

        if not gastos:
            vacio = QTreeWidgetItem(cat_item)
            vacio.setText(0, "Sin gastos fijos")
            vacio.setText(3, "Use “Copiar del anterior” o “+ Gasto”.")
            vacio.setForeground(0, QColor("#7f8c8d"))
            return

        for (det_id, concepto, monto) in gastos:
            hijo = QTreeWidgetItem(cat_item)
            hijo.setText(0, concepto or "—")
            hijo.setText(2, f"${float(monto or 0):,.2f}")
            hijo.setTextAlignment(2, Qt.AlignRight | Qt.AlignVCenter)

            widget = QWidget()
            hl = QHBoxLayout(widget)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.setSpacing(5)
            _btn = (
                "QPushButton{{background-color:{bg};color:white;border-radius:3px;"
                "padding:5px 10px;font-weight:bold;font-size:11px;border:none;}}"
                "QPushButton:hover{{background-color:{hov};}}"
            )
            btn_e = QPushButton("Editar")
            btn_e.setProperty("skip-auto-icon", True)
            btn_e.setStyleSheet(_btn.format(bg="#f39c12", hov="#c87f0a"))
            btn_e.setCursor(Qt.PointingHandCursor)
            btn_e.clicked.connect(
                lambda checked, d_id=det_id: self.editar_gasto(d_id)
            )
            btn_b = QPushButton("Borrar")
            btn_b.setProperty("skip-auto-icon", True)
            btn_b.setStyleSheet(_btn.format(bg="#c0392b", hov="#96281b"))
            btn_b.setCursor(Qt.PointingHandCursor)
            btn_b.clicked.connect(
                lambda checked, d_id=det_id, c=concepto: self.eliminar_gasto(d_id, c)
            )
            hl.addWidget(btn_e)
            hl.addWidget(btn_b)
            self.tree.setItemWidget(hijo, 4, widget)

    def abrir_ajuste_porcentaje(self, det_id, nombre, pct_actual):
        dlg = AjustarPorcentajeDialog(self.db, det_id, nombre, pct_actual, self)
        if dlg.exec_():
            self.recalcular_automatico(confirmar=False)

    def recalcular_automatico(self, confirmar=True):
        if confirmar:
            resp = QMessageBox.question(
                self,
                "Confirmar Recálculo",
                "¿Desea recalcular todo el presupuesto usando los PRECIOS y RECETAS actuales?\n\n"
                "• Los insumos 'Extras' agregados manualmente se conservarán.\n"
                "• Las ediciones manuales a insumos calculados se sobreescribirán.\n"
                "• Los porcentajes personalizados de cada insumo se conservarán.",
                QMessageBox.Yes | QMessageBox.No,
            )

            if resp != QMessageBox.Yes:
                return

        try:
            query_reps = (
                "SELECT reporte_id FROM presupuesto_reportes WHERE presupuesto_id = ?"
            )
            reps = self.db.fetch_all(query_reps, (self.presupuesto_id,))
            reportes_ids = [str(r[0]) for r in reps]

            if not reportes_ids:
                if confirmar:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "No se encontraron reportes base para recalcular.",
                    )
                return

            query_pct_existentes = "SELECT insumo_nombre, porcentaje_usado FROM detalle_presupuestos WHERE presupuesto_id = ?"
            pcts_existentes = {}
            for row in self.db.fetch_all(query_pct_existentes, (self.presupuesto_id,)):
                if row[1] is not None:
                    pcts_existentes[row[0]] = float(row[1])

            placeholders = ",".join(["?"] * len(reportes_ids))

            query_avg_pct = f"SELECT AVG(porcentaje_sugerido) FROM reportes_ventas WHERE id IN ({placeholders})"
            avg_pct_row = self.db.fetch_one(query_avg_pct, tuple(reportes_ids))
            avg_pct = float(avg_pct_row[0]) if avg_pct_row and avg_pct_row[0] else 0.0

            query_extras = """
                SELECT categoria_nombre, insumo_nombre, unidad_nombre, cantidad_requerida, monto_estimado, items_menu, detalle_calculo, porcentaje_usado
                FROM detalle_presupuestos 
                WHERE presupuesto_id = ? AND items_menu = 'Agregado Extra'
            """
            extras = self.db.fetch_all(query_extras, (self.presupuesto_id,))

            query_ventas = f"""
                SELECT reporte_id, codigo_producto, LOWER(dia_semana), SUM(promedio_medida) as cant
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
                    SELECT r.insumo_id, i.nombre, c.nombre as categoria, 
                           r.cantidad_necesaria AS cantidad_necesaria, m.nombre as menu_nombre, u.abreviatura
                    FROM v_recetas_explotadas r
                    JOIN menu_items m ON r.menu_item_id = m.id
                    JOIN insumos i ON r.insumo_id = i.id
                    LEFT JOIN categorias_insumos c ON i.categoria_id = c.id
                    LEFT JOIN unidades_medida u ON i.unidad_base_id = u.id
                    WHERE m.codigo = ?
                """
                recetas = self.db.fetch_all(query_recetas, (cod,))

                for rec in recetas:
                    ins_id, ins_nom, cat_nom, cant_nec, menu_nom, abrev_uni = rec
                    cat_nom = cat_nom if cat_nom else "Sin Categoría"
                    abrev_uni = abrev_uni if abrev_uni else "Und."

                    pct_usado = pcts_existentes.get(ins_nom, avg_pct)
                    factor_val = 1.0 + (pct_usado / 100.0)

                    cant_amplificada = (ventas_totales * cant_nec) * factor_val

                    if ins_id not in insumos_calc:
                        insumos_calc[ins_id] = {
                            "nombre": ins_nom,
                            "categoria": cat_nom,
                            "unidad_base": abrev_uni,
                            "pct_usado": pct_usado,
                            "factor": factor_val,
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

            import math

            detalles_db = []
            for ins_id, data in insumos_calc.items():
                abrev_base = data["unidad_base"]
                factor_val = data["factor"]
                pct_val = data["pct_usado"]

                query_pres = "SELECT cantidad_contenido, precio_compra, nombre FROM presentaciones_compra WHERE insumo_id = ? ORDER BY id ASC LIMIT 1"
                pres = self.db.fetch_one(query_pres, (ins_id,))

                cant_compra_exacta = 0.0
                cant_compra_final = 0.0
                costo_insumo_final = 0.0
                unidad_nombre_final = ""

                det_html = f"<div style='font-family: Arial, sans-serif;'>"
                det_html += f"<h3 style='color:#2c3e50; border-bottom: 2px solid #bdc3c7; padding-bottom: 5px;'>Detalle de Cálculo: {data['nombre']}</h3>"
                det_html += f"<table width='100%' style='margin-bottom: 15px;'><tr><td width='50%'><b>Unidad Base Recetas:</b> {abrev_base}</td><td width='50%'><b>Porcentaje Sugerido Aplicado:</b> {pct_val:.2f}% (Factor: {factor_val:.2f})</td></tr></table>"

                if pres and pres[0] > 0:
                    cant_contenido, precio_pres, nombre_pres = pres
                    cant_compra_exacta = data["qty_base_total"] / cant_contenido
                    cant_compra_final = math.ceil(cant_compra_exacta)
                    costo_insumo_final = cant_compra_final * precio_pres
                    unidad_nombre_final = nombre_pres

                    det_html += f"<div style='background-color: #e8f8f5; padding: 10px; border-radius: 4px; border: 1px solid #1abc9c; margin-bottom: 15px;'>"
                    det_html += f"<b>Presentación de Compra:</b> {nombre_pres}<br><b>Contenido:</b> {cant_contenido} {abrev_base}<br><b>Precio:</b> ${precio_pres:,.2f}</div>"
                else:
                    query_fallback = "SELECT costo_unitario FROM insumos WHERE id = ?"
                    ins_data = self.db.fetch_one(query_fallback, (ins_id,))
                    precio_uni = ins_data[0] if ins_data and ins_data[0] else 0.0
                    cant_compra_exacta = data["qty_base_total"]
                    cant_compra_final = math.ceil(cant_compra_exacta)
                    costo_insumo_final = cant_compra_final * precio_uni
                    unidad_nombre_final = abrev_base

                    det_html += f"<div style='background-color: #fcf3cf; padding: 10px; border-radius: 4px; border: 1px solid #f1c40f; margin-bottom: 15px;'>"
                    det_html += f"<i>No tiene presentación de compra asignada. Se calcula sobre unidad base.</i><br><b>Precio Unitario (Base):</b> ${precio_uni:,.2f}</div>"

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
                    det_html += f"<div style='margin-bottom: 10px; padding: 10px; border-left: 4px solid #3498db; background-color: #f8f9fa; border-radius: 0 4px 4px 0;'><b style='color:#2c3e50; font-size: 14px;'>{m_nom}</b><br><table width='100%' style='font-size: 12px; margin-top: 5px; color: #555;'><tr><td width='35%'><b>Ventas Diario (Promedio):</b></td><td>[{dias_format}]</td></tr><tr><td><b>Ventas Mensual Proyectado:</b></td><td>{m_info['ventas_mensual']:.2f} platos vendidos</td></tr><tr><td><b>Requerido en Receta:</b></td><td>{m_info['receta_cant']:.4f} {abrev_base} por plato</td></tr></table><div style='margin-top: 6px; padding-top: 6px; border-top: 1px dashed #ccc; font-family: monospace; font-size: 13px;'>Fórmula: {m_info['ventas_mensual']:.2f} platos x {m_info['receta_cant']:.4f} {abrev_base}{factor_str} = <b style='color: #c0392b;'>{m_info['total_plato']:.2f} {abrev_base}</b></div></div>"

                det_html += f"<h4 style='color:#27ae60; margin-top: 20px;'>2. Conversión a Compras y Costo Final</h4><ul style='font-size: 14px; background-color: #ecf0f1; padding: 15px 15px 15px 35px; border-radius: 5px;'><li style='margin-bottom: 5px;'><b>Total Base Requerido (Suma Platos):</b> {data['qty_base_total']:.2f} {abrev_base}</li><li style='margin-bottom: 5px;'><b>Cantidad Exacta de Compra:</b> {cant_compra_exacta:.2f} {unidad_nombre_final}</li><li style='margin-bottom: 5px; color: #c0392b;'><b>Cantidad a Comprar (Redondeada):</b> <span style='background-color:#f1c40f; padding: 2px 5px; border-radius: 3px; font-weight: bold; color: #2c3e50;'>{int(cant_compra_final)} {unidad_nombre_final}</span></li><li><b>Costo Estimado:</b> ${costo_insumo_final:,.2f}</li></ul></div>"

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
                        data["pct_usado"],
                    )
                )

            self.db.execute_query(
                "DELETE FROM detalle_presupuestos WHERE presupuesto_id = ?",
                (self.presupuesto_id,),
            )

            query_det_insert = """
                INSERT INTO detalle_presupuestos 
                (presupuesto_id, categoria_nombre, insumo_nombre, unidad_nombre, cantidad_requerida, monto_estimado, items_menu, detalle_calculo, porcentaje_usado) 
                VALUES (?,?,?,?,?,?,?,?,?)
            """

            for det in detalles_db:
                self.db.execute_query(query_det_insert, (self.presupuesto_id, *det))

            for ext in extras:
                self.db.execute_query(query_det_insert, (self.presupuesto_id, *ext))

            recalcular_total_presupuesto(self.db, self.presupuesto_id)

            if confirmar:
                QMessageBox.information(
                    self,
                    "Éxito",
                    "El presupuesto ha sido recalculado con los precios y recetas actuales.",
                )
            self.cargar_detalles()

        except Exception as e:
            import traceback

            traceback.print_exc()
            if confirmar:
                QMessageBox.critical(
                    self, "Error", f"Ha ocurrido un error al recalcular:\n{str(e)}"
                )

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

    # ------------------------ Bloque Planilla ------------------------

    def cargar_planilla(self):
        self.tabla_planilla.setRowCount(0)
        filas = self.db.fetch_all(
            """SELECT id, empleado_nombre, puesto, sucursal_nombre,
                      salario_bruto, deducciones_colab, costo_patronal, COALESCE(provisiones, 0), costo_total
               FROM detalle_presupuesto_planilla
               WHERE presupuesto_id = ?
               ORDER BY empleado_nombre""",
            (self.presupuesto_id,),
        )

        total_costo = 0.0
        for i, f in enumerate(filas):
            (det_id, nombre, puesto, sucursal,
             bruto, ded_colab, patronal, provisiones, costo_total) = f
            total_costo += float(costo_total or 0)

            self.tabla_planilla.insertRow(i)

            it_nom = QTableWidgetItem(nombre or "—")
            it_nom.setData(Qt.UserRole, det_id)
            self.tabla_planilla.setItem(i, 0, it_nom)
            self.tabla_planilla.setItem(i, 1, QTableWidgetItem(puesto or "—"))
            self.tabla_planilla.setItem(i, 2, QTableWidgetItem(sucursal or "—"))

            for col, val in [
                (3, bruto), (4, ded_colab), (5, patronal), (6, provisiones), (7, costo_total)
            ]:
                it = QTableWidgetItem(f"${float(val or 0):,.2f}")
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla_planilla.setItem(i, col, it)

            widget = QWidget()
            hl = QHBoxLayout(widget)
            hl.setContentsMargins(4, 0, 4, 0)
            hl.setSpacing(5)

            _btn_style = (
                "QPushButton{{background-color:{bg};color:white;border-radius:3px;"
                "padding:5px 10px;font-weight:bold;font-size:11px;border:none;}}"
                "QPushButton:hover{{background-color:{hov};}}"
            )

            btn_edit = QPushButton("Editar")
            btn_edit.setProperty("skip-auto-icon", True)
            btn_edit.setStyleSheet(_btn_style.format(bg="#f39c12", hov="#c87f0a"))
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.clicked.connect(
                lambda checked, d_id=det_id: self.editar_empleado_planilla(d_id)
            )

            btn_del = QPushButton("Borrar")
            btn_del.setProperty("skip-auto-icon", True)
            btn_del.setStyleSheet(_btn_style.format(bg="#c0392b", hov="#96281b"))
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.clicked.connect(
                lambda checked, d_id=det_id, nom=nombre: self.eliminar_empleado_planilla(d_id, nom)
            )

            hl.addWidget(btn_edit)
            hl.addWidget(btn_del)
            self.tabla_planilla.setCellWidget(i, 8, widget)

        self.lbl_total_planilla.setText(
            f"<span style='font-size:15px;'>Total Planilla (bruto + aportes patronales): "
            f"<b style='color:#2980b9;'>${total_costo:,.2f}</b></span>"
        )
        self.actualizar_encabezado()

    def _refrescar_planilla(self):
        """Recalcula el total de planilla y refresca ambas vistas: la pestaña
        de planilla y la categoría de planilla dentro del árbol de compras."""
        recalcular_total_planilla(self.db, self.presupuesto_id)
        self.cargar_planilla()
        self.cargar_detalles()

    def copiar_planilla_periodo(self):
        dlg = CopiarPlanillaDialog(self.db, self.presupuesto_id, self)
        if dlg.exec_():
            self._refrescar_planilla()

    def agregar_empleado_planilla(self):
        dlg = EmpleadoPlanillaDialog(self.db, self.presupuesto_id, None, self)
        if dlg.exec_():
            self._refrescar_planilla()

    def editar_empleado_planilla(self, det_id):
        dlg = EmpleadoPlanillaDialog(self.db, self.presupuesto_id, det_id, self)
        if dlg.exec_():
            self._refrescar_planilla()

    def eliminar_empleado_planilla(self, det_id, nombre):
        resp = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Seguro que desea quitar a '{nombre or '—'}' de la planilla de este presupuesto?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            self.db.execute_query(
                "DELETE FROM detalle_presupuesto_planilla WHERE id = ?", (det_id,)
            )
            self._refrescar_planilla()

    # ------------------------ Bloque Gastos Fijos ------------------------

    def _refrescar_gastos(self):
        recalcular_total_gastos(self.db, self.presupuesto_id)
        self.cargar_detalles()

    def agregar_gasto(self):
        dlg = GastoPresupuestoDialog(self.db, self.presupuesto_id, None, self)
        if dlg.exec_():
            self._refrescar_gastos()

    def editar_gasto(self, det_id):
        dlg = GastoPresupuestoDialog(self.db, self.presupuesto_id, det_id, self)
        if dlg.exec_():
            self._refrescar_gastos()

    def eliminar_gasto(self, det_id, concepto):
        resp = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Seguro que desea quitar el gasto '{concepto or '—'}' de este presupuesto?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            self.db.execute_query(
                "DELETE FROM detalle_presupuesto_gastos WHERE id = ?", (det_id,)
            )
            self._refrescar_gastos()

    def copiar_gastos_anterior(self):
        """Copia todos los gastos fijos del presupuesto anterior más reciente."""
        prev = self.db.fetch_one(
            "SELECT id, numero FROM presupuestos WHERE id <> ? ORDER BY id DESC LIMIT 1",
            (self.presupuesto_id,),
        )
        if not prev:
            QMessageBox.information(
                self, "Sin historial", "No hay otro presupuesto del cual copiar gastos."
            )
            return
        gastos = self.db.fetch_all(
            "SELECT concepto, monto FROM detalle_presupuesto_gastos WHERE presupuesto_id = ?",
            (prev[0],),
        )
        if not gastos:
            QMessageBox.information(
                self, "Sin gastos",
                f"El presupuesto N°{prev[1]} no tiene gastos fijos registrados.",
            )
            return
        resp = QMessageBox.question(
            self,
            "Copiar gastos",
            f"¿Copiar {len(gastos)} gasto(s) del presupuesto N°{prev[1]}?\n"
            "Se reemplazarán los gastos fijos actuales de este presupuesto.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return
        self.db.execute_query(
            "DELETE FROM detalle_presupuesto_gastos WHERE presupuesto_id = ?",
            (self.presupuesto_id,),
        )
        for concepto, monto in gastos:
            self.db.execute_query(
                "INSERT INTO detalle_presupuesto_gastos (presupuesto_id, concepto, monto, observacion) VALUES (?,?,?,?)",
                (self.presupuesto_id, concepto, monto, f"Copiado de N°{prev[1]}"),
            )
        self._refrescar_gastos()


def _guardar_fila_planilla(db, presupuesto_id, datos, det_id=None):
    """Calcula el costo de una fila de planilla y la inserta o actualiza.

    'datos' debe traer: empleado_id, empleado_nombre, puesto, sucursal_nombre,
    salario_hora, observacion y las 5 claves de horas (horas_regulares, etc.).
    """
    horas = {
        "horas_regulares":       datos.get("horas_regulares", 0.0),
        "horas_festivos":        datos.get("horas_festivos", 0.0),
        "horas_domingos":        datos.get("horas_domingos", 0.0),
        "horas_extra_diurnas":   datos.get("horas_extra_diurnas", 0.0),
        "horas_extra_nocturnas": datos.get("horas_extra_nocturnas", 0.0),
    }
    # Costo laboral completo (igual que el Resumen de Planilla): bruto + patronal (SS, SE, riesgos)
    # + provisiones. costo_total = costo completo; costo_patronal incluye el riesgo profesional.
    costo = calcular_costo_empleado(
        db, datos.get("salario_hora", 0.0), horas, empleado_id=datos.get("empleado_id"))

    campos = (
        datos.get("empleado_id"),
        datos.get("empleado_nombre"),
        datos.get("puesto"),
        datos.get("sucursal_nombre"),
        float(datos.get("salario_hora", 0.0) or 0.0),
        horas["horas_regulares"],
        horas["horas_festivos"],
        horas["horas_domingos"],
        horas["horas_extra_diurnas"],
        horas["horas_extra_nocturnas"],
        costo["salario_bruto"],
        costo["deducciones_colab"],
        costo["costo_patronal_total"],
        costo["provisiones_total"],
        costo["costo_total_completo"],
        datos.get("observacion"),
    )

    if det_id is None:
        db.execute_query(
            """INSERT INTO detalle_presupuesto_planilla
               (presupuesto_id, empleado_id, empleado_nombre, puesto, sucursal_nombre,
                salario_hora, horas_regulares, horas_festivos, horas_domingos,
                horas_extra_diurnas, horas_extra_nocturnas,
                salario_bruto, deducciones_colab, costo_patronal, provisiones, costo_total, observacion)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (presupuesto_id, *campos),
        )
    else:
        db.execute_query(
            """UPDATE detalle_presupuesto_planilla SET
                 empleado_id=?, empleado_nombre=?, puesto=?, sucursal_nombre=?,
                 salario_hora=?, horas_regulares=?, horas_festivos=?, horas_domingos=?,
                 horas_extra_diurnas=?, horas_extra_nocturnas=?,
                 salario_bruto=?, deducciones_colab=?, costo_patronal=?, provisiones=?, costo_total=?, observacion=?
               WHERE id=?""",
            (*campos, det_id),
        )


class CopiarPlanillaDialog(QDialog):
    """Copia las horas de uno o varios períodos de pago como base de la
    planilla del presupuesto, aplicando un multiplicador (quincena→mes)."""

    def __init__(self, db_manager, presupuesto_id, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.presupuesto_id = presupuesto_id
        self.setWindowTitle("Copiar planilla de período(s)")
        self.resize(560, 520)
        self.setStyleSheet(DIALOG_STYLES)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        info = QLabel(
            "Seleccione uno o varios períodos de pago. Las horas de los empleados "
            "se <b>suman</b> entre los períodos marcados y luego se multiplican por "
            "el factor.<br>"
            "<span style='color:#7f8c8d;'>Ej.: 1 quincena × 2 = mes • 2 quincenas × 1 = mes</span>"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addWidget(QLabel("Períodos de pago:"))
        self.list_periodos = QListWidget()
        for p in self.db.fetch_all(
            "SELECT id, nombre, fecha_inicio, fecha_fin FROM periodos_pago ORDER BY fecha_inicio DESC"
        ):
            item = QListWidgetItem(f"{p[1]}  ({p[2]} al {p[3]})")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, p[0])
            self.list_periodos.addItem(item)
        layout.addWidget(self.list_periodos)

        fila = QHBoxLayout()
        fila.addWidget(QLabel("Multiplicador:"))
        self.spin_factor = QDoubleSpinBox()
        self.spin_factor.setRange(0.1, 12.0)
        self.spin_factor.setSingleStep(0.5)
        self.spin_factor.setValue(2.0)
        self.spin_factor.setFixedWidth(90)
        fila.addWidget(self.spin_factor)
        fila.addStretch()
        layout.addLayout(fila)

        self.chk_reemplazar = QCheckBox("Reemplazar la planilla actual del presupuesto")
        self.chk_reemplazar.setChecked(True)
        layout.addWidget(self.chk_reemplazar)

        btns = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("padding: 8px;")
        btn_cancelar.clicked.connect(self.reject)
        btn_ok = QPushButton(" Copiar planilla")
        btn_ok.setStyleSheet(
            "background-color: #2980b9; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px;"
        )
        btn_ok.clicked.connect(self.copiar)
        btns.addStretch()
        btns.addWidget(btn_cancelar)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

        self.setLayout(layout)

    def _periodos_seleccionados(self):
        ids = []
        for i in range(self.list_periodos.count()):
            it = self.list_periodos.item(i)
            if it.checkState() == Qt.Checked:
                ids.append(it.data(Qt.UserRole))
        return ids

    def copiar(self):
        periodos = self._periodos_seleccionados()
        if not periodos:
            QMessageBox.warning(self, "Aviso", "Seleccione al menos un período de pago.")
            return

        factor = float(self.spin_factor.value())
        placeholders = ",".join(["?"] * len(periodos))
        filas = self.db.fetch_all(
            f"""SELECT e.id, e.nombre || ' ' || e.apellido, e.puesto,
                       COALESCE(s.nombre, '—'), e.salario_hora,
                       COALESCE(SUM(h.horas_regulares), 0),
                       COALESCE(SUM(h.horas_festivos), 0),
                       COALESCE(SUM(h.horas_domingos), 0),
                       COALESCE(SUM(h.horas_extra_diurnas), 0),
                       COALESCE(SUM(h.horas_extra_nocturnas), 0)
                FROM horas_empleado h
                JOIN empleados e ON e.id = h.empleado_id
                LEFT JOIN sucursales s ON s.id = e.sucursal_id
                WHERE h.periodo_id IN ({placeholders})
                GROUP BY e.id
                ORDER BY e.apellido, e.nombre""",
            tuple(periodos),
        )

        if not filas:
            QMessageBox.warning(
                self, "Sin datos",
                "Los períodos seleccionados no tienen horas de empleados registradas.",
            )
            return

        if self.chk_reemplazar.isChecked():
            self.db.execute_query(
                "DELETE FROM detalle_presupuesto_planilla WHERE presupuesto_id = ?",
                (self.presupuesto_id,),
            )

        for (eid, nombre, puesto, sucursal, sal_hora,
             h_reg, h_fest, h_dom, h_exd, h_exn) in filas:
            _guardar_fila_planilla(
                self.db, self.presupuesto_id,
                {
                    "empleado_id": eid,
                    "empleado_nombre": nombre,
                    "puesto": puesto,
                    "sucursal_nombre": sucursal,
                    "salario_hora": sal_hora,
                    "horas_regulares":       float(h_reg or 0) * factor,
                    "horas_festivos":        float(h_fest or 0) * factor,
                    "horas_domingos":        float(h_dom or 0) * factor,
                    "horas_extra_diurnas":   float(h_exd or 0) * factor,
                    "horas_extra_nocturnas": float(h_exn or 0) * factor,
                    "observacion": f"Base: {len(periodos)} período(s) × {factor:g}",
                },
            )

        QMessageBox.information(
            self, "Éxito",
            f"Se copiaron {len(filas)} empleado(s) a la planilla del presupuesto.",
        )
        self.accept()


class EmpleadoPlanillaDialog(QDialog):
    """Agrega o edita una fila de empleado en la planilla del presupuesto."""

    def __init__(self, db_manager, presupuesto_id, det_id=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.presupuesto_id = presupuesto_id
        self.det_id = det_id
        self.setWindowTitle(
            "Editar empleado (planilla)" if det_id else "Agregar empleado (planilla)"
        )
        self.resize(460, 520)
        self.setStyleSheet(DIALOG_STYLES)
        self.init_ui()
        if det_id:
            self._cargar()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        form = QFormLayout()
        form.setSpacing(8)

        self.txt_nombre = QLineEdit()
        self.txt_puesto = QLineEdit()
        self.txt_sucursal = QLineEdit()
        form.addRow("Nombre:", self.txt_nombre)
        form.addRow("Puesto:", self.txt_puesto)
        form.addRow("Sucursal:", self.txt_sucursal)

        self.spin_salario = QDoubleSpinBox()
        self.spin_salario.setRange(0.0, 10000.0)
        self.spin_salario.setDecimals(2)
        self.spin_salario.setPrefix("$ ")
        form.addRow("Salario/hora:", self.spin_salario)

        self.spins_horas = {}
        for clave, etiqueta in [
            ("horas_regulares", "Horas regulares:"),
            ("horas_festivos", "Horas festivos:"),
            ("horas_domingos", "Horas domingos:"),
            ("horas_extra_diurnas", "Horas extra diurnas:"),
            ("horas_extra_nocturnas", "Horas extra nocturnas:"),
        ]:
            sp = QDoubleSpinBox()
            sp.setRange(0.0, 1000.0)
            sp.setDecimals(2)
            self.spins_horas[clave] = sp
            form.addRow(etiqueta, sp)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("padding: 8px;")
        btn_cancelar.clicked.connect(self.reject)
        btn_ok = QPushButton("Guardar")
        btn_ok.setStyleSheet(
            "background-color: #27ae60; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px;"
        )
        btn_ok.clicked.connect(self.guardar)
        btns.addStretch()
        btns.addWidget(btn_cancelar)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

        self.setLayout(layout)

    def _cargar(self):
        row = self.db.fetch_one(
            """SELECT empleado_nombre, puesto, sucursal_nombre, salario_hora,
                      horas_regulares, horas_festivos, horas_domingos,
                      horas_extra_diurnas, horas_extra_nocturnas
               FROM detalle_presupuesto_planilla WHERE id = ?""",
            (self.det_id,),
        )
        if not row:
            return
        self.txt_nombre.setText(row[0] or "")
        self.txt_puesto.setText(row[1] or "")
        self.txt_sucursal.setText(row[2] or "")
        self.spin_salario.setValue(float(row[3] or 0))
        for clave, val in zip(
            ["horas_regulares", "horas_festivos", "horas_domingos",
             "horas_extra_diurnas", "horas_extra_nocturnas"],
            row[4:9],
        ):
            self.spins_horas[clave].setValue(float(val or 0))

    def guardar(self):
        nombre = self.txt_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Aviso", "El nombre del empleado es obligatorio.")
            return

        datos = {
            "empleado_id": None,
            "empleado_nombre": nombre,
            "puesto": self.txt_puesto.text().strip(),
            "sucursal_nombre": self.txt_sucursal.text().strip() or "—",
            "salario_hora": self.spin_salario.value(),
            "observacion": "Manual",
        }
        for clave, sp in self.spins_horas.items():
            datos[clave] = sp.value()

        _guardar_fila_planilla(self.db, self.presupuesto_id, datos, self.det_id)
        self.accept()


class GastoPresupuestoDialog(QDialog):
    """Agrega o edita un gasto fijo del presupuesto. Permite elegir un concepto
    del historial/catálogo (prellenando el último monto usado) o crear uno nuevo."""

    def __init__(self, db_manager, presupuesto_id, det_id=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.presupuesto_id = presupuesto_id
        self.det_id = det_id
        self.setWindowTitle("Editar gasto fijo" if det_id else "Agregar gasto fijo")
        self.resize(440, 260)
        self.setStyleSheet(DIALOG_STYLES)
        self.init_ui()
        if det_id:
            self._cargar()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        info = QLabel(
            "Elija un concepto del historial o escriba uno nuevo. "
            "Al seleccionar un concepto ya usado se sugiere su último monto."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(8)

        self.cmb_concepto = QComboBox()
        self.cmb_concepto.setEditable(True)
        self._montos_historial = {}
        for concepto in self._conceptos_historial():
            self.cmb_concepto.addItem(concepto)
        self.cmb_concepto.setCurrentText("")
        self.cmb_concepto.currentTextChanged.connect(self._sugerir_monto)
        form.addRow("Concepto:", self.cmb_concepto)

        self.spin_monto = QDoubleSpinBox()
        self.spin_monto.setRange(0.0, 9999999.99)
        self.spin_monto.setDecimals(2)
        self.spin_monto.setPrefix("$ ")
        form.addRow("Monto mensual:", self.spin_monto)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("padding: 8px;")
        btn_cancelar.clicked.connect(self.reject)
        btn_ok = QPushButton("Guardar")
        btn_ok.setStyleSheet(
            "background-color: #27ae60; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px;"
        )
        btn_ok.clicked.connect(self.guardar)
        btns.addStretch()
        btns.addWidget(btn_cancelar)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

        self.setLayout(layout)

    def _conceptos_historial(self):
        """Conceptos del catálogo + los ya usados en presupuestos, con su último
        monto como sugerencia."""
        conceptos = []
        for (c,) in self.db.fetch_all(
            "SELECT concepto FROM gastos_fijos_catalogo ORDER BY concepto"
        ):
            conceptos.append(c)
        # Último monto usado por concepto (cualquier presupuesto)
        for concepto, monto in self.db.fetch_all(
            """SELECT concepto, monto FROM detalle_presupuesto_gastos
               WHERE id IN (SELECT MAX(id) FROM detalle_presupuesto_gastos GROUP BY concepto)"""
        ):
            self._montos_historial[concepto] = float(monto or 0)
            if concepto not in conceptos:
                conceptos.append(concepto)
        return conceptos

    def _sugerir_monto(self, texto):
        # Solo sugiere al agregar (no pisar el monto al editar uno existente)
        if self.det_id:
            return
        if texto in self._montos_historial and self.spin_monto.value() == 0:
            self.spin_monto.setValue(self._montos_historial[texto])

    def _cargar(self):
        row = self.db.fetch_one(
            "SELECT concepto, monto FROM detalle_presupuesto_gastos WHERE id = ?",
            (self.det_id,),
        )
        if not row:
            return
        self.cmb_concepto.setCurrentText(row[0] or "")
        self.spin_monto.setValue(float(row[1] or 0))

    def guardar(self):
        concepto = self.cmb_concepto.currentText().strip()
        if not concepto:
            QMessageBox.warning(self, "Aviso", "El concepto del gasto es obligatorio.")
            return
        monto = self.spin_monto.value()

        # Registrar el concepto en el catálogo/historial para reutilizarlo
        self.db.execute_query(
            "INSERT OR IGNORE INTO gastos_fijos_catalogo (concepto) VALUES (?)",
            (concepto,),
        )

        if self.det_id is None:
            self.db.execute_query(
                "INSERT INTO detalle_presupuesto_gastos (presupuesto_id, concepto, monto, observacion) VALUES (?,?,?,?)",
                (self.presupuesto_id, concepto, monto, "Manual"),
            )
        else:
            self.db.execute_query(
                "UPDATE detalle_presupuesto_gastos SET concepto=?, monto=? WHERE id=?",
                (concepto, monto, self.det_id),
            )
        self.accept()
