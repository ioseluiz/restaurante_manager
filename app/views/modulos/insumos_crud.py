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
)
from PyQt5.QtCore import Qt


class InsumosCRUD(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        # Header con botones de accion
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

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nombre", "Unidad", "Stock", "Costo"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.cargar_datos()

    def cargar_datos(self):
        rows = self.db.fetch_all("SELECT * FROM insumos")
        self.table.setRowCount(0)
        for row_idx, row_data in enumerate(rows):
            self.table.insertRow(row_idx)
            for col_idx, data in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

    # Logica CRUD
    def abrir_form_crear(self):
        self.mostrar_formulario()

    def abrir_form_editar(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Alerta", "Selecciona un registro para editar")
            return

        # Obtener datos de la fila seleccionada
        data = {
            "id": self.table.item(row, 0).text(),
            "nombre": self.table.item(row, 1).text(),
            "unidad": self.table.item(row, 2).text(),
            "stock": self.table.item(row, 3).text(),
            "costo": self.table.item(row, 4).text(),
        }

        self.mostrar_formulario(data)

    def eliminar_registro(self):
        row = self.table.currentRow()
        if row < 0:
            return
        id_insumo = self.table.item(row, 0).text()
        confirm = QMessageBox.question(
            self,
            "Confirmar",
            "Estas Seguro de eliminar este insumo?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
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

        form.addRow("Nombre:", inp_nombre)
        form.addRow("Unidad (kg/lt/u):", inp_unidad)

        form.addRow("Stock Inicial:", inp_stock)
        form.addRow("Costo Unitario:", inp_costo)

        btn_save = QPushButton("Guardar")
        btn_save.clicked.connect(dialog.accept)
        form.addRow(btn_save)

        if dialog.exec_() == QDialog.Accepted:
            # Validar y guardar
            nombre = inp_nombre.text()
            unidad = inp_unidad.text()
            stock = float(inp_stock.text())
            costo = float(inp_costo.text())

        if data:
            # UPDATE
            query = "UPDATE insumos SET nombre=?, unidad_medida=?, stock_actual=?, costo_unitario=? WHERE id=?"
            params = (nombre, unidad, stock, costo, data["id"])
        else:
            # CREATE
            query = "INSERT INTO insumos (nombre, unidad_medida, stock_actual, costo_unitario) VALUES (?,?,?,?)"
            params = (nombre, unidad, stock, costo)
        self.db.execute_query(query, params)
        self.cargar_datos()
