# [FILE: app/views/modulos/compras_crud.py]
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QMessageBox,
    QLabel,
    QDoubleSpinBox,
    QDateEdit,
    QGroupBox,
    QTreeWidget,
    QTreeWidgetItem,
    QFrame,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont, QPalette
from datetime import datetime, timedelta
import calendar

from app.controllers.kardex_controller import KardexController
from app.styles import COLORS


class DetalleCompraDialog(QDialog):
    def __init__(self, db, compra_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.compra_id = compra_id
        self.setWindowTitle(f"Detalle de Compra #{compra_id}")
        self.resize(600, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        lbl_titulo = QLabel(f"<h2>Productos de la Compra #{self.compra_id}</h2>")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        lbl_titulo.setStyleSheet(f"color: {COLORS['primary']};")
        layout.addWidget(lbl_titulo)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Insumo / Presentación", "Cantidad", "Precio Unit.", "Subtotal"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.lbl_total = QLabel("Total: $0.00")
        self.lbl_total.setAlignment(Qt.AlignRight)
        self.lbl_total.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.lbl_total)

        # --- MODIFICADO: Mostrar si está enlazado a un presupuesto ---
        info_compra = self.db.fetch_one(
            "SELECT tipo_pago, presupuesto_id FROM compras WHERE id=?",
            (self.compra_id,),
        )
        tipo_pago_str = info_compra[0] if info_compra and info_compra[0] else "-"
        pres_id = info_compra[1] if info_compra and info_compra[1] else "Ninguno"

        lbl_info = QLabel(
            f"<b>Método de Pago:</b> {tipo_pago_str}  |  <b>Presupuesto Asociado:</b> #{pres_id}"
        )
        layout.addWidget(lbl_info)

        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        self.setLayout(layout)
        self.cargar_datos()

    def cargar_datos(self):
        query = """
            SELECT i.nombre, pc.nombre, dc.cantidad, dc.precio_unitario, dc.subtotal
            FROM detalle_compras dc
            JOIN presentaciones_compra pc ON dc.presentacion_id = pc.id
            JOIN insumos i ON pc.insumo_id = i.id
            WHERE dc.compra_id = ?
        """
        rows = self.db.fetch_all(query, (self.compra_id,))

        self.table.setRowCount(0)
        gran_total = 0.0

        for r, row in enumerate(rows):
            insumo_nombre = row[0]
            presentacion = row[1]
            cantidad = row[2]
            precio = row[3]
            subtotal = row[4]

            gran_total += subtotal

            self.table.insertRow(r)
            self.table.setItem(
                r, 0, QTableWidgetItem(f"{insumo_nombre} ({presentacion})")
            )
            self.table.setItem(r, 1, QTableWidgetItem(str(cantidad)))
            self.table.setItem(r, 2, QTableWidgetItem(f"${precio:.2f}"))
            self.table.setItem(r, 3, QTableWidgetItem(f"${subtotal:.2f}"))

        self.lbl_total.setText(f"Total Compra: ${gran_total:.2f}")


class ComprasCRUD(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        header = QLabel("<h2>Gestión de Compras e Inventario</h2>")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(f"color: {COLORS['text']};")
        layout.addWidget(header)

        self.tabs = QTabWidget()

        self.tab_compras = TabGestionCompras(self.db)
        self.tab_proveedores = TabProveedores(self.db)
        self.tab_resumen = TabResumenSemanal(self.db)
        self.tab_resumen_mensual = TabResumenMensual(self.db)

        self.tabs.addTab(self.tab_compras, "1. Registro de Compras")
        self.tabs.addTab(self.tab_proveedores, "2. Proveedores")
        self.tabs.addTab(self.tab_resumen, "3. Resumen Semanal")
        self.tabs.addTab(self.tab_resumen_mensual, "4. Resumen Mensual")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def cargar_datos(self):
        self.tab_compras.cargar_compras()
        self.tab_proveedores.cargar_proveedores()
        self.tab_resumen.cargar_datos()
        self.tab_resumen_mensual.cargar_datos()


class TabGestionCompras(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        btn_nueva = QPushButton("Nueva Compra / Pedido")
        btn_nueva.setProperty("class", "btn-success")
        btn_nueva.clicked.connect(self.nueva_compra)

        btn_recibir = QPushButton("Marcar como RECIBIDO (Sumar a Stock)")
        btn_recibir.setStyleSheet(
            f"background-color: {COLORS['success']}; color: white;"
        )
        btn_recibir.clicked.connect(self.recibir_compra)

        btn_ver = QPushButton("Ver Detalle")
        btn_ver.clicked.connect(self.ver_detalle)

        btn_editar = QPushButton("Editar")
        btn_editar.setStyleSheet(
            f"background-color: {COLORS['warning']}; color: black;"
        )
        btn_editar.clicked.connect(self.editar_compra)

        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.setStyleSheet(
            f"background-color: {COLORS['danger']}; color: white;"
        )
        btn_eliminar.clicked.connect(self.eliminar_compra)

        btn_layout.addWidget(btn_nueva)
        btn_layout.addWidget(btn_recibir)
        btn_layout.addWidget(btn_ver)
        btn_layout.addWidget(btn_editar)
        btn_layout.addWidget(btn_eliminar)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Proveedor", "Fecha", "Tipo Pago", "Total", "Estado", "Acción"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.cargar_compras()

    def cargar_compras(self):
        query = """
            SELECT c.id, p.nombre, c.fecha_compra, c.total, c.estado, c.tipo_pago
            FROM compras c JOIN proveedores p ON c.proveedor_id = p.id 
            ORDER BY c.id DESC
        """
        rows = self.db.fetch_all(query)
        self.table.setRowCount(0)
        for r, row in enumerate(rows):
            self.table.insertRow(r)

            id_compra = str(row[0])
            proveedor = row[1]
            fecha = row[2]
            total = row[3]
            estado = row[4]
            tipo_pago = row[5] if row[5] else "CONTADO"

            self.table.setItem(r, 0, QTableWidgetItem(id_compra))
            self.table.setItem(r, 1, QTableWidgetItem(proveedor))
            self.table.setItem(r, 2, QTableWidgetItem(fecha))
            self.table.setItem(r, 3, QTableWidgetItem(tipo_pago))
            self.table.setItem(r, 4, QTableWidgetItem(f"${total:.2f}"))

            item_estado = QTableWidgetItem(estado)
            self.table.setItem(r, 5, item_estado)

            if estado == "PENDIENTE":
                item_estado.setBackground(Qt.yellow)
                item_estado.setForeground(Qt.black)
            elif estado == "RECIBIDO":
                item_estado.setBackground(Qt.green)
                item_estado.setForeground(Qt.black)

            self.table.setItem(r, 6, QTableWidgetItem(""))

    def nueva_compra(self):
        if NuevaCompraDialog(self.db, parent=self).exec_():
            self.cargar_compras()

    def recibir_compra(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "Aviso", "Seleccione una compra")

        cid = self.table.item(row, 0).text()
        estado = self.table.item(row, 5).text()

        if estado == "RECIBIDO":
            return QMessageBox.information(
                self, "Info", "Esta compra ya fue recibida e inventariada."
            )

        if (
            QMessageBox.question(
                self,
                "Confirmar",
                "¿Confirmar recepción? Esto sumará los insumos al inventario.",
            )
            == QMessageBox.Yes
        ):
            self.procesar_recepcion(cid)

    def procesar_recepcion(self, compra_id):
        try:
            kardex = KardexController(self.db)
            detalles = self.db.fetch_all(
                "SELECT presentacion_id, cantidad FROM detalle_compras WHERE compra_id=?",
                (compra_id,),
            )

            for pres_id, cant_compra in detalles:
                pres = self.db.fetch_one(
                    "SELECT insumo_id, cantidad_contenido, nombre FROM presentaciones_compra WHERE id=?",
                    (pres_id,),
                )
                if pres:
                    insumo_id, contenido_unitario, nombre_pres = pres
                    cantidad_total_a_sumar = cant_compra * contenido_unitario

                    kardex.registrar_movimiento(
                        insumo_id=insumo_id,
                        cantidad=cantidad_total_a_sumar,
                        tipo="COMPRA",
                        referencia_id=compra_id,
                        observacion=f"Entrada por Compra (Presentación: {nombre_pres})",
                    )

            self.db.execute_query(
                "UPDATE compras SET estado='RECIBIDO' WHERE id=?", (compra_id,)
            )
            QMessageBox.information(
                self,
                "Éxito",
                "Inventario actualizado y registrado en Kardex correctamente.",
            )
            self.cargar_compras()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def ver_detalle(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(
                self, "Aviso", "Seleccione una compra de la lista para ver el detalle."
            )
        compra_id = self.table.item(row, 0).text()
        dialog = DetalleCompraDialog(self.db, compra_id, parent=self)
        dialog.exec_()

    def editar_compra(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(
                self, "Aviso", "Seleccione una compra para editar."
            )

        cid = self.table.item(row, 0).text()
        estado = self.table.item(row, 5).text()

        if estado == "RECIBIDO":
            return QMessageBox.warning(
                self,
                "Acción Denegada",
                "No se puede editar una compra ya RECIBIDA e inventariada.\nEsto afectaría el stock histórico.",
            )

        dialog = NuevaCompraDialog(self.db, compra_id=cid, parent=self)
        if dialog.exec_():
            self.cargar_compras()

    def eliminar_compra(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(
                self, "Aviso", "Seleccione una compra para eliminar."
            )

        cid = self.table.item(row, 0).text()
        estado = self.table.item(row, 5).text()

        if estado == "RECIBIDO":
            return QMessageBox.critical(
                self,
                "Error",
                "No se puede eliminar una compra RECIBIDA.\nEl stock ya fue sumado al inventario.",
            )

        confirm = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de eliminar la compra #{cid}? Esta acción es irreversible.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if confirm == QMessageBox.Yes:
            try:
                self.db.execute_query("DELETE FROM compras WHERE id=?", (cid,))
                self.cargar_compras()
                QMessageBox.information(self, "Éxito", "Compra eliminada.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar: {str(e)}")


class NuevaCompraDialog(QDialog):
    def __init__(self, db, compra_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.compra_id = compra_id

        titulo = "Editar Compra" if self.compra_id else "Registrar Compra"
        self.setWindowTitle(titulo)

        self.resize(600, 550)
        self.detalles = []
        self.init_ui()

        if self.compra_id:
            self.cargar_datos_existentes()

    def init_ui(self):
        layout = QVBoxLayout()

        form = QFormLayout()
        self.cmb_prov = QComboBox()
        self.cargar_proveedores()
        self.date_picker = QDateEdit(QDate.currentDate())
        self.date_picker.setCalendarPopup(True)
        self.cmb_tipo_pago = QComboBox()
        self.cmb_tipo_pago.addItems(["CONTADO", "CHEQUE", "TRANSFERENCIA", "CREDITO"])

        # --- NUEVO: Combo de Presupuesto ---
        self.cmb_presupuesto = QComboBox()
        self.cargar_presupuestos()

        form.addRow("Proveedor:", self.cmb_prov)
        form.addRow("Fecha Compra:", self.date_picker)
        form.addRow("Tipo de Pago:", self.cmb_tipo_pago)
        form.addRow("Vincular a Presupuesto:", self.cmb_presupuesto)  # --- NUEVO ---
        layout.addLayout(form)

        grp_items = QGroupBox("Agregar Productos")
        l_items = QHBoxLayout()
        self.cmb_pres = QComboBox()
        self.cargar_presentaciones()
        self.spin_cant = QDoubleSpinBox()
        self.spin_cant.setPrefix("Cant: ")
        self.spin_precio = QDoubleSpinBox()
        self.spin_precio.setPrefix("$ ")
        self.spin_precio.setMaximum(99999)

        btn_add = QPushButton("+")
        btn_add.clicked.connect(self.agregar_item_lista)

        l_items.addWidget(self.cmb_pres, 2)
        l_items.addWidget(self.spin_cant)
        l_items.addWidget(self.spin_precio)
        l_items.addWidget(btn_add)
        grp_items.setLayout(l_items)
        layout.addWidget(grp_items)

        self.table_det = QTableWidget()
        self.table_det.setColumnCount(4)
        self.table_det.setHorizontalHeaderLabels(
            ["Producto", "Cant", "Precio U.", "Subtotal"]
        )
        self.table_det.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_det.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_det.setSelectionMode(QTableWidget.SingleSelection)
        self.table_det.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table_det)

        hbox_acciones = QHBoxLayout()

        btn_editar_linea = QPushButton("Editar Línea Seleccionada")
        btn_editar_linea.setStyleSheet(
            f"background-color: {COLORS['warning']}; color: black;"
        )
        btn_editar_linea.clicked.connect(self.editar_item_lista)

        btn_borrar_linea = QPushButton("Borrar Línea")
        btn_borrar_linea.setStyleSheet(
            f"background-color: {COLORS['danger']}; color: white;"
        )
        btn_borrar_linea.clicked.connect(self.eliminar_item_lista)

        hbox_acciones.addWidget(btn_editar_linea)
        hbox_acciones.addWidget(btn_borrar_linea)
        hbox_acciones.addStretch()

        layout.addLayout(hbox_acciones)

        self.lbl_total = QLabel("<h2>Total: $0.00</h2>")
        self.lbl_total.setAlignment(Qt.AlignRight)
        layout.addWidget(self.lbl_total)

        btn_save = QPushButton("Guardar Compra")
        btn_save.clicked.connect(self.guardar_bd)
        layout.addWidget(btn_save)

        self.setLayout(layout)

    def cargar_proveedores(self):
        for r in self.db.fetch_all("SELECT id, nombre FROM proveedores"):
            self.cmb_prov.addItem(r[1], r[0])

    # --- NUEVO ---
    def cargar_presupuestos(self):
        self.cmb_presupuesto.addItem("Ninguno / Sin Presupuesto", None)
        query = "SELECT id, numero, mes, anio FROM presupuestos ORDER BY id DESC"
        for r in self.db.fetch_all(query):
            self.cmb_presupuesto.addItem(f"Presupuesto N° {r[1]} ({r[2]}/{r[3]})", r[0])

    def cargar_presentaciones(self):
        query = """
            SELECT p.id, p.nombre, i.nombre, p.precio_compra 
            FROM presentaciones_compra p JOIN insumos i ON p.insumo_id = i.id
        """
        for r in self.db.fetch_all(query):
            self.cmb_pres.addItem(f"{r[2]} - {r[1]}", {"id": r[0], "precio": r[3]})

    def agregar_item_lista(self):
        data = self.cmb_pres.currentData()
        pres_id = data["id"]
        texto = self.cmb_pres.currentText()
        cant = self.spin_cant.value()
        precio = self.spin_precio.value()

        if cant <= 0:
            return

        subtotal = cant * precio
        self.detalles.append(
            {
                "pres_id": pres_id,
                "texto": texto,
                "cant": cant,
                "precio": precio,
                "subtotal": subtotal,
            }
        )
        self.actualizar_tabla()

    def actualizar_tabla(self):
        self.table_det.setRowCount(0)
        total_global = 0
        for r, d in enumerate(self.detalles):
            self.table_det.insertRow(r)
            self.table_det.setItem(r, 0, QTableWidgetItem(d["texto"]))
            self.table_det.setItem(r, 1, QTableWidgetItem(str(d["cant"])))
            self.table_det.setItem(r, 2, QTableWidgetItem(f"${d['precio']:.2f}"))
            self.table_det.setItem(r, 3, QTableWidgetItem(f"${d['subtotal']:.2f}"))
            total_global += d["subtotal"]
        self.lbl_total.setText(f"<h2>Total: ${total_global:.2f}</h2>")

    def cargar_datos_existentes(self):
        # --- MODIFICADO: Seleccionar también presupuesto_id ---
        query_header = "SELECT proveedor_id, fecha_compra, tipo_pago, presupuesto_id FROM compras WHERE id=?"
        header = self.db.fetch_one(query_header, (self.compra_id,))

        if header:
            index_prov = self.cmb_prov.findData(header[0])
            if index_prov >= 0:
                self.cmb_prov.setCurrentIndex(index_prov)

            fecha_dt = datetime.strptime(header[1], "%Y-%m-%d")
            self.date_picker.setDate(fecha_dt.date())

            tipo_pago = header[2] if header[2] else "CONTADO"
            index_pago = self.cmb_tipo_pago.findText(tipo_pago)
            if index_pago >= 0:
                self.cmb_tipo_pago.setCurrentIndex(index_pago)

            # --- NUEVO: Setear el presupuesto_id en el combo ---
            pres_id = header[3]
            index_pres = self.cmb_presupuesto.findData(pres_id)
            if index_pres >= 0:
                self.cmb_presupuesto.setCurrentIndex(index_pres)

        query_det = """
            SELECT dc.presentacion_id, pc.nombre, i.nombre, dc.cantidad, dc.precio_unitario, dc.subtotal 
            FROM detalle_compras dc
            JOIN presentaciones_compra pc ON dc.presentacion_id = pc.id
            JOIN insumos i ON pc.insumo_id = i.id
            WHERE dc.compra_id = ?
        """
        rows = self.db.fetch_all(query_det, (self.compra_id,))

        for r in rows:
            pres_id = r[0]
            nombre_pres = r[1]
            nombre_insumo = r[2]
            cantidad = r[3]
            precio = r[4]
            subtotal = r[5]

            item_text = f"{nombre_insumo} - {nombre_pres}"

            self.detalles.append(
                {
                    "pres_id": pres_id,
                    "texto": item_text,
                    "cant": cantidad,
                    "precio": precio,
                    "subtotal": subtotal,
                }
            )

        self.actualizar_tabla()

    def eliminar_item_lista(self):
        row = self.table_det.currentRow()
        if row < 0:
            return QMessageBox.warning(
                self, "Aviso", "Seleccione un producto de la lista para borrar."
            )
        self.detalles.pop(row)
        self.actualizar_tabla()

    def editar_item_lista(self):
        row = self.table_det.currentRow()
        if row < 0:
            return QMessageBox.warning(
                self, "Aviso", "Seleccione un producto de la lista para editar."
            )
        item = self.detalles[row]
        pres_id_a_editar = item["pres_id"]
        index_combo = -1
        for i in range(self.cmb_pres.count()):
            data = self.cmb_pres.itemData(i)
            if data and data["id"] == pres_id_a_editar:
                index_combo = i
                break

        if index_combo != -1:
            self.cmb_pres.setCurrentIndex(index_combo)
            self.spin_cant.setValue(item["cant"])
            self.spin_precio.setValue(item["precio"])
            self.detalles.pop(row)
            self.actualizar_tabla()
            self.cmb_pres.setFocus()
        else:
            QMessageBox.warning(
                self, "Error", "No se encontró la presentación original."
            )

    def guardar_bd(self):
        if not self.detalles:
            return QMessageBox.warning(self, "Error", "La lista de compra está vacía.")

        prov_id = self.cmb_prov.currentData()
        fecha = self.date_picker.date().toString("yyyy-MM-dd")
        total = sum(d["subtotal"] for d in self.detalles)
        tipo_pago = self.cmb_tipo_pago.currentText()
        pres_id = self.cmb_presupuesto.currentData()  # --- NUEVO ---

        try:
            if self.compra_id:
                # --- MODIFICADO: Guardar presupuesto_id ---
                self.db.execute_query(
                    "UPDATE compras SET proveedor_id=?, fecha_compra=?, total=?, tipo_pago=?, presupuesto_id=? WHERE id=?",
                    (prov_id, fecha, total, tipo_pago, pres_id, self.compra_id),
                )
                self.db.execute_query(
                    "DELETE FROM detalle_compras WHERE compra_id=?", (self.compra_id,)
                )
                compra_actual = self.compra_id
                msg = "Compra actualizada correctamente."
            else:
                # --- MODIFICADO: Insertar presupuesto_id ---
                cur = self.db.execute_query(
                    "INSERT INTO compras (proveedor_id, fecha_compra, total, estado, tipo_pago, presupuesto_id) VALUES (?,?,?,?,?,?)",
                    (prov_id, fecha, total, "PENDIENTE", tipo_pago, pres_id),
                )
                compra_actual = cur.lastrowid
                msg = "Compra registrada correctamente."

            for d in self.detalles:
                self.db.execute_query(
                    "INSERT INTO detalle_compras (compra_id, presentacion_id, cantidad, precio_unitario, subtotal) VALUES (?,?,?,?,?)",
                    (
                        compra_actual,
                        d["pres_id"],
                        d["cant"],
                        d["precio"],
                        d["subtotal"],
                    ),
                )

            QMessageBox.information(self, "Éxito", msg)
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class TabProveedores(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QHBoxLayout()
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre Proveedor")
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["PROVEEDOR", "SUPERMERCADO"])
        btn_add = QPushButton("Agregar")
        btn_add.clicked.connect(self.agregar)

        form_layout.addWidget(self.txt_nombre)
        form_layout.addWidget(self.cmb_tipo)
        form_layout.addWidget(btn_add)
        layout.addLayout(form_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Tipo"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.cargar_proveedores()

    def cargar_proveedores(self):
        rows = self.db.fetch_all("SELECT id, nombre, tipo FROM proveedores")
        self.table.setRowCount(0)
        for r, row in enumerate(rows):
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(row[0])))
            self.table.setItem(r, 1, QTableWidgetItem(row[1]))
            self.table.setItem(r, 2, QTableWidgetItem(row[2]))

    def agregar(self):
        nom = self.txt_nombre.text()
        tipo = self.cmb_tipo.currentText()
        if nom:
            self.db.execute_query(
                "INSERT INTO proveedores (nombre, tipo) VALUES (?,?)", (nom, tipo)
            )
            self.cargar_proveedores()
            self.txt_nombre.clear()


class TabResumenSemanal(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.init_ui()
        self.cargar_datos()

    def init_ui(self):
        filter_frame = QFrame()
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_frame.setLayout(filter_layout)

        lbl_fecha = QLabel("Seleccione una fecha de la semana:")
        lbl_fecha.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold;")

        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setDisplayFormat("dd/MM/yyyy")
        self.date_picker.dateChanged.connect(self.al_cambiar_fecha)
        self.date_picker.setStyleSheet(
            f"background-color: {COLORS['surface']}; color: {COLORS['text']};"
        )

        self.btn_refresh = QPushButton("Actualizar Resumen")
        self.btn_refresh.clicked.connect(self.cargar_datos)
        self.btn_refresh.setStyleSheet(
            f"background-color: {COLORS['background']}; color: {COLORS['text']}; border: 1px solid {COLORS['border']};"
        )

        self.lbl_rango_semana = QLabel("")
        self.lbl_rango_semana.setStyleSheet(
            f"font-weight: bold; color: {COLORS['primary']}; margin-left: 10px;"
        )

        filter_layout.addWidget(lbl_fecha)
        filter_layout.addWidget(self.date_picker)
        filter_layout.addWidget(self.lbl_rango_semana)
        filter_layout.addWidget(self.btn_refresh)
        filter_layout.addStretch()

        self.tree = QTreeWidget()
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {COLORS["surface"]};
                color: {COLORS["text"]};
                alternate-background-color: #fcfcfc;
                border: 1px solid {COLORS["border"]};
            }}
            QHeaderView::section {{
                background-color: {COLORS["background"]};
                color: {COLORS["text"]};
                padding: 4px;
                border: 1px solid {COLORS["border"]};
                font-weight: bold;
            }}
            QTreeWidget::item {{
                color: {COLORS["text"]};
            }}
            QTreeWidget::item:selected {{
                background-color: {COLORS["primary"]};
                color: white;
            }}
        """)
        self.tree.setAlternatingRowColors(True)
        self.tree.setHeaderLabels(
            ["Insumo", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom", "Total Sem."]
        )

        palette = self.tree.palette()
        palette.setColor(QPalette.Base, QColor(COLORS["surface"]))
        palette.setColor(QPalette.Text, QColor(COLORS["text"]))
        palette.setColor(QPalette.WindowText, QColor(COLORS["text"]))
        self.tree.setPalette(palette)

        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 9):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        self.layout.addWidget(filter_frame)
        self.layout.addWidget(self.tree)

        self.lbl_gran_total = QLabel("Total Compras Semana: $0.00")
        self.lbl_gran_total.setStyleSheet(f"""
            font-size: 16px; 
            font-weight: bold; 
            padding: 10px; 
            color: {COLORS["text"]}; 
            background-color: {COLORS["background"]}; 
            border: 1px solid {COLORS["border"]};
        """)
        self.lbl_gran_total.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.lbl_gran_total)

    def al_cambiar_fecha(self):
        self.cargar_datos()

    def cargar_datos(self):
        self.tree.clear()
        qdate = self.date_picker.date()
        py_date = qdate.toPyDate()

        start_date = py_date - timedelta(days=py_date.weekday())
        end_date = start_date + timedelta(days=6)
        str_start = start_date.strftime("%Y-%m-%d")
        str_end = end_date.strftime("%Y-%m-%d")

        self.lbl_rango_semana.setText(
            f"(Semana: {start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')})"
        )

        header_labels = ["Insumo"]
        nombres_dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        temp_date = start_date
        for i in range(7):
            dia_str = f"{nombres_dias[i]} {temp_date.day}"
            header_labels.append(dia_str)
            temp_date += timedelta(days=1)
        header_labels.append("Total Sem.")
        self.tree.setHeaderLabels(header_labels)

        try:
            query = """
                SELECT 
                    cat.codigo as codigo_cat,
                    cat.nombre as categoria,
                    i.nombre as insumo,
                    c.fecha_compra as fecha_compra,
                    SUM(dc.subtotal) as monto
                FROM detalle_compras dc
                JOIN compras c ON dc.compra_id = c.id
                JOIN presentaciones_compra pc ON dc.presentacion_id = pc.id
                JOIN insumos i ON pc.insumo_id = i.id
                LEFT JOIN categorias_insumos cat ON i.categoria_id = cat.id
                WHERE c.fecha_compra BETWEEN ? AND ?
                GROUP BY cat.codigo, cat.nombre, i.nombre, c.fecha_compra
                ORDER BY cat.codigo, cat.nombre, i.nombre
            """
            rows = self.db.fetch_all(query, (str_start, str_end))
            data = {}
            gran_total_semana = 0.0

            for row in rows:
                cat_code = row[0]
                cat_name_raw = row[1]
                insumo_name = row[2]
                fecha_str = row[3]
                monto = float(row[4]) if row[4] else 0.0

                if cat_code and cat_name_raw:
                    cat_display = f"{cat_code} - {cat_name_raw}"
                elif cat_name_raw:
                    cat_display = cat_name_raw
                else:
                    cat_display = "Sin Categoría"

                try:
                    fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                    day_idx = fecha_obj.weekday()
                except ValueError:
                    continue

                if cat_display not in data:
                    data[cat_display] = {}
                if insumo_name not in data[cat_display]:
                    data[cat_display][insumo_name] = [0.0] * 7

                data[cat_display][insumo_name][day_idx] += monto
                gran_total_semana += monto

            col_count = self.tree.columnCount()
            for cat_nombre in sorted(data.keys()):
                cat_item = QTreeWidgetItem([cat_nombre])
                cat_item.setExpanded(True)
                for i in range(col_count):
                    cat_item.setBackground(i, QColor(COLORS["background"]))
                    cat_item.setForeground(i, QColor(COLORS["text"]))
                cat_item.setFont(0, QFont("Arial", 9, QFont.Bold))
                self.tree.addTopLevelItem(cat_item)

                cat_totales_dias = [0.0] * 7
                cat_total_final = 0.0

                for insumo_nombre in sorted(data[cat_nombre].keys()):
                    dias_montos = data[cat_nombre][insumo_nombre]
                    total_insumo = sum(dias_montos)
                    cat_total_final += total_insumo

                    valores_fila = (
                        [insumo_nombre]
                        + [f"${v:,.2f}" if v > 0 else "" for v in dias_montos]
                        + [f"${total_insumo:,.2f}"]
                    )
                    child_item = QTreeWidgetItem(valores_fila)
                    for i in range(col_count):
                        child_item.setForeground(i, QColor(COLORS["text"]))
                    cat_item.addChild(child_item)

                    for i, v in enumerate(dias_montos):
                        cat_totales_dias[i] += v

                for i, v in enumerate(cat_totales_dias):
                    cat_item.setText(i + 1, f"${v:,.2f}" if v > 0 else "")
                cat_item.setText(8, f"${cat_total_final:,.2f}")

            self.lbl_gran_total.setText(
                f"Total Compras Semana: ${gran_total_semana:,.2f}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar resumen: {str(e)}")


class TabResumenMensual(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.init_ui()
        self.cargar_datos()

    def init_ui(self):
        filter_frame = QFrame()
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_frame.setLayout(filter_layout)

        lbl_fecha = QLabel("Seleccione Mes/Año (Click día):")
        lbl_fecha.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold;")

        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setDisplayFormat("MMMM yyyy")
        self.date_picker.dateChanged.connect(self.al_cambiar_fecha)
        self.date_picker.setStyleSheet(
            f"background-color: {COLORS['surface']}; color: {COLORS['text']};"
        )

        self.btn_refresh = QPushButton("Actualizar")
        self.btn_refresh.clicked.connect(self.cargar_datos)
        self.btn_refresh.setStyleSheet(
            f"background-color: {COLORS['background']}; color: {COLORS['text']}; border: 1px solid {COLORS['border']};"
        )

        self.lbl_rango_mes = QLabel("")
        self.lbl_rango_mes.setStyleSheet(
            f"font-weight: bold; color: {COLORS['primary']}; margin-left: 10px;"
        )

        filter_layout.addWidget(lbl_fecha)
        filter_layout.addWidget(self.date_picker)
        filter_layout.addWidget(self.lbl_rango_mes)
        filter_layout.addWidget(self.btn_refresh)
        filter_layout.addStretch()

        self.tree = QTreeWidget()
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {COLORS["surface"]};
                color: {COLORS["text"]};
                alternate-background-color: #fcfcfc;
                border: 1px solid {COLORS["border"]};
            }}
            QHeaderView::section {{
                background-color: {COLORS["background"]};
                color: {COLORS["text"]};
                padding: 4px;
                border: 1px solid {COLORS["border"]};
                font-weight: bold;
            }}
            QTreeWidget::item {{
                color: {COLORS["text"]};
            }}
            QTreeWidget::item:selected {{
                background-color: {COLORS["primary"]};
                color: white;
            }}
        """)
        self.tree.setAlternatingRowColors(True)
        headers = [
            "Insumo",
            "Sem 1 (1-7)",
            "Sem 2 (8-14)",
            "Sem 3 (15-21)",
            "Sem 4 (22-28)",
            "Sem 5 (>29)",
            "Total Mes",
        ]
        self.tree.setHeaderLabels(headers)

        palette = self.tree.palette()
        palette.setColor(QPalette.Base, QColor(COLORS["surface"]))
        palette.setColor(QPalette.Text, QColor(COLORS["text"]))
        palette.setColor(QPalette.WindowText, QColor(COLORS["text"]))
        self.tree.setPalette(palette)

        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 7):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        self.layout.addWidget(filter_frame)
        self.layout.addWidget(self.tree)

        self.lbl_gran_total = QLabel("Total Compras Mes: $0.00")
        self.lbl_gran_total.setStyleSheet(f"""
            font-size: 16px; 
            font-weight: bold; 
            padding: 10px; 
            color: {COLORS["text"]}; 
            background-color: {COLORS["background"]}; 
            border: 1px solid {COLORS["border"]};
        """)
        self.lbl_gran_total.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.lbl_gran_total)

    def al_cambiar_fecha(self):
        self.cargar_datos()

    def cargar_datos(self):
        self.tree.clear()
        qdate = self.date_picker.date()
        year = qdate.year()
        month = qdate.month()

        try:
            last_day = calendar.monthrange(year, month)[1]
        except Exception:
            last_day = 30

        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, last_day).date()
        str_start = start_date.strftime("%Y-%m-%d")
        str_end = end_date.strftime("%Y-%m-%d")

        self.lbl_rango_mes.setText(f"(Rango: {str_start} al {str_end})")

        try:
            query = """
                SELECT 
                    cat.codigo as codigo_cat,
                    cat.nombre as categoria,
                    i.nombre as insumo,
                    c.fecha_compra as fecha_compra,
                    SUM(dc.subtotal) as monto
                FROM detalle_compras dc
                JOIN compras c ON dc.compra_id = c.id
                JOIN presentaciones_compra pc ON dc.presentacion_id = pc.id
                JOIN insumos i ON pc.insumo_id = i.id
                LEFT JOIN categorias_insumos cat ON i.categoria_id = cat.id
                WHERE c.fecha_compra BETWEEN ? AND ?
                GROUP BY cat.codigo, cat.nombre, i.nombre, c.fecha_compra
                ORDER BY cat.codigo, cat.nombre, i.nombre
            """
            rows = self.db.fetch_all(query, (str_start, str_end))
            data = {}
            gran_total_mes = 0.0

            for row in rows:
                cat_code = row[0]
                cat_name_raw = row[1]
                insumo_name = row[2]
                fecha_str = row[3]
                monto = float(row[4]) if row[4] else 0.0

                if cat_code and cat_name_raw:
                    cat_display = f"{cat_code} - {cat_name_raw}"
                elif cat_name_raw:
                    cat_display = cat_name_raw
                else:
                    cat_display = "Sin Categoría"

                try:
                    fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                    day_num = fecha_obj.day
                    week_idx = (day_num - 1) // 7
                    if week_idx > 4:
                        week_idx = 4
                except ValueError:
                    continue

                if cat_display not in data:
                    data[cat_display] = {}
                if insumo_name not in data[cat_display]:
                    data[cat_display][insumo_name] = [0.0] * 5

                data[cat_display][insumo_name][week_idx] += monto
                gran_total_mes += monto

            col_count = self.tree.columnCount()
            for cat_nombre in sorted(data.keys()):
                cat_item = QTreeWidgetItem([cat_nombre])
                cat_item.setExpanded(True)
                for i in range(col_count):
                    cat_item.setBackground(i, QColor(COLORS["background"]))
                    cat_item.setForeground(i, QColor(COLORS["text"]))
                cat_item.setFont(0, QFont("Arial", 9, QFont.Bold))
                self.tree.addTopLevelItem(cat_item)

                cat_totales_semanas = [0.0] * 5
                cat_total_final = 0.0

                for insumo_nombre in sorted(data[cat_nombre].keys()):
                    semanas_montos = data[cat_nombre][insumo_nombre]
                    total_insumo = sum(semanas_montos)
                    cat_total_final += total_insumo

                    valores_fila = (
                        [insumo_nombre]
                        + [f"${v:,.2f}" if v > 0 else "" for v in semanas_montos]
                        + [f"${total_insumo:,.2f}"]
                    )
                    child_item = QTreeWidgetItem(valores_fila)
                    for i in range(col_count):
                        child_item.setForeground(i, QColor(COLORS["text"]))
                    cat_item.addChild(child_item)

                    for i, v in enumerate(semanas_montos):
                        cat_totales_semanas[i] += v

                for i, v in enumerate(cat_totales_semanas):
                    cat_item.setText(i + 1, f"${v:,.2f}" if v > 0 else "")
                cat_item.setText(6, f"${cat_total_final:,.2f}")

            self.lbl_gran_total.setText(f"Total Compras Mes: ${gran_total_mes:,.2f}")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Error al cargar resumen mensual: {str(e)}"
            )
