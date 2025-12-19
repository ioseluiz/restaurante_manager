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
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QHeaderView,
    QMessageBox,
)
from PyQt5.QtCore import Qt
import sqlite3


class MenuCRUD(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        # Margen uniforme con el resto de la app
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- HEADER (Titulo y Botones) ---
        action_layout = QHBoxLayout()

        # Título con clase CSS
        title = QLabel("Gestión del Menú")
        title.setProperty("class", "header-title")

        # Botones de Acción
        btn_add = QPushButton(" + Nuevo Item")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setProperty("class", "btn-success")  # Clase CSS: Verde
        btn_add.clicked.connect(self.abrir_form_crear)

        btn_edit = QPushButton("Editar Item")
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.clicked.connect(self.abrir_form_editar)

        btn_del = QPushButton("Eliminar Item")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setProperty("class", "btn-danger")  # Clase CSS: Rojo
        btn_del.clicked.connect(self.eliminar_registro)

        action_layout.addWidget(title)
        action_layout.addStretch()
        action_layout.addWidget(btn_add)
        action_layout.addWidget(btn_edit)
        action_layout.addWidget(btn_del)

        layout.addLayout(action_layout)

        # --- TABLA ---
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Código", "Nombre del Plato/Bebida", "Precio Venta", "Tipo"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)

        # Mejoras visuales de la tabla
        self.table.verticalHeader().setVisible(
            False
        )  # Ocultar números de línea izquierda
        self.table.setShowGrid(False)  # Grid más limpio (controlado por CSS)
        self.table.setFocusPolicy(
            Qt.NoFocus
        )  # Quitar borde de foco azul al hacer click

        layout.addWidget(self.table)

        self.setLayout(layout)
        self.cargar_datos()

    def cargar_datos(self):
        "Consulta la base de datos y rellena la tabla"
        query = "SELECT id, codigo, nombre, precio_venta, es_preparado FROM menu_items"
        rows = self.db.fetch_all(query)

        self.table.setRowCount(0)
        for row_idx, row_data in enumerate(rows):
            self.table.insertRow(row_idx)
            # ID
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0])))
            # Codigo
            codigo_val = row_data[1] if row_data[1] else ""
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(codigo_val)))
            # Nombre
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(row_data[2])))
            # Precio formateado con 2 decimales
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"${row_data[3]:.2f}"))
            # Tipo (Convertir booleano a texto legible)
            es_preparado = row_data[4]
            tipo_txt = "Plato (Cocina)" if es_preparado else "Bebida/Directo"
            self.table.setItem(row_idx, 4, QTableWidgetItem(tipo_txt))

            # Guardamos el valor booleano real en el item para usarlo al editar
            self.table.item(row_idx, 4).setData(Qt.UserRole, es_preparado)

    # --- Logica CRUD ---
    def abrir_form_crear(self):
        self.mostrar_formulario()

    def abrir_form_editar(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, "Alerta", "Selecciona un item del menú para editar"
            )
            return

        # Recuperar datos de la tabla para prellenar el formulario
        id_item = self.table.item(row, 0).text()
        codigo = self.table.item(row, 1).text()
        nombre = self.table.item(row, 2).text()
        # Limpiamos el símbolo de $ para obtener el numero
        try:
            precio_txt = self.table.item(row, 3).text().replace("$", "").strip()
            precio = float(precio_txt)
        except ValueError:
            precio = 0.0

        # Recuperamos el booleano guardado en UserRole
        es_preparado = self.table.item(row, 4).data(Qt.UserRole)

        data = {
            "id": id_item,
            "codigo": codigo,
            "nombre": nombre,
            "precio": precio,
            "es_preparado": es_preparado,
        }
        self.mostrar_formulario(data)

    def eliminar_registro(self):
        row = self.table.currentRow()
        if row < 0:
            return

        id_item = self.table.item(row, 0).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            "¿Borrar Item?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            # Primero borramos recetas asociadas para mantener integridad
            self.db.execute_query(
                "DELETE FROM recetas WHERE menu_item_id=?", (id_item,)
            )
            # Luego borramos el item
            self.db.execute_query("DELETE FROM menu_items WHERE id=?", (id_item,))
            self.cargar_datos()

    def mostrar_formulario(self, data=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Detalle del Menú")
        dialog.setFixedSize(400, 300)  # Un poco más alto para que respire

        # Layout del formulario
        form = QFormLayout(dialog)
        form.setSpacing(15)  # Espaciado entre inputs

        # Campos
        inp_codigo = QLineEdit(data["codigo"] if data else "")
        inp_nombre = QLineEdit(data["nombre"] if data else "")

        # Usamos el DoubleSpinBox para precios
        inp_precio = QDoubleSpinBox()
        inp_precio.setPrefix("$ ")
        inp_precio.setMaximum(10000.00)
        inp_precio.setDecimals(2)
        if data:
            inp_precio.setValue(data["precio"])

        chk_preparado = QCheckBox("¿Requiere preparación en cocina?")
        chk_preparado.setToolTip(
            "Marcar si el producto usa una receta (ej. Combo de Pollo). Desmarcar si es un producto directo (ej. Soda)"
        )
        if data:
            chk_preparado.setChecked(bool(data["es_preparado"]))
        else:
            chk_preparado.setChecked(True)

        form.addRow("Código Único:", inp_codigo)
        form.addRow("Nombre del Item:", inp_nombre)
        form.addRow("Precio de Venta:", inp_precio)
        form.addRow("", chk_preparado)

        # Función interna de validación
        def validar_y_aceptar():
            codigo = inp_codigo.text().strip()
            nombre = inp_nombre.text().strip()

            if not codigo:
                QMessageBox.warning(
                    dialog, "Validación", "El campo de Código es obligatorio."
                )
                inp_codigo.setFocus()
                return

            if not nombre:
                QMessageBox.warning(
                    dialog, "Validación", "El campo de Nombre es obligatorio."
                )
                inp_nombre.setFocus()
                return

            dialog.accept()

        # Botón de Guardar
        btn_save = QPushButton("Guardar Datos")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setProperty("class", "btn-success")  # Estilo verde global
        btn_save.clicked.connect(validar_y_aceptar)

        # Espaciador antes del botón
        form.addRow(QLabel(""))
        form.addRow(btn_save)

        if dialog.exec_() == QDialog.Accepted:
            # Recoger valores
            codigo_val = inp_codigo.text().strip()
            nombre_val = inp_nombre.text().strip()
            precio_val = inp_precio.value()
            es_preparado_val = 1 if chk_preparado.isChecked() else 0

            # Validaciones básicas
            if not nombre_val or not codigo_val:
                QMessageBox.warning(
                    self, "Error", "El código y el nombre son obligatorios."
                )
                return

            try:
                if data:
                    # UPDATE
                    query = "UPDATE menu_items SET codigo=?, nombre=?, precio_venta=?, es_preparado=? WHERE id=?"
                    params = (
                        codigo_val,
                        nombre_val,
                        precio_val,
                        es_preparado_val,
                        data["id"],
                    )
                else:
                    # CREATE
                    query = """INSERT INTO menu_items (codigo, nombre, precio_venta, es_preparado) VALUES (?,?,?,?)"""
                    params = (codigo_val, nombre_val, precio_val, es_preparado_val)

                self.db.execute_query(query, params)
                self.cargar_datos()

            except sqlite3.IntegrityError:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"El código '{codigo_val}' ya existe. Usa uno diferente.",
                )
            except Exception as e:
                QMessageBox.critical(self, "Error BD", str(e))
