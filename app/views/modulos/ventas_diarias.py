# [CREAR ARCHIVO: app/views/modulos/ventas_diarias.py]
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QDateEdit,
    QMessageBox,
    QHeaderView,
    QFrame,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont

from app.controllers.kardex_controller import KardexController


class VentasDiariasView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.registro_actual_id = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)

        # --- TÍTULO ---
        lbl_title = QLabel("Registro de Cantidades Vendidas (Diario)")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        main_layout.addWidget(lbl_title)

        # --- CONTROL DE FECHA ---
        control_frame = QFrame()
        control_frame.setStyleSheet(
            "background-color: #f8f9fa; border: 1px solid #bdc3c7; border-radius: 5px;"
        )
        control_layout = QHBoxLayout(control_frame)

        lbl_date = QLabel("Fecha de Venta:")
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setDisplayFormat("yyyy-MM-dd")
        self.date_picker.dateChanged.connect(self.cargar_datos_fecha)

        # Botón para refrescar
        btn_refresh = QPushButton(" Cargar Datos")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(
            "background-color: #3498db; color: white; border: none; padding: 5px 15px; border-radius: 3px;"
        )
        btn_refresh.clicked.connect(self.cargar_datos_fecha)

        # Etiqueta de estado (Si ya se descontó inventario)
        self.lbl_status = QLabel("Estado: -")
        self.lbl_status.setStyleSheet(
            "font-weight: bold; color: #7f8c8d; margin-left: 15px;"
        )

        control_layout.addWidget(lbl_date)
        control_layout.addWidget(self.date_picker)
        control_layout.addWidget(btn_refresh)
        control_layout.addWidget(self.lbl_status)
        control_layout.addStretch()

        main_layout.addWidget(control_frame)

        # --- TABLA DE ITEMS ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Código", "Producto", "Cantidad Vendida"]
        )
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnHidden(0, True)  # Ocultar ID

        # Estilo de la tabla
        self.table.setStyleSheet("""
            QTableWidget { gridline-color: #ecf0f1; }
            QHeaderView::section { background-color: #34495e; color: white; padding: 5px; }
        """)

        main_layout.addWidget(self.table)

        # --- BOTONES DE ACCIÓN ---
        btn_layout = QHBoxLayout()

        self.btn_save = QPushButton("Guardar Cantidades")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setStyleSheet("""
            QPushButton { background-color: #27ae60; color: white; font-weight: bold; padding: 10px 20px; border-radius: 4px; }
            QPushButton:hover { background-color: #2ecc71; }
        """)
        self.btn_save.clicked.connect(self.guardar_cambios)

        # Descuenta del stock los insumos consumidos por las ventas del día (Kardex, tipo VENTA)
        self.btn_process = QPushButton("Actualizar Inventario (Kardex)")
        self.btn_process.setCursor(Qt.PointingHandCursor)
        self.btn_process.setStyleSheet("""
            QPushButton { background-color: #e67e22; color: white; font-weight: bold; padding: 10px 20px; border-radius: 4px; }
            QPushButton:hover { background-color: #d35400; }
        """)
        self.btn_process.clicked.connect(self.procesar_inventario)

        # Reabre un día ya procesado: repone el stock descontado para poder corregir las cantidades
        self.btn_reopen = QPushButton("Reabrir Día (Revertir Inventario)")
        self.btn_reopen.setCursor(Qt.PointingHandCursor)
        self.btn_reopen.setStyleSheet("""
            QPushButton { background-color: #7f8c8d; color: white; font-weight: bold; padding: 10px 20px; border-radius: 4px; }
            QPushButton:hover { background-color: #636e72; }
            QPushButton:disabled { background-color: #bdc3c7; }
        """)
        self.btn_reopen.clicked.connect(self.reabrir_dia)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_reopen)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_process)

        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)
        self.cargar_datos_fecha()

    def cargar_datos_fecha(self):
        """Carga los items del menú y cruza con las ventas guardadas de la fecha seleccionada."""
        fecha = self.date_picker.date().toString("yyyy-MM-dd")

        # 1. Verificar si existe registro diario
        header = self.db.fetch_one(
            "SELECT id, inventario_descontado FROM registro_ventas_diarias WHERE fecha = ?",
            (fecha,),
        )

        items_data = []  # Lista de tuplas: (id_item, codigo, nombre, cantidad)
        procesado = False

        if header:
            # Día existente: Cargar cantidades guardadas
            self.registro_actual_id = header[0]
            procesado = bool(header[1])

            if procesado:
                self.lbl_status.setText("Estado: INVENTARIO ACTUALIZADO (Cerrado)")
                self.lbl_status.setStyleSheet(
                    "color: #27ae60; font-weight: bold; margin-left: 15px;"
                )
                self.btn_process.setEnabled(False)  # Ya se procesó
                self.btn_save.setEnabled(False)     # Día cerrado: para corregir hay que reabrirlo
                self.btn_reopen.setEnabled(True)
            else:
                self.lbl_status.setText("Estado: BORRADOR (Inventario Pendiente)")
                self.lbl_status.setStyleSheet(
                    "color: #e67e22; font-weight: bold; margin-left: 15px;"
                )
                self.btn_process.setEnabled(True)
                self.btn_save.setEnabled(True)
                self.btn_reopen.setEnabled(False)

            # Left Join para traer todos los items, incluso los que no tienen venta registrada ese día
            query = """
                SELECT m.id, m.codigo, m.nombre, COALESCE(d.cantidad, 0)
                FROM menu_items m
                LEFT JOIN detalle_ventas_diarias d 
                ON m.id = d.menu_item_id AND d.registro_diario_id = ?
                WHERE COALESCE(m.es_componente, 0) = 0
                ORDER BY m.nombre ASC
            """
            items_data = self.db.fetch_all(query, (self.registro_actual_id,))

        else:
            # Nuevo Día
            self.registro_actual_id = None
            self.lbl_status.setText("Estado: NUEVO REGISTRO")
            self.lbl_status.setStyleSheet(
                "color: #3498db; font-weight: bold; margin-left: 15px;"
            )
            self.btn_process.setEnabled(False)  # Debe guardar primero
            self.btn_save.setEnabled(True)
            self.btn_reopen.setEnabled(False)
            procesado = False

            query = (
                "SELECT id, codigo, nombre, 0 FROM menu_items "
                "WHERE COALESCE(es_componente, 0) = 0 ORDER BY nombre ASC"
            )
            items_data = self.db.fetch_all(query)

        # 2. Llenar Tabla
        self.table.setRowCount(0)
        for i, (mid, cod, nom, cant) in enumerate(items_data):
            self.table.insertRow(i)
            for col, valor in enumerate((mid, cod, nom)):
                it = QTableWidgetItem(str(valor))
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)  # solo la cantidad se edita
                self.table.setItem(i, col, it)

            # Cantidad Editable (bloqueada si el día ya actualizó el inventario)
            qty_item = QTableWidgetItem(str(cant))
            qty_item.setBackground(QColor("#f0f0f0" if procesado else "#e8f8f5"))
            qty_item.setTextAlignment(Qt.AlignCenter)
            qty_item.setFont(QFont("Arial", 10, QFont.Bold))
            if procesado:
                qty_item.setFlags(qty_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 3, qty_item)

    def guardar_cambios(self):
        fecha = self.date_picker.date().toString("yyyy-MM-dd")
        detalles = []  # Lista de (item_id, cantidad)

        # Recolectar datos
        for row in range(self.table.rowCount()):
            try:
                qty_text = self.table.item(row, 3).text()
                qty = float(qty_text) if qty_text else 0.0
                if qty > 0:
                    item_id = int(self.table.item(row, 0).text())
                    detalles.append((item_id, qty))
            except ValueError:
                QMessageBox.warning(
                    self, "Error", f"Cantidad inválida en la fila {row + 1}"
                )
                return

        try:
            # 1. Crear o Actualizar Cabecera
            if not self.registro_actual_id:
                cur = self.db.execute_query(
                    "INSERT INTO registro_ventas_diarias (fecha) VALUES (?)", (fecha,)
                )
                self.registro_actual_id = cur.lastrowid

            # 2. Limpiar detalles anteriores (método simple de actualización)
            self.db.execute_query(
                "DELETE FROM detalle_ventas_diarias WHERE registro_diario_id=?",
                (self.registro_actual_id,),
            )

            # 3. Insertar nuevos detalles
            if detalles:
                query_ins = "INSERT INTO detalle_ventas_diarias (registro_diario_id, menu_item_id, cantidad) VALUES (?,?,?)"
                datos_batch = [(self.registro_actual_id, d[0], d[1]) for d in detalles]
                self.db.cursor.executemany(query_ins, datos_batch)
                self.db.conn.commit()

            QMessageBox.information(
                self, "Éxito", "Cantidades guardadas correctamente."
            )
            self.cargar_datos_fecha()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _cantidades_en_tabla(self):
        """{menu_item_id: cantidad} de lo que muestra la tabla (solo cantidades > 0)."""
        out = {}
        for row in range(self.table.rowCount()):
            try:
                qty = float(self.table.item(row, 3).text() or 0)
            except ValueError:
                return None
            if qty > 0:
                out[int(self.table.item(row, 0).text())] = qty
        return out

    def _hay_cambios_sin_guardar(self):
        en_tabla = self._cantidades_en_tabla()
        if en_tabla is None:
            return True
        guardado = {
            mid: float(c)
            for mid, c in self.db.fetch_all(
                "SELECT menu_item_id, cantidad FROM detalle_ventas_diarias WHERE registro_diario_id=? AND cantidad > 0",
                (self.registro_actual_id,),
            )
        }
        return {k: round(v, 6) for k, v in en_tabla.items()} != {k: round(v, 6) for k, v in guardado.items()}

    def procesar_inventario(self):
        """Descuenta del stock los insumos de las ventas del día (Kardex, tipo VENTA)."""
        if not self.registro_actual_id:
            QMessageBox.warning(self, "Aviso", "Guarde primero las cantidades del día.")
            return
        if self._hay_cambios_sin_guardar():
            QMessageBox.warning(
                self, "Aviso",
                "Hay cantidades sin guardar (o inválidas). Pulse «Guardar Cantidades» antes de actualizar el inventario.",
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirmar Actualización",
            "Se descontarán del inventario los insumos consumidos por las ventas de este día, según las recetas "
            "(incluidas las sub-recetas).\n\nEl día quedará cerrado; si necesita corregirlo podrá usar "
            "«Reabrir Día», que repone el stock descontado.\n\n¿Desea continuar?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            res = KardexController(self.db).procesar_ventas_diarias(self.registro_actual_id)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo actualizar el inventario:\n{e}")
            return

        msg = f"Inventario actualizado: {res['movimientos']} insumo(s) descontado(s) del stock."
        if res["sin_receta"]:
            msg += ("\n\nPlatos vendidos SIN receta (no descontaron nada):\n• " + "\n• ".join(res["sin_receta"]))
        if res["negativos"]:
            msg += ("\n\nInsumos que quedaron con stock NEGATIVO (revise compras o haga un conteo):\n• "
                    + "\n• ".join(res["negativos"]))
        QMessageBox.information(self, "Procesado", msg)
        self.cargar_datos_fecha()

    def reabrir_dia(self):
        """Repone el stock descontado por el día y lo deja editable otra vez."""
        if not self.registro_actual_id:
            return
        reply = QMessageBox.question(
            self,
            "Reabrir día",
            "Se devolverá al inventario lo que descontaron las ventas de este día y el registro volverá a estado "
            "BORRADOR para poder corregirlo.\n\nDespués de corregir y guardar deberá pulsar «Actualizar Inventario "
            "(Kardex)» otra vez.\n\n¿Desea continuar?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            repuestos = KardexController(self.db).revertir_ventas_diarias(self.registro_actual_id)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo reabrir el día:\n{e}")
            return
        QMessageBox.information(
            self, "Día reabierto",
            f"Día reabierto. Se repusieron {repuestos} insumo(s) al inventario." if repuestos
            else "Día reabierto. No había movimientos de inventario que revertir.",
        )
        self.cargar_datos_fecha()
