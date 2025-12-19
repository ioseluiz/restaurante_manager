from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QDialog,
    QFormLayout,
    QMessageBox,
    QHeaderView,
    QComboBox,  # Importante
)
from PyQt5.QtCore import Qt


class InsumosCRUD(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        action_layout = QHBoxLayout()
        btn_add = QPushButton("Nuevo Insumo")
        btn_add.setStyleSheet("background-color: #28a745; color: white")
        btn_add.clicked.connect(self.abrir_form_crear)
        btn_edit = QPushButton("Editar Seleccionado")
        btn_edit.clicked.connect(self.abrir_form_editar)
        btn_del = QPushButton("Eliminar Seleccionado")
        btn_del.setStyleSheet("background-color: #dc3545; color: white;")
        btn_del.clicked.connect(self.eliminar_registro)

        action_layout.addWidget(QLabel("<h2>Inventario</h2>"))
        action_layout.addStretch()
        action_layout.addWidget(btn_add)
        action_layout.addWidget(btn_edit)
        action_layout.addWidget(btn_del)

        layout.addLayout(action_layout)

        # Tabla: Agregamos columna "Categoría"
        self.table = QTableWidget()
        self.table.setColumnCount(6)  # Aumentamos columnas
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nombre", "Unidad", "Stock", "Costo", "Categoría"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.cargar_datos()

    def cargar_datos(self):
        # Hacemos JOIN para traer el nombre de la categoría
        query = """
            SELECT i.id, i.nombre, i.unidad_medida, i.stock_actual, i.costo_unitario, c.nombre, i.categoria_id
            FROM insumos i
            LEFT JOIN categorias_insumos c ON i.categoria_id = c.id
        """
        rows = self.db.fetch_all(query)
        self.table.setRowCount(0)
        for row_idx, row_data in enumerate(rows):
            self.table.insertRow(row_idx)
            # Mostramos las primeras 6 columnas (la 7ma es el ID de categoria oculto si quisieramos usarlo)
            for col_idx in range(6):
                val = (
                    row_data[col_idx]
                    if row_data[col_idx] is not None
                    else "Sin Categoría"
                )
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(val)))

            # Guardamos el categoria_id real en el item de la columna Categoria (index 5) para editarlo luego
            cat_id = row_data[6]  # El indice 6 es categoria_id
            if cat_id:
                self.table.item(row_idx, 5).setData(Qt.UserRole, cat_id)

    def abrir_form_crear(self):
        self.mostrar_formulario()

    def abrir_form_editar(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Alerta", "Selecciona un registro para editar")
            return

        data = {
            "id": self.table.item(row, 0).text(),
            "nombre": self.table.item(row, 1).text(),
            "unidad": self.table.item(row, 2).text(),
            "stock": self.table.item(row, 3).text(),
            "costo": self.table.item(row, 4).text(),
            "categoria_id": self.table.item(row, 5).data(
                Qt.UserRole
            ),  # Recuperamos el ID oculto
        }
        self.mostrar_formulario(data)

    def eliminar_registro(self):
        row = self.table.currentRow()
        if row < 0:
            return
        id_insumo = self.table.item(row, 0).text()
        if (
            QMessageBox.question(
                self, "Confirmar", "¿Eliminar insumo?", QMessageBox.Yes | QMessageBox.No
            )
            == QMessageBox.Yes
        ):
            self.db.execute_query("DELETE FROM insumos WHERE id=?", (id_insumo,))
            self.cargar_datos()

    def mostrar_formulario(self, data=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Gestion de Insumo")
        form = QFormLayout(dialog)

        inp_nombre = QLineEdit(data["nombre"] if data else "")
        inp_unidad = QLineEdit(data["unidad"] if data else "")
        inp_stock = QLineEdit(data["stock"] if data else "0")
        inp_costo = QLineEdit(data["costo"] if data else "0")

        # --- Selector de Categoría ---
        cmb_categoria = QComboBox()
        cmb_categoria.addItem("Seleccione Categoría...", None)  # Opción default

        # Cargar categorías de la BD
        cats = self.db.fetch_all("SELECT id, codigo, nombre FROM categorias_insumos")
        for c in cats:
            # c[0]=id, c[1]=code, c[2]=name. Mostramos "5008 - CARNES"
            display_text = f"{c[1]} - {c[2]}"
            cmb_categoria.addItem(display_text, c[0])  # Guardamos el ID como userdata

        # Si estamos editando, pre-seleccionar
        if data and data.get("categoria_id"):
            index = cmb_categoria.findData(data["categoria_id"])
            if index >= 0:
                cmb_categoria.setCurrentIndex(index)

        form.addRow("Nombre:", inp_nombre)
        form.addRow("Categoría:", cmb_categoria)  # Añadido al form
        form.addRow("Unidad (kg/lt/u):", inp_unidad)
        form.addRow("Stock Inicial:", inp_stock)
        form.addRow("Costo Unitario:", inp_costo)

        btn_save = QPushButton("Guardar")
        btn_save.clicked.connect(dialog.accept)
        form.addRow(btn_save)

        if dialog.exec_() == QDialog.Accepted:
            nombre = inp_nombre.text()
            unidad = inp_unidad.text()
            stock = float(inp_stock.text())
            costo = float(inp_costo.text())
            cat_id = (
                cmb_categoria.currentData()
            )  # Obtenemos el ID de la categoría seleccionada

            if data:
                # UPDATE
                query = "UPDATE insumos SET nombre=?, unidad_medida=?, stock_actual=?, costo_unitario=?, categoria_id=? WHERE id=?"
                params = (nombre, unidad, stock, costo, cat_id, data["id"])
            else:
                # CREATE
                query = "INSERT INTO insumos (nombre, unidad_medida, stock_actual, costo_unitario, categoria_id) VALUES (?,?,?,?,?)"
                params = (nombre, unidad, stock, costo, cat_id)

            self.db.execute_query(query, params)
            self.cargar_datos()
