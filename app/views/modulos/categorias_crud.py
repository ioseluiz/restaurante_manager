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


class CategoriasCRUD(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Header
        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("<h2>Categorías de Insumos</h2>"))
        action_layout.addStretch()

        btn_add = QPushButton("Nueva Categoría")
        btn_add.setStyleSheet("background-color: #28a745; color: white")
        btn_add.clicked.connect(self.abrir_form_crear)

        btn_del = QPushButton("Eliminar")
        btn_del.setStyleSheet("background-color: #dc3545; color: white")
        btn_del.clicked.connect(self.eliminar_registro)

        action_layout.addWidget(btn_add)
        action_layout.addWidget(btn_del)
        layout.addLayout(action_layout)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Código", "Nombre Categoría"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.cargar_datos()

    def cargar_datos(self):
        rows = self.db.fetch_all("SELECT id, codigo, nombre FROM categorias_insumos")
        self.table.setRowCount(0)
        for row_idx, row_data in enumerate(rows):
            self.table.insertRow(row_idx)
            for col_idx, data in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

    def abrir_form_crear(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nueva Categoría")
        form = QFormLayout(dialog)

        inp_code = QLineEdit()
        inp_name = QLineEdit()

        form.addRow("Código (ej. 5008):", inp_code)
        form.addRow("Nombre (ej. CARNES):", inp_name)

        btn_save = QPushButton("Guardar")
        btn_save.clicked.connect(dialog.accept)
        form.addRow(btn_save)

        if dialog.exec_() == QDialog.Accepted:
            codigo = inp_code.text().strip()
            nombre = inp_name.text().strip()
            if codigo and nombre:
                try:
                    self.db.execute_query(
                        "INSERT INTO categorias_insumos (codigo, nombre) VALUES (?,?)",
                        (codigo, nombre),
                    )
                    self.cargar_datos()
                except Exception as e:
                    QMessageBox.warning(
                        self, "Error", f"Error (probablemente código duplicado): {e}"
                    )

    def eliminar_registro(self):
        row = self.table.currentRow()
        if row < 0:
            return
        id_cat = self.table.item(row, 0).text()

        # Validar si está en uso
        uso = self.db.fetch_all(
            "SELECT COUNT(*) FROM insumos WHERE categoria_id=?", (id_cat,)
        )
        if uso[0][0] > 0:
            QMessageBox.warning(
                self,
                "No permitido",
                "No puedes eliminar una categoría que tiene insumos asociados.",
            )
            return

        if (
            QMessageBox.question(self, "Confirmar", "¿Eliminar categoría?")
            == QMessageBox.Yes
        ):
            self.db.execute_query(
                "DELETE FROM categorias_insumos WHERE id=?", (id_cat,)
            )
            self.cargar_datos()
