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
    QHeaderView,
    QMessageBox,
    QComboBox,
    QDoubleSpinBox,
)
from PyQt5.QtCore import Qt


# Clase auxiliar para ordenar números correctamente (1, 2, 10 en lugar de 1, 10, 2)
class NumericItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            return super().__lt__(other)


class RecetasCRUD(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.filtros = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        title = QLabel("Gestión de Recetas (Fichas Técnicas)")
        title.setProperty("class", "header-title")

        btn_edit_recipe = QPushButton(" Ver/Editar Ingredientes")
        btn_edit_recipe.setCursor(Qt.PointingHandCursor)
        btn_edit_recipe.setProperty("class", "btn-primary")
        btn_edit_recipe.clicked.connect(self.abrir_editor_receta)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(btn_edit_recipe)
        layout.addLayout(header_layout)

        # --- FILTROS ---
        filter_layout = QHBoxLayout()
        self.input_filtro_codigo = QLineEdit()
        self.input_filtro_codigo.setPlaceholderText("Filtrar por Código...")
        self.input_filtro_codigo.textChanged.connect(self.aplicar_filtros)

        self.input_filtro_nombre = QLineEdit()
        self.input_filtro_nombre.setPlaceholderText("Filtrar por Nombre del Plato...")
        self.input_filtro_nombre.textChanged.connect(self.aplicar_filtros)

        filter_layout.addWidget(self.input_filtro_codigo)
        filter_layout.addWidget(self.input_filtro_nombre)
        layout.addLayout(filter_layout)

        # --- TABLA DE ITEMS DEL MENÚ ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Código", "Nombre del Plato", "N° Ingredientes"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # --- CORRECCIÓN: HABILITAR ORDENAMIENTO ---
        self.table.setSortingEnabled(True)

        layout.addWidget(self.table)
        self.setLayout(layout)

        self.cargar_datos()

    def cargar_datos(self):
        """
        Carga los items del menú y cuenta cuántos ingredientes tienen configurados.
        """
        # --- CORRECCIÓN: DESACTIVAR ORDENAMIENTO AL CARGAR ---
        self.table.setSortingEnabled(False)

        self.table.setRowCount(0)

        query = """
            SELECT m.id, m.codigo, m.nombre, COUNT(r.id) as num_ingredientes
            FROM menu_items m
            LEFT JOIN recetas r ON m.id = r.menu_item_id
            WHERE m.es_preparado = 1
            GROUP BY m.id
            ORDER BY m.nombre ASC
        """
        rows = self.db.fetch_all(query)

        for row_idx, row_data in enumerate(rows):
            self.table.insertRow(row_idx)

            # Usamos NumericItem para que el ID se ordene como número
            self.table.setItem(row_idx, 0, NumericItem(str(row_data[0])))

            self.table.setItem(row_idx, 1, QTableWidgetItem(str(row_data[1])))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(row_data[2])))

            cant_ing = row_data[3]
            # Usamos NumericItem para que la cantidad se ordene numéricamente
            item_cant = NumericItem(str(cant_ing))
            item_cant.setTextAlignment(Qt.AlignCenter)

            if cant_ing > 0:
                item_cant.setForeground(Qt.darkGreen)
            else:
                item_cant.setForeground(Qt.red)
                item_cant.setText(
                    "Sin receta"
                )  # Nota: Esto afectará el orden numérico si mezclas texto, pero es visualmente útil.

            self.table.setItem(row_idx, 3, item_cant)

        # --- CORRECCIÓN: REACTIVAR ORDENAMIENTO AL TERMINAR ---
        self.table.setSortingEnabled(True)

        # Re-aplicar filtros si había texto escrito
        self.aplicar_filtros()

    def aplicar_filtros(self):
        txt_code = self.input_filtro_codigo.text().lower()
        txt_name = self.input_filtro_nombre.text().lower()

        for row in range(self.table.rowCount()):
            code_item = self.table.item(row, 1).text().lower()
            name_item = self.table.item(row, 2).text().lower()

            mostrar = True
            if txt_code and txt_code not in code_item:
                mostrar = False
            if txt_name and txt_name not in name_item:
                mostrar = False

            self.table.setRowHidden(row, not mostrar)

    def abrir_editor_receta(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, "Atención", "Seleccione un plato para editar su receta."
            )
            return

        menu_item_id = self.table.item(row, 0).text()
        nombre_plato = self.table.item(row, 2).text()

        dialog = RecetaEditorDialog(self.db, menu_item_id, nombre_plato, self)
        dialog.exec_()
        self.cargar_datos()


