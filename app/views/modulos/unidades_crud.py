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
    QHeaderView,
    QMessageBox,
)
from PyQt5.QtCore import Qt


class NumericItem(QTableWidgetItem):
    """Permite ordenar columnas numéricas correctamente."""

    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            return super().__lt__(other)


class UnidadesCRUD(QWidget):
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
        title = QLabel("<h2>Gestión de Unidades de Medida</h2>")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # BOTONES DE ACCION
        btn_add = QPushButton(" + Nueva Unidad")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setProperty("class", "btn-success")
        btn_add.clicked.connect(self.abrir_crear)

        btn_edit = QPushButton("Editar Seleccionada")
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.clicked.connect(self.abrir_editar)

        btn_del = QPushButton("Eliminar")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setProperty("class", "btn-danger")
        btn_del.clicked.connect(self.eliminar)

        header_layout.addWidget(btn_add)
        header_layout.addWidget(btn_edit)
        header_layout.addWidget(btn_del)
        layout.addLayout(header_layout)

        # --- FILTROS ---
        filter_layout = QHBoxLayout()
        # Definición de columnas para filtro: índice y placeholder
        config_filtros = [
            (0, "Filtrar ID"),
            (1, "Filtrar Nombre"),
            (2, "Filtrar Abreviatura"),
        ]

        for col_idx, placeholder in config_filtros:
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setClearButtonEnabled(True)
            inp.textChanged.connect(self.aplicar_filtros)
            self.filtros[col_idx] = inp
            filter_layout.addWidget(inp)

        layout.addLayout(filter_layout)

        # --- TABLA ---
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Abreviatura"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)  # Habilitar ordenamiento
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.cargar_datos()

    def cargar_datos(self):
        self.table.setSortingEnabled(False)  # Desactivar mientras se carga
        rows = self.db.fetch_all(
            "SELECT id, nombre, abreviatura FROM unidades_medida ORDER BY id"
        )
        self.table.setRowCount(0)

        for r_idx, row in enumerate(rows):
            self.table.insertRow(r_idx)
            # ID (Numérico)
            self.table.setItem(r_idx, 0, NumericItem(str(row[0])))
            # Nombre
            self.table.setItem(r_idx, 1, QTableWidgetItem(row[1]))
            # Abreviatura
            self.table.setItem(r_idx, 2, QTableWidgetItem(row[2]))

        self.table.setSortingEnabled(True)
        self.aplicar_filtros()  # Re-aplicar filtros si había texto escrito

    def aplicar_filtros(self):
        rows = self.table.rowCount()
        for row in range(rows):
            mostrar = True
            for col, inp in self.filtros.items():
                texto_filtro = inp.text().lower().strip()
                if not texto_filtro:
                    continue
                item = self.table.item(row, col)
                if item:
                    if texto_filtro not in item.text().lower():
                        mostrar = False
                        break
            self.table.setRowHidden(row, not mostrar)

    # --- OPERACIONES CRUD ---
    def abrir_crear(self):
        dlg = UnidadDialog(self.db, parent=self)
        if dlg.exec_():
            self.cargar_datos()

    def abrir_editar(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(
                self, "Aviso", "Seleccione una unidad para editar."
            )

        id_unidad = self.table.item(row, 0).text()
        nombre = self.table.item(row, 1).text()
        abrev = self.table.item(row, 2).text()

        data = {"id": id_unidad, "nombre": nombre, "abreviatura": abrev}

        dlg = UnidadDialog(self.db, data=data, parent=self)
        if dlg.exec_():
            self.cargar_datos()

    def eliminar(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(
                self, "Aviso", "Seleccione una unidad para eliminar."
            )

        id_unidad = self.table.item(row, 0).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar",
            "¿Eliminar esta unidad de medida?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            try:
                self.db.execute_query(
                    "DELETE FROM unidades_medida WHERE id=?", (id_unidad,)
                )
                self.cargar_datos()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"No se puede eliminar (probablemente esté en uso).\n{e}",
                )


# --- DIALOGO FORMULARIO ---
class UnidadDialog(QDialog):
    def __init__(self, db, data=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.data = data
        self.setWindowTitle("Detalle de Unidad")
        self.setFixedWidth(350)

        layout = QFormLayout()

        self.txt_nombre = QLineEdit()
        self.txt_abrev = QLineEdit()

        if data:
            self.txt_nombre.setText(data["nombre"])
            self.txt_abrev.setText(data["abreviatura"])

        layout.addRow("Nombre (ej. Kilogramo):", self.txt_nombre)
        layout.addRow("Abreviatura (ej. kg):", self.txt_abrev)

        btn_save = QPushButton("Guardar")
        btn_save.setProperty("class", "btn-success")
        btn_save.clicked.connect(self.guardar)
        layout.addRow(btn_save)

        self.setLayout(layout)

    def guardar(self):
        nom = self.txt_nombre.text().strip()
        abr = self.txt_abrev.text().strip()

        if not nom or not abr:
            return QMessageBox.warning(
                self, "Error", "Todos los campos son obligatorios"
            )

        try:
            if self.data:
                # Update
                self.db.execute_query(
                    "UPDATE unidades_medida SET nombre=?, abreviatura=? WHERE id=?",
                    (nom, abr, self.data["id"]),
                )
            else:
                # Insert
                self.db.execute_query(
                    "INSERT INTO unidades_medida (nombre, abreviatura) VALUES (?,?)",
                    (nom, abr),
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
