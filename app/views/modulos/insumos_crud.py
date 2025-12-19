# app/views/modulos/insumos_crud.py
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
    QComboBox,
)
from PyQt5.QtCore import Qt


class InsumosCRUD(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)  # Espaciado uniforme

        # --- HEADER ---
        header_layout = QHBoxLayout()

        lbl_title = QLabel("Inventario de Insumos")
        lbl_title.setProperty("class", "header-title")

        header_layout.addWidget(lbl_title)
        header_layout.addStretch()

        # Botones de Acción
        btn_add = QPushButton(" + Nuevo Insumo")
        btn_add.setProperty("class", "btn-success")  # CSS Class
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(self.abrir_form_crear)

        btn_edit = QPushButton("Editar")
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.clicked.connect(self.abrir_form_editar)

        btn_del = QPushButton("Eliminar")
        btn_del.setProperty("class", "btn-danger")  # CSS Class
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.clicked.connect(self.eliminar_registro)

        header_layout.addWidget(btn_add)
        header_layout.addWidget(btn_edit)
        header_layout.addWidget(btn_del)

        layout.addLayout(header_layout)

        # --- TABLA ---
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nombre", "Unidad", "Stock", "Costo", "Categoría"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(
            False
        )  # Ocultar numeros de linea izquierda
        self.table.setShowGrid(False)  # Estilo más limpio, gridlines sutiles por CSS

        layout.addWidget(self.table)
        self.setLayout(layout)
        self.cargar_datos()

    # ... [El resto de métodos cargar_datos, abrir_form, etc. se mantienen igual, la lógica no cambia] ...
    # Solo asegúrate que en mostrar_formulario, los inputs ya se estilizarán solos por el CSS global.

    def cargar_datos(self):
        # ... (código existente sin cambios) ...
        query = """
            SELECT i.id, i.nombre, i.unidad_medida, i.stock_actual, i.costo_unitario, c.nombre, i.categoria_id
            FROM insumos i
            LEFT JOIN categorias_insumos c ON i.categoria_id = c.id
        """
        rows = self.db.fetch_all(query)
        self.table.setRowCount(0)
        for row_idx, row_data in enumerate(rows):
            self.table.insertRow(row_idx)
            for col_idx in range(6):
                val = (
                    row_data[col_idx]
                    if row_data[col_idx] is not None
                    else "Sin Categoría"
                )
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(val)))

            # Guardamos ID oculto
            cat_id = row_data[6]
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
            "categoria_id": self.table.item(row, 5).data(Qt.UserRole),
        }
        self.mostrar_formulario(data)

    def eliminar_registro(self):
        # ... (código existente sin cambios) ...
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
        dialog.setWindowTitle("Gestión de Insumo")
        dialog.setMinimumWidth(300)  # Un poco más ancho
        form = QFormLayout(dialog)
        form.setSpacing(10)

        inp_nombre = QLineEdit(data["nombre"] if data else "")
        inp_unidad = QLineEdit(data["unidad"] if data else "")
        inp_stock = QLineEdit(data["stock"] if data else "0")
        inp_costo = QLineEdit(data["costo"] if data else "0")

        cmb_categoria = QComboBox()
        cmb_categoria.addItem("Seleccione Categoría...", None)
        cats = self.db.fetch_all("SELECT id, codigo, nombre FROM categorias_insumos")
        for c in cats:
            display_text = f"{c[1]} - {c[2]}"
            cmb_categoria.addItem(display_text, c[0])

        if data and data.get("categoria_id"):
            index = cmb_categoria.findData(data["categoria_id"])
            if index >= 0:
                cmb_categoria.setCurrentIndex(index)

        form.addRow("Nombre:", inp_nombre)
        form.addRow("Categoría:", cmb_categoria)
        form.addRow("Unidad:", inp_unidad)
        form.addRow("Stock Inicial:", inp_stock)
        form.addRow("Costo Unitario:", inp_costo)

        btn_save = QPushButton("Guardar Datos")
        btn_save.setProperty("class", "btn-success")  # Estilo verde
        btn_save.clicked.connect(dialog.accept)
        form.addRow(btn_save)

        if dialog.exec_() == QDialog.Accepted:
            # ... (logica de guardado igual que antes) ...
            nombre = inp_nombre.text()
            unidad = inp_unidad.text()
            stock = float(inp_stock.text())
            costo = float(inp_costo.text())
            cat_id = cmb_categoria.currentData()

            if data:
                query = "UPDATE insumos SET nombre=?, unidad_medida=?, stock_actual=?, costo_unitario=?, categoria_id=? WHERE id=?"
                params = (nombre, unidad, stock, costo, cat_id, data["id"])
            else:
                query = "INSERT INTO insumos (nombre, unidad_medida, stock_actual, costo_unitario, categoria_id) VALUES (?,?,?,?,?)"
                params = (nombre, unidad, stock, costo, cat_id)

            self.db.execute_query(query, params)
            self.cargar_datos()