# (La clase RecetaEditorDialog se mantiene igual que en la respuesta anterior)
class RecetaEditorDialog(QDialog):
    def __init__(self, db_manager, menu_item_id, nombre_plato, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.menu_item_id = menu_item_id
        self.setWindowTitle(f"Receta: {nombre_plato}")
        self.resize(700, 500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Parte Superior: Formulario
        form_group = QWidget()
        form_layout = QHBoxLayout(form_group)

        self.combo_insumos = QComboBox()
        self.combo_insumos.setMinimumWidth(250)

        self.spin_cantidad = QDoubleSpinBox()
        self.spin_cantidad.setRange(0.001, 9999)
        self.spin_cantidad.setDecimals(3)
        self.spin_cantidad.setSuffix(" (Cant)")

        btn_add = QPushButton("Agregar / Actualizar")
        btn_add.setProperty("class", "btn-success")
        btn_add.clicked.connect(self.agregar_insumo)

        form_layout.addWidget(QLabel("Insumo:"))
        form_layout.addWidget(self.combo_insumos)
        form_layout.addWidget(QLabel("Cantidad:"))
        form_layout.addWidget(self.spin_cantidad)
        form_layout.addWidget(btn_add)

        layout.addWidget(form_group)
        layout.addWidget(
            QLabel(
                "<b>Nota:</b> La cantidad debe estar expresada en la unidad base del insumo."
            )
        )

        # Tabla de ingredientes
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID Receta", "Insumo", "Cantidad", "Unidad", "Acción"]
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        # Activar ordenamiento también en el detalle si lo deseas
        self.table.setSortingEnabled(True)

        layout.addWidget(self.table)
        self.setLayout(layout)

        self.cargar_combo_insumos()
        self.cargar_receta_actual()

    def cargar_combo_insumos(self):
        self.combo_insumos.clear()
        query = """
            SELECT i.id, i.nombre, u.abreviatura 
            FROM insumos i 
            LEFT JOIN unidades_medida u ON i.unidad_base_id = u.id
            ORDER BY i.nombre
        """
        insumos = self.db.fetch_all(query)
        for ins in insumos:
            unidad = ins[2] if ins[2] else "?"
            texto = f"{ins[1]} ({unidad})"
            self.combo_insumos.addItem(texto, userData=ins[0])

    def cargar_receta_actual(self):
        self.table.setSortingEnabled(False)  # Pausar ordenamiento
        self.table.setRowCount(0)
        query = """
            SELECT r.id, i.nombre, r.cantidad_necesaria, u.abreviatura
            FROM recetas r
            JOIN insumos i ON r.insumo_id = i.id
            LEFT JOIN unidades_medida u ON i.unidad_base_id = u.id
            WHERE r.menu_item_id = ?
        """
        rows = self.db.fetch_all(query, (self.menu_item_id,))

        for idx, row in enumerate(rows):
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, NumericItem(str(row[0])))  # ID numérico
            self.table.setItem(idx, 1, QTableWidgetItem(str(row[1])))
            self.table.setItem(idx, 2, NumericItem(str(row[2])))  # Cantidad numérica
            self.table.setItem(idx, 3, QTableWidgetItem(row[3] if row[3] else ""))

            btn_del = QPushButton("X")
            btn_del.setFixedWidth(40)
            btn_del.setStyleSheet(
                "background-color: #e74c3c; color: white; font-weight: bold;"
            )
            btn_del.clicked.connect(
                lambda _, r_id=row[0]: self.eliminar_ingrediente(r_id)
            )
            self.table.setCellWidget(idx, 4, btn_del)

        self.table.setSortingEnabled(True)  # Reactivar ordenamiento

    def agregar_insumo(self):
        insumo_id = self.combo_insumos.currentData()
        cantidad = self.spin_cantidad.value()

        if cantidad <= 0:
            QMessageBox.warning(self, "Error", "La cantidad debe ser mayor a 0.")
            return

        check_query = "SELECT id FROM recetas WHERE menu_item_id=? AND insumo_id=?"
        existe = self.db.fetch_all(check_query, (self.menu_item_id, insumo_id))

        try:
            if existe:
                receta_id = existe[0][0]
                self.db.execute_query(
                    "UPDATE recetas SET cantidad_necesaria=? WHERE id=?",
                    (cantidad, receta_id),
                )
            else:
                self.db.execute_query(
                    "INSERT INTO recetas (menu_item_id, insumo_id, cantidad_necesaria) VALUES (?,?,?)",
                    (self.menu_item_id, insumo_id, cantidad),
                )
            self.cargar_receta_actual()
            self.spin_cantidad.setValue(0)

        except Exception as e:
            QMessageBox.critical(self, "Error BD", str(e))

    def eliminar_ingrediente(self, receta_id):
        confirm = QMessageBox.question(
            self,
            "Confirmar",
            "¿Quitar este ingrediente?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self.db.execute_query("DELETE FROM recetas WHERE id=?", (receta_id,))
            self.cargar_receta_actual()
