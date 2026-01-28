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
)
from PyQt5.QtCore import Qt, QDate


class ComprasCRUD(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        header = QLabel("<h2>Gestión de Compras e Inventario</h2>")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        self.tabs = QTabWidget()
        self.tab_compras = TabGestionCompras(self.db)
        self.tab_proveedores = TabProveedores(self.db)

        self.tabs.addTab(self.tab_compras, "1. Registro de Compras")
        self.tabs.addTab(self.tab_proveedores, "2. Proveedores")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def cargar_datos(self):
        self.tab_compras.cargar_compras()
        self.tab_proveedores.cargar_proveedores()


# --- PESTAÑA DE COMPRAS ---
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
        btn_recibir.setStyleSheet("background-color: #2ecc71; color: white;")
        btn_recibir.clicked.connect(self.recibir_compra)

        btn_ver = QPushButton("Ver Detalle")
        btn_ver.clicked.connect(self.ver_detalle)

        btn_layout.addWidget(btn_nueva)
        btn_layout.addWidget(btn_recibir)
        btn_layout.addWidget(btn_ver)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Proveedor", "Fecha", "Total", "Estado", "Acción"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.cargar_compras()

    def cargar_compras(self):
        query = """
            SELECT c.id, p.nombre, c.fecha_compra, c.total, c.estado 
            FROM compras c JOIN proveedores p ON c.proveedor_id = p.id 
            ORDER BY c.id DESC
        """
        rows = self.db.fetch_all(query)
        self.table.setRowCount(0)
        for r, row in enumerate(rows):
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(row[0])))
            self.table.setItem(r, 1, QTableWidgetItem(row[1]))
            self.table.setItem(r, 2, QTableWidgetItem(row[2]))
            self.table.setItem(r, 3, QTableWidgetItem(f"${row[3]:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(row[4]))

            # Colorear estado
            if row[4] == "PENDIENTE":
                self.table.item(r, 4).setBackground(Qt.yellow)
            elif row[4] == "RECIBIDO":
                self.table.item(r, 4).setBackground(Qt.green)

    def nueva_compra(self):
        if NuevaCompraDialog(self.db, parent=self).exec_():
            self.cargar_compras()

    def recibir_compra(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "Aviso", "Seleccione una compra")

        cid = self.table.item(row, 0).text()
        estado = self.table.item(row, 4).text()

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
            # 1. Obtener detalles
            detalles = self.db.fetch_all(
                "SELECT presentacion_id, cantidad FROM detalle_compras WHERE compra_id=?",
                (compra_id,),
            )

            for pres_id, cant_compra in detalles:
                # 2. Obtener datos de la presentacion (cuanto contenido tiene) y el insumo asociado
                pres = self.db.fetch_one(
                    "SELECT insumo_id, cantidad_contenido FROM presentaciones_compra WHERE id=?",
                    (pres_id,),
                )
                if pres:
                    insumo_id, contenido_unitario = pres
                    cantidad_total_a_sumar = cant_compra * contenido_unitario

                    # 3. Actualizar Stock
                    self.db.execute_query(
                        "UPDATE insumos SET stock_actual = stock_actual + ? WHERE id=?",
                        (cantidad_total_a_sumar, insumo_id),
                    )

            # 4. Actualizar estado compra
            self.db.execute_query(
                "UPDATE compras SET estado='RECIBIDO' WHERE id=?", (compra_id,)
            )
            QMessageBox.information(
                self, "Éxito", "Inventario actualizado correctamente."
            )
            self.cargar_compras()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def ver_detalle(self):
        # Lógica simple para ver detalle (puedes expandirla)
        pass


# --- DIALOGO NUEVA COMPRA ---
class NuevaCompraDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Registrar Compra")
        self.resize(600, 500)
        self.detalles = []  # Lista temporal de items
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Cabecera
        form = QFormLayout()
        self.cmb_prov = QComboBox()
        self.cargar_proveedores()
        self.date_picker = QDateEdit(QDate.currentDate())
        self.date_picker.setCalendarPopup(True)
        form.addRow("Proveedor:", self.cmb_prov)
        form.addRow("Fecha Compra:", self.date_picker)
        layout.addLayout(form)

        # Agregar Items
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

        # Tabla Resumen
        self.table_det = QTableWidget()
        self.table_det.setColumnCount(4)
        self.table_det.setHorizontalHeaderLabels(
            ["Producto", "Cant", "Precio U.", "Subtotal"]
        )
        self.table_det.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_det)

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

    def cargar_presentaciones(self):
        # Muestra Presentacion + Insumo
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

    def guardar_bd(self):
        if not self.detalles:
            return
        prov_id = self.cmb_prov.currentData()
        fecha = self.date_picker.date().toString("yyyy-MM-dd")

        # Calcular total
        total = sum(d["subtotal"] for d in self.detalles)

        try:
            # 1. Crear Cabecera
            cur = self.db.execute_query(
                "INSERT INTO compras (proveedor_id, fecha_compra, total, estado) VALUES (?,?,?,?)",
                (prov_id, fecha, total, "PENDIENTE"),
            )
            compra_id = cur.lastrowid

            # 2. Crear Detalles
            for d in self.detalles:
                self.db.execute_query(
                    "INSERT INTO detalle_compras (compra_id, presentacion_id, cantidad, precio_unitario, subtotal) VALUES (?,?,?,?,?)",
                    (compra_id, d["pres_id"], d["cant"], d["precio"], d["subtotal"]),
                )

            QMessageBox.information(
                self, "Éxito", "Compra registrada en estado PENDIENTE."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# --- PESTAÑA DE PROVEEDORES (Simplificada) ---
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
